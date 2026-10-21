"""
Pharmacy views and viewsets.
"""
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.accounts.models import User, PharmacyMembership
from apps.accounts.serializers import PharmacyMembershipSerializer, AddMemberSerializer
from apps.core.permissions import (
    IsSystemAdmin, IsPharmacyAdmin,
    IsOwnPharmacyOrSystemAdmin, IsPharmacyAdminOfOwnPharmacy,
)
from .models import Pharmacy, PharmacyMedicine
from .serializers import (
    PharmacySerializer,
    PharmacyPublicSerializer,
    PharmacyAdminUpdateSerializer,
    PharmacyMedicineSerializer,
)


class PharmacyViewSet(viewsets.ModelViewSet):
    """
    CRUD for pharmacies.

    - Anonymous / public: read-only, public fields only.
    - system_admin: full CRUD on all pharmacies.
    - pharmacy_admin: read all, update own only.
    - inventory_staff: read-only.
    """
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "city", "region"]

    def get_queryset(self):
        qs = Pharmacy.objects.all()
        is_active = self.request.query_params.get("is_active")
        city = self.request.query_params.get("city")
        region = self.request.query_params.get("region")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        if city:
            qs = qs.filter(city__icontains=city)
        if region:
            qs = qs.filter(region__icontains=region)
        return qs

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        if self.action == "create":
            return [IsSystemAdmin()]
        if self.action in ["update", "partial_update"]:
            return [IsAuthenticated(), IsPharmacyAdminOfOwnPharmacy()]
        if self.action == "destroy":
            return [IsSystemAdmin()]
        if self.action in ["members", "add_member", "remove_member"]:
            return [IsAuthenticated(), IsOwnPharmacyOrSystemAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        # Public (unauthenticated) gets limited fields
        if not self.request.user or not self.request.user.is_authenticated:
            return PharmacyPublicSerializer
        # pharmacy_admin update uses restricted serializer
        if self.action in ["update", "partial_update"]:
            user = self.request.user
            if user.role == "pharmacy_admin":
                return PharmacyAdminUpdateSerializer
        return PharmacySerializer

    def perform_destroy(self, instance):
        """Soft delete — set is_active=False."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    # ---- Member management actions ----

    @extend_schema(tags=["pharmacies"])
    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, pk=None):
        pharmacy = self.get_object()
        self.check_object_permissions(request, pharmacy)
        memberships = PharmacyMembership.objects.filter(
            pharmacy=pharmacy, is_active=True
        ).select_related("user")
        serializer = PharmacyMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["pharmacies"])
    @action(detail=True, methods=["post"], url_path="members/add")
    def add_member(self, request, pk=None):
        pharmacy = self.get_object()
        self.check_object_permissions(request, pharmacy)

        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=serializer.validated_data["email"])
        role = serializer.validated_data["role"]

        membership, created = PharmacyMembership.objects.get_or_create(
            user=user,
            pharmacy=pharmacy,
            defaults={"role": role, "is_active": True},
        )
        if not created:
            if membership.is_active:
                return Response(
                    {"error": {"code": "conflict", "message": "User is already a member of this pharmacy."}},
                    status=status.HTTP_409_CONFLICT,
                )
            membership.is_active = True
            membership.role = role
            membership.save(update_fields=["is_active", "role"])

        # Update the user's role to match the membership role
        user.role = role
        user.save(update_fields=["role"])

        return Response(
            PharmacyMembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["pharmacies"])
    @action(detail=True, methods=["delete"], url_path="members/(?P<user_pk>[^/.]+)")
    def remove_member(self, request, pk=None, user_pk=None):
        pharmacy = self.get_object()
        self.check_object_permissions(request, pharmacy)

        membership = get_object_or_404(
            PharmacyMembership, pharmacy=pharmacy, user_id=user_pk, is_active=True
        )
        membership.is_active = False
        membership.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PharmacyMedicineViewSet(viewsets.ModelViewSet):
    """
    Per-pharmacy medicine threshold management.
    Accessed at /api/pharmacies/{pharmacy_pk}/medicines/
    """
    serializer_class = PharmacyMedicineSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsPharmacyAdmin()]

    def get_queryset(self):
        pharmacy_pk = self.kwargs.get("pharmacy_pk")
        qs = PharmacyMedicine.objects.filter(
            pharmacy_id=pharmacy_pk, is_tracked=True
        ).select_related("medicine")

        user = self.request.user
        if user.role != "system_admin":
            pharmacy_ids = user.get_pharmacy_ids()
            if str(pharmacy_pk) not in [str(pid) for pid in pharmacy_ids]:
                return PharmacyMedicine.objects.none()

        return qs

    def perform_create(self, serializer):
        pharmacy = get_object_or_404(Pharmacy, pk=self.kwargs["pharmacy_pk"])
        serializer.save(pharmacy=pharmacy)
