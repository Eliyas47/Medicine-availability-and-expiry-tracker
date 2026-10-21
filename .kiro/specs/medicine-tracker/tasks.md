# Implementation Tasks
## Medicine Availability & Expiry Tracker

Tasks are ordered by dependency. Each phase must be completed, tested, and verified before the next begins.

---

## Phase 1: Project Scaffolding & Infrastructure

- [ ] 1.1 Create `.gitignore` covering Python venv, `__pycache__`, `.env`, node_modules, dist, `*.pyc`, `db.sqlite3`, `.DS_Store`, and IDE files.
- [ ] 1.2 Initialize Django project with the `config/` settings package structure (`base.py`, `development.py`, `production.py`).
- [ ] 1.3 Create `backend/requirements/base.txt`, `development.txt`, `production.txt` with pinned versions:
  - Django 5.1, djangorestframework 3.15, djangorestframework-simplejwt 5.3, psycopg2-binary 2.9, django-cors-headers 4.4, drf-spectacular 0.27, python-decouple 3.8, Pillow 10.4, django-filter 24.3, pytest-django 4.8, pytest 8.3, factory-boy 3.3, coverage 7.6
- [ ] 1.4 Configure `base.py`: installed apps, middleware, REST_FRAMEWORK defaults, JWT settings, SPECTACULAR_SETTINGS, TIME_ZONE=Africa/Addis_Ababa.
- [ ] 1.5 Configure `development.py`: DEBUG=True, SQLite fallback for quick local start, CORS allow localhost:5173.
- [ ] 1.6 Configure PostgreSQL DATABASE_URL parsing via `python-decouple` + `dj-database-url`.
- [ ] 1.7 Create backend `.env.example`.
- [ ] 1.8 Initialize Vite + React + TypeScript frontend project in `frontend/`.
- [ ] 1.9 Install and configure Tailwind CSS, `shadcn/ui`, `react-router-dom v6`, `@tanstack/react-query v5`, `axios`, `react-hook-form`, `zod`, `recharts`, `react-hot-toast`, `lucide-react`.
- [ ] 1.10 Create frontend `.env.example` with `VITE_API_BASE_URL=http://localhost:8000/api`.
- [ ] 1.11 Set up `frontend/src/api/client.ts`: Axios instance with base URL, request interceptor (attach token), response interceptor (silent refresh on 401).
- [ ] 1.12 Configure `vite.config.ts` proxy for `/api` → `localhost:8000` in development.
- [ ] 1.13 Create `core` Django app with: `StandardResultsPagination`, custom exception handler, base permission classes.
- [ ] 1.14 Wire up `config/urls.py` with API prefix, drf-spectacular schema routes, and Django admin.
- [ ] 1.15 Verify: `python manage.py check` passes; `npm run build` succeeds with no TypeScript errors.

---

## Phase 2: Accounts & Authentication

- [ ] 2.1 Create `accounts` Django app.
- [ ] 2.2 Implement `User` model (UUID PK, email login, role field, phone, is_active, date_joined). Register as AUTH_USER_MODEL.
- [ ] 2.3 Implement `PharmacyMembership` model linking User → Pharmacy with role + is_active.
- [ ] 2.4 Create and run initial migration for accounts.
- [ ] 2.5 Implement `UserSerializer`, `RegisterSerializer` (with password confirm & complexity validation), `LoginSerializer`, `ChangePasswordSerializer`, `ProfileSerializer`.
- [ ] 2.6 Implement auth views: `RegisterView`, `LoginView` (custom, returns user data alongside tokens), `LogoutView` (blacklists refresh token), `ProfileView`.
- [ ] 2.7 Configure `TokenRefreshView` from Simple JWT (blacklist-aware).
- [ ] 2.8 Wire accounts URLs at `/api/auth/`.
- [ ] 2.9 Write tests: register success, register duplicate email, login correct/incorrect, refresh valid/expired token, logout blacklists token, profile get/update, password change with wrong current password.
- [ ] 2.10 Create `AuthContext` in React: stores access token in memory, refresh token in localStorage, provides `login()`, `logout()`, `user` state.
- [ ] 2.11 Implement `LoginPage` and `RegisterPage` with `react-hook-form` + `zod` validation and API integration.
- [ ] 2.12 Implement `ProtectedRoute` component that redirects to login if not authenticated.
- [ ] 2.13 Implement `UserProfilePage` with profile edit and password change forms.
- [ ] 2.14 Verify: login → token stored → protected route accessible; logout → redirect to login.

