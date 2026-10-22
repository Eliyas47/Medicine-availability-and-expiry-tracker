"""
Tests for inventory service, batch views, and movement views.
"""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, PharmacyMembership, UserRole
from apps.pharmacies.models import Pharmacy
from apps.medicines.models import Medicine, Category
from apps.inventory.models import Batch, StockMovement, BatchStatus, MovementType
from apps.inventory.services import compute_batch_status, perform_movement


# ---- Fixtures ----

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def system_admin(db):
    return User.objects.create_user(
        email="sysadmin@test.et", password="Admin123!", full_name="Sys Admin",
        role=UserRole.SYSTEM_ADMIN,
    )


@pytest.fixture
def pharmacy_admin_user(db):
    return User.objects.create_user(
        email="padmin@test.et", password="PAdmin123!", full_name="Pharm Admin",
        role=UserRole.PHARMACY_ADMIN,
    )


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        email="staff@test.et", password="Staff123!", full_name="Staff User",
        role=UserRole.INVENTORY_STAFF,
    )


@pytest.fixture
def pharmacy(db):
    return Pharmacy.objects.create(
        name="Test Pharmacy", license_number="LIC-TEST",
        address="Test Address", city="Addis Ababa", region="Addis Ababa",
        phone="+251911111111", expiry_warning_days=90,
    )


@pytest.fixture
def pharmacy_b(db):
    return Pharmacy.objects.create(
        name="Other Pharmacy", license_number="LIC-OTHER",
        address="Other Address", city="Dire Dawa", region="Dire Dawa",
        phone="+251922222222",
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name="Antibiotics")


@pytest.fixture
def medicine(db, category):
    return Medicine.objects.create(
        generic_name="Amoxicillin", strength="500mg",
        dosage_form="capsule", category=category,
    )


@pytest.fixture
def active_batch(db, pharmacy, medicine, staff_user):
    future = date.today() + timedelta(days=365)
    return Batch.objects.create(
        pharmacy=pharmacy, medicine=medicine,
        batch_number="AMX-001", quantity=100,
        received_date=date.today(), expiry_date=future,
        created_by=staff_user, status=BatchStatus.ACTIVE,
    )


@pytest.fixture
def expired_batch(db, pharmacy, medicine, staff_user):
    past = date.today() - timedelta(days=10)
    return Batch.objects.create(
        pharmacy=pharmacy, medicine=medicine,
        batch_number="AMX-EXP", quantity=50,
        received_date=date.today() - timedelta(days=100),
        expiry_date=past,
        created_by=staff_user, status=BatchStatus.EXPIRED,
    )


def get_token(api_client, email, password):
    resp = api_client.post("/api/auth/login/", {"email": email, "password": password}, format="json")
    return resp.data["access"]


@pytest.fixture
def staff_client(api_client, staff_user, pharmacy):
    PharmacyMembership.objects.create(user=staff_user, pharmacy=pharmacy, role=UserRole.INVENTORY_STAFF)
    token = get_token(api_client, "staff@test.et", "Staff123!")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def admin_client(api_client, pharmacy_admin_user, pharmacy):
    PharmacyMembership.objects.create(user=pharmacy_admin_user, pharmacy=pharmacy, role=UserRole.PHARMACY_ADMIN)
    token = get_token(api_client, "padmin@test.et", "PAdmin123!")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


# ---- Service layer tests ----

class TestComputeBatchStatus:
    def test_depleted_when_zero(self, active_batch):
        active_batch.quantity = 0
        assert compute_batch_status(active_batch) == BatchStatus.DEPLETED

    def test_expired_when_past_expiry(self, active_batch):
        active_batch.expiry_date = date.today() - timedelta(days=1)
        active_batch.quantity = 10
        assert compute_batch_status(active_batch) == BatchStatus.EXPIRED

    def test_expiring_soon_within_window(self, active_batch):
        active_batch.expiry_date = date.today() + timedelta(days=30)
        active_batch.quantity = 10
        assert compute_batch_status(active_batch, warning_days=90) == BatchStatus.EXPIRING_SOON

    def test_active_when_healthy(self, active_batch):
        active_batch.expiry_date = date.today() + timedelta(days=365)
        active_batch.quantity = 100
        assert compute_batch_status(active_batch, warning_days=90) == BatchStatus.ACTIVE


