"""
Report views with optional CSV export.
All reports are scoped to the requesting user's pharmacy (or all pharmacies for system_admin).
"""
import csv
import io
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.core.permissions import IsPharmacyMember
from apps.inventory.models import Batch, StockMovement, BatchStatus


def get_pharmacy_scope(request):
    """Return queryset scope based on user's pharmacy membership."""
    user = request.user
    if user.role == "system_admin":
        pharmacy_param = request.query_params.get("pharmacy")
        if pharmacy_param:
            return Q(pharmacy_id=pharmacy_param)
        return Q()  # all pharmacies
    pharmacy_ids = user.get_pharmacy_ids()
    return Q(pharmacy_id__in=pharmacy_ids)


def parse_date_filters(request):
    """Extract and return date_from, date_to from query params."""
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    return date_from, date_to


def make_csv_response(rows: list[dict], filename: str) -> HttpResponse:
    """Build and return an HTTP CSV download response."""
    if not rows:
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


class StockSummaryReportView(APIView):
    """GET /api/reports/stock-summary/"""
    permission_classes = [IsAuthenticated, IsPharmacyMember]

    @extend_schema(tags=["reports"])
    def get(self, request):
        today = timezone.localdate()
        scope = get_pharmacy_scope(request)
        medicine_filter = request.query_params.get("medicine")
        category_filter = request.query_params.get("category")

        qs = (
            Batch.objects.filter(scope)
            .values(
                "medicine__id",
                "medicine__generic_name",
                "medicine__strength",
                "medicine__dosage_form",
                "medicine__category__name",
                "pharmacy__name",
            )
            .annotate(
                total_batches=Count("id"),
                usable_quantity=Sum("quantity", filter=Q(expiry_date__gte=today, quantity__gt=0)),
                expired_quantity=Sum("quantity", filter=Q(expiry_date__lt=today, quantity__gt=0)),
            )
            .order_by("medicine__generic_name")
        )

        if medicine_filter:
            qs = qs.filter(
                Q(medicine__generic_name__icontains=medicine_filter) |
                Q(medicine__brand_name__icontains=medicine_filter)
            )
        if category_filter:
            qs = qs.filter(medicine__category_id=category_filter)

        rows = [
            {
                "pharmacy": r["pharmacy__name"],
                "medicine": r["medicine__generic_name"],
                "strength": r["medicine__strength"],
                "dosage_form": r["medicine__dosage_form"],
                "category": r["medicine__category__name"] or "Uncategorized",
                "usable_quantity": r["usable_quantity"] or 0,
                "expired_quantity": r["expired_quantity"] or 0,
                "total_batches": r["total_batches"],
            }
            for r in qs
        ]

        if request.query_params.get("format") == "csv":
            return make_csv_response(rows, f"stock_summary_{today}.csv")

        return Response({"count": len(rows), "results": rows})


class ExpiringReportView(APIView):
    """GET /api/reports/expiring/"""
    permission_classes = [IsAuthenticated, IsPharmacyMember]

    @extend_schema(tags=["reports"])
    def get(self, request):
        today = timezone.localdate()
        scope = get_pharmacy_scope(request)

        date_from = request.query_params.get("date_from", str(today))
        date_to = request.query_params.get("date_to")
        if not date_to:
            from apps.inventory.models import SystemConfig
            config = SystemConfig.get()
            expiry_cutoff = today + timezone.timedelta(days=config.expiry_warning_days)
            date_to = str(expiry_cutoff)

        qs = (
            Batch.objects.filter(scope)
            .filter(expiry_date__gte=date_from, expiry_date__lte=date_to, quantity__gt=0)
            .select_related("medicine", "pharmacy")
            .order_by("expiry_date")
        )

        rows = [
            {
                "pharmacy": b.pharmacy.name,
                "batch_number": b.batch_number,
                "medicine": b.medicine.generic_name,
                "strength": b.medicine.strength,
                "quantity": b.quantity,
                "expiry_date": str(b.expiry_date),
                "days_until_expiry": (b.expiry_date - today).days,
                "supplier": b.supplier,
            }
            for b in qs
        ]

        if request.query_params.get("format") == "csv":
            return make_csv_response(rows, f"expiring_stock_{today}.csv")

        return Response({"count": len(rows), "results": rows})


