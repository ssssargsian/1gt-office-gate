import cv2
import numpy as np
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

def detect_car(image_path):
    image = cv2.imread(image_path)
    height, width, _ = image.shape
    results = model(image)

    cars_detected = []

    def is_facing_forward(x1, y1, x2, y2):
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

                if is_facing_forward(x1, y1, x2, y2) and (0.2 * width < x_center < 0.8 * width):
                    score = y2 * 2 + area * 0.1
                    cars_detected.append((x1, y1, x2, y2, confidence, class_id, area, score))

    if not cars_detected:
        return False, None

    closest_car = max(cars_detected, key=lambda c: c[7])
    x1, y1, x2, y2, confidence, class_id, _, _ = closest_car
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)

    processed_path = f"/tmp/detected_{image_path.split('/')[-1]}"
    cv2.imwrite(processed_path, image)

    return True, processed_path