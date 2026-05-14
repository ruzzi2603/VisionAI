from rest_framework import viewsets
from .models import Suspect
from .serializers import SuspectSerializer
class SuspectViewSet(viewsets.ModelViewSet):
 queryset=Suspect.objects.select_related('camera').order_by('-last_seen')
 serializer_class=SuspectSerializer
