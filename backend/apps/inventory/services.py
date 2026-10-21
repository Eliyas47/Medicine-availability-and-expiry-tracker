"""
Core inventory business logic.

All stock mutations go through perform_movement() — never update batch.quantity directly.
"""
from datetime import date
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Batch, BatchStatus, StockMovement, MovementType, SystemConfig


def compute_batch_status(batch: Batch, warning_days: int | None = None) -> str:
    """
    Compute and return the correct BatchStatus for a batch.

    Priority order:
    1. depleted  (quantity = 0)
    2. expired   (expiry_date < today)
    3. expiring_soon (expiry_date <= today + warning_days)
    4. low_stock (quantity <= pharmacy threshold for this medicine)
    5. active
    """
    today = timezone.localdate()

    if batch.quantity == 0:
        return BatchStatus.DEPLETED

    if batch.expiry_date < today:
        return BatchStatus.EXPIRED

    if warning_days is None:
        # Try to get from pharmacy config, fall back to system config
        try:
            warning_days = batch.pharmacy.expiry_warning_days
        except Exception:
            warning_days = SystemConfig.get().expiry_warning_days

    if (batch.expiry_date - today).days <= warning_days:
        return BatchStatus.EXPIRING_SOON

    # Check low stock threshold
    try:
        from apps.pharmacies.models import PharmacyMedicine
        pm = PharmacyMedicine.objects.get(pharmacy=batch.pharmacy, medicine=batch.medicine)
        if batch.quantity <= pm.minimum_stock_threshold and pm.minimum_stock_threshold > 0:
            return BatchStatus.LOW_STOCK
    except Exception:
        pass

    return BatchStatus.ACTIVE


def get_usable_quantity(pharmacy_id, medicine_id) -> int:
    """
    Return the total usable (non-expired, non-depleted) quantity for a
    medicine at a pharmacy across all its batches.
    """
    today = timezone.localdate()
    batches = Batch.objects.filter(
        pharmacy_id=pharmacy_id,
        medicine_id=medicine_id,
        expiry_date__gte=today,
        quantity__gt=0,
    )
    return sum(b.quantity for b in batches)


@transaction.atomic
def perform_movement(
    batch_id: str,
    quantity: int,
    movement_type: str,
    user,
    unit_price=None,
    reference_number: str = "",
    notes: str = "",
    requires_approval: bool = False,
) -> tuple[Batch, StockMovement]:
    """
    The single authoritative function for all stock mutations.

    quantity is SIGNED:
      - positive = stock in  (received)
      - negative = stock out (sold, dispensed, adjustment, expired_removal, correction)

    Uses SELECT FOR UPDATE to prevent concurrent race conditions.
    """
    # Lock the batch row for the duration of this transaction
    batch = Batch.objects.select_for_update().get(pk=batch_id)

    # ---- Validation ----
    new_quantity = batch.quantity + quantity

    if new_quantity < 0:
        raise ValidationError(
            f"Insufficient stock. Current quantity: {batch.quantity}, "
            f"requested reduction: {abs(quantity)}."
        )

    # Prevent movements on expired batches (except expired_removal)
    today = timezone.localdate()
    if batch.expiry_date < today and movement_type not in (
        MovementType.EXPIRED_REMOVAL, MovementType.CORRECTION
    ):
        raise ValidationError(
            "Cannot perform stock movements on an expired batch. "
            "Use 'expired_removal' to remove expired stock."
        )

    # ---- Apply mutation ----
    batch.quantity = new_quantity
    batch.status = compute_batch_status(batch)
    batch.save(update_fields=["quantity", "status", "updated_at"])

    # ---- Record movement ----
    is_approved = not requires_approval
    movement = StockMovement.objects.create(
        pharmacy=batch.pharmacy,
        medicine=batch.medicine,
        batch=batch,
        movement_type=movement_type,
        quantity=quantity,
        unit_price=unit_price,
        reference_number=reference_number,
        notes=notes,
        performed_by=user,
        is_approved=is_approved,
    )

    return batch, movement


@transaction.atomic
def approve_movement(movement_id: str, approver) -> StockMovement:
    """Approve a pending correction movement."""
    movement = StockMovement.objects.select_for_update().get(pk=movement_id)
    if movement.is_approved:
        raise ValidationError("This movement has already been approved.")
    if movement.movement_type != MovementType.CORRECTION:
        raise ValidationError("Only correction movements require approval.")

    movement.is_approved = True
    movement.approved_by = approver
    movement.approved_at = timezone.now()
    movement.save(update_fields=["is_approved", "approved_by", "approved_at"])
    return movement
