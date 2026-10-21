"""
Serializers for user accounts and authentication.
"""
import re
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, PharmacyMembership, UserRole


# ---------------------------------------------------------------------------
# Auth serializers
# ---------------------------------------------------------------------------

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["email", "full_name", "phone", "password", "password_confirm"]

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        # Use Django's built-in validators (min length, common passwords, etc.)
        validate_password(value)
        # Additional complexity: at least one letter and one digit
        if not re.search(r"[A-Za-z]", value):
            raise serializers.ValidationError("Password must contain at least one letter.")
        if not re.search(r"\d", value):
            raise serializers.ValidationError("Password must contain at least one number.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        # New self-registrations default to inventory_staff
        # pharmacy_admin is assigned by a system_admin
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        email = attrs.get("email", "").lower()
        password = attrs.get("password")

        user = authenticate(request=self.context.get("request"), username=email, password=password)

        if not user:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid email or password."]},
                code="authentication_failed",
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"non_field_errors": ["This account has been deactivated."]},
                code="account_disabled",
            )

        attrs["user"] = user
        return attrs


class TokenResponseSerializer(serializers.Serializer):
    """Shape of the login response."""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        user = obj["user"]
        return UserSerializer(user).data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


# ---------------------------------------------------------------------------
# User serializers
# ---------------------------------------------------------------------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "phone", "role",
            "is_active", "date_joined", "last_login",
        ]
        read_only_fields = ["id", "email", "date_joined", "last_login"]


class UserProfileSerializer(serializers.ModelSerializer):
    """For updating own profile (cannot change email or role)."""
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "phone", "role", "is_active", "date_joined"]
        read_only_fields = ["id", "email", "role", "is_active", "date_joined"]


class UserAdminSerializer(serializers.ModelSerializer):
    """For system admin user management — can set role and is_active."""
    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "phone", "role",
            "is_active", "is_staff", "date_joined", "last_login",
        ]
        read_only_fields = ["id", "email", "date_joined", "last_login"]


class CreateUserSerializer(serializers.ModelSerializer):
    """System admin creates a user (can set any role)."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "full_name", "phone", "role", "password", "password_confirm"]

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


# ---------------------------------------------------------------------------
# Membership serializers
# ---------------------------------------------------------------------------

class PharmacyMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    pharmacy_name = serializers.CharField(source="pharmacy.name", read_only=True)

    class Meta:
        model = PharmacyMembership
        fields = ["id", "user", "pharmacy", "pharmacy_name", "role", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class AddMemberSerializer(serializers.Serializer):
    """Add a user to a pharmacy by email."""
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[(UserRole.PHARMACY_ADMIN, "Pharmacy Admin"), (UserRole.INVENTORY_STAFF, "Inventory Staff")]
    )

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value.lower())
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        if user.role == UserRole.SYSTEM_ADMIN:
            raise serializers.ValidationError("System administrators cannot be added as pharmacy members.")
        return value.lower()
