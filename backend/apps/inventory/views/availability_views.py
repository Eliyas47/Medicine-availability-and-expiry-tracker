"""
Public availability search — no authentication required.
"""
from django.db.models import Sum, Max
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter


class AvailabilitySearchView(APIView):
    """
    GET /api/availability/?medicine=amoxicillin&city=Addis+Ababa

    Public endpoint. Returns active pharmacies with usable stock
    for the searched medicine. Expired batches are excluded.
    Results include a staleness flag when stock hasn't been confirmed recently.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["availability"],
        parameters=[
            OpenApiParameter("medicine", str, required=True, description="Medicine name (partial match)"),
            OpenApiParameter("city", str, required=False),
            OpenApiParameter("region", str, required=False),
        ],
    )
    def get(self, request):
        medicine_query = request.query_params.get("medicine", "").strip()
        if not medicine_query:
            raise ValidationError({"medicine": "medicine search term is required."})

        city = request.query_params.get("city", "").strip()
        region = request.query_params.get("region", "").strip()

        today = timezone.localdate()
        now = timezone.now()

        from apps.inventory.models import Batch, StockMovement, SystemConfig
        from apps.medicines.models import Medicine
        from apps.pharmacies.models import Pharmacy

        config = SystemConfig.get()
        stale_days = config.stale_stock_days

        # Find matching medicines (case-insensitive partial match)
        medicines = Medicine.objects.filter(
            is_active=True,
        ).filter(
            __import__("django.db.models", fromlist=["Q"]).Q(generic_name__icontains=medicine_query) |
            __import__("django.db.models", fromlist=["Q"]).Q(brand_name__icontains=medicine_query)
        )

        if not medicines.exists():
            return Response({"query": medicine_query, "results": []})

        # Find pharmacies with usable stock for these medicines
        pharmacy_qs = Pharmacy.objects.filter(is_active=True)
        if city:
            pharmacy_qs = pharmacy_qs.filter(city__icontains=city)
        if region:
            pharmacy_qs = pharmacy_qs.filter(region__icontains=region)

        results = []
        for medicine in medicines:
            # Aggregate usable quantity per pharmacy
            batch_agg = (
                Batch.objects.filter(
                    medicine=medicine,
                    pharmacy__in=pharmacy_qs,
                    expiry_date__gte=today,
                    quantity__gt=0,
                )
                .values("pharmacy_id")
                .annotate(usable_quantity=Sum("quantity"))
            )

            pharmacy_qty_map = {str(row["pharmacy_id"]): row["usable_quantity"] for row in batch_agg}

            for pharmacy in pharmacy_qs:
                usable_qty = pharmacy_qty_map.get(str(pharmacy.pk), 0)
                if usable_qty <= 0:
                    continue

                # Get last confirmed timestamp from movements
                last_movement = (
                    StockMovement.objects.filter(pharmacy=pharmacy, medicine=medicine)
                    .aggregate(last=Max("created_at"))["last"]
                )

                stale_threshold = now - timezone.timedelta(days=stale_days)
                is_stale = (last_movement is None) or (last_movement < stale_threshold)

                results.append({
                    "pharmacy": {
                        "id": str(pharmacy.pk),
                        "name": pharmacy.name,
                        "address": pharmacy.address,
                        "city": pharmacy.city,
                        "region": pharmacy.region,
                        "phone": pharmacy.phone,
                    },
                    "medicine": {
                        "id": str(medicine.pk),
                        "generic_name": medicine.generic_name,
                        "brand_name": medicine.brand_name,
                        "strength": medicine.strength,
                        "dosage_form": medicine.dosage_form,
                        "requires_prescription": medicine.requires_prescription,
                    },
                    "usable_quantity": usable_qty,
                    "last_confirmed_at": last_movement.isoformat() if last_movement else None,
                    "is_stale": is_stale,
                })

        # Sort: non-stale first, then by quantity descending
        results.sort(key=lambda r: (r["is_stale"], -r["usable_quantity"]))

        return Response({"query": medicine_query, "results": results})