---

## Phase 3: Pharmacies

- [ ] 3.1 Create `pharmacies` Django app.
- [ ] 3.2 Implement `Pharmacy` model (all fields from schema including `expiry_warning_days`, `stale_stock_days`).
- [ ] 3.3 Implement `PharmacyMedicine` model (pharmacy, medicine FK stub — medicine app not yet created; add FK migration later).
- [ ] 3.4 Create and run migrations.
- [ ] 3.5 Implement `IsSystemAdmin`, `IsPharmacyAdmin`, `IsPharmacyMember`, `IsOwnPharmacy` permission classes in `core/permissions.py`.
- [ ] 3.6 Implement `PharmacySerializer` (full for admins, public-safe for anonymous), `PharmacyMembershipSerializer`.
- [ ] 3.7 Implement `PharmacyViewSet` with:
  - `get_queryset()` scoped by role
  - `get_serializer_class()` returns public serializer for anonymous
  - Custom actions: `members`, `add_member`, `remove_member`
- [ ] 3.8 Wire pharmacy URLs at `/api/pharmacies/`.
- [ ] 3.9 Write tests: public list (no auth), system_admin CRUD, pharmacy_admin edits own/fails on other, staff view only.
- [ ] 3.10 Implement React `PharmacyProfilePage`: edit form for pharmacy_admin; view-only for staff.
- [ ] 3.11 Implement `PharmacyMembersSection`: list members, add member by email, remove member (admin only).
- [ ] 3.12 Verify: pharmacy profile saves correctly; non-admin cannot edit.

---

## Phase 4: Medicine Catalog

- [ ] 4.1 Create `medicines` Django app.
- [ ] 4.2 Implement `Category` model.
- [ ] 4.3 Implement `Medicine` model (all fields; FK to Category).
- [ ] 4.4 Add FK from `PharmacyMedicine` to `Medicine` (migration).
- [ ] 4.5 Create and run migrations.
- [ ] 4.6 Implement `CategorySerializer`, `MedicineSerializer`, `MedicineListSerializer` (compact for dropdowns).
- [ ] 4.7 Implement `CategoryViewSet` (system_admin write, all read).
- [ ] 4.8 Implement `MedicineViewSet` with search filters (`SearchFilter` on generic_name, brand_name), `django-filter` on category and dosage_form.
- [ ] 4.9 Wire medicine and category URLs at `/api/medicines/`, `/api/categories/`.
- [ ] 4.10 Write tests: public search, system_admin CRUD, non-admin cannot create.
- [ ] 4.11 Implement React `MedicineCatalogPage` (admin): table, add/edit/deactivate medicine.
- [ ] 4.12 Implement `MedicineSelect` async-search component.
- [ ] 4.13 Implement category management section within settings or medicine page.
- [ ] 4.14 Verify: medicine search returns case-insensitive partial matches.

---

## Phase 5: Batch Inventory

- [ ] 5.1 Create `inventory` Django app.
- [ ] 5.2 Implement `Batch` model (all fields; DB CheckConstraint quantity ≥ 0).
- [ ] 5.3 Implement `SystemConfig` singleton model.
- [ ] 5.4 Create and run migrations (include data migrations for default SystemConfig and categories).
- [ ] 5.5 Implement `compute_batch_status(batch, warning_days)` in `inventory/services.py`.
- [ ] 5.6 Implement `BatchSerializer` with computed fields: `days_until_expiry`, `status` (read-only), `usable_quantity` annotated at queryset level.
- [ ] 5.7 Implement `BatchViewSet`:
  - `get_queryset()` scoped to user's pharmacy
  - `perform_create()`: validates expiry_date > today, auto-creates `received` StockMovement
  - Custom list actions: `expiring/`, `expired/`, `low_stock/`
- [ ] 5.8 Wire batch URLs at `/api/batches/`.
- [ ] 5.9 Write tests: create batch (movement auto-created), past expiry rejected, scoping (staff at pharmacy A cannot see pharmacy B), status computed correctly.
- [ ] 5.10 Implement React `BatchListPage`: data table with filters, status badges, expiry countdown.
- [ ] 5.11 Implement `BatchFormPage`: add batch form with medicine select, date pickers, validation.
- [ ] 5.12 Verify: adding a batch creates a movement; batch appears in inventory.

