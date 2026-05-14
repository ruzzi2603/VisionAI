from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "channels",
    "apps.authentication",
    "apps.cameras",
    "apps.events",
    "apps.suspects",
    "apps.alerts",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

if os.getenv("USE_SQLITE", "False").lower() == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": os.getenv("POSTGRES_DB", "visionguard"), "USER": os.getenv("POSTGRES_USER", "visionguard"), "PASSWORD": os.getenv("POSTGRES_PASSWORD", "visionguard"), "HOST": os.getenv("POSTGRES_HOST", "localhost"), "PORT": os.getenv("POSTGRES_PORT", "5432")}}
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
if os.getenv("USE_SQLITE", "False").lower() == "true":
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
else:
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": {"hosts": [REDIS_URL]}}}

REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",), "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",)}
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=30), "REFRESH_TOKEN_LIFETIME": timedelta(days=1)}

CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL", "True").lower() == "true"
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost:5173").split(",")
VISION_INGEST_TOKEN = os.getenv("VISION_INGEST_TOKEN", "visionguard-local-token")
LIVE_VIEW_BASE_URL = os.getenv("LIVE_VIEW_BASE_URL", "http://localhost:8000/live/camera")

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
