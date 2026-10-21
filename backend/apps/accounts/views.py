"""
Authentication and user profile views.
"""
from django.contrib.auth import login
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.core.permissions import IsSystemAdmin
from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserAdminSerializer,
    CreateUserSerializer,
    ChangePasswordSerializer,
)


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Register a new user (defaults to inventory_staff role).
    """
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, tags=["auth"])
    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Registration successful. You can now log in."},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/auth/login/
    Returns JWT access + refresh tokens and user info.
    """
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, tags=["auth"])
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklist the provided refresh token.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["auth"])
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": {"code": "validation_error", "message": "Refresh token is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            # Already blacklisted or invalid — still return success (idempotent logout)
            pass
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET/PATCH /api/auth/profile/
    View or update the authenticated user's own profile.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    @extend_schema(tags=["auth"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["auth"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    # Disable full PUT — only PATCH is supported
    def put(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Change the authenticated user's password (requires current password).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, tags=["auth"])
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Blacklist all existing tokens after password change
        try:
            # If refresh token was sent, blacklist it
            refresh_token = request.data.get("refresh")
            if refresh_token:
                RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass

        return Response(
            {"message": "Password changed successfully. Please log in again."},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# System admin user management
# ---------------------------------------------------------------------------

class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/users/  — List all users (system admin only)
    POST /api/users/  — Create a user with any role (system admin only)
    """
    permission_classes = [IsSystemAdmin]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateUserSerializer
        return UserAdminSerializer

    def get_queryset(self):
        qs = User.objects.all()
        role = self.request.query_params.get("role")
        is_active = self.request.query_params.get("is_active")
        search = self.request.query_params.get("search")
        if role:
            qs = qs.filter(role=role)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        if search:
            qs = qs.filter(full_name__icontains=search) | qs.filter(email__icontains=search)
        return qs

    @extend_schema(tags=["users"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["users"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    GET/PATCH /api/users/{id}/  — Manage a specific user (system admin only)
    """
    permission_classes = [IsSystemAdmin]
    serializer_class = UserAdminSerializer
    queryset = User.objects.all()

    @extend_schema(tags=["users"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["users"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class UserActivateView(APIView):
    """POST /api/users/{pk}/activate/ — Activate a deactivated user."""
    permission_classes = [IsSystemAdmin]

    @extend_schema(tags=["users"])
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "User not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response({"message": f"User {user.email} has been activated."})


class UserDeactivateView(APIView):
    """POST /api/users/{pk}/deactivate/ — Deactivate a user account."""
    permission_classes = [IsSystemAdmin]

    @extend_schema(tags=["users"])
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "User not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if user == request.user:
            return Response(
                {"error": {"code": "validation_error", "message": "You cannot deactivate your own account."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response({"message": f"User {user.email} has been deactivated."})
