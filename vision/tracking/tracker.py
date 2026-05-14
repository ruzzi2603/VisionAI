from deep_sort_realtime.deepsort_tracker import DeepSort
class PersonTracker:
    def __init__(self) -> None:
        self.tracker=DeepSort(max_age=30)
    def update(self,detections,frame):
        ds=[(d["bbox"],d["confidence"],d["label"]) for d in detections]
        tracks=self.tracker.update_tracks(ds,frame=frame)
        out=[]
        for t in tracks:
            if t.is_confirmed():
                out.append({"track_id":t.track_id,"bbox":[int(v) for v in t.to_ltrb()]})
        return out