class TestPerformMovement:
    def test_sell_reduces_quantity(self, db, active_batch, staff_user):
        batch, movement = perform_movement(
            batch_id=str(active_batch.pk),
            quantity=-10,
            movement_type=MovementType.SOLD,
            user=staff_user,
        )
        active_batch.refresh_from_db()
        assert active_batch.quantity == 90
        assert movement.quantity == -10
        assert movement.movement_type == MovementType.SOLD

    def test_receive_increases_quantity(self, db, active_batch, staff_user):
        batch, movement = perform_movement(
            batch_id=str(active_batch.pk),
            quantity=50,
            movement_type=MovementType.RECEIVED,
            user=staff_user,
        )
        active_batch.refresh_from_db()
        assert active_batch.quantity == 150

    def test_negative_stock_rejected(self, db, active_batch, staff_user):
        from rest_framework.exceptions import ValidationError
        with pytest.raises(ValidationError):
            perform_movement(
                batch_id=str(active_batch.pk),
                quantity=-200,  # more than available (100)
                movement_type=MovementType.SOLD,
                user=staff_user,
            )
        active_batch.refresh_from_db()
        assert active_batch.quantity == 100  # unchanged

    def test_movement_on_expired_batch_rejected(self, db, expired_batch, staff_user):
        from rest_framework.exceptions import ValidationError
        with pytest.raises(ValidationError):
            perform_movement(
                batch_id=str(expired_batch.pk),
                quantity=-5,
                movement_type=MovementType.SOLD,
                user=staff_user,
            )

    def test_expired_removal_allowed_on_expired_batch(self, db, expired_batch, staff_user):
        batch, movement = perform_movement(
            batch_id=str(expired_batch.pk),
            quantity=-50,
            movement_type=MovementType.EXPIRED_REMOVAL,
            user=staff_user,
        )
        expired_batch.refresh_from_db()
        assert expired_batch.quantity == 0
        assert expired_batch.status == BatchStatus.DEPLETED

    def test_correction_requires_approval(self, db, active_batch, staff_user):
        batch, movement = perform_movement(
            batch_id=str(active_batch.pk),
            quantity=-5,
            movement_type=MovementType.CORRECTION,
            user=staff_user,
            requires_approval=True,
        )
        assert movement.is_approved is False


# ---- Batch API tests ----

