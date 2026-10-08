# HeartGuard Frontend Architecture

> **Phase 21 — React Frontend** | Last updated: September 2026

## Table of Contents

- [Overview](#overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Component Architecture](#component-architecture)
  - [Common Components](#common-components)
  - [Layout Components](#layout-components)
  - [Route Guards](#route-guards)
- [State Management](#state-management)
- [API Service Layer](#api-service-layer)
- [Authentication Flow](#authentication-flow)
- [Role-Based Routing](#role-based-routing)
- [Design System](#design-system)
- [Responsive Design](#responsive-design)
- [Chart Integration](#chart-integration)
- [File-by-File Overview](#file-by-file-overview)
- [Production Build](#production-build)

---

## Overview

The HeartGuard frontend is a single-page application (SPA) built with React 19, Vite 8, and Tailwind CSS 4. It communicates with a FastAPI backend via a RESTful API layer and supports three user roles: **Patient**, **Reviewer**, and **Admin**.

The frontend is entirely decoupled from the Streamlit monolith — it runs as a standalone Vite dev server and builds to static assets for production deployment.

---

## Technology Stack

| Category         | Technology                          | Version   |
|------------------|-------------------------------------|-----------|
| UI Framework     | React                               | 19.2.8    |
| Build Tool       | Vite                                | 8.2.2     |
| CSS              | Tailwind CSS (via `@tailwindcss/vite`) | 4.3.3    |
| Routing          | React Router DOM                    | 7.18.3    |
| HTTP Client      | Axios                               | 1.20.0    |
| Animations       | Framer Motion                       | 13.2.0    |
| Icons            | Lucide React                        | 1.42.0    |
| Charts           | Recharts                            | 3.10.1    |
| Linter           | oxlint                              | 1.79.0    |

---

## Project Structure

```
frontend/
├── .env                          # VITE_API_BASE_URL=/api
├── .gitignore
├── .oxlintrc.json                # Linter config
├── index.html                    # HTML entry point
├── package.json
├── package-lock.json
├── vite.config.js                # Vite + React + Tailwind + API proxy
├── public/                       # Static assets
├── dist/                         # Production build output
└── src/
    ├── main.jsx                  # React entry point (BrowserRouter, ToastProvider)
    ├── App.jsx                   # Root component with all route definitions
    ├── index.css                 # Global styles + Tailwind import
    ├── context/
    │   └── AuthContext.jsx       # Authentication state and methods
    ├── services/
    │   └── api.js                # Axios instance + all API endpoint functions
    ├── components/
    │   ├── common/               # Reusable UI primitives
    │   │   ├── Badge.jsx
    │   │   ├── Button.jsx
    │   │   ├── Card.jsx
    │   │   ├── EmptyState.jsx
    │   │   ├── ErrorState.jsx
    │   │   ├── Input.jsx
    │   │   ├── Loading.jsx
    │   │   ├── Modal.jsx
    │   │   ├── PageHeader.jsx
    │   │   ├── RiskGauge.jsx
    │   │   ├── Select.jsx
    │   │   ├── StatCard.jsx
    │   │   └── Toast.jsx
    │   ├── layout/               # Layout wrappers per role
    │   │   ├── AdminLayout.jsx
    │   │   ├── PatientLayout.jsx
    │   │   ├── ReviewerLayout.jsx
    │   │   ├── Sidebar.jsx
    │   │   └── Topbar.jsx
    │   └── routes/               # Route guard components
    │       ├── ProtectedRoute.jsx
    │       └── RoleRoute.jsx
    └── pages/
        ├── LandingPage.jsx       # Public marketing page
        ├── About.jsx             # Public about page
        ├── NotFound.jsx          # 404 page
        ├── auth/
        │   ├── LoginPage.jsx
        │   └── RegisterPage.jsx
        ├── patient/
        │   ├── Dashboard.jsx
        │   ├── AssessmentPage.jsx
        │   ├── PredictionResult.jsx
        │   ├── HistoryPage.jsx
        │   ├── AlertsPage.jsx
        │   ├── RecommendationsPage.jsx
        │   ├── PatientAnalyticsPage.jsx
        │   ├── LifestyleAnalyzerPage.jsx
        │   └── ReportsPage.jsx
        ├── reviewer/
        │   ├── ReviewerDashboard.jsx
        │   ├── ReviewQueue.jsx
        │   └── ReviewDetail.jsx
        └── admin/
            ├── AdminDashboard.jsx
            ├── AdminAnalytics.jsx
            ├── ModelMonitoring.jsx
            ├── DataQuality.jsx
            ├── SystemHealth.jsx
            ├── AuditLogs.jsx
            └── UserManagement.jsx
```

---

## Development Setup

### Prerequisites

- Node.js >= 18
- Python virtual environment with FastAPI running on port 8000

### Start the dev server

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server runs on `http://localhost:5173` by default.

### API Proxy

Vite proxies all `/api` requests to `http://localhost:8000` (the FastAPI backend) via the configuration in `vite.config.js`:

```js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
},
```

This means the frontend never makes cross-origin requests during development — the browser sees everything as same-origin.

### Available Scripts

| Script            | Description                              |
|-------------------|------------------------------------------|
| `npm run dev`     | Start Vite dev server with HMR           |
| `npm run build`   | Production build to `dist/`              |
| `npm run preview` | Preview production build locally         |
| `npm run lint`    | Run oxlint                               |

---

## Component Architecture

### Common Components

Reusable UI primitives in `src/components/common/`. All are stateless, accept props, and use Tailwind classes exclusively.

| Component      | Purpose                                                        | Key Props                                      |
|----------------|----------------------------------------------------------------|------------------------------------------------|
| `Button`       | Styled button with variants and loading state                  | `variant`, `size`, `loading`, `disabled`       |
| `Card`         | White card container with optional header and actions          | `header`, `actions`, `className`               |
| `Badge`        | Colored status badge (risk levels, review states)              | `variant` (low/moderate/high/critical/etc.)    |
| `Input`        | Form input with label and error state                          | `label`, `error`, `helperText`                 |
| `Select`       | Dropdown select with label, options, and error state           | `label`, `options`, `placeholder`, `error`     |
| `Modal`        | Overlay modal dialog with backdrop                             | `open`, `onClose`, `title`, `maxWidth`         |
| `Loading`      | Spinner with optional text, full-screen or inline              | `text`, `fullScreen`                           |
| `PageHeader`   | Page title + description + optional action buttons             | `title`, `description`, `actions`              |
| `StatCard`     | Metric card with icon, value, trend indicator                  | `icon`, `label`, `value`, `trend`, `color`     |
| `RiskGauge`    | SVG circular gauge showing risk score 0-100                    | `score`, `size`                                |
| `Toast`        | Notification system with context provider and auto-dismiss     | `addToast(message, type)` via context           |
| `EmptyState`   | Placeholder when no data is available                          | `icon`, `title`, `message`                     |
| `ErrorState`   | Error display with retry button                                | `title`, `message`, `onRetry`                  |

### Layout Components

Three role-specific layouts in `src/components/layout/`, each wrapping a sidebar + topbar + main content area.

| Layout             | Sidebar Nav Items | Target Role |
|--------------------|-------------------|-------------|
| `PatientLayout`    | Uses shared `Sidebar.jsx` | Patient     |
| `ReviewerLayout`   | Dashboard, Review Queue | Reviewer, Admin |
| `AdminLayout`      | Dashboard, Analytics, Monitoring, Data Quality, Health, Audit, Users | Admin |

**Shared components:**
- `Sidebar.jsx` — Patient-specific sidebar with navigation links, user info, and sign-out button
- `Topbar.jsx` — Sticky top bar with notification bell, user avatar, and sign-out button

All layouts use a responsive pattern:
- **Desktop (lg+):** Fixed 256px sidebar (`w-64`) + main content with left margin
- **Mobile (<lg):** Hamburger menu button → slide-in sidebar with backdrop overlay

### Route Guards

| Component           | Purpose                                                        |
|---------------------|----------------------------------------------------------------|
| `ProtectedRoute`    | Redirects unauthenticated users to `/login`. Shows loading spinner during auth check. |
| `RoleRoute`         | Redirects users without the required role to `/dashboard`.     |

---

## State Management

The app uses React's built-in state management via Context API and local component state. No external state library (Redux, Zustand, etc.) is used.

### AuthContext (`src/context/AuthContext.jsx`)

The central authentication state provider. Exposed values:

| Value            | Type       | Description                                      |
|------------------|------------|--------------------------------------------------|
| `user`           | `object`   | Current user object (`id`, `name`, `email`, `role`) |
| `token`          | `string`   | JWT access token                                 |
| `loading`        | `boolean`  | True while checking auth status on mount         |
| `isAuthenticated`| `boolean`  | `true` if both token and user are present        |
| `login(email, pw)` | function | Authenticates user, stores token, sets user      |
| `register(data)` | function   | Registers new user, stores token, sets user      |
| `logout()`       | function   | Clears token, resets user, navigates to `/login` |
| `hasRole(roles)` | function   | Checks if current user has one of the given roles|

### Local State

Page-level components use `useState` and `useEffect` for:
- Form state (assessment form, login form)
- API data fetching (dashboard data, review queue, audit logs)
- Loading and error states
- UI state (modal open/close, step progress)

---

## API Service Layer

All HTTP communication is centralized in `src/services/api.js`.

### Axios Configuration

```js
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})
```

### Request Interceptor

Automatically attaches the JWT token from `localStorage` to every request:

```js
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('heartguard_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

### Response Interceptor

On 401 responses, clears the token and redirects to `/login`:

```js
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('heartguard_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

### API Endpoints

| Namespace          | Method | Endpoint                              | Description                    |
|--------------------|--------|---------------------------------------|--------------------------------|
| `api.auth`         | POST   | `/api/auth/login`                     | Authenticate user              |
|                    | POST   | `/api/auth/register`                  | Register new user              |
|                    | GET    | `/api/auth/me`                        | Get current user profile       |
| `api.assessments`  | POST   | `/api/assessments`                    | Create heart risk assessment   |
|                    | GET    | `/api/assessments`                    | List user assessments          |
|                    | GET    | `/api/assessments/:id`                | Get assessment by ID           |
|                    | GET    | `/api/assessments/latest`             | Get latest assessment          |
| `api.dashboard`    | GET    | `/api/dashboard`                      | Get patient dashboard data     |
| `api.reviews`      | GET    | `/api/reviews/queue`                  | Get review queue               |
|                    | GET    | `/api/reviews/pending`                | Get pending reviews            |
|                    | POST   | `/api/reviews/:assessmentId`          | Create review for assessment   |
|                    | PUT    | `/api/reviews/:id`                    | Update review                  |
|                    | GET    | `/api/reviews/stats`                  | Get review statistics          |
| `api.admin`        | GET    | `/api/admin/analytics`                | Get aggregated analytics       |
|                    | GET    | `/api/admin/model/status`             | Get model status               |
|                    | GET    | `/api/admin/model/drift`              | Get drift detection results    |
|                    | GET    | `/api/admin/data-quality`             | Get data quality report        |
|                    | GET    | `/api/admin/model/performance`        | Get model performance metrics  |
|                    | GET    | `/api/admin/health`                   | Get system health              |
|                    | GET    | `/api/admin/audit-logs`               | Get audit log entries          |
|                    | GET    | `/api/admin/audit-stats`              | Get audit statistics           |
|                    | GET    | `/api/admin/users`                    | List all users                 |
| `api.recommendations` | GET | `/api/recommendations/assessment/:id` | Get recommendations for assessment |
|                    | GET    | `/api/recommendations`                | Get all user recommendations   |
| `api.reports`      | POST   | `/api/reports/generate/:id`           | Generate PDF report            |
|                    | GET    | `/api/reports/:id/download`           | Download PDF report            |
| `api.security`     | GET    | `/api/security/audit-logs`            | Get user's audit logs          |
| `api.health`       | GET    | `/api/health`                         | Health check                   |

---

## Authentication Flow

1. **Login:** User submits email/password → `POST /api/auth/login` → receives `{ access_token, user }` → token stored in `localStorage` under key `heartguard_token`
2. **Registration:** User submits name/email/password → `POST /api/auth/register` → same token flow as login
3. **Session restore:** On app mount, `AuthProvider` checks for stored token → calls `GET /api/auth/me` → if valid, sets user state; if invalid, clears token
4. **Authenticated requests:** Axios interceptor attaches `Authorization: Bearer <token>` to every outgoing request
5. **Token expiry:** Backend returns 401 → response interceptor clears token and redirects to `/login`
6. **Logout:** `logout()` clears `localStorage`, resets user/token state, navigates to `/login`

---

## Role-Based Routing

Routes in `App.jsx` are organized in three nested groups:

```
/ (public)
├── /login
├── /register
├── /about

Patient (ProtectedRoute)
├── /dashboard
├── /assessment
├── /assessment/result
├── /history
├── /alerts
├── /recommendations
├── /analytics
├── /lifestyle
└── /reports

Reviewer (ProtectedRoute + RoleRoute [reviewer, admin])
├── /reviewer
├── /reviewer/queue
└── /reviewer/assessment/:id

Admin (ProtectedRoute + RoleRoute [admin])
├── /admin
├── /admin/analytics
├── /admin/monitoring
├── /admin/data-quality
├── /admin/health
├── /admin/audit
└── /admin/users
```

**Post-login redirect logic** (in `LoginPage.jsx`):
- `role === 'admin'` → `/admin`
- `role === 'reviewer'` → `/reviewer`
- `role === 'patient'` → `/dashboard`

---

## Design System

### Colors

The app uses Tailwind's Slate palette as the neutral base and Red as the primary brand color.

| Role            | Color Classes                  | Usage                              |
|-----------------|--------------------------------|-------------------------------------|
| Primary         | `red-600` / `red-700`         | Buttons, links, accents, CTA       |
| Background      | `slate-50`                     | Page backgrounds                    |
| Surface         | `white`                        | Cards, modals, sidebars            |
| Text Primary    | `slate-900`                    | Headings, strong text              |
| Text Secondary  | `slate-500` / `slate-600`     | Descriptions, labels               |
| Border          | `slate-200`                    | Card borders, dividers             |
| Success         | `green-600` / `green-100`     | Risk gauge (low), success toasts   |
| Warning         | `amber-600` / `amber-100`     | Risk gauge (moderate), warnings    |
| Danger          | `red-100` / `red-800`         | Error states, critical badges      |
| Info            | `blue-100` / `blue-800`       | Info badges, reviewer accents      |

### Typography

- **Font family:** Inter (via Tailwind `font-sans`)
- **Weights:** `font-medium` (500), `font-semibold` (600), `font-bold` (700), `font-extrabold` (800)
- **Sizes:** `text-xs` (12px), `text-sm` (14px), `text-base` (16px), `text-lg` (18px), `text-xl` (20px), `text-2xl` (24px), `text-3xl` (30px), `text-4xl` (36px)

### Spacing

Standard Tailwind spacing scale. Common patterns:
- Page padding: `p-6`
- Card padding: `p-6`
- Section gaps: `space-y-6`, `gap-6`
- Form field gaps: `space-y-5`
- Sidebar nav items: `px-3 py-2.5`

### Border Radius

- Cards: `rounded-xl`
- Buttons: `rounded-lg`
- Inputs: `rounded-lg`
- Badges: `rounded-full`
- Avatars: `rounded-full`

---

## Responsive Design

The frontend uses a **mobile-first** approach with Tailwind breakpoints:

| Breakpoint | Prefix | Behavior                                           |
|------------|--------|----------------------------------------------------|
| Default    | (none) | Mobile: single column, hamburger menu              |
| 640px      | `sm:`  | Slightly wider layouts, side-by-side form fields   |
| 1024px     | `lg:`  | Desktop: fixed sidebar visible, multi-column grids |

**Key responsive patterns:**
- **Sidebar:** Hidden on mobile with hamburger toggle; fixed 256px on `lg:`
- **Grids:** `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4` for stat cards
- **Assessment form:** Single column on mobile, 2-column on `sm:`
- **Topbar:** User name hidden on mobile (`hidden sm:block`)

---

## Chart Integration

Charts use **Recharts** (v3.10.1). The primary chart type is `LineChart` for risk trend visualization.

```jsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

<ResponsiveContainer width="100%" height={200}>
  <LineChart data={trend}>
    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
    <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
    <Tooltip />
    <Line type="monotone" dataKey="risk_score" stroke="#DC2626" strokeWidth={2} dot={{ r: 4 }} />
  </LineChart>
</ResponsiveContainer>
```

Charts are wrapped in `ResponsiveContainer` to automatically fill their parent container's width.

---

## File-by-File Overview

### Entry Points

| File               | Purpose                                                      |
|--------------------|--------------------------------------------------------------|
| `index.html`       | HTML shell with `<div id="root">` and Vite script tag        |
| `main.jsx`         | Mounts React app with `BrowserRouter` and `ToastProvider`    |
| `App.jsx`          | Defines all routes, wraps in `AuthProvider`                  |
| `index.css`        | Imports Tailwind, sets Inter font, global body styles        |

### Context & Services

| File               | Purpose                                                      |
|--------------------|--------------------------------------------------------------|
| `AuthContext.jsx`  | Auth state (user, token), login/register/logout, role checks |
| `api.js`           | Axios client, interceptors, all API endpoint functions       |

### Route Guards

| File               | Purpose                                                      |
|--------------------|--------------------------------------------------------------|
| `ProtectedRoute.jsx` | Redirects to `/login` if not authenticated                |
| `RoleRoute.jsx`      | Redirects to `/dashboard` if user lacks required role     |

### Common Components

| File               | Purpose                                                      |
|--------------------|--------------------------------------------------------------|
| `Button.jsx`       | Button with `primary`/`secondary`/`danger`/`ghost` variants |
| `Card.jsx`         | White card with optional header and actions slot             |
| `Badge.jsx`        | Status badge with color variants for risk/review states      |
| `Input.jsx`        | Text input with label and error state                        |
| `Select.jsx`       | Dropdown with label, options, and error state                |
| `Modal.jsx`        | Overlay modal with backdrop click to close                   |
| `Loading.jsx`      | Animated spinner with text, full-screen or inline            |
| `PageHeader.jsx`   | Page title + description + optional action buttons           |
| `StatCard.jsx`     | Metric card with icon, value, trend arrow                    |
| `RiskGauge.jsx`    | SVG circular gauge (0-100%) with color thresholds            |
| `Toast.jsx`        | Toast notification context provider and auto-dismiss         |
| `EmptyState.jsx`   | Placeholder icon + message for empty data states             |
| `ErrorState.jsx`   | Error icon + message with optional retry button              |

### Layout Components

| File               | Purpose                                                      |
|--------------------|--------------------------------------------------------------|
| `Sidebar.jsx`      | Patient sidebar with 8 nav items, user info, sign-out       |
| `Topbar.jsx`       | Sticky header with notification bell, user avatar, sign-out  |
| `PatientLayout.jsx`| Sidebar + Topbar + main content for patient routes           |
| `ReviewerLayout.jsx`| Custom sidebar (2 items) + Topbar for reviewer routes       |
| `AdminLayout.jsx`  | Custom sidebar (7 items) + Topbar for admin routes           |

### Pages

| File                       | Purpose                                                 |
|----------------------------|---------------------------------------------------------|
| `LandingPage.jsx`          | Marketing page with hero, features, how-it-works, CTA  |
| `About.jsx`                | About page with project information                     |
| `NotFound.jsx`             | 404 page                                                |
| `auth/LoginPage.jsx`       | Email/password login form with validation               |
| `auth/RegisterPage.jsx`    | Registration form with name, email, password            |
| `patient/Dashboard.jsx`    | Patient home: stats, risk gauge, trend chart, recents   |
| `patient/AssessmentPage.jsx` | 4-step wizard: personal → clinical → lifestyle → review |
| `patient/PredictionResult.jsx` | Displays assessment results with risk score         |
| `patient/HistoryPage.jsx`  | Assessment history list with filters                    |
| `patient/AlertsPage.jsx`   | Critical risk alerts                                    |
| `patient/RecommendationsPage.jsx` | Personalized health recommendations              |
| `patient/PatientAnalyticsPage.jsx` | Patient-specific analytics charts              |
| `patient/LifestyleAnalyzerPage.jsx` | NLP-based lifestyle risk analysis            |
| `patient/ReportsPage.jsx`  | PDF report generation and download                      |
| `reviewer/ReviewerDashboard.jsx` | Reviewer home: stats and pending reviews          |
| `reviewer/ReviewQueue.jsx` | List of assessments awaiting review                     |
| `reviewer/ReviewDetail.jsx` | Individual assessment review with notes              |
| `admin/AdminDashboard.jsx` | Admin home: aggregated stats and system overview        |
| `admin/AdminAnalytics.jsx` | Platform-wide analytics                                 |
| `admin/ModelMonitoring.jsx` | ML model status, drift, and comparison                |
| `admin/DataQuality.jsx`    | Data quality monitoring reports                         |
| `admin/SystemHealth.jsx`   | System health and readiness checks                      |
| `admin/AuditLogs.jsx`      | Security audit log viewer with filters                  |
| `admin/UserManagement.jsx` | User list and management                                |

---

## Production Build

### Build command

```bash
cd frontend
npm run build
```

This outputs optimized static assets to `frontend/dist/`.

### Build output

```
dist/
├── index.html
├── assets/
│   ├── index-[hash].js       # Bundled JS (~150KB gzipped)
│   └── index-[hash].css      # Bundled CSS (~20KB gzipped)
└── ...
```

### Environment Variables

| Variable              | Default            | Description                          |
|-----------------------|--------------------|--------------------------------------|
| `VITE_API_BASE_URL`  | `/api`             | Base URL for API requests            |

For production, set `VITE_API_BASE_URL` to the full API URL or configure a reverse proxy (nginx, Caddy) to route `/api` to the FastAPI backend.

### Production Deployment

1. Build the frontend: `npm run build`
2. Serve `dist/` with a static file server (nginx, Apache, Caddy)
3. Configure reverse proxy: `/api` → `http://localhost:8000`
4. Ensure CORS is configured on the FastAPI backend for the production domain

```nginx
# Example nginx config
server {
    listen 80;
    server_name heartguard.example.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
