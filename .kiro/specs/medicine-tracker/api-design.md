# API Endpoint Design
## Medicine Availability & Expiry Tracker

Base URL: `/api/`  
Authentication: `Authorization: Bearer <access_token>` (except public endpoints)  
Pagination: `?page=1&page_size=20` on all list endpoints  
Format: JSON unless `?format=csv` is specified on report endpoints

---

## 1. Authentication (`/api/auth/`)

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| POST | `/api/auth/register/` | No | — | Register new user (staff/pharmacy_admin) |
| POST | `/api/auth/login/` | No | — | Login → access + refresh tokens |
| POST | `/api/auth/logout/` | Yes | Any | Blacklist refresh token |
| POST | `/api/auth/token/refresh/` | No | — | Exchange refresh → new access token |
| GET | `/api/auth/profile/` | Yes | Any | Get own profile |
| PATCH | `/api/auth/profile/` | Yes | Any | Update own profile |
| POST | `/api/auth/change-password/` | Yes | Any | Change password (requires current) |

### Register Request Body
```json
{
  "email": "staff@pharma.et",
  "full_name": "Abebe Kebede",
  "phone": "+251911000000",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!"
}
```

### Login Response
```json
{
  "access": "<jwt>",
  "refresh": "<jwt>",
  "user": {
    "id": "uuid",
    "email": "staff@pharma.et",
    "full_name": "Abebe Kebede",
    "role": "inventory_staff"
  }
}
```

---

## 2. Users (`/api/users/`) — system_admin only

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/users/` | List all users (filterable by role, is_active) |
| GET | `/api/users/{id}/` | Get user detail |
| PATCH | `/api/users/{id}/` | Update user (role, is_active) |
| POST | `/api/users/{id}/deactivate/` | Deactivate user account |
| POST | `/api/users/{id}/activate/` | Reactivate user account |
| POST | `/api/users/` | Create user (system_admin creates system_admin accounts) |

---

## 3. Pharmacies (`/api/pharmacies/`)

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/api/pharmacies/` | No | Public | List active pharmacies (public fields only) |
| POST | `/api/pharmacies/` | Yes | system_admin | Create pharmacy |
| GET | `/api/pharmacies/{id}/` | No | Public | Get pharmacy detail (public fields) |
| PUT/PATCH | `/api/pharmacies/{id}/` | Yes | system_admin, pharmacy_admin (own) | Update pharmacy |
| DELETE | `/api/pharmacies/{id}/` | Yes | system_admin | Soft-delete (set is_active=false) |
| GET | `/api/pharmacies/{id}/members/` | Yes | pharmacy_admin (own), system_admin | List staff members |
| POST | `/api/pharmacies/{id}/members/` | Yes | pharmacy_admin (own), system_admin | Add staff member |
| DELETE | `/api/pharmacies/{id}/members/{user_id}/` | Yes | pharmacy_admin (own), system_admin | Remove staff member |

### Public pharmacy list query params
- `?city=Addis+Ababa`
- `?region=Addis+Ababa`
- `?search=Apollo` (name search)
- `?is_active=true`

---

## 4. Medicine Categories (`/api/categories/`)

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/api/categories/` | No | Public | List all active categories |
| POST | `/api/categories/` | Yes | system_admin | Create category |
| GET | `/api/categories/{id}/` | No | Public | Get category |
| PATCH | `/api/categories/{id}/` | Yes | system_admin | Update category |
| DELETE | `/api/categories/{id}/` | Yes | system_admin | Soft-delete |

---

## 5. Medicines (`/api/medicines/`)

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/api/medicines/` | No | Public | List medicines (filterable, searchable) |
| POST | `/api/medicines/` | Yes | system_admin | Create medicine |
| GET | `/api/medicines/{id}/` | No | Public | Get medicine detail |
| PUT/PATCH | `/api/medicines/{id}/` | Yes | system_admin | Update medicine |
| DELETE | `/api/medicines/{id}/` | Yes | system_admin | Soft-delete |

