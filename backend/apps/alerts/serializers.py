from rest_framework import serializers
from .models import Alert
class AlertSerializer(serializers.ModelSerializer):
    event_type = serializers.CharField(source="event.event_type", read_only=True)
    camera_id = serializers.IntegerField(source="event.camera_id", read_only=True)
    event_id = serializers.IntegerField(source="event.id", read_only=True)
    status = serializers.CharField(source="event.status", read_only=True)
    started_at = serializers.DateTimeField(source="event.started_at", read_only=True)
    ended_at = serializers.DateTimeField(source="event.ended_at", read_only=True)
    is_active = serializers.BooleanField(source="event.is_active", read_only=True)
    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        if obj.event and obj.event.image:
            return obj.event.image.url
        return None
    
    def get_video_url(self, obj):
        if obj.event and obj.event.video:
            return obj.event.video.url
        return None

    class Meta:
        model=Alert
        fields=["id","event","event_id","event_type","camera_id","status","started_at","ended_at","is_active","image_url","video_url","risk_level","message","acknowledged","created_at"]
