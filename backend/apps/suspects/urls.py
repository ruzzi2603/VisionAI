from rest_framework.routers import DefaultRouter
from .views import SuspectViewSet
router=DefaultRouter(); router.register('',SuspectViewSet,basename='suspect'); urlpatterns=router.urls
