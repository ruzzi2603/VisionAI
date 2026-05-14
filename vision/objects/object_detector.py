from ultralytics import YOLO

# Labels from COCO (YOLOv8 default model names).
RELEVANT_OBJECTS = {
    "person",
    "cell phone",
    "laptop",
    "backpack",
    "handbag",
    "suitcase",
    "bottle",
    "knife",
    "scissors",
    "dog",
    "cat",
    "bird",
    "horse",
    "cow",
}

SUSPICIOUS_OBJECTS = {"knife", "scissors"}


class ObjectDetector:
    def __init__(self, model_path: str = "yolov8n.pt", conf: float = 0.35, imgsz: int = 640) -> None:
        self.model = YOLO(model_path)
        self.conf = conf
        self.imgsz = imgsz

    def detect(self, frame):
        out = []
        for result in self.model(frame, conf=self.conf, imgsz=self.imgsz, verbose=False):
            for box in result.boxes:
                cls = int(box.cls[0])
                label = self.model.names.get(cls, str(cls))
                if label not in RELEVANT_OBJECTS:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                out.append(
                    {
                        "label": label,
                        "confidence": float(box.conf[0]),
                        "bbox": [x1, y1, x2 - x1, y2 - y1],
                        "is_suspicious": label in SUSPICIOUS_OBJECTS,
                    }
                )
        return out
