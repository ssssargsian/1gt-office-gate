from detector import detect_car

image_path = "car_detect.jpg"
car_detected, processed_path = detect_car(image_path)

print("Машина найдена:", car_detected)
if car_detected:
    print("Обработанное изображение сохранено в:", processed_path)
