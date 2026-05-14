from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_alert(payload: dict) -> None:
    try:
        layer = get_channel_layer()
        async_to_sync(layer.group_send)("alerts", {"type": "alert.message", "payload": payload})
    except Exception:
        # Do not break alert persistence if realtime infra is unavailable.
        return
