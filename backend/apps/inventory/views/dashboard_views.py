"""
Dashboard aggregation views.
"""
from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from apps.core.permissions import IsSystemAdmin, IsPharmacyMember
from apps.inventory.models import Batch, StockMovement, BatchStatus, SystemConfig
from apps.inventory.serializers import StockMovementSerializer


class PharmacyDashboardView(APIView):
    """GET /api/dashboard/pharmacy/ — Aggregated stats for the user's pharmacy."""
    permission_classes = [IsAuthenticated, IsPharmacyMember]

    @extend_schema(tags=["dashboard"])
    def get(self, request):
        user = request.user
        pharmacy = user.get_pharmacy()
        if not pharmacy:
            return Response(
                {"error": {"code": "not_found", "message": "You are not assigned to a pharmacy."}},
                status=404,
            )

        today = timezone.localdate()
        warning_days = pharmacy.expiry_warning_days
        expiry_cutoff = today + timezone.timedelta(days=warning_days)
        week_cutoff = today + timezone.timedelta(days=7)
        month_cutoff = today + timezone.timedelta(days=30)

        batches = Batch.objects.filter(pharmacy=pharmacy)

        stats = batches.aggregate(
            total_batches=Count("id"),
            active_batches=Count("id", filter=Q(status=BatchStatus.ACTIVE)),
            low_stock_items=Count("id", filter=Q(status=BatchStatus.LOW_STOCK)),
            expiring_soon_batches=Count("id", filter=Q(status=BatchStatus.EXPIRING_SOON)),
            expired_batches=Count("id", filter=Q(expiry_date__lt=today, quantity__gt=0)),
            depleted_items=Count("id", filter=Q(status=BatchStatus.DEPLETED)),
        )

        # Unique medicines in active batches
        total_medicines = batches.filter(
            expiry_date__gte=today, quantity__gt=0
        ).values("medicine").distinct().count()

        # Stock value (unit_cost * quantity for non-expired batches)
        value_agg = batches.filter(
            expiry_date__gte=today, quantity__gt=0, unit_cost__isnull=False
        ).aggregate(
            total_value=Sum(
                __import__("django.db.models", fromlist=["F"]).F("unit_cost") *
                __import__("django.db.models", fromlist=["F"]).F("quantity")
            )
        )

        # Expiry breakdown
        expiry_breakdown = {
            "this_week": batches.filter(
                expiry_date__gte=today, expiry_date__lte=week_cutoff, quantity__gt=0
            ).count(),
            "this_month": batches.filter(
                expiry_date__gte=today, expiry_date__lte=month_cutoff, quantity__gt=0
            ).count(),
            "within_warning_window": batches.filter(
                expiry_date__gte=today, expiry_date__lte=expiry_cutoff, quantity__gt=0
            ).count(),
        }

        # Stock by category
        from django.db.models import Sum as DjangoSum
        stock_by_category = (
            batches.filter(expiry_date__gte=today, quantity__gt=0)
            .values("medicine__category__name")
            .annotate(
                usable_quantity=DjangoSum("quantity"),
                batch_count=Count("id"),
            )
            .order_by("-usable_quantity")
        )
        category_data = [
            {
                "category": item["medicine__category__name"] or "Uncategorized",
                "usable_quantity": item["usable_quantity"] or 0,
                "batch_count": item["batch_count"],
            }
            for item in stock_by_category
        ]

        # Recent movements (last 10)
        recent_movements = (
            StockMovement.objects.filter(pharmacy=pharmacy)
            .select_related("medicine", "batch", "performed_by")
            .order_by("-created_at")[:10]
        )

        return Response({
            "pharmacy": {"id": str(pharmacy.pk), "name": pharmacy.name},
            "stats": {
                "total_medicines": total_medicines,
                "total_batches": stats["total_batches"],
                "active_batches": stats["active_batches"],
                "expired_batches": stats["expired_batches"],
                "expiring_soon_batches": stats["expiring_soon_batches"],
                "low_stock_items": stats["low_stock_items"],
                "depleted_items": stats["depleted_items"],
                "total_usable_stock_value": str(value_agg["total_value"] or 0),
            },
            "expiry_breakdown": expiry_breakdown,
            "stock_by_category": category_data,
            "recent_movements": StockMovementSerializer(recent_movements, many=True).data,
        })


class SystemDashboardView(APIView):
    """GET /api/dashboard/system/ — System-wide stats for system admins."""
    permission_classes = [IsAuthenticated, IsSystemAdmin]

    @extend_schema(tags=["dashboard"])
    def get(self, request):
        from apps.pharmacies.models import Pharmacy
        from apps.medicines.models import Medicine
        from apps.accounts.models import User
        today = timezone.localdate()

        return Response({
            "total_pharmacies": Pharmacy.objects.filter(is_active=True).count(),
            "total_medicines": Medicine.objects.filter(is_active=True).count(),
            "total_users": User.objects.filter(is_active=True).count(),
            "total_batches": Batch.objects.count(),
            "system_low_stock": Batch.objects.filter(status=BatchStatus.LOW_STOCK).count(),
            "system_expired": Batch.objects.filter(expiry_date__lt=today, quantity__gt=0).count(),
            "system_expiring_soon": Batch.objects.filter(status=BatchStatus.EXPIRING_SOON).count(),
        })
