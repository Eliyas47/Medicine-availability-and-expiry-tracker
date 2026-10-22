from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.batch_views import BatchViewSet

router = DefaultRouter()
router.register(r"", BatchViewSet, basename="batch")

urlpatterns = [path("", include(router.urls))]
