from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PharmacyViewSet, PharmacyMedicineViewSet

router = DefaultRouter()
router.register(r"", PharmacyViewSet, basename="pharmacy")

# Nested router for pharmacy medicines
medicine_router = DefaultRouter()
medicine_router.register(r"medicines", PharmacyMedicineViewSet, basename="pharmacy-medicine")

urlpatterns = [
    path("", include(router.urls)),
    path("<uuid:pharmacy_pk>/", include(medicine_router.urls)),
]
