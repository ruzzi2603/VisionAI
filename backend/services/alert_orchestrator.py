import os
from django.conf import settings
from apps.alerts.models import Alert
from apps.events.models import Event, Notification, EventStatus
from services.realtime import broadcast_alert
from services.telegram_service import TelegramService


def _build_message(event: Event) -> str:
    start_time = event.started_at.strftime("%H:%M:%S") if event.started_at else "-"
    end_time = event.ended_at.strftime("%H:%M:%S") if event.ended_at else "ainda acontecendo"
    camera_name = event.camera.name
    stream_link = f"{settings.LIVE_VIEW_BASE_URL}/{event.camera.id}"
    status_label = dict(EventStatus.choices).get(event.status, event.status)
    return (
        "ALERTA - VisionGuard AI\n\n"
        f"Tipo: {event.event_type}\n"
        f"Nivel: {event.risk_level}\n"
        f"Status: {status_label}\n"
        f"Camera: {camera_name}\n"
        f"Inicio: {start_time}\n"
        f"Fim: {end_time}\n\n"
        f"Ver ao vivo: {stream_link}"
    )


def handle_new_event(event: Event) -> Alert | None:
    if event.status == EventStatus.ONGOING:
        return None

    message = _build_message(event)
    alert = Alert.objects.create(
        event=event,
        risk_level=event.risk_level,
        message=message,
    )

    payload = {
        "alert_id": alert.id,
        "event_id": event.id,
        "event_type": event.event_type,
        "risk_level": event.risk_level,
        "status": event.status,
        "camera_id": event.camera_id,
        "camera_name": event.camera.name,
        "timestamp": event.created_at.isoformat(),
        "started_at": event.started_at.isoformat() if event.started_at else None,
        "ended_at": event.ended_at.isoformat() if event.ended_at else None,
        "is_active": event.is_active,
        "message": alert.message,
        "image_url": event.image.url if event.image else None,
        "video_url": event.video.url if event.video else None,
    }
    broadcast_alert(payload)
    Notification.objects.create(event=event, channel="websocket", status="sent", details=payload)

    telegram = TelegramService()
    image_path = event.image.path if event.image and os.path.exists(event.image.path) else None
    sent = telegram.send_alert(message=message, image_path=image_path)
    Notification.objects.create(
        event=event,
        channel="telegram",
        status="sent" if sent else "skipped",
        details={"has_image": bool(image_path)},
    )
    return alert
