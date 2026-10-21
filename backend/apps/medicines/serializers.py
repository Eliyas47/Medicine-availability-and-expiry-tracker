from rest_framework import serializers
from .models import Category, Medicine


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value


class MedicineListSerializer(serializers.ModelSerializer):
    """Compact serializer for dropdowns / search results."""
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    dosage_form_display = serializers.CharField(source="get_dosage_form_display", read_only=True)

    class Meta:
        model = Medicine
        fields = [
            "id", "generic_name", "brand_name", "strength",
            "dosage_form", "dosage_form_display", "category_name",
            "requires_prescription", "is_active",
        ]


class MedicineSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    dosage_form_display = serializers.CharField(source="get_dosage_form_display", read_only=True)

    class Meta:
        model = Medicine
        fields = [
            "id", "generic_name", "brand_name", "strength",
            "dosage_form", "dosage_form_display", "category", "category_name",
            "description", "unit_of_measure", "requires_prescription",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "dosage_form_display", "category_name", "created_at", "updated_at"]
