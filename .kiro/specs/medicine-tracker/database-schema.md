# Database Schema & Relationships
## Medicine Availability & Expiry Tracker

---

## 1. Entity Relationship Overview

```
SystemConfig (1)

User ──────────────────────────────────────────────────────────┐
  │  PharmacyMembership (many)                                 │
  │     └── Pharmacy (1)                                       │
  │                                                            │
  │  Pharmacy ──────────────────────────────────────────────┐  │
  │    │  PharmacyMedicine (many)  ─── Medicine             │  │
  │    │  Batch (many)             ─── Medicine             │  │
  │    │  StockMovement (many)     ─── Batch, Medicine      │  │
  │                                                         │  │
  │  Medicine ─── Category                                  │  │
  │                                                         │  │
  └──────────────────────────────────────────────────────── AuditLog
```

---

## 2. Table Definitions

### 2.1 `accounts_user`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Generated via `uuid4` |
| email | VARCHAR(254) | UNIQUE, NOT NULL | Login identifier |
| full_name | VARCHAR(200) | NOT NULL | |
| phone | VARCHAR(20) | NULL | |
| role | VARCHAR(30) | NOT NULL | `system_admin`, `pharmacy_admin`, `inventory_staff` |
| is_active | BOOLEAN | DEFAULT TRUE | Deactivated users blocked at login |
| is_staff | BOOLEAN | DEFAULT FALSE | Django admin access |
| date_joined | TIMESTAMPTZ | DEFAULT NOW() | |
| last_login | TIMESTAMPTZ | NULL | Updated by Simple JWT |
| password | VARCHAR(128) | NOT NULL | Hashed (PBKDF2/Argon2) |

**Indexes:** `email` (unique), `role`

---

### 2.2 `pharmacies_pharmacy`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(200) | NOT NULL | |
| license_number | VARCHAR(100) | UNIQUE, NOT NULL | |
| address | TEXT | NOT NULL | Street address |
| city | VARCHAR(100) | NOT NULL | |
| region | VARCHAR(100) | NOT NULL | Ethiopian region |
| phone | VARCHAR(20) | NOT NULL | |
| email | VARCHAR(254) | NULL | |
| latitude | DECIMAL(9,6) | NULL | |
| longitude | DECIMAL(9,6) | NULL | |
| operating_hours | JSONB | NULL | `{"mon": "08:00-20:00", ...}` |
| is_active | BOOLEAN | DEFAULT TRUE | |
| expiry_warning_days | INTEGER | DEFAULT 90 | Per-pharmacy config |
| stale_stock_days | INTEGER | DEFAULT 30 | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | AUTO | |

**Indexes:** `city`, `region`, `is_active`, `license_number`

---

### 2.3 `accounts_pharmacymembership`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| user_id | UUID | FK → accounts_user | |
| pharmacy_id | UUID | FK → pharmacies_pharmacy | |
| role | VARCHAR(30) | NOT NULL | `pharmacy_admin`, `inventory_staff` |
| is_active | BOOLEAN | DEFAULT TRUE | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

**Unique constraint:** `(user_id, pharmacy_id)`

---

### 2.4 `medicines_category`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(100) | UNIQUE, NOT NULL | |
| description | TEXT | NULL | |
| is_active | BOOLEAN | DEFAULT TRUE | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

---

### 2.5 `medicines_medicine`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| generic_name | VARCHAR(200) | NOT NULL | |
| brand_name | VARCHAR(200) | NULL | |
| strength | VARCHAR(100) | NOT NULL | e.g., "500mg", "10mg/5ml" |
| dosage_form | VARCHAR(50) | NOT NULL | `tablet`, `capsule`, `syrup`, `injection`, `cream`, `drops`, `other` |
| category_id | UUID | FK → medicines_category | NULL allowed |
| description | TEXT | NULL | |
| unit_of_measure | VARCHAR(50) | DEFAULT "unit" | e.g., "tablet", "ml", "vial" |
| requires_prescription | BOOLEAN | DEFAULT FALSE | |
| is_active | BOOLEAN | DEFAULT TRUE | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | AUTO | |

**Indexes:** `generic_name`, `brand_name`, `category_id`, `dosage_form`

---

### 2.6 `pharmacies_pharmacymedicine`

Stores per-pharmacy thresholds for a medicine.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| pharmacy_id | UUID | FK → pharmacies_pharmacy | |
| medicine_id | UUID | FK → medicines_medicine | |
| minimum_stock_threshold | INTEGER | DEFAULT 0, CHECK ≥ 0 | |
| is_tracked | BOOLEAN | DEFAULT TRUE | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

**Unique constraint:** `(pharmacy_id, medicine_id)`

---

