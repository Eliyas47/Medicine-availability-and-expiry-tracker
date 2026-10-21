# Requirements & Acceptance Criteria
## Medicine Availability & Expiry Tracker

---

## 1. Project Context

A multi-pharmacy inventory and availability platform for Ethiopian pharmacy operations. It allows pharmacies to manage their own medicine stock — batches, expiry dates, movements — and exposes curated, timestamped availability data to the public.

---

## 2. Functional Requirements

### 2.1 Authentication & User Management

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| AUTH-1 | Users can register with email, full name, password, and role selection (staff/admin). System admin accounts are created by the system administrator only. | Registration form validates all fields; duplicate emails are rejected with a clear error; passwords must be ≥8 chars with complexity rules. |
| AUTH-2 | Registered users can log in with email and password. | Login returns a JWT access token (15 min) and refresh token (7 days); invalid credentials return 401 with a generic message. |
| AUTH-3 | Access tokens can be refreshed silently via a `/api/auth/token/refresh/` endpoint. | Frontend automatically refreshes tokens before expiry; expired refresh tokens force re-login. |
| AUTH-4 | Logged-in users can log out, invalidating the refresh token. | Refresh token is blacklisted; subsequent refresh attempts return 401. |
| AUTH-5 | Users can view and update their own profile (name, phone, password). | Password change requires current password confirmation; email changes require re-verification (optional v2). |
| AUTH-6 | Password validation enforces minimum length and complexity. | Backend rejects weak passwords with descriptive validation messages. |

### 2.2 Role-Based Access Control

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| RBAC-1 | Four roles: `system_admin`, `pharmacy_admin`, `inventory_staff`, `public`. | Role is stored per user; enforced in every API view; not merely hidden in the frontend. |
| RBAC-2 | `system_admin` can manage all users, pharmacies, categories, and system configuration. | System admin endpoints return 403 to any non-system-admin user. |
| RBAC-3 | `pharmacy_admin` manages their own pharmacy's profile, staff, medicine catalog, and inventory. | Attempting to access another pharmacy's resources returns 403. |
| RBAC-4 | `inventory_staff` can record stock movements and view inventory for their assigned pharmacy only. | Staff cannot edit the pharmacy profile or manage other staff. |
| RBAC-5 | Unauthenticated visitors can only access the public availability search and pharmacy listings. | All private endpoints return 401 for unauthenticated requests. |

### 2.3 Pharmacy Management

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| PHARM-1 | System admin can create, edit, deactivate, and delete pharmacies. | Pharmacy fields: name, license number, address, city, region, phone, email, GPS coordinates, operating hours, is_active. |
| PHARM-2 | Pharmacy admin can update their own pharmacy's profile and operating details. | Cannot change license number or is_active status. |
| PHARM-3 | Pharmacies can be searched and filtered on the public API by name, city, and region. | Results include only active pharmacies and exclude private contact fields not intended for public display. |

### 2.4 Medicine Catalog

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| MED-1 | Authenticated admins can create, edit, and deactivate medicine records. | Fields: generic_name, brand_name, strength, dosage_form (tablet/capsule/syrup/injection/cream/drops/other), category, description, unit_of_measure, requires_prescription, is_active. |
| MED-2 | Medicine catalog is shared across all pharmacies (not per-pharmacy). | A pharmacy references catalog medicines in its inventory; catalog edits by system_admin only. |
| MED-3 | Medicines can be searched and filtered by generic name, brand name, category, and dosage form. | Search is case-insensitive and supports partial matching. |

### 2.5 Batch Inventory

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| INV-1 | Each pharmacy maintains batches: a batch references a medicine, has a batch number, quantity, received date, expiry date, supplier, unit cost, and status. | Batch statuses: `active`, `low_stock`, `expired`, `depleted`. Status is computed automatically. |
| INV-2 | Expiry status is computed server-side: a batch is `expired` if expiry_date < today; `low_stock` if quantity ≤ pharmacy's threshold for that medicine. | Expired batches are excluded from usable stock counts and public availability. |
| INV-3 | Total usable quantity for a medicine at a pharmacy = sum of quantities from non-expired, non-depleted batches. | API returns usable_quantity separately from total_quantity. |
| INV-4 | Stock quantities cannot go negative. | Any operation that would reduce quantity below 0 is rejected with HTTP 400 and a clear message. |
| INV-5 | Batch expiry dates cannot be set in the past when creating a new batch. | Backend validates this; frontend shows an inline error. |

### 2.6 Stock Movements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| MOV-1 | Every change in stock quantity is recorded as a movement. Types: `received`, `sold`, `dispensed`, `adjustment`, `expired_removal`, `correction`. | Movements are append-only; existing records cannot be deleted or modified. |
| MOV-2 | Movements record: pharmacy, medicine, batch, movement_type, quantity, unit_price (optional), reference_number, notes, performed_by, timestamp. | All fields are stored; performed_by is automatically set to the requesting user. |
| MOV-3 | Only `correction` type movements require an admin approval flag. | Corrections are flagged pending_approval until a pharmacy_admin or system_admin approves. |
| MOV-4 | Stock movements are viewable as a filterable, paginated history. | Filters: pharmacy, medicine, movement type, date range. Exportable to CSV. |

