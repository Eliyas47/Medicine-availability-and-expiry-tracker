"""
Reusable serializer and viewset mixins.
"""
from rest_framework import serializers


class TimestampMixin(serializers.Serializer):
    """Adds read-only created_at and updated_at to any serializer."""
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class SoftDeleteMixin:
    """
    ViewSet mixin: override destroy() to do a soft delete
    by setting is_active=False instead of deleting the row.
    """
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])