### 2.7 `inventory_batch`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| pharmacy_id | UUID | FK → pharmacies_pharmacy | |
| medicine_id | UUID | FK → medicines_medicine | |
| batch_number | VARCHAR(100) | NOT NULL | |
| quantity | INTEGER | NOT NULL, CHECK ≥ 0 | Current usable quantity |
| received_date | DATE | NOT NULL | |
| expiry_date | DATE | NOT NULL | |
| supplier | VARCHAR(200) | NULL | |
| unit_cost | DECIMAL(10,2) | NULL | |
| status | VARCHAR(30) | NOT NULL | `active`, `low_stock`, `expiring_soon`, `expired`, `depleted` |
| notes | TEXT | NULL | |
| created_by_id | UUID | FK → accounts_user | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | AUTO | |

**Unique constraint:** `(pharmacy_id, batch_number)`  
**Indexes:** `pharmacy_id`, `medicine_id`, `expiry_date`, `status`  
**Check constraint:** `quantity >= 0`

---

### 2.8 `inventory_stockmovement`

Append-only ledger. Never updated or deleted after creation.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| pharmacy_id | UUID | FK → pharmacies_pharmacy | |
| medicine_id | UUID | FK → medicines_medicine | |
| batch_id | UUID | FK → inventory_batch, NULL | NULL only for pharmacy-level adjustments |
| movement_type | VARCHAR(30) | NOT NULL | `received`, `sold`, `dispensed`, `adjustment`, `expired_removal`, `correction` |
| quantity | INTEGER | NOT NULL | Positive = increase, negative = decrease |
| unit_price | DECIMAL(10,2) | NULL | |
| reference_number | VARCHAR(100) | NULL | Invoice/prescription reference |
| notes | TEXT | NULL | |
| performed_by_id | UUID | FK → accounts_user | |
| is_approved | BOOLEAN | DEFAULT TRUE | FALSE for `correction` until approved |
| approved_by_id | UUID | FK → accounts_user, NULL | |
| approved_at | TIMESTAMPTZ | NULL | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

**Indexes:** `pharmacy_id`, `medicine_id`, `batch_id`, `movement_type`, `created_at`

---

### 2.9 `inventory_systemconfig`

Singleton table (enforced in application code).

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PK | Always 1 |
| expiry_warning_days | INTEGER | DEFAULT 90 | Global default |
| stale_stock_days | INTEGER | DEFAULT 30 | |
| low_stock_default_threshold | INTEGER | DEFAULT 10 | |
| updated_by_id | UUID | FK → accounts_user, NULL | |
| updated_at | TIMESTAMPTZ | AUTO | |

---

### 2.10 `audit_auditlog`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | BIGSERIAL | PK | |
| user_id | UUID | FK → accounts_user, NULL | NULL for system actions |
| user_email | VARCHAR(254) | NOT NULL | Denormalized in case user is deleted |
| action | VARCHAR(30) | NOT NULL | `create`, `update`, `delete` |
| model_name | VARCHAR(100) | NOT NULL | e.g., "Batch" |
| object_id | VARCHAR(100) | NOT NULL | String PK of the affected object |
| object_repr | VARCHAR(500) | NULL | Human-readable string |
| changes | JSONB | NULL | `{"field": [old, new], ...}` |
| ip_address | INET | NULL | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

**Indexes:** `user_id`, `model_name`, `action`, `created_at`

---

## 3. Key Relationships Summary

```
User 1──* PharmacyMembership *──1 Pharmacy
Pharmacy 1──* PharmacyMedicine *──1 Medicine
Pharmacy 1──* Batch *──1 Medicine
Batch 1──* StockMovement
Pharmacy 1──* StockMovement
Medicine *──1 Category
User 1──* StockMovement (performed_by)
User 1──* AuditLog
```

---

## 4. Computed / Derived Values

These are **not stored columns** but computed at query time:

| Derived Value | Computation |
|---------------|-------------|
| `usable_quantity` | `SUM(quantity) WHERE batch.status NOT IN ('expired', 'depleted') AND pharmacy = X AND medicine = Y` |
| `batch.status` | Computed: expired if `expiry_date < today`; low_stock if `quantity ≤ threshold`; expiring_soon if `expiry_date ≤ today + warning_days`; depleted if `quantity = 0`; else active |
| `last_confirmed_at` | `MAX(created_at) FROM StockMovement WHERE pharmacy = X AND medicine = Y` |
| `is_stale` | `last_confirmed_at < now() - stale_stock_days` |
| `days_until_expiry` | `expiry_date - today` |

---

## 5. Migration Strategy

- All migrations generated by `python manage.py makemigrations`.
- Initial migration creates all tables in the correct dependency order.
- A `0002_seed_categories.py` data migration adds default medicine categories.
- A `0003_seed_systemconfig.py` data migration creates the singleton SystemConfig row.
- Each app manages its own migrations folder.
