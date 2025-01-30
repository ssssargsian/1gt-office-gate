import cv2
import os
import numpy as np
from ultralytics import YOLO
from google.colab.patches import cv2_imshow

# Загружаем модель YOLO
model = YOLO("yolov8n.pt")

# Указываем путь к изображению
IMAGE_PATH = "/content/photo_2024-11-16_11-30-46.jpg"

if not os.path.exists(IMAGE_PATH):
    print(f"Файл {IMAGE_PATH} не найден!")
    exit()

image = cv2.imread(IMAGE_PATH)
height, width, _ = image.shape

# Запускаем распознавание
results = model(image)

# Храним найденные автомобили
cars_detected = []

def is_facing_forward(x1, y1, x2, y2):
    """ Улучшенная проверка переднего вида автомобиля """
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
            x_center = (x1 + x2) / 2  

            # **Фильтр: только машины в центральной зоне кадра**
            if is_facing_forward(x1, y1, x2, y2) and (0.2 * width < x_center < 0.8 * width):
                # Добавляем вес `y2 * 2 + area * 0.1` 
                score = y2 * 2 + area * 0.1
                cars_detected.append((x1, y1, x2, y2, confidence, class_id, area, score))

# **ШАГ 1: Выбираем машину, которая и большая, и ближе к нижней части экрана**
if cars_detected:
    # Учитываем `y2` и `area`, но **только в центральной зоне**
    closest_car = max(cars_detected, key=lambda c: c[7])

    x1, y1, x2, y2, confidence, class_id, _, _ = closest_car
    label = "Car" if class_id == 2 else "Truck" if class_id == 7 else "Bus"
    color = (0, 255, 0)

    cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)
    cv2.putText(image, f"{label} {confidence:.2f}", (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    print(f"Выбран ближайший автомобиль: {label}, Y2={y2}, Area={_}")

cv2_imshow(image)
output_path = "/content/detected_image.jpg"
cv2.imwrite(output_path, image)
print(f"Обработанное изображение сохранено: {output_path}")
