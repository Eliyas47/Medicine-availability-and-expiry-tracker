"""
Pharmacy model — represents a physical pharmacy participating in the platform.
"""
import uuid
from django.db import models


class Pharmacy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(max_length=254, blank=True, default="")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # JSONB-equivalent: store as JSON {"mon": "08:00-20:00", ...}
    operating_hours = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # Per-pharmacy configuration
    expiry_warning_days = models.PositiveIntegerField(default=90)
    stale_stock_days = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pharmacies_pharmacy"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["city"]),
            models.Index(fields=["region"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name_plural = "pharmacies"

    def __str__(self):
        return f"{self.name} ({self.city})"


class PharmacyMedicine(models.Model):
    """
    Tracks per-pharmacy minimum stock thresholds for a medicine.
    Created when a pharmacy starts managing a specific medicine.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        related_name="pharmacy_medicines",
    )
    medicine = models.ForeignKey(
        "medicines.Medicine",
        on_delete=models.CASCADE,
        related_name="pharmacy_medicines",
    )
    minimum_stock_threshold = models.PositiveIntegerField(default=0)
    is_tracked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pharmacies_pharmacymedicine"
        unique_together = [("pharmacy", "medicine")]
        ordering = ["pharmacy", "medicine"]

    def __str__(self):
        return f"{self.pharmacy.name} — {self.medicine.generic_name}"
