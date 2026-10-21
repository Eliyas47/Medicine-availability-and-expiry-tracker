"""
Tests for system admin user management endpoints.
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
def system_admin(db):
    return User.objects.create_user(
        email="sysadmin@test.et",
        password="SysAdmin123",
        full_name="System Admin",
        role=UserRole.SYSTEM_ADMIN,
        is_staff=True,
    )


@pytest.fixture
def pharmacy_admin(db):
    return User.objects.create_user(
        email="pharm@test.et",
        password="PharmAdmin123",
        full_name="Pharmacy Admin",
        role=UserRole.PHARMACY_ADMIN,
    )


@pytest.fixture
def inventory_staff(db):
    return User.objects.create_user(
        email="staff@test.et",
        password="StaffPass123",
        full_name="Inventory Staff",
        role=UserRole.INVENTORY_STAFF,
    )


@pytest.fixture
def admin_client(api_client, system_admin):
    response = api_client.post(
        reverse("auth-login"),
        {"email": "sysadmin@test.et", "password": "SysAdmin123"},
        format="json",
    )
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def staff_client(api_client, inventory_staff):
    response = api_client.post(
        reverse("auth-login"),
        {"email": "staff@test.et", "password": "StaffPass123"},
        format="json",
    )
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


class TestUserManagement:
    def test_admin_can_list_users(self, admin_client, system_admin, inventory_staff):
        response = admin_client.get("/api/users/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 2

    def test_staff_cannot_list_users(self, staff_client):
        response = staff_client.get("/api/users/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_create_user(self, admin_client):
        response = admin_client.post(
            "/api/users/",
            {
                "email": "newuser@test.et",
                "full_name": "New User",
                "role": "pharmacy_admin",
                "password": "NewUser123",
                "password_confirm": "NewUser123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="newuser@test.et").exists()

    def test_admin_can_deactivate_user(self, admin_client, inventory_staff):
        response = admin_client.post(f"/api/users/{inventory_staff.pk}/deactivate/")
        assert response.status_code == status.HTTP_200_OK
        inventory_staff.refresh_from_db()
        assert inventory_staff.is_active is False

    def test_admin_can_activate_user(self, admin_client, inventory_staff):
        inventory_staff.is_active = False
        inventory_staff.save()
        response = admin_client.post(f"/api/users/{inventory_staff.pk}/activate/")
        assert response.status_code == status.HTTP_200_OK
        inventory_staff.refresh_from_db()
        assert inventory_staff.is_active is True

    def test_admin_cannot_deactivate_self(self, admin_client, system_admin):
        response = admin_client.post(f"/api/users/{system_admin.pk}/deactivate/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_by_role(self, admin_client, system_admin, inventory_staff, pharmacy_admin):
        response = admin_client.get("/api/users/?role=inventory_staff")
        assert response.status_code == status.HTTP_200_OK
        for user_data in response.data["results"]:
            assert user_data["role"] == "inventory_staff"
