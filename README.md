# 💊 Medicine Availability & Expiry Tracker !

A full-stack pharmacy inventory and availability platform built for Ethiopian pharmacy operations.

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.1-green)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-19-blue)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue)](https://typescriptlang.org)
[![Tests](https://img.shields.io/badge/tests-62%20passing-brightgreen)](#testing)

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [API Documentation](#api-documentation)
- [User Roles](#user-roles)
- [Production Deployment](#production-deployment)
- [Developer](#developer)

---

## Overview

Pharmacies use this platform to:
- Manage medicine batches with quantities, expiry dates, and supplier info
- Track all stock movements with a full audit trail
- Get alerted about expiring and low-stock items
- Allow the public to search for medicine availability nearby

Key safety guarantees:
- Expired batches are **never** counted as usable stock or shown as publicly available
- Stock quantities cannot go negative (enforced at DB and service layer)
- Concurrent updates are protected by `SELECT FOR UPDATE` transactions
- All movements are append-only and auditable

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, Django 5.1, Django REST Framework 3.15 |
| Auth | Simple JWT 5.3 (15 min access, 7 day refresh, blacklist) |
| Database | PostgreSQL 16 (SQLite for quick local dev) |
| API Docs | drf-spectacular 0.27 (OpenAPI 3.0 + Swagger UI) |
| Frontend | React 19, TypeScript 5.7, Vite 6 |
| Styling | Tailwind CSS 3 |
| State | TanStack Query v5, React Hook Form, Zod |
| Charts | Recharts |
| Testing | pytest + pytest-django, Vitest + React Testing Library |

---

## Features

- **Authentication** — JWT login/logout/refresh, registration, password change
- **Role-based access** — system_admin, pharmacy_admin, inventory_staff
- **Pharmacy management** — profiles, members, operating hours, GPS coordinates
- **Medicine catalog** — shared across all pharmacies, searchable
- **Batch inventory** — lot-level tracking with expiry dates and quantities
- **Stock movements** — received, sold, dispensed, adjustment, correction (with approval)
- **Expiry management** — configurable warning window, expired batch removal
- **Low-stock alerts** — per-medicine minimum thresholds
- **Availability search** — public search with staleness indicator
- **Dashboard** — real aggregated data, charts, recent activity
- **Reports** — stock summary, expiring, expired, movements, low-stock (+ CSV export)
- **Audit log** — immutable change history with user and IP
- **OpenAPI docs** — auto-generated Swagger UI at `/api/docs/`

---

## Project Structure

```
Medicine-availability-and-expiry-tracker/
├── backend/                    # Django REST API
│   ├── config/                 # Settings (base, development, production)
│   ├── apps/
│   │   ├── accounts/           # Users, JWT auth, RBAC
│   │   ├── pharmacies/         # Pharmacy profiles and membership
│   │   ├── medicines/          # Shared medicine catalog
│   │   ├── inventory/          # Batches, movements, dashboard, search
│   │   ├── reports/            # Report generation and CSV export
│   │   ├── audit/              # Immutable audit log
│   │   └── core/               # Pagination, permissions, exceptions
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   ├── manage.py
│   └── .env.example
└── frontend/                   # React + Vite application
    ├── src/
    │   ├── api/                # Typed Axios service functions
    │   ├── features/auth/      # Auth context and protected routes
    │   ├── layouts/            # Public and Dashboard layouts
    │   ├── pages/              # Route-level page components
    │   ├── types/              # TypeScript interfaces
    │   └── utils/              # Date formatting, helpers
    ├── package.json
    └── .env.example
```

---

## Prerequisites

- **Python** 3.11+ (tested on 3.13)
- **Node.js** 18+ (tested on 24)
- **PostgreSQL** 14+ (or SQLite for quick local start)
- **Git**

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/Eliyas47/Medicine-availability-and-expiry-tracker.git
cd Medicine-availability-and-expiry-tracker
```

### 2. Backend setup

```bash
# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements/development.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env — set DATABASE_URL if using PostgreSQL

# Run migrations
cd backend
python manage.py migrate

# Create a superuser (system admin)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

The API will be available at `http://localhost:8000`.

### 3. Frontend setup

```bash
# From the repo root
cd frontend

cp .env.example .env.local
# Edit .env.local if your backend runs on a different port

npm install --legacy-peer-deps
npm run dev
```

The app will be available at `http://localhost:5173`.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | — | Django secret key |
| `DEBUG` | No | `False` | Enable debug mode |
| `DATABASE_URL` | No | SQLite | PostgreSQL connection string |
| `ALLOWED_HOSTS` | No | `localhost` | Comma-separated allowed hosts |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost:5173` | Frontend URL |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | No | `15` | Access token lifetime |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | No | `7` | Refresh token lifetime |
| `TIME_ZONE` | No | `Africa/Addis_Ababa` | Server timezone |

### Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | No | `http://localhost:8000/api` | Backend API base URL |
| `VITE_APP_NAME` | No | `Medicine Tracker` | App display name |

---

## Running Tests

### Backend (62 tests)

```bash
cd backend

# Run all tests
python -m pytest

# Run with coverage report
python -m pytest --cov=apps --cov-report=term-missing

# Run a specific app
python -m pytest apps/inventory/tests/ -v
```

### Frontend

```bash
cd frontend
npm test
```

---

## API Documentation

Once the backend is running:

| URL | Description |
|-----|-------------|
| `http://localhost:8000/api/docs/` | Swagger UI |
| `http://localhost:8000/api/redoc/` | ReDoc |
| `http://localhost:8000/api/schema/` | Raw OpenAPI 3.0 schema |

---

## User Roles

| Role | Description |
|------|-------------|
| `system_admin` | Manages all pharmacies, users, medicines, and system config. Created via `createsuperuser`. |
| `pharmacy_admin` | Manages own pharmacy profile, staff, inventory, and approves corrections. |
| `inventory_staff` | Records stock movements and views own pharmacy's inventory. |
| Public (unauthenticated) | Can only access the availability search and public pharmacy listings. |

---

## Production Deployment

1. Set `DJANGO_SETTINGS_MODULE=config.settings.production`
2. Set all required environment variables (especially `SECRET_KEY`, `DATABASE_URL`, `CORS_ALLOWED_ORIGINS`)
3. Run `python manage.py migrate` and `python manage.py collectstatic`
4. Serve with Gunicorn: `gunicorn config.wsgi:application`
5. Build frontend: `npm run build` and serve `dist/` with Nginx
6. Use Nginx to reverse-proxy `/api/*` to Gunicorn

---

## Developer

**Eliyas Siyum**  
Software Engineer | Backend Development | AI Enthusiast 
GitHub: [@Eliyas47](https://github.com/Eliyas47)

---

*Building practical software platform to support better medicine inventory management and availability awareness in Ethiopia.*
