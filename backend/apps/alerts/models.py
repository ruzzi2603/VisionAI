from django.db import models
from apps.events.models import Event
from services.enums import RiskLevel
class Alert(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="alerts")
    risk_level = models.CharField(max_length=16, choices=RiskLevel.choices)
    message = models.TextField()
    acknowledged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
