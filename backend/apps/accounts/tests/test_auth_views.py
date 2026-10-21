"""
Integration tests for authentication endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, UserRole


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        email="staff@test.et",
        password="StaffPass123",
        full_name="Test Staff",
        role=UserRole.INVENTORY_STAFF,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@test.et",
        password="AdminPass123",
        full_name="System Admin",
        role=UserRole.SYSTEM_ADMIN,
        is_staff=True,
    )


@pytest.fixture
def auth_client(api_client, staff_user):
    """API client pre-authenticated as inventory staff."""
    response = api_client.post(
        reverse("auth-login"),
        {"email": "staff@test.et", "password": "StaffPass123"},
        format="json",
    )
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


# ---- Registration ----

class TestRegister:
    def test_register_success(self, api_client, db):
        response = api_client.post(
            reverse("auth-register"),
            {
                "email": "newuser@test.et",
                "full_name": "New User",
                "password": "NewPass123",
                "password_confirm": "NewPass123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="newuser@test.et").exists()

    def test_register_duplicate_email(self, api_client, staff_user):
        response = api_client.post(
            reverse("auth-register"),
            {
                "email": "staff@test.et",
                "full_name": "Another User",
                "password": "AnotherPass123",
                "password_confirm": "AnotherPass123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, api_client, db):
        response = api_client.post(
            reverse("auth-register"),
            {
                "email": "new@test.et",
                "full_name": "User",
                "password": "Pass12345",
                "password_confirm": "Different12",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, api_client, db):
        response = api_client.post(
            reverse("auth-register"),
            {
                "email": "weak@test.et",
                "full_name": "Weak Pass User",
                "password": "password",  # no digits
                "password_confirm": "password",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_defaults_to_inventory_staff(self, api_client, db):
        api_client.post(
            reverse("auth-register"),
            {
                "email": "newstaff@test.et",
                "full_name": "Staff User",
                "password": "StaffPass123",
                "password_confirm": "StaffPass123",
            },
            format="json",
        )
        user = User.objects.get(email="newstaff@test.et")
        assert user.role == UserRole.INVENTORY_STAFF


# ---- Login ----

class TestLogin:
    def test_login_success(self, api_client, staff_user):
        response = api_client.post(
            reverse("auth-login"),
            {"email": "staff@test.et", "password": "StaffPass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == "staff@test.et"

    def test_login_wrong_password(self, api_client, staff_user):
        response = api_client.post(
            reverse("auth-login"),
            {"email": "staff@test.et", "password": "WrongPassword1"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_wrong_email(self, api_client, db):
        response = api_client.post(
            reverse("auth-login"),
            {"email": "nobody@test.et", "password": "SomePass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_deactivated_user(self, api_client, staff_user):
        staff_user.is_active = False
        staff_user.save()
        response = api_client.post(
            reverse("auth-login"),
            {"email": "staff@test.et", "password": "StaffPass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---- Token Refresh ----

class TestTokenRefresh:
    def test_refresh_success(self, api_client, staff_user):
        # Login first
        login_response = api_client.post(
            reverse("auth-login"),
            {"email": "staff@test.et", "password": "StaffPass123"},
            format="json",
        )
        refresh_token = login_response.data["refresh"]

        # Refresh
        response = api_client.post(
            reverse("token-refresh"),
            {"refresh": refresh_token},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_invalid_token(self, api_client, db):
        response = api_client.post(
            reverse("token-refresh"),
            {"refresh": "not-a-valid-token"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---- Logout ----

class TestLogout:
    def test_logout_success(self, api_client, staff_user):
        login_response = api_client.post(
            reverse("auth-login"),
            {"email": "staff@test.et", "password": "StaffPass123"},
            format="json",
        )
        access = login_response.data["access"]
        refresh = login_response.data["refresh"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.post(
            reverse("auth-logout"),
            {"refresh": refresh},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # Refresh should now fail (token is blacklisted)
        refresh_response = api_client.post(
            reverse("token-refresh"),
            {"refresh": refresh},
            format="json",
        )
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_requires_auth(self, api_client, db):
        response = api_client.post(reverse("auth-logout"), {"refresh": "token"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---- Profile ----

class TestProfile:
    def test_get_profile(self, auth_client, staff_user):
        response = auth_client.get(reverse("auth-profile"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "staff@test.et"

    def test_update_profile(self, auth_client, staff_user):
        response = auth_client.patch(
            reverse("auth-profile"),
            {"full_name": "Updated Name"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "Updated Name"
        staff_user.refresh_from_db()
        assert staff_user.full_name == "Updated Name"

    def test_cannot_change_role_via_profile(self, auth_client, staff_user):
        response = auth_client.patch(
            reverse("auth-profile"),
            {"role": "system_admin"},
            format="json",
        )
        staff_user.refresh_from_db()
        assert staff_user.role == UserRole.INVENTORY_STAFF  # role unchanged

    def test_profile_requires_auth(self, api_client, db):
        response = api_client.get(reverse("auth-profile"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---- Change Password ----

class TestChangePassword:
    def test_change_password_success(self, auth_client, staff_user):
        response = auth_client.post(
            reverse("auth-change-password"),
            {
                "current_password": "StaffPass123",
                "new_password": "NewStaff456!",
                "new_password_confirm": "NewStaff456!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        staff_user.refresh_from_db()
        assert staff_user.check_password("NewStaff456!")

    def test_change_password_wrong_current(self, auth_client):
        response = auth_client.post(
            reverse("auth-change-password"),
            {
                "current_password": "WrongCurrent1",
                "new_password": "NewPass123!",
                "new_password_confirm": "NewPass123!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_mismatch(self, auth_client):
        response = auth_client.post(
            reverse("auth-change-password"),
            {
                "current_password": "StaffPass123",
                "new_password": "NewPass123!",
                "new_password_confirm": "DifferentPass1",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
