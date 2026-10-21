"""
Serializers for pharmacy management.
"""
from rest_framework import serializers
from .models import Pharmacy, PharmacyMedicine


class PharmacyPublicSerializer(serializers.ModelSerializer):
    """Safe public view — no internal config fields exposed."""
    class Meta:
        model = Pharmacy
        fields = [
            "id", "name", "address", "city", "region",
            "phone", "email", "latitude", "longitude",
            "operating_hours", "is_active",
        ]
        read_only_fields = fields


class PharmacySerializer(serializers.ModelSerializer):
    """Full pharmacy serializer for authenticated users."""
    class Meta:
        model = Pharmacy
        fields = [
            "id", "name", "license_number", "address", "city", "region",
            "phone", "email", "latitude", "longitude", "operating_hours",
            "is_active", "expiry_warning_days", "stale_stock_days",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_license_number(self, value):
        qs = Pharmacy.objects.filter(license_number=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A pharmacy with this license number already exists.")
        return value


class PharmacyAdminUpdateSerializer(serializers.ModelSerializer):
    """
    Pharmacy admin can update their pharmacy but cannot change
    the license number or is_active status.
    """
    class Meta:
        model = Pharmacy
        fields = [
            "name", "address", "city", "region", "phone", "email",
            "latitude", "longitude", "operating_hours",
            "expiry_warning_days", "stale_stock_days",
        ]


class PharmacyMedicineSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source="medicine.generic_name", read_only=True)
    medicine_strength = serializers.CharField(source="medicine.strength", read_only=True)

    class Meta:
        model = PharmacyMedicine
        fields = [
            "id", "pharmacy", "medicine", "medicine_name",
            "medicine_strength", "minimum_stock_threshold",
            "is_tracked", "created_at",
        ]
        read_only_fields = ["id", "created_at", "pharmacy"]
