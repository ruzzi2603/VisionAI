import sys 
from pathlib import Path 
sys.path.insert(0, str(Path(__file__).resolve().parent)) 
from vision.main import YOLO_MODEL_PATH, RECORDINGS_DIR, VIDEO_BACKEND 
from vision.tracking.tracker import PersonTracker 
from vision.main import PersonDetector, ObjectDetector 
print('MODEL_PATH', YOLO_MODEL_PATH) 
print('RECORDINGS_DIR', RECORDINGS_DIR) 
print('VIDEO_BACKEND', VIDEO_BACKEND) 
tracker=PersonTracker() 
print('TRACKER OK', tracker.tracker.__class__) 
person=PersonDetector(str(YOLO_MODEL_PATH), conf=0.45, imgsz=640) 
object=ObjectDetector(str(YOLO_MODEL_PATH), conf=0.4, imgsz=640) 
