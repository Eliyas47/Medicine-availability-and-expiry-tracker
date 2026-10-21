"""
Development settings — debug mode, SQLite fallback, permissive CORS.
"""
from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# ---------------------------------------------------------------------------
# Database — PostgreSQL preferred; SQLite as fallback for quick start
# ---------------------------------------------------------------------------
import dj_database_url

_database_url = config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")  # noqa: F405
DATABASES = {
    "default": dj_database_url.parse(_database_url, conn_max_age=600)
}

# ---------------------------------------------------------------------------
# CORS — allow Vite dev server
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
).split(",")
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Email backend — print to console
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# Django REST Framework — add BrowsableAPIRenderer in dev
# ---------------------------------------------------------------------------
REST_FRAMEWORK_EXTRA = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

from .base import REST_FRAMEWORK  # noqa: E402
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]
