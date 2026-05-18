from django.conf import settings
import json
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Event
from .serializers import EventSerializer, VisionIngestSerializer
from services.alert_orchestrator import handle_new_event


class IsVisionService(permissions.BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get("X-Vision-Token", "")
        return bool(token) and token == settings.VISION_INGEST_TOKEN


class EventViewSet(viewsets.ModelViewSet):
 queryset=Event.objects.select_related('camera','suspect').prefetch_related('detections')
 serializer_class=EventSerializer


class VisionIngestView(APIView):
    permission_classes = [IsVisionService]

    def _normalize_field(self, payload, field):
        value = payload.get(field)
        if isinstance(value, str):
            try:
                payload[field] = json.loads(value)
            except json.JSONDecodeError:
                return
        elif isinstance(value, (list, tuple)):
            if field == "object_labels":
                payload[field] = [str(item) for item in value]
            elif field == "metadata":
                if len(value) == 1 and isinstance(value[0], str):
                    try:
                        payload[field] = json.loads(value[0])
                    except json.JSONDecodeError:
                        payload[field] = {}
            elif field == "detections":
                if len(value) == 1 and isinstance(value[0], str):
                    try:
                        payload[field] = json.loads(value[0])
                    except json.JSONDecodeError:
                        pass

    def post(self, request):
        payload = request.data.copy()
        for field in ("object_labels", "metadata", "detections"):
            self._normalize_field(payload, field)
        serializer = VisionIngestSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        alert = handle_new_event(event)
        return Response(
            {
                "event_id": event.id,
                "alert_id": alert.id if alert else None,
                "risk_level": event.risk_level,
                "status": event.status,
            },
            status=status.HTTP_201_CREATED,
        )
