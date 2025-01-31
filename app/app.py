from flask import Flask, request, jsonify
import requests
import os
import json
from detector import detect_car

app = Flask(__name__)

SMARTY_API_URL = "https://smarty.mail.ru/api/v1/objects/detect"
WORK_API = "https://work.1gt.ru/api/cardetect/open-gate"

WORK_API_TOKEN = os.getenv("WORK_API_TOKEN")
SMARTY_API_TOKEN = os.getenv("SMARTY_API_TOKEN")

if not SMARTY_API_TOKEN:
    print("Ошибка: SMARTY_API_TOKEN не загружен!")
if not WORK_API_TOKEN:
    print("Ошибка: WORK_API_TOKEN не загружен!")

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
        headers = {"Authorization": f"Bearer {SMARTY_API_TOKEN}"}
        url = f"{SMARTY_API_URL}?oauth_token={SMARTY_API_TOKEN}&oauth_provider=mcs"
        response = requests.post(url, headers=headers, files=files, data=data)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        print(response_json)
        return jsonify({"error": "Invalid JSON response from SMARTY"}), 500

    body = response_json.get("body")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            print('NTRC',response_json)
            return jsonify({"error": "Invalid body JSON from SMARTY"}), 500

    car_number_labels = body.get("car_number_labels", [])
    if not car_number_labels or car_number_labels[0].get("status") != 0:
        return jsonify({"message": "Car number not detected"}), 200

    car_number = car_number_labels[0]["labels"][0]["eng"]

    headers = {
        "Authorization": f"Bearer {WORK_API_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = f"carNumber={car_number}"

    print("➡️ Отправка в WORK API:")
    print(f"URL: {WORK_API}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")

    target_response = requests.post(WORK_API, headers=headers, data=data)
    print(f"⬅️ Ответ от WORK API: {target_response.status_code}")
    print(target_response.text)

    if target_response.status_code == 204:
        return jsonify({"message": "Car number sent successfully", "car_number": car_number}), 200
    else:
        return jsonify({"error": target_response.text}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
