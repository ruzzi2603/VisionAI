from django.db import models
from apps.cameras.models import Camera
class Suspect(models.Model):
    external_id = models.CharField(max_length=64, unique=True)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="suspects")
    face_image = models.ImageField(upload_to="suspects/", blank=True, null=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
