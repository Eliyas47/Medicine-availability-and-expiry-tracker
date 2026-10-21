from django.contrib import admin
from .models import Pharmacy, PharmacyMedicine


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "region", "phone", "is_active"]
    list_filter = ["is_active", "city", "region"]
    search_fields = ["name", "license_number", "city"]


@admin.register(PharmacyMedicine)
class PharmacyMedicineAdmin(admin.ModelAdmin):
    list_display = ["pharmacy", "medicine", "minimum_stock_threshold", "is_tracked"]
    list_filter = ["is_tracked"]
    search_fields = ["pharmacy__name", "medicine__generic_name"]
