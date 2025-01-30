import os
import cv2
import time
import numpy as np
import requests
from ultralytics import YOLO

# RTSP-ссылка камеры (замени на свою)
RTSP_URL = "rtsp://user:password@camera_ip:port/stream"

# PHP сервер
PHP_SERVER_URL = "http://php-app:8080/detect"

# Загружаем модель YOLO
model = YOLO("yolov8n.pt")

def detect_car(frame):
    """Функция обработки кадра"""
    height, width, _ = frame.shape
    results = model(frame)
    cars_detected = []

    def is_facing_forward(x1, y1, x2, y2):
        """ Проверка переднего вида автомобиля """
        w = x2 - x1
        h = y2 - y1
        aspect_ratio = w / h
        return 0.4 < aspect_ratio < 1.0

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = box.conf[0].item()
            class_id = int(box.cls[0].item())

            if class_id in [2, 5, 7]:
                area = (x2 - x1) * (y2 - y1)
                x_center = (x1 + x2) / 4

                if is_facing_forward(x1, y1, x2, y2) and (0.2 * width < x_center < 0.8 * width):
                    score = y2 * 2 + area * 0.1
                    cars_detected.append((x1, y1, x2, y2, confidence, class_id, area, score))

    if not cars_detected:
        return None  # Нет машины, ничего не отправляем

    # 1. Отфильтровываем маленькие машины
    filtered_cars = [c for c in cars_detected if c[6] > 0.05 * (width * height)]

    if filtered_cars:
        tallest_car = max(filtered_cars, key=lambda c: c[3] - c[1])
        closest_car = max(filtered_cars, key=lambda c: (c[3] - c[1]) * 3 + (height - c[1]) * 2)

        if (closest_car[3] - closest_car[1]) < 0.8 * (tallest_car[3] - tallest_car[1]):
            closest_car = tallest_car
    else:
        closest_car = max(cars_detected, key=lambda c: c[6])

    x1, y1, x2, y2, confidence, class_id, area, _ = closest_car
    label = "Car" if class_id == 2 else "Truck" if class_id == 7 else "Bus"

    # Сохраняем изображение
    output_path = "/app/detected_image.jpg"
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
    cv2.putText(frame, f"{label} {confidence:.2f}", (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.imwrite(output_path, frame)

    return output_path

def process_stream():
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        print("Ошибка: Не удалось подключиться к RTSP-потоку!")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Ошибка: не удалось считать кадр!")
            break

        detected_image = detect_car(frame)

        if detected_image:
            # Отправляем в PHP-контейнер
            with open(detected_image, 'rb') as img_file:
                response = requests.post(PHP_SERVER_URL, files={'file': img_file})

            print(f"Отправлен кадр в PHP. Ответ: {response.status_code}")

        time.sleep(2)

if __name__ == "__main__":
    process_stream()