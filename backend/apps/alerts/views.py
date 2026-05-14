from rest_framework import viewsets
from .models import Alert
from .serializers import AlertSerializer
class AlertViewSet(viewsets.ModelViewSet):
 queryset=Alert.objects.select_related('event').all()
 serializer_class=AlertSerializer
