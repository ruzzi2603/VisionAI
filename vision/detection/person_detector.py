from ultralytics import YOLO
class PersonDetector:
    def __init__(self, model_path: str = "yolov8n.pt", conf: float = 0.4, imgsz: int = 640) -> None:
        self.model = YOLO(model_path)
        self.conf = conf
        self.imgsz = imgsz
    def detect(self, frame):
        out=[]
        results=self.model(frame,classes=[0],conf=self.conf,imgsz=self.imgsz,verbose=False)
        for r in results:
            for b in r.boxes:
                x1,y1,x2,y2=map(int,b.xyxy[0].tolist())
                out.append({"bbox":[x1,y1,x2-x1,y2-y1],"confidence":float(b.conf[0]),"label":"person"})
        return out
