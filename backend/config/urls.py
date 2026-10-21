"""
Root URL configuration for Medicine Availability & Expiry Tracker API.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # API routes
    path("api/auth/", include("apps.accounts.urls")),
    path("api/users/", include("apps.accounts.user_urls")),
    path("api/pharmacies/", include("apps.pharmacies.urls")),
    path("api/categories/", include("apps.medicines.category_urls")),
    path("api/medicines/", include("apps.medicines.urls")),
    path("api/batches/", include("apps.inventory.batch_urls")),
    path("api/movements/", include("apps.inventory.movement_urls")),
    path("api/dashboard/", include("apps.inventory.dashboard_urls")),
    path("api/availability/", include("apps.inventory.availability_urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/config/", include("apps.inventory.config_urls")),

    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
