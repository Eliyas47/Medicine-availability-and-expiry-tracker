from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.core.permissions import IsSystemAdmin
from apps.core.mixins import SoftDeleteMixin
from .models import Category, Medicine
from .serializers import CategorySerializer, MedicineSerializer, MedicineListSerializer


class CategoryViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    Category CRUD.
    - All: read
    - system_admin: write
    """
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        return Category.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsSystemAdmin()]


class MedicineViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    Medicine catalog CRUD.
    - All: read and search
    - system_admin: write
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "dosage_form", "requires_prescription", "is_active"]
    search_fields = ["generic_name", "brand_name", "strength"]
    ordering_fields = ["generic_name", "brand_name", "created_at"]
    ordering = ["generic_name"]

    def get_queryset(self):
        qs = Medicine.objects.select_related("category")
        # By default show only active; system admin can see all with ?is_active=false
        is_active_param = self.request.query_params.get("is_active", "true")
        if is_active_param.lower() == "false":
            if self.request.user.is_authenticated and self.request.user.role == "system_admin":
                return qs  # system admin sees everything
            return qs.filter(is_active=True)
        return qs.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == "list":
            return MedicineListSerializer
        return MedicineSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsSystemAdmin()]
