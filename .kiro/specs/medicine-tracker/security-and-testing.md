# Security & Authorization Design + Testing Strategy
## Medicine Availability & Expiry Tracker

---

## Part A: Security & Authorization

### 1. Permission Matrix

| Resource | Action | public | inventory_staff | pharmacy_admin | system_admin |
|----------|--------|--------|-----------------|----------------|--------------|
| Auth endpoints | register/login/refresh | ✅ | ✅ | ✅ | ✅ |
| Own profile | view/edit | — | ✅ | ✅ | ✅ |
| All users | view/create/edit | ❌ | ❌ | ❌ | ✅ |
| Pharmacies (public) | list/view | ✅ | ✅ | ✅ | ✅ |
| Pharmacies (manage) | create/delete | ❌ | ❌ | ❌ | ✅ |
| Own pharmacy | edit | ❌ | ❌ | ✅ | ✅ |
| Other pharmacy | edit | ❌ | ❌ | ❌ | ✅ |
| Pharmacy members | manage | ❌ | ❌ | ✅ (own) | ✅ |
| Medicine catalog | view | ✅ | ✅ | ✅ | ✅ |
| Medicine catalog | create/edit/delete | ❌ | ❌ | ❌ | ✅ |
| Categories | view | ✅ | ✅ | ✅ | ✅ |
| Categories | create/edit/delete | ❌ | ❌ | ❌ | ✅ |
| Batches (own pharmacy) | view | ❌ | ✅ | ✅ | ✅ |
| Batches (own pharmacy) | create | ❌ | ✅ | ✅ | ✅ |
| Batches (own pharmacy) | edit | ❌ | ❌ | ✅ | ✅ |
| Batches (other pharmacy) | any | ❌ | ❌ | ❌ | ✅ |
| Movements (own pharmacy) | view | ❌ | ✅ | ✅ | ✅ |
| Movements (own pharmacy) | create | ❌ | ✅ | ✅ | ✅ |
| Corrections | approve | ❌ | ❌ | ✅ (own) | ✅ |
| Dashboard | own pharmacy | ❌ | ✅ | ✅ | ✅ |
| Dashboard | system-wide | ❌ | ❌ | ❌ | ✅ |
| Availability search | view | ✅ | ✅ | ✅ | ✅ |
| Reports | own pharmacy | ❌ | ✅ | ✅ | ✅ |
| Audit logs | view | ❌ | ❌ | ❌ | ✅ |
| System config | view/edit | ❌ | ❌ | ❌ | ✅ |

---

### 2. Custom DRF Permission Classes

```python
# apps/core/permissions.py

class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'system_admin'

class IsPharmacyAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('system_admin', 'pharmacy_admin')

class IsPharmacyMember(BasePermission):
    """True if user has any membership in a pharmacy (admin or staff)."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role != 'public'

class IsOwnPharmacy(BasePermission):
    """Object-level: user must belong to the pharmacy this resource belongs to."""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'system_admin':
            return True
        pharmacy_id = getattr(obj, 'pharmacy_id', None) or getattr(obj, 'id', None)
        return request.user.memberships.filter(
            pharmacy_id=pharmacy_id, is_active=True
        ).exists()
```

---

### 3. JWT Configuration (Simple JWT)

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_BLACKLIST_ENABLED': True,
}
```

Frontend token handling:
- Access token stored in memory (React state / context).
- Refresh token stored in `localStorage` (v1, acceptable for non-bank-grade; documented).
- Silent refresh: Axios interceptor catches 401, calls `/api/auth/token/refresh/`, retries original request once.
- On refresh failure → clear tokens → redirect to login.

---

### 4. Pharmacy Isolation

All viewsets that deal with pharmacy-owned data override `get_queryset()`:

```python
def get_queryset(self):
    user = self.request.user
    if user.role == 'system_admin':
        return Batch.objects.all()
    pharmacy_ids = user.memberships.filter(is_active=True).values_list('pharmacy_id', flat=True)
    return Batch.objects.filter(pharmacy_id__in=pharmacy_ids)
