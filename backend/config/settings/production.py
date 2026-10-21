"""
Production settings — strict security, PostgreSQL required, whitenoise for static.
"""
from .base import *  # noqa: F401, F403
from decouple import config
import dj_database_url

DEBUG = False

# ---------------------------------------------------------------------------
# Database — PostgreSQL required in production
# ---------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.parse(
        config("DATABASE_URL"),  # Will raise if not set
        conn_max_age=600,
        ssl_require=config("DATABASE_SSL", default=True, cast=bool),
    )
}

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# CORS — restrict to deployed frontend
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=lambda v: [s.strip() for s in v.split(",")])
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Static files — whitenoise serves compressed static assets
# ---------------------------------------------------------------------------
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@medicinetracker.et")
