"""
System configuration view — singleton GET/PATCH.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from apps.core.permissions import IsSystemAdmin
from apps.inventory.models import SystemConfig
from apps.inventory.serializers import SystemConfigSerializer


class SystemConfigView(APIView):
    """
    GET  /api/config/ — Retrieve system configuration
    PATCH /api/config/ — Update system configuration (system_admin only)
    """
    permission_classes = [IsAuthenticated, IsSystemAdmin]

    @extend_schema(tags=["config"])
    def get(self, request):
        config = SystemConfig.get()
        return Response(SystemConfigSerializer(config).data)

    @extend_schema(tags=["config"])
    def patch(self, request):
        config = SystemConfig.get()
        serializer = SystemConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(updated_by=request.user)
        return Response(SystemConfigSerializer(instance).data)
