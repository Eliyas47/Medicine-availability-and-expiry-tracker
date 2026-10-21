# System Architecture
## Medicine Availability & Expiry Tracker

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PUBLIC INTERNET                             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTPS
          ┌────────────────┴────────────────┐
          │           NGINX (prod)          │
          │   static files  /  reverse proxy│
          └────────────────┬────────────────┘
                 ┌─────────┴──────────┐
                 │                    │
        ┌────────▼────────┐  ┌────────▼────────┐
        │   React + Vite  │  │  Django + DRF   │
        │   (Frontend)    │  │   (Backend API) │
        │  TypeScript     │  │  Python 3.12    │
        │  Tailwind CSS   │  │  Gunicorn       │
        └─────────────────┘  └────────┬────────┘
                                      │
                             ┌────────▼────────┐
                             │   PostgreSQL 16  │
                             │   (Primary DB)   │
                             └─────────────────┘
```

### Development topology

```
Browser → Vite dev server (localhost:5173) → Axios → Django dev server (localhost:8000)
```

### Production topology

```
Browser → NGINX → 
  /           → React static build (served by NGINX)
  /api/*      → Gunicorn (Django)
  /api/docs/* → Gunicorn (Django, Swagger UI)
```

---

## 2. Repository Layout

```
Medicine-availability-and-expiry-tracker/
├── backend/                    # Django project root
│   ├── config/                 # Django settings package
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/
│   │   ├── accounts/           # User model, auth, roles
│   │   ├── pharmacies/         # Pharmacy profiles
│   │   ├── medicines/          # Medicine catalog & categories
│   │   ├── inventory/          # Batches, movements, alerts
│   │   ├── reports/            # Report generation & CSV export
│   │   ├── audit/              # Audit log
│   │   └── core/               # Shared utilities, permissions, pagination
│   ├── manage.py
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   └── .env.example
├── frontend/                   # React + Vite project
│   ├── src/
│   │   ├── api/                # Axios instances & typed API services
│   │   ├── components/         # Reusable UI components
│   │   │   ├── ui/             # Base design-system components
│   │   │   ├── forms/          # Form primitives
│   │   │   ├── tables/         # Data table + pagination
│   │   │   └── charts/         # Chart wrappers
│   │   ├── features/           # Feature slices (auth, inventory, etc.)
│   │   ├── hooks/              # Custom React hooks
│   │   ├── layouts/            # Page layout shells
│   │   ├── pages/              # Route-level page components
│   │   ├── types/              # TypeScript interfaces & enums
│   │   ├── utils/              # Date formatting, helpers
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── .env.example
├── .gitignore
└── README.md
```

---

## 3. Django Application Structure

### 3.1 `accounts` app
- Custom `User` model extending `AbstractBaseUser`
- `Role` choices: `system_admin`, `pharmacy_admin`, `inventory_staff`
- `PharmacyMembership` model: links a user to a pharmacy with a role
- JWT auth via `djangorestframework-simplejwt`
- Endpoints: register, login, logout, token refresh, profile

### 3.2 `pharmacies` app
- `Pharmacy` model
- `PharmacyMedicine` model: per-pharmacy minimum stock threshold
- Endpoints: pharmacy CRUD, public listing, membership management

### 3.3 `medicines` app
- `Category` model
- `Medicine` model (shared catalog)
- Endpoints: category CRUD, medicine CRUD, public search

### 3.4 `inventory` app
- `Batch` model: per-pharmacy per-medicine batch
- `StockMovement` model: append-only movement ledger
- `SystemConfig` model: global settings (expiry window, stale threshold)
- Business logic in `services.py`: `record_movement()`, `get_usable_quantity()`, `compute_batch_status()`
- Endpoints: batch CRUD, movement create/list, low-stock list, dashboard stats, availability search

### 3.5 `reports` app
- Report views that query the inventory app
- CSV export via Python `csv` module
- Endpoints: stock summary, expiring, expired, movements, low-stock — all with `?format=csv` support

### 3.6 `audit` app
- `AuditLog` model
- Django signal receivers on critical models to write logs
- Middleware captures request user and IP
- Endpoints: audit log list (system_admin only)

### 3.7 `core` app
- Custom pagination class (`StandardResultsPagination`)
- Base permission classes
- Exception handler
- Common serializer mixins

---

## 4. Frontend Architecture

### 4.1 Routing (React Router v6)

```
/                         → PublicLandingPage
/search                   → AvailabilitySearchPage
/auth/login               → LoginPage
/auth/register            → RegisterPage
/dashboard                → DashboardShell (protected)
  /dashboard/overview     → DashboardOverviewPage
  /dashboard/inventory    → InventoryPage
  /dashboard/batches      → BatchListPage
  /dashboard/batches/new  → BatchFormPage
  /dashboard/movements    → MovementsPage
  /dashboard/expiry       → ExpiryPage
  /dashboard/alerts       → AlertsPage
  /dashboard/reports      → ReportsPage
  /dashboard/pharmacy     → PharmacyProfilePage
  /dashboard/medicines    → MedicineCatalogPage  (admin)
  /dashboard/users        → UsersPage            (admin)
  /dashboard/audit        → AuditLogPage         (system_admin)
  /dashboard/settings     → SettingsPage         (admin)
/profile                  → UserProfilePage (protected)
```

### 4.2 State Management
- **Server state**: React Query (TanStack Query v5) — all API data, caching, refetch.
- **UI state**: React `useState` / `useReducer` within components.
- **Auth state**: Context + `localStorage` for token storage (access token in memory preferred; refresh token in `httpOnly` cookie in production).

### 4.3 API Layer
- Single Axios instance with base URL from `VITE_API_BASE_URL`.
- Request interceptor attaches `Authorization: Bearer <token>`.
- Response interceptor handles 401 → silent token refresh → retry.
- Typed service functions per resource (e.g., `inventoryService.getBatches(params)`).

### 4.4 Design System
- Tailwind CSS with a custom theme (brand color: a pharmacy green `#0d9488` teal).
- `shadcn/ui` component primitives (Button, Input, Select, Dialog, Table, Badge, Card, Toast).
- Recharts for dashboard charts.
- `react-hot-toast` for notifications.
- `react-hook-form` + `zod` for form validation.

---

## 5. Security Design

| Layer | Mechanism |
|-------|-----------|
| Transport | HTTPS (TLS 1.2+) enforced in production |
| Authentication | JWT (access 15 min, refresh 7 days) via Simple JWT with token blacklisting |
| Authorization | DRF custom permission classes checked in every view |
| Object-level auth | `get_queryset()` scoped to the requesting user's pharmacy |
| CSRF | Stateless JWT; Django CSRF middleware disabled for API (re-enabled for admin) |
| CORS | `django-cors-headers` with explicit `CORS_ALLOWED_ORIGINS` |
| SQL injection | Django ORM parameterized queries throughout |
| Input validation | DRF serializers + model constraints |
| Concurrent updates | `select_for_update()` on stock operations inside `transaction.atomic()` |
| Secrets | `.env` files; `python-decouple` for reading; never committed |
| Rate limiting | `django-ratelimit` on auth endpoints (v1: configurable) |

---

## 6. Database Transactions & Concurrency

All stock-modifying operations follow this pattern:

```python
with transaction.atomic():
    batch = Batch.objects.select_for_update().get(pk=batch_id)
    # validate
    batch.quantity -= quantity
    batch.save()
    StockMovement.objects.create(...)
```

This ensures that two simultaneous requests cannot both read the same quantity and both succeed, preventing phantom over-dispensing.

---

## 7. Environment Configuration

### Backend `.env.example`
```
SECRET_KEY=your-django-secret-key-here
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
DATABASE_URL=postgres://user:password@localhost:5432/medicine_tracker
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
TIME_ZONE=Africa/Addis_Ababa
```

### Frontend `.env.example`
```
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_NAME=Medicine Tracker
```
