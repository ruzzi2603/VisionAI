import json
import os
from datetime import datetime

import cv2
import requests

from behavior.analyzer import BehaviorAnalyzer
from detection.person_detector import PersonDetector
from face_capture.capture import FaceCapture
from objects.object_detector import ObjectDetector
from tracking.tracker import PersonTracker
from visualization.annotator import draw_annotations

API_URL = os.getenv("VISION_API_URL", "http://127.0.0.1:8000/api/events/ingest/")
VISION_TOKEN = os.getenv("VISION_INGEST_TOKEN", "visionguard-local-token")
CAMERA_CODE = os.getenv("VISION_CAMERA_CODE", "CAM-001")
SENSITIVE_AREA = os.getenv("VISION_SENSITIVE_AREA", "False").lower() == "true"
EVENT_END_TIMEOUT_SECONDS = int(os.getenv("VISION_EVENT_END_TIMEOUT_SECONDS", "4"))
SCENE_COOLDOWN_SECONDS = int(os.getenv("VISION_SCENE_COOLDOWN_SECONDS", "8"))
RECORDINGS_DIR = os.getenv("VISION_RECORDINGS_DIR", "captures/recordings")
PROCESS_EVERY_N_FRAMES = int(os.getenv("VISION_PROCESS_EVERY_N_FRAMES", "2"))
CAPTURE_WIDTH = int(os.getenv("VISION_CAPTURE_WIDTH", "960"))
CAPTURE_HEIGHT = int(os.getenv("VISION_CAPTURE_HEIGHT", "540"))


def _to_detection_rows(items: list[dict]) -> list[dict]:
    rows = []
    for item in items:
        x, y, w, h = item["bbox"]
        rows.append(
            {
                "label": item["label"],
                "confidence_score": float(item.get("confidence", 0.0)),
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
            }
        )
    return rows


def _save_evidence_frame(frame, tag: str) -> str:
    os.makedirs("captures/events", exist_ok=True)
    path = f"captures/events/{tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    cv2.imwrite(path, frame)
    return path


def _start_event_recorder(event_key: str, frame_shape):
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    safe_key = event_key.replace(":", "_")
    path = os.path.join(RECORDINGS_DIR, f"{safe_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
    h, w = frame_shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, 20.0, (w, h))
    return writer, path


def _post_event(
    *,
    external_event_id: str,
    event_type: str,
    status: str,
    speed: float,
    people_count: int,
    person_dets: list[dict],
    object_dets: list[dict],
    image_path: str | None,
    video_path: str | None = None,
) -> None:
    payload = {
        "camera_code": CAMERA_CODE,
        "external_event_id": external_event_id,
        "event_type": event_type,
        "status": status,
        "confidence_score": max([d.get("confidence", 0.0) for d in person_dets + object_dets] + [0.0]),
        "people_count": people_count,
        "speed": float(speed),
        "object_labels": [o["label"] for o in object_dets],
        "metadata": {"pipeline_version": "1.1.0"},
        "detections": _to_detection_rows(person_dets + object_dets),
    }
    headers = {"X-Vision-Token": VISION_TOKEN}
    try:
        if (image_path and os.path.exists(image_path)) or (video_path and os.path.exists(video_path)):
            files = {}
            if image_path and os.path.exists(image_path):
                files["image"] = open(image_path, "rb")
            if video_path and os.path.exists(video_path):
                files["video"] = open(video_path, "rb")
            try:
                response = requests.post(
                    API_URL,
                    data={
                        **payload,
                        "object_labels": json.dumps(payload["object_labels"]),
                        "metadata": json.dumps(payload["metadata"]),
                        "detections": json.dumps(payload["detections"]),
                    },
                    files=files,
                    headers=headers,
                    timeout=12,
                )
                if response.status_code >= 400:
                    print(f"[vision] ingest failed ({response.status_code}): {response.text[:200]}")
            finally:
                for f in files.values():
                    f.close()
        else:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=8)
            if response.status_code >= 400:
                print(f"[vision] ingest failed ({response.status_code}): {response.text[:200]}")
    except requests.RequestException:
        return


def _bbox_center(bbox: list[int]) -> tuple[int, int]:
    x, y, w, h = bbox
    return x + w // 2, y + h // 2


def _is_suspicious_object_in_hand(track_bbox_xyxy: list[int], object_bbox_xywh: list[int]) -> bool:
    x1, y1, x2, y2 = track_bbox_xyxy
    cx, cy = _bbox_center(object_bbox_xywh)
    hand_region_x1 = x1 + int((x2 - x1) * 0.15)
    hand_region_x2 = x1 + int((x2 - x1) * 0.85)
    hand_region_y1 = y1 + int((y2 - y1) * 0.20)
    hand_region_y2 = y1 + int((y2 - y1) * 0.70)
    return hand_region_x1 <= cx <= hand_region_x2 and hand_region_y1 <= cy <= hand_region_y2


