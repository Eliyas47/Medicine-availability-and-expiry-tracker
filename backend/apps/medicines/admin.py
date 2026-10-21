from django.contrib import admin
from .models import Category, Medicine


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at"]
    search_fields = ["name"]


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ["generic_name", "brand_name", "strength", "dosage_form", "category", "is_active"]
    list_filter = ["dosage_form", "category", "requires_prescription", "is_active"]
    search_fields = ["generic_name", "brand_name"]