```

This means even if a client sends `?pharmacy=other-uuid`, they only see their own data.

---

### 5. Concurrency Safety

All stock-modifying views use a transaction with row-level lock:

```python
@transaction.atomic
def perform_movement(batch_id, quantity, movement_type, user):
    batch = Batch.objects.select_for_update().get(pk=batch_id)
    new_qty = batch.quantity + quantity  # quantity is signed
    if new_qty < 0:
        raise ValidationError("Insufficient stock.")
    batch.quantity = new_qty
    batch.status = compute_batch_status(batch)
    batch.save(update_fields=['quantity', 'status', 'updated_at'])
    StockMovement.objects.create(
        pharmacy=batch.pharmacy,
        medicine=batch.medicine,
        batch=batch,
        movement_type=movement_type,
        quantity=quantity,
        performed_by=user,
    )
    return batch
```

---

### 6. Input Validation

- DRF serializers validate all incoming data.
- Model `clean()` methods enforce business rules (expiry date, positive quantity).
- Database `CheckConstraint` ensures `quantity >= 0` at the DB level.
- Expiry date validation: `expiry_date > date.today()` enforced in serializer.

---

## Part B: Testing Strategy

### 1. Backend Tests (pytest + pytest-django)

#### Directory Layout
```
backend/
└── apps/
    ├── accounts/
    │   └── tests/
    │       ├── test_models.py
    │       ├── test_serializers.py
    │       └── test_views.py
    ├── pharmacies/tests/
    ├── medicines/tests/
    ├── inventory/tests/
    │   ├── test_batch_views.py
    │   ├── test_movement_service.py   ← concurrency tests here
    │   └── test_availability.py
    ├── reports/tests/
    └── audit/tests/
```

#### Test Categories

**Unit Tests (services & models)**
- `test_compute_batch_status`: all status transitions
- `test_usable_quantity_excludes_expired`: set expiry=yesterday, verify qty=0
- `test_negative_stock_rejected`: movement that would make qty < 0
- `test_expiry_in_past_rejected`: creating batch with past expiry
- `test_audit_log_created_on_batch_create`: signal fires, log written

**Integration Tests (API views)**
- Auth: register, login, refresh, logout, wrong password
- RBAC: each role attempting each resource → assert 200 / 403
- Pharmacy isolation: staff at pharmacy A cannot see pharmacy B's batches
- Batch creation → movement auto-created
- Movement creation → batch quantity updated
- Correction approval workflow
- CSV export returns `text/csv` with correct headers

**Concurrency Tests**
- Two threads simultaneously reduce the same batch by 50 (batch has 60). One should succeed, one should fail with 422.

#### Configuration
```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --reuse-db --strict-markers
```

```python
# conftest.py fixtures
@pytest.fixture
def system_admin(db): ...
@pytest.fixture
def pharmacy_admin(db): ...
@pytest.fixture
def inventory_staff(db): ...
@pytest.fixture
def pharmacy(db): ...
@pytest.fixture
def medicine(db): ...
@pytest.fixture
def batch(db, pharmacy, medicine): ...
@pytest.fixture
def api_client(): return APIClient()
@pytest.fixture
def auth_client(api_client, inventory_staff): 
    # returns client with staff JWT
```

---

### 2. Frontend Tests

#### Tool: Vitest + React Testing Library + MSW (Mock Service Worker)

**Unit Tests**
- Utility functions: `formatDate`, `daysUntilExpiry`, `computeStatus`
- Form validation schemas (Zod)
- Custom hooks: `useAuth`, `useDebounce`

**Component Tests**
- `StatusBadge` renders correct color and label per status
- `ExpiryCountdown` shows red for expired, orange for <30 days
- `DataTable` renders rows, sorts, paginates
- `BatchFormPage` shows validation errors on submit with missing fields
- `ConfirmDialog` calls onConfirm/onCancel correctly

**Integration Tests (with MSW)**
- `LoginPage`: successful login → redirects to dashboard
- `AvailabilitySearchPage`: search → results shown; no results → empty state
- `BatchListPage`: loads and displays batch data; filter changes refetch

---

### 3. Coverage Targets

| Area | Target |
|------|--------|
| Backend business logic (services, models) | ≥ 85% |
| Backend API views | ≥ 80% |
| Backend permissions | 100% (all role combinations tested) |
| Frontend utilities | ≥ 80% |
| Frontend components | ≥ 70% |

---

### 4. CI/CD Notes (future)

When a CI pipeline is added:
1. `python -m pytest --cov=apps --cov-report=term-missing`
2. `npm run test -- --run` (Vitest single run)
3. `python manage.py check --deploy` on production settings
4. `npm run build` — must succeed with no type errors