---

## Phase 6: Stock Movements

- [ ] 6.1 Implement `StockMovement` model in `inventory` app (all fields; append-only enforced by disabling update/delete in serializer and viewset).
- [ ] 6.2 Add migration.
- [ ] 6.3 Implement `perform_movement(batch_id, quantity, movement_type, user, **kwargs)` service with `select_for_update()` + `transaction.atomic`.
- [ ] 6.4 Implement `StockMovementSerializer` with signed quantity (negative for outbound movements).
- [ ] 6.5 Implement `StockMovementViewSet`:
  - Create → calls `perform_movement` service
  - Custom action `approve/` for corrections
  - `get_queryset()` scoped to user's pharmacy
- [ ] 6.6 Wire movement URLs at `/api/movements/`.
- [ ] 6.7 Write tests: sell reduces batch qty, sell beyond qty rejected (422), correction requires approval, concurrent sell (thread safety), pharmacy scoping.
- [ ] 6.8 Implement React `MovementsPage`: filterable timeline table, pending correction badges.
- [ ] 6.9 Implement `MovementFormModal`: batch select, type, quantity, reference.
- [ ] 6.10 Verify: movement recorded → batch quantity updated → history shows correctly.

---

## Phase 7: Expiry Management & Low-Stock Alerts

- [ ] 7.1 Implement `ExpiryManagementView` (list batches by expiry status) in `inventory` app.
- [ ] 7.2 Implement `LowStockView` (list pharmacy medicines below threshold).
- [ ] 7.3 Add `PharmacyMedicine` threshold endpoint at `/api/pharmacies/{id}/medicines/`.
- [ ] 7.4 Implement bulk `expired_removal` action: creates `expired_removal` movements for selected expired batches.
- [ ] 7.5 Write tests: expiring-soon includes batches within warning window, expired excludes batches from usable qty, low-stock reflects threshold.
- [ ] 7.6 Implement React `ExpiryPage`: tabs for expiring soon / expired, bulk removal action.
- [ ] 7.7 Implement React `AlertsPage`: low-stock table, inline threshold editing.
- [ ] 7.8 Verify: expired batch → usable_quantity = 0 → not in availability search.

---

## Phase 8: Dashboard & Availability Search

- [ ] 8.1 Implement `PharmacyDashboardView` in `inventory` app: aggregated stats via a single optimized query (use `annotate` + `Count` + `Sum`).
- [ ] 8.2 Implement `SystemDashboardView` (system_admin): system-wide aggregations.
- [ ] 8.3 Implement `AvailabilitySearchView` (public): search by medicine name + optional city/region filters. Returns only usable, non-expired, active-pharmacy results.
- [ ] 8.4 Add `is_stale` annotation: `last_confirmed_at < now() - stale_stock_days`.
- [ ] 8.5 Write tests: dashboard stats match known fixture data; availability search excludes expired; stale flag set correctly.
- [ ] 8.6 Implement React `DashboardOverviewPage`: stats cards, expiry breakdown, category pie chart, movements bar chart, recent movements table.
- [ ] 8.7 Implement React `AvailabilitySearchPage`: search form, results list, stale warning badges.
- [ ] 8.8 Implement React `PublicLandingPage`: hero, features, search CTA.
- [ ] 8.9 Verify: dashboard shows real data; search returns real results; empty state handled.

---

## Phase 9: Reports & CSV Export

- [ ] 9.1 Create `reports` Django app.
- [ ] 9.2 Implement `StockSummaryReportView`, `ExpiringReportView`, `ExpiredReportView`, `MovementsReportView`, `LowStockReportView`.
- [ ] 9.3 Implement CSV export: each view returns `text/csv` response when `?format=csv` is passed. Use Python `csv.DictWriter`.
- [ ] 9.4 Wire report URLs at `/api/reports/`.
- [ ] 9.5 Write tests: each report returns correct JSON; CSV export returns correct headers and rows; date range filter applied correctly.
- [ ] 9.6 Implement React `ReportsPage`: tabbed reports, date range picker, medicine/category filters, CSV export button.
- [ ] 9.7 Verify: CSV download works; report filters correctly scope data.

