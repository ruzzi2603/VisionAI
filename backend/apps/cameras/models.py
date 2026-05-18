from django.db import models
from django.utils import timezone

class Camera(models.Model):
    name = models.CharField(max_length=120)
    camera_code = models.CharField(max_length=64, unique=True)
    stream_url = models.URLField(blank=True)
    source = models.CharField(max_length=120, default="0")
    location = models.CharField(max_length=255, blank=True)
    is_online = models.BooleanField(default=False)
    is_sensitive_area = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_heartbeat(self):
        """Atualiza heartbeat quando o pipeline está ativo."""
        self.last_heartbeat = timezone.now()
        self.is_online = True
        self.save(update_fields=["last_heartbeat", "is_online"])

    def check_online_status(self, timeout_seconds=10):
        """Verifica se está online baseado no heartbeat."""
        if not self.last_heartbeat:
            self.is_online = False
            return
        time_since = timezone.now() - self.last_heartbeat
        self.is_online = time_since.total_seconds() < timeout_seconds
        if not self.is_online:
            self.save(update_fields=["is_online"])
