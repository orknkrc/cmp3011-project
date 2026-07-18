#vehicle detection with YOLOv8
#which vehicles are in this frame?

from ultralytics import YOLO

#vehicle class ids in the COCO dataset. these ids are fixed because YOLOv8 model is trained on COCO.
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

class VehicleDetector:
    def __init__(self, model_path="yolov8n.pt", conf_threshold=0.4):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def detect(self, frame):
        #verbose=False dont log to the terminal for every frame
        results = self.model(frame, verbose=False)[0]

        boxes = []
        for box in results.boxes:
            class_id = int(box.cls[0])
            score = float(box.conf[0])

            if class_id not in VEHICLE_CLASSES: #just vehicles
                continue
            #drop low confidence detections for reducing false positives
            if score < self.conf_threshold:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            boxes.append((int(x1), int(y1), int(x2), int(y2), VEHICLE_CLASSES[class_id]))

        return boxes

#computes the centre point of a box
def box_to_centroid(box):
    x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
    cx = int((x1 + x2) / 2)
    cy = int((y1 + y2) / 2)
    return (cx, cy)
