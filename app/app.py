from flask import Flask, request, jsonify
import requests
import os
import json
from detector import detect_car

app = Flask(__name__)

SMARTY_API_URL = "https://smarty.mail.ru/api/v1/objects/detect"
TARGET_API_URL = "https://api.krosspark.ru/send_number"
OAUTH_TOKEN = os.getenv("OAUTH_TOKEN")

@app.route("/detect", methods=["POST"])
def detect():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    image = request.files["file"]
    image_path = f"/tmp/{image.filename}"
    image.save(image_path)

    car_detected, processed_image_path = detect_car(image_path)

    if not car_detected:
        return jsonify({"message": "No suitable car detected"}), 200

    with open(processed_image_path, "rb") as img_file:
        files = {"file": (processed_image_path, img_file, "image/jpeg")}
        data = {
            "meta": '{"mode": ["car_number"], "images": [{"name": "file"}]}'
        }
        print(OAUTH_TOKEN)
        headers = {"Authorization": f"Bearer {OAUTH_TOKEN}"}
        url = f"{SMARTY_API_URL}?oauth_token={OAUTH_TOKEN}&oauth_provider=mcs"
        response = requests.post(url, headers=headers, files=files, data=data)

    print("🔍 RAW SMARTY RESPONSE:", response.text)  # Логируем сырой ответ

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        print("❌ Ошибка: SMARTY вернул некорректный JSON!")
        return jsonify({"error": "Invalid JSON response from SMARTY", "raw_response": response.text}), 500

    print("✅ Ответ SMARTY в формате JSON:", response_json)

    # Проверяем, есть ли "body" в ответе
    body = response_json.get("body")
    if body is None:
        return jsonify({"error": "Некорректный ответ: отсутствует body"}), 500

    # Если "body" пришел строкой, парсим его в JSON
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            print("❌ Ошибка: 'body' не является корректным JSON:", body)
            return jsonify({"error": "Некорректное тело ответа от SMARTY", "raw_body": body}), 500

    # Проверяем наличие "car_number_labels"
    car_number_labels = body.get("car_number_labels", [])

    print('Тест', car_number_labels)

    if not car_number_labels or car_number_labels[0].get("status") != 0:
        return jsonify({"message": "Номер автомобиля не обнаружен"}), 200

    # Исправленный доступ к номеру автомобиля
    car_number = car_number_labels[0]["labels"][0]["eng"]

    # Отправляем номер автомобиля в целевой API
    payload = {"car_number": car_number}
    target_response = requests.post(TARGET_API_URL, json=payload)

    if target_response.status_code == 200:
        return jsonify({"message": "Number", "car_number": car_number}), 200
    else:
        return jsonify({"error": "Не удалось отправить номер автомобиля"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
