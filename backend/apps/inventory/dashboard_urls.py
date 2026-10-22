from django.urls import path
from .views.dashboard_views import PharmacyDashboardView, SystemDashboardView

urlpatterns = [
    path("pharmacy/", PharmacyDashboardView.as_view(), name="dashboard-pharmacy"),
    path("system/", SystemDashboardView.as_view(), name="dashboard-system"),
]
