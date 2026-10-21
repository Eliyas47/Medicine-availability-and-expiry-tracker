"""
Tests for pharmacy management endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, PharmacyMembership, UserRole
from apps.pharmacies.models import Pharmacy


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def system_admin(db):
    return User.objects.create_user(
        email="sysadmin@test.et", password="SysAdmin123",
        full_name="System Admin", role=UserRole.SYSTEM_ADMIN,
    )


@pytest.fixture
def pharmacy_admin_user(db):
    return User.objects.create_user(
        email="pharm_admin@test.et", password="PharmAdmin123",
        full_name="Pharmacy Admin", role=UserRole.PHARMACY_ADMIN,
    )


@pytest.fixture
def inventory_staff_user(db):
    return User.objects.create_user(
        email="staff@test.et", password="StaffPass123",
        full_name="Staff User", role=UserRole.INVENTORY_STAFF,
    )


@pytest.fixture
def pharmacy_a(db):
    return Pharmacy.objects.create(
        name="Apollo Pharmacy", license_number="LIC-001",
        address="Bole Road", city="Addis Ababa", region="Addis Ababa",
        phone="+251111111111",
    )


@pytest.fixture
def pharmacy_b(db):
    return Pharmacy.objects.create(
        name="Beta Pharmacy", license_number="LIC-002",
        address="Piassa", city="Addis Ababa", region="Addis Ababa",
        phone="+251222222222",
    )


@pytest.fixture
def pharmacy_admin_membership(pharmacy_admin_user, pharmacy_a):
    return PharmacyMembership.objects.create(
        user=pharmacy_admin_user, pharmacy=pharmacy_a, role=UserRole.PHARMACY_ADMIN,
    )


@pytest.fixture
def admin_client(api_client, system_admin):
    resp = api_client.post("/api/auth/login/", {"email": "sysadmin@test.et", "password": "SysAdmin123"}, format="json")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return api_client


@pytest.fixture
def pharm_admin_client(api_client, pharmacy_admin_user, pharmacy_admin_membership):
    resp = api_client.post("/api/auth/login/", {"email": "pharm_admin@test.et", "password": "PharmAdmin123"}, format="json")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return api_client


@pytest.fixture
def staff_client(api_client, inventory_staff_user, pharmacy_a):
    PharmacyMembership.objects.create(
        user=inventory_staff_user, pharmacy=pharmacy_a, role=UserRole.INVENTORY_STAFF,
    )
    resp = api_client.post("/api/auth/login/", {"email": "staff@test.et", "password": "StaffPass123"}, format="json")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return api_client


class TestPharmacyPublicAccess:
    def test_public_can_list_pharmacies(self, api_client, pharmacy_a, pharmacy_b):
        response = api_client.get("/api/pharmacies/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_public_sees_limited_fields(self, api_client, pharmacy_a):
        response = api_client.get(f"/api/pharmacies/{pharmacy_a.pk}/")
        assert response.status_code == status.HTTP_200_OK
        # Public should NOT see license_number or expiry_warning_days
        assert "license_number" not in response.data
        assert "expiry_warning_days" not in response.data

    def test_public_cannot_create_pharmacy(self, api_client):
        response = api_client.post("/api/pharmacies/", {
            "name": "New Pharmacy", "license_number": "LIC-999",
            "address": "Test", "city": "Addis Ababa", "region": "Addis Ababa",
            "phone": "+251999999999",
        }, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPharmacyCRUD:
    def test_system_admin_can_create_pharmacy(self, admin_client):
        response = admin_client.post("/api/pharmacies/", {
            "name": "New Pharmacy", "license_number": "LIC-NEW",
            "address": "Test", "city": "Addis Ababa", "region": "Addis Ababa",
            "phone": "+251333333333",
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_duplicate_license_rejected(self, admin_client, pharmacy_a):
        response = admin_client.post("/api/pharmacies/", {
            "name": "Another", "license_number": "LIC-001",  # duplicate
            "address": "Test", "city": "Addis Ababa", "region": "Addis Ababa",
            "phone": "+251444444444",
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_pharmacy_admin_can_edit_own(self, pharm_admin_client, pharmacy_a):
        response = pharm_admin_client.patch(
            f"/api/pharmacies/{pharmacy_a.pk}/",
            {"phone": "+251555555555"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_pharmacy_admin_cannot_edit_other(self, pharm_admin_client, pharmacy_b):
        response = pharm_admin_client.patch(
            f"/api/pharmacies/{pharmacy_b.pk}/",
            {"phone": "+251910937423"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_staff_cannot_edit_pharmacy(self, staff_client, pharmacy_a):
        response = staff_client.patch(
            f"/api/pharmacies/{pharmacy_a.pk}/",
            {"phone": "+251777777777"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_system_admin_soft_deletes_pharmacy(self, admin_client, pharmacy_a):
        response = admin_client.delete(f"/api/pharmacies/{pharmacy_a.pk}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        pharmacy_a.refresh_from_db()
        assert pharmacy_a.is_active is False


class TestPharmacySearch:
    def test_search_by_name(self, api_client, pharmacy_a, pharmacy_b):
        response = api_client.get("/api/pharmacies/?search=Apollo")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Apollo Pharmacy"

    def test_filter_by_city(self, api_client, pharmacy_a, pharmacy_b):
        response = api_client.get("/api/pharmacies/?city=Addis+Ababa")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 2
