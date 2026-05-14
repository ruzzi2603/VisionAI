from rest_framework import serializers
from django.utils import timezone
from .models import Event, Detection, Notification, EventStatus
from apps.cameras.models import Camera
from services.risk_engine import classify_risk
class DetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Detection
        fields = "__all__"
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
class EventSerializer(serializers.ModelSerializer):
    detections = DetectionSerializer(many=True, read_only=True)
    class Meta:
        model = Event
        fields = "__all__"


class VisionDetectionSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=120)
    confidence_score = serializers.FloatField()
    x = serializers.IntegerField()
    y = serializers.IntegerField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class VisionIngestSerializer(serializers.Serializer):
    camera_code = serializers.CharField(max_length=64)
    external_event_id = serializers.CharField(max_length=140, required=False, allow_blank=True)
    event_type = serializers.CharField(max_length=120)
    status = serializers.ChoiceField(choices=EventStatus.choices, default=EventStatus.STARTED)
    confidence_score = serializers.FloatField(default=0.0)
    people_count = serializers.IntegerField(min_value=0, default=0)
    speed = serializers.FloatField(default=0.0)
    object_labels = serializers.ListField(child=serializers.CharField(max_length=120), default=list)
    metadata = serializers.JSONField(default=dict)
    detections = VisionDetectionSerializer(many=True, required=False)
    image = serializers.ImageField(required=False, allow_null=True)
    video = serializers.FileField(required=False, allow_null=True)

    def validate_camera_code(self, value: str) -> str:
        if not Camera.objects.filter(camera_code=value).exists():
            raise serializers.ValidationError("Camera nao encontrada para o camera_code informado.")
        return value

    def create(self, validated_data):
        camera_code = validated_data["camera_code"]
        external_event_id = validated_data.get("external_event_id", "")
        detections = validated_data.pop("detections", [])
        object_labels = validated_data.pop("object_labels", [])
        people_count = validated_data.pop("people_count", 0)
        speed = validated_data.pop("speed", 0.0)
        event_type = validated_data["event_type"]
        event_status = validated_data.get("status", EventStatus.STARTED)
        risk = classify_risk(event_type, object_labels, people_count, speed)
        camera = Camera.objects.get(camera_code=camera_code)

        metadata = validated_data.get("metadata", {})
        metadata.update(
            {
                "people_count": people_count,
                "speed": speed,
                "object_labels": object_labels,
                "source": "vision-pipeline",
            }
        )

        if external_event_id:
            event = Event.objects.filter(external_event_id=external_event_id, camera=camera).order_by("-id").first()
        else:
            event = None

        if event and event_status in {EventStatus.ONGOING, EventStatus.ENDED}:
            event.confidence_score = max(event.confidence_score, validated_data.get("confidence_score", 0.0))
            event.metadata = metadata
            if validated_data.get("image"):
                event.image = validated_data.get("image")
            if validated_data.get("video"):
                event.video = validated_data.get("video")
            if event_status == EventStatus.ENDED:
                event.status = EventStatus.ENDED
                event.ended_at = timezone.now()
                event.is_active = False
            else:
                event.status = EventStatus.ONGOING
                event.is_active = True
            event.save()
            return event

        event = Event.objects.create(
            external_event_id=external_event_id,
            camera=camera,
            event_type=event_type,
            risk_level=risk,
            status=event_status,
            confidence_score=validated_data.get("confidence_score", 0.0),
            metadata=metadata,
            image=validated_data.get("image"),
            video=validated_data.get("video"),
            is_active=event_status != EventStatus.ENDED,
            ended_at=timezone.now() if event_status == EventStatus.ENDED else None,
        )

        for d in detections:
            Detection.objects.create(event=event, **d)
        return event
