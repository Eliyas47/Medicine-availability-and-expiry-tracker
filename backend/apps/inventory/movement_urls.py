from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.movement_views import StockMovementViewSet

router = DefaultRouter()
router.register(r"", StockMovementViewSet, basename="movement")

# Also expose create via the router (override list to handle POST)
urlpatterns = [path("", include(router.urls))]
