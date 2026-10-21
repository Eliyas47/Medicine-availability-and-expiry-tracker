"""
Batch inventory views.
"""
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from apps.core.permissions import IsPharmacyAdmin, IsOwnPharmacyOrSystemAdmin, IsPharmacyMember
from apps.inventory.models import Batch, BatchStatus, MovementType, SystemConfig
from apps.inventory.serializers import BatchSerializer, BatchUpdateSerializer
from apps.inventory.services import perform_movement, compute_batch_status


class BatchViewSet(viewsets.ModelViewSet):
    """
    Inventory batch management.
    Creating a batch automatically records a 'received' stock movement.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "medicine"]
    search_fields = ["batch_number", "medicine__generic_name", "supplier"]
    ordering_fields = ["expiry_date", "quantity", "created_at"]
    ordering = ["expiry_date"]

    def get_queryset(self):
        user = self.request.user
        qs = Batch.objects.select_related("pharmacy", "medicine", "created_by")

        if user.role == "system_admin":
            pharmacy_param = self.request.query_params.get("pharmacy")
            if pharmacy_param:
                return qs.filter(pharmacy_id=pharmacy_param)
            return qs

        # Scope to the user's pharmacies
        pharmacy_ids = user.get_pharmacy_ids()
        return qs.filter(pharmacy_id__in=pharmacy_ids)

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return BatchUpdateSerializer
        return BatchSerializer

    def get_permissions(self):
        if self.action in ["create"]:
            return [IsAuthenticated(), IsPharmacyMember()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsPharmacyAdmin()]
        return [IsAuthenticated(), IsPharmacyMember()]

    def perform_create(self, serializer):
        user = self.request.user
        # Determine pharmacy: system_admin must provide pharmacy_id param
        if user.role == "system_admin":
            pharmacy_id = self.request.data.get("pharmacy")
            if not pharmacy_id:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"pharmacy": "System admin must specify a pharmacy."})
            from apps.pharmacies.models import Pharmacy
            pharmacy = Pharmacy.objects.get(pk=pharmacy_id)
        else:
            pharmacy = user.get_pharmacy()
            if not pharmacy:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("You are not assigned to a pharmacy.")

        # Save batch (with initial quantity from serializer)
        initial_quantity = serializer.validated_data["quantity"]
        batch = serializer.save(
            pharmacy=pharmacy,
            created_by=user,
            status=compute_batch_status(
                type("obj", (), {
                    "quantity": initial_quantity,
                    "expiry_date": serializer.validated_data["expiry_date"],
                    "pharmacy": pharmacy,
                    "medicine": serializer.validated_data.get("medicine") or
                                type("med", (), {"pk": serializer.validated_data["medicine_id"]})(),
                })(),
                warning_days=pharmacy.expiry_warning_days,
            ),
        )

        # Auto-create a 'received' stock movement
        # The batch was just created so quantity is already set;
        # we record the movement without modifying the quantity again
        from apps.inventory.models import StockMovement
        StockMovement.objects.create(
            pharmacy=pharmacy,
            medicine=batch.medicine,
            batch=batch,
            movement_type=MovementType.RECEIVED,
            quantity=initial_quantity,  # positive
            performed_by=user,
            is_approved=True,
        )

    def perform_destroy(self, instance):
        if instance.quantity > 0:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                "Cannot delete a batch with remaining stock. "
                "Reduce quantity to zero first."
            )
        instance.delete()

    # ---- Custom list actions ----

    @extend_schema(tags=["batches"])
    @action(detail=False, methods=["get"], url_path="expiring")
    def expiring(self, request):
        """Batches expiring within the pharmacy's warning window."""
        qs = self.get_queryset()
        today = timezone.localdate()

        # Get warning days from pharmacy or system config
        user = request.user
        if user.role == "system_admin":
            warning_days = SystemConfig.get().expiry_warning_days
        else:
            pharmacy = user.get_pharmacy()
            warning_days = pharmacy.expiry_warning_days if pharmacy else SystemConfig.get().expiry_warning_days

        expiry_cutoff = today + timezone.timedelta(days=warning_days)
        qs = qs.filter(
            expiry_date__gt=today,
            expiry_date__lte=expiry_cutoff,
            quantity__gt=0,
        ).order_by("expiry_date")

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = BatchSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(BatchSerializer(qs, many=True).data)

    @extend_schema(tags=["batches"])
    @action(detail=False, methods=["get"], url_path="expired")
    def expired(self, request):
        """All expired batches with remaining quantity."""
        qs = self.get_queryset()
        today = timezone.localdate()
        qs = qs.filter(expiry_date__lt=today, quantity__gt=0).order_by("expiry_date")

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = BatchSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(BatchSerializer(qs, many=True).data)

    @extend_schema(tags=["batches"])
    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        """Batches below their pharmacy's minimum threshold."""
        from apps.pharmacies.models import PharmacyMedicine
        from django.db.models import F

        user = request.user
        if user.role == "system_admin":
            pharmacy_ids = list(
                __import__("apps.pharmacies.models", fromlist=["Pharmacy"])
                .Pharmacy.objects.filter(is_active=True).values_list("id", flat=True)
            )
        else:
            pharmacy_ids = user.get_pharmacy_ids()

        # Find batches where quantity <= threshold for that (pharmacy, medicine) pair
        low_batches = []
        pm_qs = PharmacyMedicine.objects.filter(
            pharmacy_id__in=pharmacy_ids,
            minimum_stock_threshold__gt=0,
            is_tracked=True,
        )
        for pm in pm_qs:
            from django.db.models import Sum
            today = timezone.localdate()
            usable_qty = (
                Batch.objects.filter(
                    pharmacy=pm.pharmacy,
                    medicine=pm.medicine,
                    expiry_date__gte=today,
                    quantity__gt=0,
                ).aggregate(total=Sum("quantity"))["total"] or 0
            )
            if usable_qty <= pm.minimum_stock_threshold:
                low_batches.append({
                    "medicine_id": str(pm.medicine_id),
                    "medicine_name": pm.medicine.generic_name,
                    "pharmacy_id": str(pm.pharmacy_id),
                    "pharmacy_name": pm.pharmacy.name,
                    "usable_quantity": usable_qty,
                    "minimum_threshold": pm.minimum_stock_threshold,
                    "shortfall": max(0, pm.minimum_stock_threshold - usable_qty),
                })

        return Response({"count": len(low_batches), "results": low_batches})