class ExpiredReportView(APIView):
    """GET /api/reports/expired/"""
    permission_classes = [IsAuthenticated, IsPharmacyMember]

    @extend_schema(tags=["reports"])
    def get(self, request):
        today = timezone.localdate()
        scope = get_pharmacy_scope(request)

        qs = (
            Batch.objects.filter(scope)
            .filter(expiry_date__lt=today, quantity__gt=0)
            .select_related("medicine", "pharmacy")
            .order_by("expiry_date")
        )

        rows = [
            {
                "pharmacy": b.pharmacy.name,
                "batch_number": b.batch_number,
                "medicine": b.medicine.generic_name,
                "strength": b.medicine.strength,
                "quantity": b.quantity,
                "expiry_date": str(b.expiry_date),
                "days_expired": (today - b.expiry_date).days,
                "supplier": b.supplier,
            }
            for b in qs
        ]

        if request.query_params.get("format") == "csv":
            return make_csv_response(rows, f"expired_stock_{today}.csv")

        return Response({"count": len(rows), "results": rows})


class MovementsReportView(APIView):
    """GET /api/reports/movements/"""
    permission_classes = [IsAuthenticated, IsPharmacyMember]

    @extend_schema(tags=["reports"])
    def get(self, request):
        today = timezone.localdate()
        scope = get_pharmacy_scope(request)
        date_from, date_to = parse_date_filters(request)
        movement_type = request.query_params.get("movement_type")

        qs = StockMovement.objects.filter(scope).select_related(
            "medicine", "pharmacy", "batch", "performed_by"
        ).order_by("-created_at")

        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if movement_type:
            qs = qs.filter(movement_type=movement_type)

        rows = [
            {
                "date": m.created_at.strftime("%Y-%m-%d %H:%M"),
                "pharmacy": m.pharmacy.name,
                "medicine": m.medicine.generic_name,
                "batch": m.batch.batch_number if m.batch else "",
                "movement_type": m.movement_type,
                "quantity": m.quantity,
                "unit_price": str(m.unit_price) if m.unit_price else "",
                "reference": m.reference_number,
                "performed_by": m.performed_by.full_name if m.performed_by else "",
                "approved": "Yes" if m.is_approved else "Pending",
            }
            for m in qs[:5000]  # cap at 5000 rows for CSV
        ]

        if request.query_params.get("format") == "csv":
            return make_csv_response(rows, f"movements_{today}.csv")

        return Response({"count": len(rows), "results": rows})


class LowStockReportView(APIView):
    """GET /api/reports/low-stock/"""
    permission_classes = [IsAuthenticated, IsPharmacyMember]

    @extend_schema(tags=["reports"])
    def get(self, request):
        from apps.pharmacies.models import PharmacyMedicine
        from django.db.models import Sum

        today = timezone.localdate()
        user = request.user

        if user.role == "system_admin":
            pharmacy_param = request.query_params.get("pharmacy")
            pm_qs = PharmacyMedicine.objects.filter(minimum_stock_threshold__gt=0, is_tracked=True)
            if pharmacy_param:
                pm_qs = pm_qs.filter(pharmacy_id=pharmacy_param)
        else:
            pharmacy_ids = user.get_pharmacy_ids()
            pm_qs = PharmacyMedicine.objects.filter(
                pharmacy_id__in=pharmacy_ids,
                minimum_stock_threshold__gt=0,
                is_tracked=True,
            )

        pm_qs = pm_qs.select_related("pharmacy", "medicine")
        rows = []
        for pm in pm_qs:
            usable_qty = (
                Batch.objects.filter(
                    pharmacy=pm.pharmacy,
                    medicine=pm.medicine,
                    expiry_date__gte=today,
                    quantity__gt=0,
                ).aggregate(total=Sum("quantity"))["total"] or 0
            )
            if usable_qty <= pm.minimum_stock_threshold:
                rows.append({
                    "pharmacy": pm.pharmacy.name,
                    "medicine": pm.medicine.generic_name,
                    "strength": pm.medicine.strength,
                    "usable_quantity": usable_qty,
                    "minimum_threshold": pm.minimum_stock_threshold,
                    "shortfall": max(0, pm.minimum_stock_threshold - usable_qty),
                })

        rows.sort(key=lambda r: r["shortfall"], reverse=True)

        if request.query_params.get("format") == "csv":
            return make_csv_response(rows, f"low_stock_{timezone.localdate()}.csv")

        return Response({"count": len(rows), "results": rows})