class TestBatchAPI:
    def test_staff_can_list_own_batches(self, staff_client, active_batch):
        response = staff_client.get("/api/batches/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_staff_cannot_see_other_pharmacy_batches(self, staff_client, db, pharmacy_b, medicine):
        other_batch = Batch.objects.create(
            pharmacy=pharmacy_b, medicine=medicine,
            batch_number="OTHER-001", quantity=50,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status=BatchStatus.ACTIVE,
        )
        response = staff_client.get("/api/batches/")
        ids = [r["id"] for r in response.data["results"]]
        assert str(other_batch.pk) not in ids

    def test_create_batch_auto_creates_received_movement(self, staff_client, pharmacy, medicine):
        future_date = (date.today() + timedelta(days=400)).isoformat()
        response = staff_client.post("/api/batches/", {
            "medicine_id": str(medicine.pk),
            "batch_number": "NEW-BATCH-001",
            "quantity": 200,
            "received_date": date.today().isoformat(),
            "expiry_date": future_date,
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        batch_id = response.data["id"]
        movement = StockMovement.objects.filter(batch_id=batch_id, movement_type=MovementType.RECEIVED).first()
        assert movement is not None
        assert movement.quantity == 200

    def test_past_expiry_date_rejected(self, staff_client, medicine):
        response = staff_client.post("/api/batches/", {
            "medicine_id": str(medicine.pk),
            "batch_number": "PAST-EXP-001",
            "quantity": 10,
            "received_date": date.today().isoformat(),
            "expiry_date": (date.today() - timedelta(days=1)).isoformat(),
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_expiring_endpoint_returns_correct_batches(self, staff_client, db, pharmacy, medicine, staff_user):
        # Create a batch expiring in 30 days (within 90-day window)
        expiring_batch = Batch.objects.create(
            pharmacy=pharmacy, medicine=medicine,
            batch_number="EXP-SOON-001", quantity=10,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
            status=BatchStatus.EXPIRING_SOON,
        )
        response = staff_client.get("/api/batches/expiring/")
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert str(expiring_batch.pk) in ids

    def test_expired_endpoint_excludes_non_expired(self, staff_client, active_batch, expired_batch):
        response = staff_client.get("/api/batches/expired/")
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert str(expired_batch.pk) in ids
        assert str(active_batch.pk) not in ids


# ---- Movement API tests ----

class TestMovementAPI:
    def test_record_sale(self, staff_client, active_batch):
        response = staff_client.post("/api/movements/", {
            "batch": str(active_batch.pk),
            "movement_type": "sold",
            "quantity": 15,
            "reference_number": "RX-001",
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        active_batch.refresh_from_db()
        assert active_batch.quantity == 85

    def test_oversell_rejected(self, staff_client, active_batch):
        response = staff_client.post("/api/movements/", {
            "batch": str(active_batch.pk),
            "movement_type": "sold",
            "quantity": 500,  # more than 100 available
        }, format="json")
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
        active_batch.refresh_from_db()
        assert active_batch.quantity == 100  # unchanged

    def test_correction_requires_admin_approval(self, staff_client, active_batch):
        response = staff_client.post("/api/movements/", {
            "batch": str(active_batch.pk),
            "movement_type": "correction",
            "quantity": 5,
            "notes": "Count correction",
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_approved"] is False

    def test_admin_can_approve_correction(self, db, pharmacy, medicine, staff_user, pharmacy_admin_user):
        """Admin approves a correction that staff created."""
        from rest_framework.test import APIClient

        # Ensure memberships exist
        PharmacyMembership.objects.get_or_create(
            user=staff_user, pharmacy=pharmacy,
            defaults={"role": UserRole.INVENTORY_STAFF}
        )
        PharmacyMembership.objects.get_or_create(
            user=pharmacy_admin_user, pharmacy=pharmacy,
            defaults={"role": UserRole.PHARMACY_ADMIN}
        )

        # Active batch
        batch = Batch.objects.create(
            pharmacy=pharmacy, medicine=medicine,
            batch_number="APPROVE-TEST", quantity=100,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status=BatchStatus.ACTIVE,
        )

        # Staff client posts correction
        sc = APIClient()
        sc_token = get_token(sc, "staff@test.et", "Staff123!")
        sc.credentials(HTTP_AUTHORIZATION=f"Bearer {sc_token}")
        resp = sc.post("/api/movements/", {
            "batch": str(batch.pk),
            "movement_type": "correction",
            "quantity": 3,
            "notes": "Admin approval test",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        movement_id = resp.data["id"]

        # Admin client approves
        ac = APIClient()
        ac_token = get_token(ac, "padmin@test.et", "PAdmin123!")
        ac.credentials(HTTP_AUTHORIZATION=f"Bearer {ac_token}")
        approve_resp = ac.post(f"/api/movements/{movement_id}/approve/")
        assert approve_resp.status_code == status.HTTP_200_OK
        assert approve_resp.data["is_approved"] is True


# ---- Availability search tests ----

class TestAvailabilitySearch:
    def test_search_returns_pharmacy_with_stock(self, api_client, active_batch):
        response = api_client.get("/api/availability/?medicine=Amoxicillin")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
        result = response.data["results"][0]
        assert result["usable_quantity"] > 0

    def test_expired_stock_excluded(self, api_client, db, pharmacy, medicine):
        # Only expired batch — should not appear
        Batch.objects.filter(pharmacy=pharmacy, medicine=medicine).delete()
        Batch.objects.create(
            pharmacy=pharmacy, medicine=medicine,
            batch_number="EXP-ONLY", quantity=50,
            received_date=date.today() - timedelta(days=200),
            expiry_date=date.today() - timedelta(days=5),
            status=BatchStatus.EXPIRED,
        )
        response = api_client.get("/api/availability/?medicine=Amoxicillin")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_search_requires_medicine_param(self, api_client):
        response = api_client.get("/api/availability/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_city_filter(self, api_client, active_batch):
        response = api_client.get("/api/availability/?medicine=Amoxicillin&city=Addis+Ababa")
        assert response.status_code == status.HTTP_200_OK
        for r in response.data["results"]:
            assert "Addis Ababa" in r["pharmacy"]["city"]