def run_pipeline(source=0):
    person_detector = PersonDetector(os.getenv("YOLO_MODEL_PATH", "yolov8n.pt"), conf=0.45, imgsz=640)
    object_detector = ObjectDetector(os.getenv("YOLO_MODEL_PATH", "yolov8n.pt"), conf=0.4, imgsz=640)
    tracker = PersonTracker()
    behavior = BehaviorAnalyzer()
    face_capture = FaceCapture()
    cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 30)

    active_events = {}  # event_key -> {"last_seen": datetime, "writer": VideoWriter, "video_path": str}
    scene_last_alert_at = None
    event_feed = []
    frame_idx = 0
    last_people = []
    last_objects = []
    last_tracks = []

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame_idx += 1
        now = datetime.now()
        run_detection = frame_idx % max(1, PROCESS_EVERY_N_FRAMES) == 0
        if run_detection:
            people = person_detector.detect(frame)
            objects = object_detector.detect(frame)
            tracks = tracker.update(people, frame)
            last_people, last_objects, last_tracks = people, objects, tracks
        else:
            people, objects, tracks = last_people, last_objects, last_tracks

        suspicious_scene_objects = [obj for obj in objects if obj.get("is_suspicious")]
        seen_event_keys = set()
        local_event_lines = []

        for track in tracks:
            x1, y1, x2, y2 = track["bbox"]
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            behaviors = behavior.analyze(track["track_id"], center, len(tracks), SENSITIVE_AREA)
            suspicious_in_hand = [
                obj for obj in objects if obj.get("is_suspicious") and _is_suspicious_object_in_hand(track["bbox"], obj["bbox"])
            ]
            if suspicious_in_hand:
                behaviors.append({"type": "suspicious_object_in_hand", "speed": 0.0})

            for behavior_event in behaviors:
                event_type = behavior_event["type"]
                event_key = f"{CAMERA_CODE}:{track['track_id']}:{event_type}"
                seen_event_keys.add(event_key)
                is_new = event_key not in active_events
                if is_new:
                    writer, video_path = _start_event_recorder(event_key, frame.shape)
                    active_events[event_key] = {"last_seen": now, "writer": writer, "video_path": video_path}
                else:
                    active_events[event_key]["last_seen"] = now

                if is_new:
                    evidence = _save_evidence_frame(frame, f"{event_type}_{track['track_id']}")
                    os.makedirs("captures/suspects", exist_ok=True)
                    face_capture.capture(
                        frame,
                        track["bbox"],
                        f"captures/suspects/face_{track['track_id']}_{now.strftime('%Y%m%d_%H%M%S')}.jpg",
                    )
                    relevant_objects = suspicious_in_hand if event_type == "suspicious_object_in_hand" else objects
                    _post_event(
                        external_event_id=event_key,
                        event_type=event_type,
                        status="started",
                        speed=behavior_event.get("speed", 0.0),
                        people_count=len(tracks),
                        person_dets=people,
                        object_dets=relevant_objects,
                        image_path=evidence,
                        video_path=None,
                    )
                    local_event_lines.append(f"{event_type} iniciado | ID {track['track_id']}")

        if suspicious_scene_objects:
            scene_key = f"{CAMERA_CODE}:scene:suspicious_object"
            scene_is_new = scene_key not in active_events
            if scene_is_new or not scene_last_alert_at or (now - scene_last_alert_at).total_seconds() >= SCENE_COOLDOWN_SECONDS:
                seen_event_keys.add(scene_key)
                if scene_is_new:
                    writer, video_path = _start_event_recorder(scene_key, frame.shape)
                    active_events[scene_key] = {"last_seen": now, "writer": writer, "video_path": video_path}
                else:
                    active_events[scene_key]["last_seen"] = now
                scene_last_alert_at = now
                evidence = _save_evidence_frame(frame, "scene_suspicious_object")
                _post_event(
                    external_event_id=scene_key,
                    event_type="suspicious_object",
                    status="started" if scene_is_new else "ongoing",
                    speed=0.0,
                    people_count=len(tracks),
                    person_dets=people,
                    object_dets=suspicious_scene_objects,
                    image_path=evidence,
                    video_path=None,
                )
                local_event_lines.append("objeto suspeito detectado na cena")

        for info in active_events.values():
            writer = info.get("writer")
            if writer:
                writer.write(frame)

        expired = []
        for event_key, info in active_events.items():
            if event_key in seen_event_keys:
                continue
            if (now - info["last_seen"]).total_seconds() >= EVENT_END_TIMEOUT_SECONDS:
                parts = event_key.split(":")
                event_type = parts[-1]
                if info.get("writer"):
                    info["writer"].release()
                _post_event(
                    external_event_id=event_key,
                    event_type=event_type,
                    status="ended",
                    speed=0.0,
                    people_count=len(tracks),
                    person_dets=people,
                    object_dets=objects,
                    image_path=None,
                    video_path=info.get("video_path"),
                )
                local_event_lines.append(f"{event_type} encerrado")
                expired.append(event_key)
        for key in expired:
            active_events.pop(key, None)

        event_feed.extend(local_event_lines)
        draw_annotations(frame, tracks=tracks, people=people, objects=objects, event_lines=event_feed)
        cv2.imshow("VisionGuard AI", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    for info in active_events.values():
        if info.get("writer"):
            info["writer"].release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_pipeline(0)
