from django.db import models
class Camera(models.Model):
    name = models.CharField(max_length=120)
    camera_code = models.CharField(max_length=64, unique=True)
    stream_url = models.URLField(blank=True)
    source = models.CharField(max_length=120, default="0")
    location = models.CharField(max_length=255, blank=True)
    is_online = models.BooleanField(default=False)
    is_sensitive_area = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
