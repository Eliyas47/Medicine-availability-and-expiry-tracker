"""
Custom DRF permission classes for role-based access control.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSystemAdmin(BasePermission):
    """Only system administrators."""
    message = "Only system administrators can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "system_admin"
        )


class IsPharmacyAdmin(BasePermission):
    """Pharmacy administrators or system admins."""
    message = "Only pharmacy or system administrators can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("system_admin", "pharmacy_admin")
        )


class IsPharmacyMember(BasePermission):
    """Any authenticated user with a pharmacy membership (staff or admin)."""
    message = "You must be a member of a pharmacy to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("system_admin", "pharmacy_admin", "inventory_staff")
        )


class IsOwnerOrSystemAdmin(BasePermission):
    """Object-level: the object belongs to the requesting user, or they are a system admin."""
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "system_admin":
            return True
        return obj == request.user


class IsOwnPharmacyOrSystemAdmin(BasePermission):
    """
    Object-level: the resource belongs to a pharmacy the requesting user is a member of,
    or the user is a system admin.
    Expects `obj` to have a `pharmacy_id` attribute or be a Pharmacy itself.
    """
    message = "You do not have permission to access this pharmacy's resources."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "system_admin":
            return True
        # obj may be a Pharmacy or have a pharmacy_id FK
        from apps.pharmacies.models import Pharmacy
        if isinstance(obj, Pharmacy):
            pharmacy_id = obj.pk
        else:
            pharmacy_id = getattr(obj, "pharmacy_id", None)
        if pharmacy_id is None:
            return False
        return request.user.memberships.filter(
            pharmacy_id=pharmacy_id, is_active=True
        ).exists()


class IsPharmacyAdminOfOwnPharmacy(BasePermission):
    """
    Object-level: the user is a pharmacy_admin of the pharmacy this resource belongs to,
    or a system_admin.
    """
    message = "Only the pharmacy's administrator can perform this action."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "system_admin":
            return True
        from apps.pharmacies.models import Pharmacy
        if isinstance(obj, Pharmacy):
            pharmacy_id = obj.pk
        else:
            pharmacy_id = getattr(obj, "pharmacy_id", None)
        if pharmacy_id is None:
            return False
        return request.user.memberships.filter(
            pharmacy_id=pharmacy_id,
            role="pharmacy_admin",
            is_active=True,
        ).exists()


class ReadOnly(BasePermission):
    """Allow GET, HEAD, OPTIONS; deny everything else."""
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
