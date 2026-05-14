import cv2


CLASS_COLORS = {
    "person": (0, 220, 0),
    "cell phone": (255, 140, 0),
    "laptop": (255, 140, 0),
    "backpack": (0, 200, 255),
    "handbag": (0, 200, 255),
    "suitcase": (0, 200, 255),
    "knife": (0, 0, 255),
    "scissors": (0, 0, 255),
    "dog": (200, 0, 200),
    "cat": (200, 0, 200),
    "bird": (200, 0, 200),
}


def _draw_box(frame, bbox, label: str, color):
    x, y, w, h = bbox
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    cv2.rectangle(frame, (x, y - 22), (x + 180, y), color, -1)
    cv2.putText(frame, label, (x + 4, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (15, 15, 15), 1, cv2.LINE_AA)


def draw_annotations(frame, tracks, people, objects, event_lines: list[str]):
    person_by_track = []
    for track in tracks:
        x1, y1, x2, y2 = track["bbox"]
        bbox = [x1, y1, x2 - x1, y2 - y1]
        label = f"pessoa | ID {track['track_id']}"
        _draw_box(frame, bbox, label, (0, 220, 0))
        person_by_track.append({"track_id": track["track_id"], "bbox": bbox})

    for obj in objects:
        label = obj["label"]
        conf = obj.get("confidence", 0.0)
        draw_label = f"{label} {conf:.2f}"
        color = CLASS_COLORS.get(label, (255, 255, 0))
        if obj.get("is_suspicious"):
            color = (0, 0, 255)
        _draw_box(frame, obj["bbox"], draw_label, color)

    y = 24
    for line in event_lines[-6:]:
        cv2.putText(frame, line, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 245, 255), 2, cv2.LINE_AA)
        y += 24