---

## Phase 10: Audit Logs & Admin

- [ ] 10.1 Create `audit` Django app.
- [ ] 10.2 Implement `AuditLog` model.
- [ ] 10.3 Implement `AuditMiddleware`: captures request user + IP, stores in thread-local.
- [ ] 10.4 Implement `log_action(user, action, instance, changes=None)` utility.
- [ ] 10.5 Add Django signal receivers (`post_save`, `post_delete`) on critical models: Batch, StockMovement, Pharmacy, Medicine, User, PharmacyMembership.
- [ ] 10.6 Implement `AuditLogViewSet` (read-only, system_admin only, filterable).
- [ ] 10.7 Wire audit URLs at `/api/audit/`.
- [ ] 10.8 Implement `SystemConfigView` (GET + PATCH, system_admin only).
- [ ] 10.9 Implement `UsersViewSet` (system_admin only): list, get, update role/is_active, activate/deactivate.
- [ ] 10.10 Write tests: audit log created on batch create/update/delete; non-system-admin gets 403; config update saved.
- [ ] 10.11 Implement React `AuditLogPage`: filterable table with expandable changes column.
- [ ] 10.12 Implement React `UsersPage`: user management table, activate/deactivate, role change.
- [ ] 10.13 Implement React `SettingsPage`: system config form.
- [ ] 10.14 Verify: batch creation creates audit entry; system admin sees it; staff cannot access.

---

## Phase 11: Polish, Accessibility & Documentation

- [ ] 11.1 Add loading skeletons to all data-fetching pages.
- [ ] 11.2 Add empty states to all list pages (pharmacy-specific empty messages).
- [ ] 11.3 Add `ConfirmDialog` to all destructive actions (delete, deactivate, bulk removal).
- [ ] 11.4 Audit all forms for validation messages (inline, not just toast).
- [ ] 11.5 Audit color contrast (WCAG AA) for all badge colors.
- [ ] 11.6 Add `aria-label` to all icon-only buttons.
- [ ] 11.7 Add keyboard navigation testing for dialogs and dropdowns.
- [ ] 11.8 Implement responsive sidebar (hamburger menu on mobile, bottom nav on xs).
- [ ] 11.9 Add `react-helmet` or Vite meta tags for page titles.
- [ ] 11.10 Finalize drf-spectacular schema: add `@extend_schema` decorators to all viewsets.
- [ ] 11.11 Write comprehensive `README.md` with: prerequisites, local setup, database setup, seed data, run instructions, test instructions, env variable reference, production deployment notes.
- [ ] 11.12 Add `CONTRIBUTING.md` and update `LICENSE`.
- [ ] 11.13 Run `pytest --cov=apps --cov-report=term-missing` and achieve ≥ 80% on business-logic modules.
- [ ] 11.14 Run `npm run build` → zero TypeScript errors, zero Tailwind warnings.
- [ ] 11.15 Final review: check every page for hardcoded data, confirm all API calls use real endpoints, verify CORS settings.

---

## Dependency Map

```
Phase 1 (scaffolding)
  └── Phase 2 (accounts)
        ├── Phase 3 (pharmacies)
        │     └── Phase 4 (medicines)
        │           └── Phase 5 (batches)
        │                 └── Phase 6 (movements)
        │                       ├── Phase 7 (expiry/alerts)
        │                       ├── Phase 8 (dashboard/search)
        │                       └── Phase 9 (reports)
        │                             └── Phase 10 (audit/admin)
        │                                   └── Phase 11 (polish/docs)
        └── Phase 3 also requires Phase 2 user model for membership FK
```

---

## Notes for Implementer

1. **Do not start Phase N+1 until all Phase N tests pass.**
2. Database migrations must be kept in sync — run `makemigrations` after every model change.
3. Frontend `.env` must be configured before any API calls are tested.
4. Token refresh logic in Axios must be complete before any protected page is built.
5. The `perform_movement` service is the single source of truth for stock changes — never update `batch.quantity` outside this service.
6. Never delete StockMovement records — if a correction is needed, create a compensating movement.
7. All `get_queryset()` overrides must be audited before Phase 10 to ensure no data leaks.
