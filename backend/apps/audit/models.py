"""
Audit log model — immutable record of all significant changes.
"""
from django.db import models


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"


class AuditLog(models.Model):
    """
    Append-only audit trail. Records are never modified or deleted.
    """
    # BigAutoField for high-volume append performance
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    # Denormalized so the record is intact even if the user is deleted
    user_email = models.EmailField(max_length=254)
    action = models.CharField(max_length=30, choices=AuditAction.choices)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=500, blank=True, default="")
    # {"field_name": [old_value, new_value], ...}
    changes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_auditlog"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["model_name"]),
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.action} {self.model_name}#{self.object_id} by {self.user_email}"
