"""
Audit logging utility functions.
Called from Django signals and views to write AuditLog entries.
"""
from .middleware import get_current_user, get_current_ip
from .models import AuditLog, AuditAction


def log_action(
    action: str,
    instance,
    changes: dict | None = None,
    user=None,
    ip_address: str | None = None,
):
    """
    Write an audit log entry for a model instance change.

    Args:
        action: AuditAction value ('create', 'update', 'delete')
        instance: The Django model instance affected
        changes: Dict of {field: [old_value, new_value]}
        user: Override the request user (defaults to thread-local)
        ip_address: Override the IP (defaults to thread-local)
    """
    resolved_user = user or get_current_user()
    resolved_ip = ip_address or get_current_ip()

    # Don't log if no user context (e.g., migrations, management commands)
    if resolved_user is None or not getattr(resolved_user, "pk", None):
        return

    try:
        # Avoid logging anonymous users
        if not resolved_user.is_authenticated:
            return
    except AttributeError:
        return

    try:
        AuditLog.objects.create(
            user=resolved_user,
            user_email=resolved_user.email,
            action=action,
            model_name=instance.__class__.__name__,
            object_id=str(instance.pk),
            object_repr=str(instance)[:500],
            changes=changes,
            ip_address=resolved_ip or None,
        )
    except Exception:
        # Never let audit logging break the main operation
        pass
