"""
Custom User model with email-based authentication and role-based access control.
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    SYSTEM_ADMIN = "system_admin", "System Administrator"
    PHARMACY_ADMIN = "pharmacy_admin", "Pharmacy Administrator"
    INVENTORY_STAFF = "inventory_staff", "Inventory Staff"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.SYSTEM_ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.
    - Email is the login identifier (not username).
    - Role determines system-wide permissions.
    - Pharmacy membership is tracked via PharmacyMembership.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=254)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, default="")
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.INVENTORY_STAFF,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Django admin access
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def is_system_admin(self):
        return self.role == UserRole.SYSTEM_ADMIN

    @property
    def is_pharmacy_admin(self):
        return self.role == UserRole.PHARMACY_ADMIN

    @property
    def is_inventory_staff(self):
        return self.role == UserRole.INVENTORY_STAFF

    def get_pharmacy(self):
        """Return the primary pharmacy for this user (first active membership)."""
        membership = self.memberships.filter(is_active=True).select_related("pharmacy").first()
        return membership.pharmacy if membership else None

    def get_pharmacy_ids(self):
        """Return all pharmacy IDs this user is a member of."""
        return list(self.memberships.filter(is_active=True).values_list("pharmacy_id", flat=True))


class PharmacyMembership(models.Model):
    """
    Links a user to a pharmacy with a specific role.
    A user can belong to at most one pharmacy (enforced via unique constraint).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=30,
        choices=[
            (UserRole.PHARMACY_ADMIN, UserRole.PHARMACY_ADMIN.label),
            (UserRole.INVENTORY_STAFF, UserRole.INVENTORY_STAFF.label),
        ],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_pharmacymembership"
        unique_together = [("user", "pharmacy")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.full_name} @ {self.pharmacy.name} ({self.role})"
