from django.db import models
from django.utils import timezone
from apps.cameras.models import Camera
from apps.suspects.models import Suspect
from services.enums import RiskLevel


class EventStatus(models.TextChoices):
    STARTED = "started", "Iniciou"
    ONGOING = "ongoing", "Em andamento"
    ENDED = "ended", "Encerrado"


class Event(models.Model):
    external_event_id = models.CharField(max_length=140, blank=True, default="")
    event_type = models.CharField(max_length=120)
    risk_level = models.CharField(max_length=16, choices=RiskLevel.choices)
    status = models.CharField(max_length=20, choices=EventStatus.choices, default=EventStatus.STARTED)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="events")
    suspect = models.ForeignKey(Suspect, on_delete=models.SET_NULL, blank=True, null=True, related_name="events")
    image = models.ImageField(upload_to="events/", blank=True, null=True)
    video = models.FileField(upload_to="recordings/incidents/", blank=True, null=True)
    confidence_score = models.FloatField(default=0.0)
    metadata = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
class Detection(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="detections")
    label = models.CharField(max_length=120)
    confidence_score = models.FloatField()
    x = models.IntegerField(); y = models.IntegerField(); width = models.IntegerField(); height = models.IntegerField()
class Notification(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default="pending")
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