### Query params
- `?search=amoxicillin` (generic or brand name)
- `?category={uuid}`
- `?dosage_form=tablet`
- `?requires_prescription=true`

---

## 6. Pharmacy Medicines (thresholds) (`/api/pharmacies/{id}/medicines/`)

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/api/pharmacies/{id}/medicines/` | Yes | pharmacy members, system_admin | List medicines tracked by this pharmacy |
| POST | `/api/pharmacies/{id}/medicines/` | Yes | pharmacy_admin (own) | Start tracking a medicine (set threshold) |
| PATCH | `/api/pharmacies/{id}/medicines/{medicine_id}/` | Yes | pharmacy_admin (own) | Update threshold |
| DELETE | `/api/pharmacies/{id}/medicines/{medicine_id}/` | Yes | pharmacy_admin (own) | Stop tracking |

---

## 7. Inventory Batches (`/api/batches/`)

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/api/batches/` | Yes | pharmacy members, system_admin | List batches for user's pharmacy |
| POST | `/api/batches/` | Yes | pharmacy_admin, inventory_staff | Create batch (adds `received` movement) |
| GET | `/api/batches/{id}/` | Yes | pharmacy members, system_admin | Get batch detail |
| PATCH | `/api/batches/{id}/` | Yes | pharmacy_admin (own) | Update non-quantity fields |
| DELETE | `/api/batches/{id}/` | Yes | pharmacy_admin (own) | Only if quantity=0 |
| GET | `/api/batches/expiring/` | Yes | pharmacy members | Batches expiring within warning window |
| GET | `/api/batches/expired/` | Yes | pharmacy members | All expired batches |
| GET | `/api/batches/low-stock/` | Yes | pharmacy members | Batches below threshold |

### Query params
- `?pharmacy={uuid}` (system_admin only; staff scoped automatically)
- `?medicine={uuid}`
- `?status=active|low_stock|expiring_soon|expired|depleted`
- `?expiry_before=2025-01-01`
- `?expiry_after=2024-01-01`

### Batch Response
```json
{
  "id": "uuid",
  "pharmacy": {"id": "uuid", "name": "Apollo Pharmacy"},
  "medicine": {"id": "uuid", "generic_name": "Amoxicillin", "strength": "500mg", "dosage_form": "capsule"},
  "batch_number": "AMX-2024-001",
  "quantity": 150,
  "received_date": "2024-03-01",
  "expiry_date": "2026-03-01",
  "supplier": "Addis Pharma Dist.",
  "unit_cost": "12.50",
  "status": "active",
  "days_until_expiry": 327,
  "created_at": "2024-03-01T10:00:00Z"
}
```

---

## 8. Stock Movements (`/api/movements/`)

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/api/movements/` | Yes | pharmacy members, system_admin | List movements (paginated) |
| POST | `/api/movements/` | Yes | pharmacy_admin, inventory_staff | Record a movement |
| GET | `/api/movements/{id}/` | Yes | pharmacy members, system_admin | Get movement detail |
| POST | `/api/movements/{id}/approve/` | Yes | pharmacy_admin (own), system_admin | Approve a pending correction |

### Movement Request Body
```json
{
  "batch": "uuid",
  "movement_type": "sold",
  "quantity": 10,
  "unit_price": "15.00",
  "reference_number": "RX-00123",
  "notes": "Sold to patient"
}
```

### Movement Response
```json
{
  "id": "uuid",
  "pharmacy": {"id": "uuid", "name": "Apollo Pharmacy"},
  "medicine": {"id": "uuid", "generic_name": "Amoxicillin"},
  "batch": {"id": "uuid", "batch_number": "AMX-2024-001"},
  "movement_type": "sold",
  "quantity": -10,
  "unit_price": "15.00",
  "reference_number": "RX-00123",
  "performed_by": {"id": "uuid", "full_name": "Tigist Alemu"},
  "is_approved": true,
  "created_at": "2024-03-15T14:30:00Z"
}
```

---

## 9. Dashboard (`/api/dashboard/`)

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/api/dashboard/pharmacy/` | Yes | pharmacy members | Pharmacy dashboard stats |
| GET | `/api/dashboard/system/` | Yes | system_admin | System-wide stats |

