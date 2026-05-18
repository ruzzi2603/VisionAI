from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from apps.authentication.views import TokenObtainWithProfileView


def root_view(request):
    return JsonResponse(
        {
            "message": "VisionGuard AI backend is running.",
            "frontend": "http://localhost:5173",
            "api_root": "/api/",
        }
    )

urlpatterns = [
    path("", root_view, name="backend-root"),
    path("admin/", admin.site.urls),
    path("api/auth/login/", TokenObtainWithProfileView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/", include("apps.authentication.urls")),
    path("api/cameras/", include("apps.cameras.urls")),
    path("api/events/", include("apps.events.urls")),
    path("api/alerts/", include("apps.alerts.urls")),
    path("api/suspects/", include("apps.suspects.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
