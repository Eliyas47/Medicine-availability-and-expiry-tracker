"""
Inventory models: Batch, StockMovement, SystemConfig.
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class BatchStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    LOW_STOCK = "low_stock", "Low Stock"
    EXPIRING_SOON = "expiring_soon", "Expiring Soon"
    EXPIRED = "expired", "Expired"
    DEPLETED = "depleted", "Depleted"


class MovementType(models.TextChoices):
    RECEIVED = "received", "Received"
    SOLD = "sold", "Sold"
    DISPENSED = "dispensed", "Dispensed"
    ADJUSTMENT = "adjustment", "Adjustment"
    EXPIRED_REMOVAL = "expired_removal", "Expired Removal"
    CORRECTION = "correction", "Correction"


class Batch(models.Model):
    """
    A batch represents a specific delivery/lot of a medicine at a pharmacy.
    Quantities are maintained here; movements record the history.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy",
        on_delete=models.CASCADE,
        related_name="batches",
    )
    medicine = models.ForeignKey(
        "medicines.Medicine",
        on_delete=models.PROTECT,
        related_name="batches",
    )
    batch_number = models.CharField(max_length=100)
    quantity = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    received_date = models.DateField()
    expiry_date = models.DateField()
    supplier = models.CharField(max_length=200, blank=True, default="")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=BatchStatus.choices,
        default=BatchStatus.ACTIVE,
    )
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_batches",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_batch"
        unique_together = [("pharmacy", "batch_number")]
        ordering = ["expiry_date"]
        indexes = [
            models.Index(fields=["pharmacy"]),
            models.Index(fields=["medicine"]),
            models.Index(fields=["expiry_date"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=0),
                name="batch_quantity_non_negative",
            )
        ]

    def __str__(self):
        return f"{self.batch_number} — {self.medicine.generic_name} @ {self.pharmacy.name}"

    @property
    def is_expired(self):
        return self.expiry_date < timezone.localdate()

    @property
    def days_until_expiry(self):
        delta = self.expiry_date - timezone.localdate()
        return delta.days


class StockMovement(models.Model):
    """
    Append-only ledger of all stock changes.
    quantity is SIGNED: positive = stock in, negative = stock out.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy",
        on_delete=models.CASCADE,
        related_name="movements",
    )
    medicine = models.ForeignKey(
        "medicines.Medicine",
        on_delete=models.PROTECT,
        related_name="movements",
    )
    batch = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements",
    )
    movement_type = models.CharField(max_length=30, choices=MovementType.choices)
    quantity = models.IntegerField(help_text="Positive=in, Negative=out")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    performed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="performed_movements",
    )
    is_approved = models.BooleanField(default=True)
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_movements",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_stockmovement"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["pharmacy"]),
            models.Index(fields=["medicine"]),
            models.Index(fields=["batch"]),
            models.Index(fields=["movement_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.movement_type} {self.quantity} x {self.medicine.generic_name} @ {self.pharmacy.name}"


class SystemConfig(models.Model):
    """
    Singleton table for system-wide configuration defaults.
    Only one row (id=1) should ever exist.
    """
    expiry_warning_days = models.PositiveIntegerField(
        default=90,
        help_text="Number of days before expiry to flag a batch as 'expiring soon'",
    )
    stale_stock_days = models.PositiveIntegerField(
        default=30,
        help_text="Days since last movement before stock is considered stale in availability search",
    )
    low_stock_default_threshold = models.PositiveIntegerField(
        default=10,
        help_text="Default minimum stock threshold for new PharmacyMedicine records",
    )
    updated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_systemconfig"
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configuration"

    def __str__(self):
        return "System Configuration"

    @classmethod
    def get(cls):
        """Return the singleton instance, creating it if it doesn't exist."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
