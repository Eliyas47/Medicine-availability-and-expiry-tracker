"""
Stock movement views.
"""
from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from apps.core.permissions import IsPharmacyAdmin, IsPharmacyMember
from apps.inventory.models import StockMovement, MovementType
from apps.inventory.serializers import StockMovementSerializer
from apps.inventory.services import perform_movement, approve_movement


class StockMovementViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Stock movements are append-only (no update, no delete).
    - GET  /api/movements/       — list movements for user's pharmacy
    - POST /api/movements/       — record a new movement
    - GET  /api/movements/{id}/  — movement detail
    - POST /api/movements/{id}/approve/ — approve a pending correction
    """
    serializer_class = StockMovementSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["movement_type", "medicine", "batch"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = StockMovement.objects.select_related(
            "pharmacy", "medicine", "batch", "performed_by", "approved_by"
        )
        if user.role == "system_admin":
            pharmacy_param = self.request.query_params.get("pharmacy")
            if pharmacy_param:
                qs = qs.filter(pharmacy_id=pharmacy_param)
        else:
            pharmacy_ids = user.get_pharmacy_ids()
            qs = qs.filter(pharmacy_id__in=pharmacy_ids)

        # Date range filters
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs

    def get_permissions(self):
        return [IsAuthenticated(), IsPharmacyMember()]

    @extend_schema(tags=["movements"])
    def create(self, request, *args, **kwargs):
        """Record a new stock movement."""
        serializer = StockMovementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        batch = serializer.validated_data["batch"]

        # Verify the user has access to this batch's pharmacy
        user = request.user
        if user.role != "system_admin":
            pharmacy_ids = user.get_pharmacy_ids()
            if str(batch.pharmacy_id) not in [str(pid) for pid in pharmacy_ids]:
                return Response(
                    {"error": {"code": "permission_denied", "message": "You do not have access to this pharmacy's inventory."}},
                    status=status.HTTP_403_FORBIDDEN,
                )

        movement_type = serializer.validated_data["movement_type"]
        raw_quantity = serializer.validated_data["quantity"]

        # For outbound movements, negate the quantity
        OUTBOUND_TYPES = {
            MovementType.SOLD, MovementType.DISPENSED,
            MovementType.ADJUSTMENT, MovementType.EXPIRED_REMOVAL,
        }
        signed_quantity = -abs(raw_quantity) if movement_type in OUTBOUND_TYPES else abs(raw_quantity)

        requires_approval = movement_type == MovementType.CORRECTION

        _, movement = perform_movement(
            batch_id=str(batch.pk),
            quantity=signed_quantity,
            movement_type=movement_type,
            user=request.user,
            unit_price=serializer.validated_data.get("unit_price"),
            reference_number=serializer.validated_data.get("reference_number", ""),
            notes=serializer.validated_data.get("notes", ""),
            requires_approval=requires_approval,
        )

        return Response(
            StockMovementSerializer(movement).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["movements"])
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """Approve a pending correction movement. Requires pharmacy_admin or system_admin."""
        if request.user.role not in ("pharmacy_admin", "system_admin"):
            return Response(
                {"error": {"code": "permission_denied", "message": "Only pharmacy admins can approve corrections."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        movement = self.get_object()

        # Pharmacy admin can only approve their own pharmacy's movements
        if request.user.role == "pharmacy_admin":
            pharmacy_ids = request.user.get_pharmacy_ids()
            if str(movement.pharmacy_id) not in [str(pid) for pid in pharmacy_ids]:
                return Response(
                    {"error": {"code": "permission_denied", "message": "You can only approve movements for your own pharmacy."}},
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            approved = approve_movement(str(movement.pk), request.user)
        except Exception as e:
            return Response(
                {"error": {"code": "validation_error", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(StockMovementSerializer(approved).data)
