from ultralytics import YOLO

model = YOLO("yolov8n.pt")

THREAT_CLASSES = ["person", "car", "motorcycle", "bus", "truck"]

def detect_intrusion(image_path):

    results = model(image_path)

    detected_classes = []

    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        class_name = model.names[cls_id]
        detected_classes.append(class_name)

    intrusion = any(cls in THREAT_CLASSES for cls in detected_classes)

    plotted = results[0].plot()

    return plotted, intrusion, detected_classes