### Pharmacy Dashboard Response
```json
{
  "pharmacy": {"id": "uuid", "name": "Apollo Pharmacy"},
  "stats": {
    "total_medicines": 45,
    "total_batches": 120,
    "active_batches": 98,
    "expired_batches": 8,
    "expiring_soon_batches": 14,
    "low_stock_items": 5,
    "depleted_items": 2,
    "total_usable_stock_value": "125000.00"
  },
  "expiry_breakdown": {
    "this_week": 2,
    "this_month": 5,
    "within_warning_window": 14
  },
  "stock_by_category": [
    {"category": "Antibiotics", "usable_quantity": 1200, "batch_count": 8}
  ],
  "recent_movements": [...]
}
```

---

## 10. Availability Search (`/api/availability/`) — Public

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/api/availability/` | No | Public | Search medicine availability |

### Query params
- `?medicine=amoxicillin` (required; partial match on generic or brand name)
- `?city=Addis+Ababa` (optional)
- `?region=Addis+Ababa` (optional)

### Response
```json
{
  "query": "amoxicillin",
  "results": [
    {
      "pharmacy": {
        "id": "uuid",
        "name": "Apollo Pharmacy",
        "address": "Bole Road, Addis Ababa",
        "city": "Addis Ababa",
        "phone": "+251111234567"
      },
      "medicine": {
        "id": "uuid",
        "generic_name": "Amoxicillin",
        "brand_name": "Amoxil",
        "strength": "500mg",
        "dosage_form": "capsule"
      },
      "usable_quantity": 150,
      "last_confirmed_at": "2024-03-15T14:30:00Z",
      "is_stale": false,
      "requires_prescription": false
    }
  ]
}
```

---

## 11. Reports (`/api/reports/`)

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/api/reports/stock-summary/` | Yes | pharmacy members | Current stock summary |
| GET | `/api/reports/expiring/` | Yes | pharmacy members | Expiring stock (date range) |
| GET | `/api/reports/expired/` | Yes | pharmacy members | Expired batches |
| GET | `/api/reports/movements/` | Yes | pharmacy members | Movement history |
| GET | `/api/reports/low-stock/` | Yes | pharmacy members | Low-stock items |

All report endpoints support `?format=csv` for CSV download.

### Common query params
- `?pharmacy={uuid}` (system_admin: any; others: own only)
- `?medicine={uuid}`
- `?category={uuid}`
- `?date_from=2024-01-01`
- `?date_to=2024-12-31`

---

## 12. Audit Logs (`/api/audit/`)

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/api/audit/` | Yes | system_admin | List audit logs |
| GET | `/api/audit/{id}/` | Yes | system_admin | Get single audit log entry |

### Query params
- `?user={uuid}`
- `?model=Batch`
- `?action=delete`
- `?date_from=2024-01-01`
- `?date_to=2024-12-31`

---

## 13. System Configuration (`/api/config/`)

| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/api/config/` | Yes | system_admin | Get system config |
| PATCH | `/api/config/` | Yes | system_admin | Update system config |

---

## 14. API Documentation

| Path | Description |
|------|-------------|
| `/api/schema/` | OpenAPI 3.0 schema (YAML/JSON) |
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc UI |

---

## 15. Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input",
    "details": {
      "quantity": ["Quantity cannot be negative."],
      "expiry_date": ["Expiry date cannot be in the past."]
    }
  }
}
```

Standard HTTP status codes:
- `200 OK` — successful GET/PATCH
- `201 Created` — successful POST
- `204 No Content` — successful DELETE
- `400 Bad Request` — validation error
- `401 Unauthorized` — missing or invalid token
- `403 Forbidden` — authenticated but insufficient permissions
- `404 Not Found` — resource not found
- `409 Conflict` — duplicate (e.g., batch number already exists)
- `422 Unprocessable Entity` — business rule violation (e.g., quantity would go negative)
