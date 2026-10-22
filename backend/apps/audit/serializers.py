from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id", "user", "user_name", "user_email",
            "action", "model_name", "object_id", "object_repr",
            "changes", "ip_address", "created_at",
        ]
        read_only_fields = fields  # Audit logs are always read-only
