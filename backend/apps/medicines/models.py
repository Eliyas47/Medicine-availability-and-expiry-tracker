"""
Shared medicine catalog — medicines and categories used across all pharmacies.
"""
import uuid
from django.db import models


class DosageForm(models.TextChoices):
    TABLET = "tablet", "Tablet"
    CAPSULE = "capsule", "Capsule"
    SYRUP = "syrup", "Syrup"
    INJECTION = "injection", "Injection"
    CREAM = "cream", "Cream"
    DROPS = "drops", "Drops"
    SUPPOSITORY = "suppository", "Suppository"
    PATCH = "patch", "Patch"
    INHALER = "inhaler", "Inhaler"
    OTHER = "other", "Other"


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "medicines_category"
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Medicine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    generic_name = models.CharField(max_length=200)
    brand_name = models.CharField(max_length=200, blank=True, default="")
    strength = models.CharField(max_length=100, help_text='e.g. "500mg", "10mg/5ml"')
    dosage_form = models.CharField(max_length=50, choices=DosageForm.choices)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medicines",
    )
    description = models.TextField(blank=True, default="")
    unit_of_measure = models.CharField(max_length=50, default="unit")
    requires_prescription = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "medicines_medicine"
        ordering = ["generic_name"]
        indexes = [
            models.Index(fields=["generic_name"]),
            models.Index(fields=["brand_name"]),
            models.Index(fields=["dosage_form"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        parts = [self.generic_name, self.strength, self.get_dosage_form_display()]
        if self.brand_name:
            parts.append(f"({self.brand_name})")
        return " ".join(parts)