### 2.7 Expiry Management

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| EXP-1 | The system computes expiry status for every batch daily (and on every request). | Batches within N days of expiry are flagged `expiring_soon`; N is configurable per pharmacy (default 90 days). |
| EXP-2 | Dashboard shows counts of: expiring this week, expiring this month, expiring in configured window, and already expired. | Counts exclude depleted batches. |
| EXP-3 | Expired stock is never included in usable quantity or public availability. | Verified by an automated test that sets expiry_date = yesterday and confirms usable_quantity = 0. |

### 2.8 Low-Stock Alerts

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| ALERT-1 | Each medicine at a pharmacy has a configurable minimum_stock_threshold. | Default threshold is 0 (alert only when depleted). Threshold is stored at the PharmacyMedicine level. |
| ALERT-2 | The API returns a list of low-stock items for a pharmacy. | Item is low-stock if usable_quantity ≤ threshold. |
| ALERT-3 | Dashboard displays low-stock items with the current quantity, threshold, and a reorder recommendation. | Items are sorted by severity (quantity / threshold ratio ascending). |

### 2.9 Availability Search (Public)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| SRCH-1 | Public visitors can search for a medicine by generic or brand name. | Returns a list of pharmacies with that medicine in usable stock, ordered by availability confidence. |
| SRCH-2 | Each result shows: pharmacy name, address, phone, usable_quantity, and last_confirmed_at timestamp. | `last_confirmed_at` is the timestamp of the most recent stock movement for that medicine at that pharmacy. |
| SRCH-3 | Results only include active pharmacies with usable_quantity > 0. | Stale stock (not confirmed in > configured days, default 30) is marked with a `stale` flag but still shown. |
| SRCH-4 | Results can be filtered by city and region. | Filter parameters are optional; empty returns all results. |

### 2.10 Dashboard

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| DASH-1 | Pharmacy dashboard shows: total medicines, total batches, usable stock value, low-stock count, expiring-soon count, expired count, recent movements. | All numbers are real API data; no hardcoded values. |
| DASH-2 | Dashboard includes a bar or pie chart of stock by category. | Chart renders with real data; shows empty state when no data. |
| DASH-3 | System admin dashboard shows: total pharmacies, total medicines, total users, system-wide low-stock count, system-wide expired count. | Scoped to system_admin role. |

### 2.11 Reports

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| RPT-1 | Stock summary report: all medicines, usable quantity, value, status. | Filterable by pharmacy, category, status. |
| RPT-2 | Expiring stock report: batches expiring within a user-selected date range. | Shows batch number, medicine, expiry date, quantity, days remaining. |
| RPT-3 | Expired stock report: all expired batches. | Includes removal recommendation. |
| RPT-4 | Stock movements report: movements in a date range. | Filterable by type, medicine, pharmacy. |
| RPT-5 | Low-stock report: all medicines below threshold. | Sortable by quantity and threshold. |
| RPT-6 | All reports can be exported to CSV. | Export includes all visible columns; filename includes report type and date. |

### 2.12 Audit Logs

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| AUD-1 | All create/update/delete actions on critical models are logged. | Log entry contains: action type, model name, object ID, changed fields (before/after), user, timestamp, IP address. |
| AUD-2 | Audit logs are read-only to all users including admins. | No API endpoint allows modification of audit log entries. |
| AUD-3 | System admin can view and filter audit logs. | Filters: user, model, action, date range. Paginated. |

### 2.13 Administration

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| ADMIN-1 | System admin can manage all user accounts: view, activate/deactivate, assign roles, reset passwords. | Deactivated users cannot log in. |
| ADMIN-2 | System admin can manage medicine categories (CRUD). | Category name must be unique. |
| ADMIN-3 | System admin can configure system-wide defaults (expiry warning window, stale stock threshold). | Stored in a SystemConfig model; editable via a dedicated endpoint. |

---

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | All private API endpoints require a valid JWT access token. |
| NFR-2 | HTTPS must be used in production; enforce via settings. |
| NFR-3 | CORS is configured to allow only the deployed frontend origin in production. |
| NFR-4 | No secrets, database URLs, or credentials in version control. `.env.example` provided. |
| NFR-5 | Concurrent stock updates are protected by `select_for_update()` transactions. |
| NFR-6 | Database constraints enforce non-negative quantities and referential integrity. |
| NFR-7 | API responses are paginated (default 20 items). |
| NFR-8 | API is documented with OpenAPI 3.0 via drf-spectacular, accessible at `/api/schema/` and `/api/docs/`. |
| NFR-9 | Backend test coverage ≥ 80% for business-logic modules. |
| NFR-10 | Frontend is responsive from 320px (mobile) to 1920px (desktop). |
| NFR-11 | Time zone: Africa/Addis_Ababa (UTC+3) used for display; UTC stored in the database. |
| NFR-12 | Accessibility: WCAG 2.1 AA color contrast, semantic HTML, keyboard navigation, ARIA labels on interactive elements. |

---

## 4. Out of Scope (v1)

- Email/SMS notifications (architecture supports adding them in v2).
- Native mobile apps.
- Integration with external pharmacy management systems.
- E-commerce or prescription ordering.
- Multi-language support beyond English (Amharic-ready architecture).
