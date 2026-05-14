import cv2
import mediapipe as mp
class FaceCapture:
    def __init__(self):
        self.detector=mp.solutions.face_detection.FaceDetection(model_selection=0,min_detection_confidence=0.5)
    def capture(self,frame,bbox,output_path:str)->bool:
        x1,y1,x2,y2=bbox
        crop=frame[max(y1,0):max(y2,0),max(x1,0):max(x2,0)]
        if crop.size==0:return False
        result=self.detector.process(cv2.cvtColor(crop,cv2.COLOR_BGR2RGB))
        if not result.detections:return False
        h,w,_=crop.shape; rel=result.detections[0].location_data.relative_bounding_box
        fx1,fy1=int(rel.xmin*w),int(rel.ymin*h); fw,fh=int(rel.width*w),int(rel.height*h)
        face=crop[max(fy1,0):max(fy1+fh,0),max(fx1,0):max(fx1+fw,0)]
        if face.size==0:return False
        cv2.imwrite(output_path,cv2.resize(face,(256,256))); return True
