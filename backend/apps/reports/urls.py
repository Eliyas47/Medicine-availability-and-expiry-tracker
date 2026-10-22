from django.urls import path
from .views import (
    StockSummaryReportView,
    ExpiringReportView,
    ExpiredReportView,
    MovementsReportView,
    LowStockReportView,
)

urlpatterns = [
    path("stock-summary/", StockSummaryReportView.as_view(), name="report-stock-summary"),
    path("expiring/", ExpiringReportView.as_view(), name="report-expiring"),
    path("expired/", ExpiredReportView.as_view(), name="report-expired"),
    path("movements/", MovementsReportView.as_view(), name="report-movements"),
    path("low-stock/", LowStockReportView.as_view(), name="report-low-stock"),
]
