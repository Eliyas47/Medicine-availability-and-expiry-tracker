from django.urls import path
from .views.availability_views import AvailabilitySearchView

urlpatterns = [
    path("", AvailabilitySearchView.as_view(), name="availability-search"),
]
