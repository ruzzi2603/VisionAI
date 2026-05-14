from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import EventViewSet, VisionIngestView
router=DefaultRouter(); router.register('',EventViewSet,basename='event')
urlpatterns = [path("ingest/", VisionIngestView.as_view(), name="vision-ingest")]
urlpatterns += router.urls
