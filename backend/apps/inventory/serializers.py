"""
Serializers for batches, movements, and system config.
"""
from datetime import date
from django.utils import timezone
from rest_framework import serializers

from apps.medicines.serializers import MedicineListSerializer
from apps.pharmacies.serializers import PharmacyPublicSerializer
from apps.accounts.serializers import UserSerializer
from .models import Batch, StockMovement, SystemConfig, MovementType


class BatchSerializer(serializers.ModelSerializer):
    medicine = MedicineListSerializer(read_only=True)
    medicine_id = serializers.UUIDField(write_only=True)
    pharmacy_name = serializers.CharField(source="pharmacy.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True, default=None)
    days_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = [
            "id", "pharmacy", "pharmacy_name",
            "medicine", "medicine_id",
            "batch_number", "quantity", "received_date", "expiry_date",
            "supplier", "unit_cost", "status", "days_until_expiry",
            "notes", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "pharmacy", "pharmacy_name", "status",
            "days_until_expiry", "created_by_name", "created_at", "updated_at",
        ]

    def get_days_until_expiry(self, obj) -> int:
        return (obj.expiry_date - timezone.localdate()).days

    def validate_expiry_date(self, value: date) -> date:
        if value <= timezone.localdate():
            raise serializers.ValidationError(
                "Expiry date must be in the future when creating a new batch."
            )
        return value

    def validate_quantity(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Initial quantity must be greater than zero.")
        return value


class BatchCreateSerializer(BatchSerializer):
    """Used only for creation — includes initial quantity validation."""
    pass


class BatchUpdateSerializer(serializers.ModelSerializer):
    """Pharmacy admin can update non-quantity fields."""
    class Meta:
        model = Batch
        fields = ["supplier", "unit_cost", "notes"]


class StockMovementSerializer(serializers.ModelSerializer):
    pharmacy_name = serializers.CharField(source="pharmacy.name", read_only=True)
    medicine_name = serializers.CharField(source="medicine.generic_name", read_only=True)
    batch_number = serializers.CharField(source="batch.batch_number", read_only=True, default=None)
    performed_by_name = serializers.CharField(source="performed_by.full_name", read_only=True, default=None)
    approved_by_name = serializers.CharField(source="approved_by.full_name", read_only=True, default=None)
    movement_type_display = serializers.CharField(source="get_movement_type_display", read_only=True)

    # Write fields
    batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all(),
        write_only=False,
        required=True,
    )

    class Meta:
        model = StockMovement
        fields = [
            "id", "pharmacy", "pharmacy_name",
            "medicine", "medicine_name",
            "batch", "batch_number",
            "movement_type", "movement_type_display",
            "quantity", "unit_price", "reference_number", "notes",
            "performed_by", "performed_by_name",
            "is_approved", "approved_by", "approved_by_name", "approved_at",
            "created_at",
        ]
        read_only_fields = [
            "id", "pharmacy", "pharmacy_name", "medicine", "medicine_name",
            "batch_number", "performed_by", "performed_by_name",
            "is_approved", "approved_by", "approved_by_name", "approved_at",
            "created_at",
        ]

    def validate(self, attrs):
        movement_type = attrs.get("movement_type")
        quantity = attrs.get("quantity")

        if quantity is None or quantity == 0:
            raise serializers.ValidationError({"quantity": "Quantity must not be zero."})

        # Outbound movements: quantity should be positive and will be negated in the service
        OUTBOUND_TYPES = {
            MovementType.SOLD, MovementType.DISPENSED,
            MovementType.ADJUSTMENT, MovementType.EXPIRED_REMOVAL,
        }
        if movement_type in OUTBOUND_TYPES and quantity < 0:
            raise serializers.ValidationError(
                {"quantity": "Enter a positive quantity. The direction is determined by movement type."}
            )
        if movement_type == MovementType.RECEIVED and quantity < 0:
            raise serializers.ValidationError({"quantity": "Received quantity must be positive."})

        return attrs


class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = [
            "expiry_warning_days", "stale_stock_days",
            "low_stock_default_threshold", "updated_at",
        ]
        read_only_fields = ["updated_at"]
