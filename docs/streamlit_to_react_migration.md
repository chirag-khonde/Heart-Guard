# Streamlit to React Migration

> **Phase 21 — Migration Complete** | Last updated: September 2026

## Table of Contents

- [Executive Summary](#executive-summary)
- [Old Architecture (Streamlit)](#old-architecture-streamlit)
- [New Architecture (React + FastAPI)](#new-architecture-react--fastapi)
- [Feature Mapping](#feature-mapping)
- [API Endpoints Created](#api-endpoints-created)
- [What Was Preserved](#what-was-preserved)
- [What Was Added](#what-was-added)
- [Streamlit Dependencies That Can Be Removed](#streamlit-dependencies-that-can-be-removed)
- [Running Both Systems](#running-both-systems)
- [Migration Status](#migration-status)

---

## Executive Summary

Phase 21 replaces the Streamlit frontend with a modern React SPA and a thin FastAPI REST layer. All existing Python backend services (risk engine, analytics, recommendations, alerts, reports, security, audit logging) are **unchanged** — the FastAPI layer is a passthrough that calls the same service functions Streamlit was calling directly.

The Streamlit application (`app.py` + `pages/`) remains functional and can run alongside the new system during the transition period.

---

## Old Architecture (Streamlit)

```
┌─────────────────────────────────────────────┐
│              Streamlit App                   │
│                                              │
│  app.py  ←→  pages/*.py  ←→  src/*.py       │
│  (UI + routing)  (page views)  (services)    │
│                                              │
│  ┌───────────────────────────────────────┐   │
│  │  Streamlit widgets render the UI      │   │
│  │  st.write, st.form, st.columns, etc.  │   │
│  │  Session state for auth + data cache  │   │
│  └───────────────────────────────────────┘   │
│                                              │
│  ┌───────────────────────────────────────┐   │
│  │  Python services (business logic)     │   │
│  │  - src/risk_engine/                   │   │
│  │  - src/analytics/                     │   │
│  │  - src/recommendations/              │   │
│  │  - src/alerts/                        │   │
│  │  - src/reports/                       │   │
│  │  - src/security/                      │   │
│  │  - src/auth/                          │   │
│  │  - src/review/                        │   │
│  │  - src/health/                        │   │
│  └───────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**Characteristics:**
- Monolithic Python application
- UI and business logic tightly coupled
- Session-based authentication (`st.session_state`)
- Server-side rendering (every interaction triggers a full Python rerun)
- Single process handles UI + backend
- No REST API — Python calls services directly

---

## New Architecture (React + FastAPI)

```
┌──────────────────┐     HTTP/JSON     ┌──────────────────┐
│                  │  ──────────────→  │                  │
│  React Frontend  │                   │  FastAPI Backend  │
│  (Vite, port     │  ←──────────────  │  (port 8000)     │
│   5173)          │                   │                  │
│                  │                   │  ┌────────────┐  │
│  - React Router  │                   │  │ api/*.py   │  │
│  - AuthContext   │                   │  │ (routers)  │  │
│  - Axios client  │                   │  └─────┬──────┘  │
│  - Tailwind CSS  │                   │        │         │
│  - Recharts      │                   │  ┌─────▼──────┐  │
│                  │                   │  │ src/*.py    │  │
│                  │                   │  │ (services)  │  │
│                  │                   │  └────────────┘  │
└──────────────────┘                   └──────────────────┘
```

**Characteristics:**
- Decoupled frontend and backend
- RESTful API contract between React and FastAPI
- JWT-based stateless authentication
- Client-side rendering with SPA routing
- Independent scaling of frontend and backend
- Same Python services — zero business logic changes

---

## Feature Mapping

### Public Pages

| Streamlit Page              | React Page            | API Endpoint                | Status    |
|-----------------------------|-----------------------|-----------------------------|-----------|
| `app.py` (home/landing)    | `LandingPage.jsx`     | None (static)               | COMPLETE  |
| `pages/about.py`           | `About.jsx`           | None (static)               | COMPLETE  |
| `pages/login.py`           | `LoginPage.jsx`       | `POST /api/auth/login`      | COMPLETE  |
| `pages/register.py`        | `RegisterPage.jsx`    | `POST /api/auth/register`   | COMPLETE  |

### Patient Pages

| Streamlit Page                    | React Page                  | API Endpoint                        | Status    |
|-----------------------------------|-----------------------------|-------------------------------------|-----------|
| `pages/dashboard.py`              | `patient/Dashboard.jsx`     | `GET /api/dashboard`                | COMPLETE  |
| `pages/risk_assessment.py`        | `patient/AssessmentPage.jsx`| `POST /api/assessments`             | COMPLETE  |
| (inline result display)           | `patient/PredictionResult.jsx` | `GET /api/assessments/:id`       | COMPLETE  |
| `pages/history.py`                | `patient/HistoryPage.jsx`   | `GET /api/assessments`              | COMPLETE  |
| `pages/history.py` (alerts)       | `patient/AlertsPage.jsx`    | `GET /api/assessments`              | COMPLETE  |
| `pages/explainable_ai.py`         | `patient/RecommendationsPage.jsx` | `GET /api/recommendations`    | COMPLETE  |
| `pages/patient_analytics.py`      | `patient/PatientAnalyticsPage.jsx` | `GET /api/dashboard`          | COMPLETE  |
| `pages/lifestyle_analyzer.py`     | `patient/LifestyleAnalyzerPage.jsx` | `POST /api/assessments`      | COMPLETE  |
| `pages/history.py` (reports)      | `patient/ReportsPage.jsx`   | `POST /api/reports/generate/:id`    | COMPLETE  |

### Reviewer Pages

| Streamlit Page                    | React Page                  | API Endpoint                        | Status    |
|-----------------------------------|-----------------------------|-------------------------------------|-----------|
| `pages/review.py`                 | `reviewer/ReviewerDashboard.jsx` | `GET /api/reviews/stats`        | COMPLETE  |
| (inline queue)                    | `reviewer/ReviewQueue.jsx`  | `GET /api/reviews/queue`            | COMPLETE  |
| (inline detail)                   | `reviewer/ReviewDetail.jsx` | `GET /api/assessments/:id`          | COMPLETE  |
| (review actions)                  | `reviewer/ReviewDetail.jsx` | `POST/PUT /api/reviews/:id`         | COMPLETE  |

### Admin Pages

| Streamlit Page                    | React Page                  | API Endpoint                        | Status    |
|-----------------------------------|-----------------------------|-------------------------------------|-----------|
| `pages/admin.py`                  | `admin/AdminDashboard.jsx`  | `GET /api/admin/analytics`          | COMPLETE  |
| `pages/analytics_dashboard.py`    | `admin/AdminAnalytics.jsx`  | `GET /api/admin/analytics`          | COMPLETE  |
| `pages/model_performance.py`      | `admin/ModelMonitoring.jsx` | `GET /api/admin/model/*`            | COMPLETE  |
| `pages/model_monitoring.py`       | `admin/ModelMonitoring.jsx` | `GET /api/admin/model/drift`        | COMPLETE  |
| (inline data quality)             | `admin/DataQuality.jsx`     | `GET /api/admin/data-quality`       | COMPLETE  |
| (inline system health)            | `admin/SystemHealth.jsx`    | `GET /api/admin/health`             | COMPLETE  |
| `pages/security.py` (audit logs)  | `admin/AuditLogs.jsx`       | `GET /api/admin/audit`              | COMPLETE  |
| `pages/security.py` (users)       | `admin/UserManagement.jsx`  | `GET /api/admin/users`              | COMPLETE  |

---

## API Endpoints Created

All endpoints are prefixed with `/api` and require JWT authentication unless noted.

### Authentication (`api/auth.py`)

| Method | Path                  | Auth Required | Role Required | Description               |
|--------|-----------------------|---------------|---------------|---------------------------|
| POST   | `/api/auth/register`  | No            | —             | Register new user         |
| POST   | `/api/auth/login`     | No            | —             | Authenticate, get JWT     |
| GET    | `/api/auth/me`        | Yes           | Any           | Get current user profile  |

### Assessments (`api/assessments.py`)

| Method | Path                        | Auth Required | Role Required | Description               |
|--------|-----------------------------|---------------|---------------|---------------------------|
| POST   | `/api/assessments`          | Yes           | Any           | Create risk assessment    |
| GET    | `/api/assessments`          | Yes           | Any           | List assessments          |
| GET    | `/api/assessments/latest`   | Yes           | Any           | Get latest assessment     |
| GET    | `/api/assessments/:id`      | Yes           | Any           | Get assessment by ID      |

### Dashboard (`api/dashboard.py`)

| Method | Path                | Auth Required | Role Required | Description               |
|--------|---------------------|---------------|---------------|---------------------------|
| GET    | `/api/dashboard`    | Yes           | Any           | Get dashboard data        |

### Reviews (`api/reviews.py`)

| Method | Path                          | Auth Required | Role Required     | Description               |
|--------|-------------------------------|---------------|-------------------|---------------------------|
| GET    | `/api/reviews/queue`          | Yes           | reviewer, admin   | Get review queue          |
| GET    | `/api/reviews/pending`        | Yes           | reviewer, admin   | Get pending reviews       |
| POST   | `/api/reviews/:assessmentId`  | Yes           | reviewer, admin   | Create review             |
| PUT    | `/api/reviews/:id`            | Yes           | reviewer, admin   | Update review             |
| GET    | `/api/reviews/stats`          | Yes           | reviewer, admin   | Get review statistics     |

### Admin (`api/admin.py`)

| Method | Path                          | Auth Required | Role Required | Description               |
|--------|-------------------------------|---------------|---------------|---------------------------|
| GET    | `/api/admin/analytics`        | Yes           | admin         | Aggregated analytics      |
| GET    | `/api/admin/model/status`     | Yes           | admin         | Model status summary      |
| GET    | `/api/admin/model/drift`      | Yes           | admin         | Drift detection results   |
| GET    | `/api/admin/model/performance`| Yes           | admin         | Performance metrics       |
| GET    | `/api/admin/data-quality`     | Yes           | admin         | Data quality report       |
| GET    | `/api/admin/health`           | Yes           | admin         | System health             |
| GET    | `/api/admin/audit`            | Yes           | admin         | Audit log entries         |
| GET    | `/api/admin/audit/stats`      | Yes           | admin         | Audit statistics          |
| GET    | `/api/admin/users`            | Yes           | admin         | List all users            |

### Recommendations (`api/recommendations.py`)

| Method | Path                                    | Auth Required | Role Required | Description               |
|--------|-----------------------------------------|---------------|---------------|---------------------------|
| GET    | `/api/recommendations/:assessmentId`    | Yes           | Any           | Get insights for assessment|
| GET    | `/api/recommendations`                  | Yes           | Any           | Get all user recommendations|

### Reports (`api/reports.py`)

| Method | Path                            | Auth Required | Role Required | Description               |
|--------|---------------------------------|---------------|---------------|---------------------------|
| POST   | `/api/reports/generate/:id`     | Yes           | Any           | Generate PDF report       |
| GET    | `/api/reports/:id/download`     | Yes           | Any           | Download PDF report       |

### Security (`api/security.py`)

| Method | Path                    | Auth Required | Role Required | Description               |
|--------|-------------------------|---------------|---------------|---------------------------|
| GET    | `/api/security/audit`   | Yes           | Any           | User's audit logs         |

### Health (`api/health.py`)

| Method | Path                | Auth Required | Role Required | Description               |
|--------|---------------------|---------------|---------------|---------------------------|
| GET    | `/api/health`       | No            | —             | Health check              |
| GET    | `/api/health/ready` | No            | —             | Readiness probe           |
| GET    | `/api/health/live`  | No            | —             | Liveness probe            |

---

## What Was Preserved

**All Python backend services are completely unchanged:**

| Service Directory              | Description                              |
|--------------------------------|------------------------------------------|
| `src/risk_engine/`             | Multimodal heart disease risk engine     |
| `src/analytics/`               | Analytics, history, trends, data quality |
| `src/recommendations/`         | Rule-based recommendation engine         |
| `src/alerts/`                  | Critical risk alert manager              |
| `src/reports/`                 | PDF report generator                     |
| `src/security/`                | Audit logging, rate limiting             |
| `src/auth/`                    | User auth, authorization, session mgmt   |
| `src/review/`                  | Clinical review workflow                 |
| `src/health/`                  | System health monitoring                 |
| `src/ui/`                      | Streamlit UI utilities (still used by old frontend) |
| `config/`                      | Settings and configuration               |
| `models/`                      | Trained ML models and artifacts          |
| `data/`                        | Database and data files                  |
| `scripts/`                     | Utility and setup scripts                |
| `tests/`                       | Pytest test suite                        |

---

## What Was Added

### FastAPI Layer (`api/`)

| File               | Purpose                                                      |
|--------------------|--------------------------------------------------------------|
| `main.py`          | FastAPI app, CORS, middleware, router registration           |
| `deps.py`          | JWT auth, role checking, rate limiting, `CurrentUser` model  |
| `auth.py`          | Register, login, get-me endpoints                            |
| `assessments.py`   | CRUD for heart risk assessments                              |
| `dashboard.py`     | Patient dashboard aggregation                                |
| `reviews.py`       | Clinical review workflow endpoints                           |
| `admin.py`         | Admin analytics, monitoring, audit, user management          |
| `recommendations.py` | Recommendation retrieval                                    |
| `reports.py`       | PDF report generation and download                           |
| `security.py`      | Security audit log access                                    |
| `health.py`        | Health/readiness/liveness probes                             |
| `requirements.txt` | FastAPI, uvicorn, python-jose, pydantic                      |

### React Frontend (`frontend/`)

| Directory          | Files | Purpose                                    |
|--------------------|-------|--------------------------------------------|
| `src/`             | 4     | Entry points, global styles, app routing   |
| `src/context/`     | 1     | Auth state management                      |
| `src/services/`    | 1     | API client layer                           |
| `src/components/`  | 20    | Reusable UI components and layouts         |
| `src/pages/`       | 25    | All page views for 3 roles + public        |
| Config files       | 5     | Vite, package.json, env, linter, gitignore |

---

## Streamlit Dependencies That Can Be Removed

After confirming the React frontend is fully operational, these Streamlit-specific items can be removed:

| File/Directory                | Reason                                      |
|-------------------------------|---------------------------------------------|
| `app.py`                      | Streamlit entry point (replaced by React SPA)|
| `pages/*.py` (all 16 files)   | Streamlit page views (replaced by React pages)|
| `.streamlit/`                 | Streamlit configuration directory            |
| `src/ui.py`                   | Streamlit UI utilities (`render_sidebar`, `inject_global_theme`) |
| `streamlit` in `requirements.txt` | Streamlit package dependency            |
| `st` imports throughout `src/` | Only if `src/ui.py` is removed; some services may reference session state |

**Note:** Keep `src/ui.py` and Streamlit dependencies until the React system is validated in production. The old system serves as a fallback during the transition.

---

## Running Both Systems

### Old System (Streamlit)

```bash
# From project root
streamlit run app.py --server.port 8501
```

Available at `http://localhost:8501`. All existing functionality works unchanged.

### New System (React + FastAPI)

**Terminal 1 — FastAPI backend:**
```bash
cd C:\Alpha\HeartGuard
python -m uvicorn api.main:app --reload --port 8000
```

**Terminal 2 — React dev server:**
```bash
cd C:\Alpha\HeartGuard\frontend
npm run dev
```

Available at `http://localhost:5173`. The Vite proxy forwards `/api` requests to port 8000.

### Running Both Simultaneously

Both systems can run on the same machine without conflicts:

| System     | Port | URL                          |
|------------|------|------------------------------|
| Streamlit  | 8501 | `http://localhost:8501`      |
| FastAPI    | 8000 | `http://localhost:8000`      |
| React      | 5173 | `http://localhost:5173`      |

Both systems share the same:
- SQLite database (`data/`)
- Trained models (`models/`)
- Configuration (`config/`)
- Python services (`src/`)

---

## Migration Status

| Category              | Status      | Notes                                        |
|-----------------------|-------------|----------------------------------------------|
| FastAPI backend       | COMPLETE    | 9 routers, 30+ endpoints                    |
| React frontend        | COMPLETE    | 25 pages, 20 components, 3 layouts          |
| Auth (JWT)            | COMPLETE    | Register, login, session restore             |
| Patient features      | COMPLETE    | Dashboard, assessment, history, alerts, etc. |
| Reviewer features     | COMPLETE    | Review queue, review detail, notes           |
| Admin features        | COMPLETE    | Analytics, monitoring, audit, users          |
| Design system         | COMPLETE    | Tailwind, consistent color/type/radius       |
| Responsive design     | COMPLETE    | Mobile-first, lg: breakpoint for desktop    |
| API proxy             | COMPLETE    | Vite dev proxy + production nginx config    |
| Streamlit preserved   | COMPLETE    | Old system runs unchanged as fallback       |
| Production docs       | COMPLETE    | This document and frontend architecture doc |

**Migration is COMPLETE.** The React frontend is feature-equivalent to the Streamlit application and ready for production deployment.
