from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from apps.events.models import Event
from apps.alerts.models import Alert
from apps.cameras.models import Camera

class DashboardStatsView(APIView):
    def get(self, request):
        risk_distribution = list(Event.objects.values("risk_level").annotate(total=Count("id")).order_by())
        return Response({"total_cameras": Camera.objects.count(), "online_cameras": Camera.objects.filter(is_online=True).count(), "total_events": Event.objects.count(), "open_alerts": Alert.objects.filter(acknowledged=False).count(), "risk_distribution": risk_distribution})
