from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")

def detect_intrusion(image_path):
    results = model(image_path)
    result_img = results[0].plot()
    return result_img