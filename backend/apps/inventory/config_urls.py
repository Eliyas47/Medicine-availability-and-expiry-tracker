from django.urls import path
from .views.config_views import SystemConfigView

urlpatterns = [
    path("", SystemConfigView.as_view(), name="system-config"),
]
