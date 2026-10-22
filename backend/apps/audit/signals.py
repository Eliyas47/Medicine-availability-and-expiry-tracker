"""
Django signal receivers that create audit log entries for critical models.
Connected in AuditConfig.ready().
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .utils import log_action
from .models import AuditAction

# Models to audit
AUDITED_MODELS = []


def register_audit_signals():
    """Lazily import and register signals to avoid circular imports."""
    from apps.inventory.models import Batch, StockMovement
    from apps.pharmacies.models import Pharmacy
    from apps.medicines.models import Medicine
    from apps.accounts.models import User

    for model in [Batch, StockMovement, Pharmacy, Medicine, User]:
        post_save.connect(_handle_save, sender=model, weak=False)
        post_delete.connect(_handle_delete, sender=model, weak=False)


def _handle_save(sender, instance, created, **kwargs):
    action = AuditAction.CREATE if created else AuditAction.UPDATE
    log_action(action=action, instance=instance)


def _handle_delete(sender, instance, **kwargs):
    log_action(action=AuditAction.DELETE, instance=instance)
