from collections import defaultdict, deque
import math
class BehaviorAnalyzer:
    def __init__(self, history_size: int = 30):
        self.history=defaultdict(lambda:deque(maxlen=history_size))
    def analyze(self,track_id:int,center:tuple[int,int],people_count:int,sensitive_area:bool):
        self.history[track_id].append(center)
        pts=list(self.history[track_id])
        if len(pts)<2:return []
        dx=pts[-1][0]-pts[-2][0]; dy=pts[-1][1]-pts[-2][1]; speed=math.sqrt(dx*dx+dy*dy)
        ev=[]
        if speed>25: ev.append({"type":"suspicious_run","speed":speed})
        if speed<1.5 and len(pts)>=20: ev.append({"type":"loitering","speed":speed})
        if people_count>=6: ev.append({"type":"crowd","speed":speed})
        if sensitive_area and speed<1.0 and len(pts)>=12: ev.append({"type":"sensitive_area_stop","speed":speed})
        return ev
