from services.enums import RiskLevel


def classify_risk(event_type: str, object_labels: list[str], people_count: int, speed: float) -> str:
    if any(label in {"knife", "gun", "weapon"} for label in object_labels):
        return RiskLevel.CRITICAL
    if event_type == "suspicious_object_in_hand":
        return RiskLevel.CRITICAL
    if event_type == "suspicious_object":
        return RiskLevel.HIGH
    if event_type in {"suspicious_run", "anomalous_movement"} and speed > 3.2:
        return RiskLevel.HIGH
    if event_type in {"crowd", "loitering", "sensitive_area_stop"} and people_count >= 5:
        return RiskLevel.HIGH
    if people_count >= 3:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
