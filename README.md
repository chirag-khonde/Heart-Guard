# HeartGuard

**Early Heart Disease Risk Prediction with Explainable AI**

> HeartGuard is an academic and research prototype. It is not a medical diagnostic system.
> Model predictions are experimental estimates and must not replace clinical evaluation
> or advice from a qualified healthcare professional.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Machine Learning Models](#machine-learning-models)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Usage](#usage)
- [Documentation](#documentation)
- [Known Limitations](#known-limitations)
- [Clinical Disclaimer](#clinical-disclaimer)
- [License](#license)

---

## Overview

Heart disease is the leading cause of death globally, responsible for approximately 17.9 million deaths annually (WHO). Early detection of cardiovascular risk can significantly improve patient outcomes through timely intervention. However, existing risk assessment tools often lack transparency, making it difficult for clinicians and patients to understand why a particular risk level was assigned.

HeartGuard addresses this gap by providing a multimodal risk prediction platform that combines clinical machine learning with explainable AI and natural language lifestyle analysis.

### Core Capabilities

1. **Machine Learning** -- Four clinical classifiers (Logistic Regression, Random Forest, XGBoost, Neural Network) trained on the Cleveland Heart Disease dataset.
2. **Explainable AI (SHAP)** -- Every prediction includes a transparent, feature-level explanation of model decisions.
3. **NLP Lifestyle Analysis** -- Free-text lifestyle descriptions are analyzed using a rule-based NLP engine to quantify behavioural risk factors.
4. **Multimodal Risk Fusion** -- Clinical ML predictions (70%) and lifestyle risk scores (30%) are combined into a unified risk score.
5. **Professional Review** -- Authorized reviewers can inspect AI predictions and record clinical observations.
6. **Emergency Alerts** -- Critical risk cases trigger SMS notifications via Twilio.
7. **Monitoring** -- Data drift detection, model performance tracking, and data quality monitoring.

---

## Key Features

| Feature | Description |
|---|---|
| Risk Assessment | Multimodal clinical and lifestyle risk prediction |
| Explainable AI | SHAP-based feature importance and patient-level explanations |
| Lifestyle NLP | Free-text lifestyle risk factor extraction and scoring |
| Emergency Alerts | Twilio SMS notifications for critical risk levels |
| Security and Auth | Bcrypt authentication, RBAC, JWT tokens, rate limiting, audit logging |
| History and Reports | Assessment history, trend analysis, PDF report generation |
| Doctor Review | Professional review portal for clinical observation recording |
| Dashboard | Interactive dashboard with KPIs and charts |
| Model Evaluation | Comprehensive ML model evaluation and comparison |
| Analytics and Monitoring | Drift detection, data quality, anomaly detection, performance monitoring |

---

## Architecture

```
+-------------------------------------------------------------+
|                   React Frontend (Vite)                      |
|  +------+ +------+ +------+ +------+ +------+ +------+     |
|  |Login | |Dash  | |Assess| |Histry| |Review| |Admin |     |
|  +--+---+ +--+---+ +--+---+ +--+---+ +--+---+ +--+---+     |
+-----+--------+--------+--------+--------+--------+----------+
      |        |        |        |        |        |
+-----+--------+--------+--------+--------+--------+----------+
|              REST API Layer (FastAPI)                         |
|  +----------+ +----------+ +----------+ +----------+        |
|  |  Auth    | |Assessment| | Dashboard| |  Reviews |        |
|  |  API     | |   API    | |   API    | |   API    |        |
|  +----------+ +----------+ +----------+ +----------+        |
+--------------------------------------------------------------+
|                    Python Backend Services                    |
|  +----------+ +----------+ +----------+ +----------+        |
|  |  Auth    | |   ML     | |  Risk    | | SHAP     |        |
|  |  Module  | | Pipeline | |  Engine  | | Explainer|        |
|  +----------+ +----------+ +----------+ +----------+        |
|  +----------+ +----------+ +----------+ +----------+        |
|  |  NLP     | |  Alerts  | | Reports  | | Security |        |
|  | Lifestyle| |  Twilio  | | PDF Gen  | | Audit    |        |
|  +----------+ +----------+ +----------+ +----------+        |
+--------------------------------------------------------------+
|                    SQLite Databases                           |
|  +--------+ +--------+ +--------+ +--------+ +--------+    |
|  |  Auth  | |Audit   | |Assess  | |Alerts  | |Reviews |    |
|  +--------+ +--------+ +--------+ +--------+ +--------+    |
+--------------------------------------------------------------+
```

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Frontend | React 19, Vite, Tailwind CSS 4, Recharts, Framer Motion |
| API Layer | FastAPI, Uvicorn |
| ML Libraries | scikit-learn, XGBoost, TensorFlow |
| Explainability | SHAP |
| NLP | NLTK |
| Visualization | Recharts (frontend), Matplotlib (backend) |
| PDF Reports | ReportLab |
| Notifications | Twilio |
| Database | SQLite |
| Authentication | bcrypt, JWT (python-jose) |
| Testing | pytest (40+ test modules) |
| Deployment | Docker (multi-stage build) |
| CI | GitHub Actions |

---

## Machine Learning Models

| Model | Type | CV ROC-AUC |
|---|---|---|
| Logistic Regression | Linear | 0.4357 |
| Random Forest | Ensemble | 0.5381 |
| XGBoost | Gradient Boosting | 0.6078 |
| Neural Network | MLP | 0.4978 |

**Best Model**: XGBoost (selected by highest cross-validated ROC-AUC).

**Multimodal Formula**: `Overall Risk = (Clinical ML Risk x 0.70) + (Lifestyle NLP Risk x 0.30)`

> Note: ROC-AUC scores are modest due to the small dataset size (303 samples). This is an academic prototype, not a clinical-grade system.

---

## Project Structure

```
HeartGuard/
├── api/                        # FastAPI REST API layer
│   ├── main.py                 # FastAPI application entry point
│   ├── auth.py                 # Authentication endpoints
│   ├── assessments.py          # Assessment CRUD endpoints
│   ├── dashboard.py            # Dashboard data endpoints
│   ├── reviews.py              # Review workflow endpoints
│   ├── admin.py                # Admin analytics and monitoring endpoints
│   ├── recommendations.py      # Recommendations endpoints
│   ├── reports.py              # Report generation endpoints
│   ├── lifestyle.py            # Lifestyle analysis endpoints
│   ├── security.py             # Security audit endpoints
│   ├── health.py               # Health check endpoints
│   └── deps.py                 # Auth dependencies and rate limiting
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Page components (patient, reviewer, admin)
│   │   ├── context/            # React context (auth)
│   │   ├── services/           # API service layer
│   │   └── utils/              # Frontend utilities
│   ├── package.json
│   └── vite.config.js
├── src/                        # Python backend services
│   ├── auth/                   # Authentication and authorization
│   ├── ml/                     # ML training and prediction
│   ├── data/                   # Data loading and preprocessing
│   ├── explainability/         # SHAP implementation
│   ├── nlp/                    # Lifestyle NLP analysis
│   ├── risk_engine/            # Multimodal risk calculation
│   ├── alerts/                 # Emergency SMS alerts
│   ├── reports/                # PDF report generation
│   ├── review/                 # Doctor review workflow
│   ├── recommendations/        # Recommendation engine
│   ├── security/               # Security and audit logging
│   ├── analytics/              # Analytics and monitoring
│   ├── evaluation/             # Model evaluation
│   ├── health/                 # Health checks
│   ├── startup/                # Startup validation
│   └── utils/                  # Shared utilities
├── config/                     # Centralized configuration
│   ├── settings.py             # Application settings
│   ├── security.py             # Security policies
│   └── monitoring.py           # Monitoring thresholds
├── tests/                      # Automated test suite
├── models/                     # Trained model artifacts (.pkl)
├── data/                       # Databases and datasets
│   └── raw/heart.csv           # Cleveland Heart Disease dataset
├── reports/                    # Evaluation reports and figures
├── docs/                       # Project documentation
├── scripts/                    # Admin and utility scripts
├── notebooks/                  # Exploratory data analysis
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Multi-stage production Docker build
├── .env.example                # Environment variable template
├── conftest.py                 # Pytest path configuration
└── pytest.ini                  # Pytest settings
```

---

## Installation

### Prerequisites

- Python 3.12 or higher
- Node.js 18 or higher
- pip
- npm

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Yuval0402/heart-guard.git
cd heart-guard

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your settings (at minimum, set SECRET_KEY)

# Start the API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend runs on `http://localhost:5173` and proxies API requests to `http://localhost:8000`.

### Docker Deployment

```bash
# Build the image
docker build -t heartguard .

# Run the container
docker run -p 8000:8000 \
  -e SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
  -e ADMIN_EMAIL=admin@heartguard.local \
  -e ADMIN_PASSWORD=YourSecurePassword \
  heartguard
```

The Docker image uses a multi-stage build: Python dependencies are compiled in a builder stage, the React frontend is built with Node.js, and both are combined into a minimal production image running as a non-root user.

---

## Configuration

All configuration is managed through environment variables. See `.env.example` for the complete template.

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Application secret key (must be changed in production) |
| `ADMIN_EMAIL` | Yes | Admin account email |
| `ADMIN_PASSWORD` | Yes | Admin account password |
| `REVIEWER_EMAIL` | No | Reviewer account email |
| `REVIEWER_PASSWORD` | No | Reviewer account password |
| `TWILIO_ACCOUNT_SID` | No | Twilio account SID for SMS alerts |
| `TWILIO_AUTH_TOKEN` | No | Twilio auth token |
| `ALERTS_ENABLED` | No | Enable SMS alerts (default: `false`) |
| `DEBUG` | No | Debug mode (default: `false`) |
| `ENVIRONMENT` | No | `development`, `testing`, or `production` (default: `development`) |
| `HEARTGUARD_CORS_ORIGINS` | No | Allowed CORS origins (default: `http://localhost:5173`) |

When `ALERTS_ENABLED` is `false` (the default), the application runs in demo mode where all features are operational but external SMS notifications are disabled.

---

## API Reference

The FastAPI backend provides auto-generated interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register a patient account | No |
| `POST` | `/api/auth/login` | Login and receive a JWT | No |
| `GET` | `/api/auth/me` | Current user information | Yes |
| `POST` | `/api/assessments` | Create a new risk assessment | Yes |
| `GET` | `/api/assessments` | List assessments for the current user | Yes |
| `GET` | `/api/assessments/latest` | Retrieve the latest assessment | Yes |
| `GET` | `/api/dashboard` | Dashboard summary data | Yes |
| `GET` | `/api/reviews/queue` | Review queue for pending assessments | Reviewer |
| `POST` | `/api/reviews/{id}` | Submit a professional review | Reviewer |
| `GET` | `/api/admin/analytics` | System analytics overview | Admin |
| `GET` | `/api/admin/health` | System health status | Admin |
| `GET` | `/api/health` | Public health check | No |

---

## Testing

The project includes a comprehensive test suite with 40+ test modules covering authentication, security, ML pipeline, SHAP explainability, risk engine, NLP analysis, review workflows, deployment validation, and more.

```bash
# Run the full test suite
pytest -q

# Run specific test categories
pytest tests/test_auth.py -v                    # Authentication
pytest tests/test_security_phase15.py -v        # Security hardening
pytest tests/test_shap.py -v                    # SHAP explainability
pytest tests/test_multimodal_risk.py -v         # Risk engine
pytest tests/test_review_service.py -v          # Review workflow
pytest tests/test_deployment.py -v              # Deployment checks
pytest tests/test_drift_detection.py -v         # Drift detection
pytest tests/test_preprocessing.py -v           # Data preprocessing
pytest tests/test_pipeline.py -v                # ML pipeline
```

---

## Usage

### Patient Workflow

1. Navigate to the landing page and register an account or log in.
2. View the dashboard with risk summary and trend visualizations.
3. Create a new risk assessment by entering clinical data and a lifestyle description.
4. Review the risk result with SHAP-based explanations.
5. View personalized recommendations based on identified risk factors.
6. Access assessment history and download PDF reports.

### Reviewer Workflow

1. Log in with reviewer credentials.
2. View the reviewer dashboard with queue statistics.
3. Browse pending assessments in the review queue.
4. Inspect AI predictions and explanations for each assessment.
5. Submit professional clinical observations.

### Admin Workflow

1. Log in with admin credentials.
2. View the admin dashboard with system-wide analytics.
3. Monitor model performance, data drift, and data quality.
4. Review audit logs and security events.
5. Manage user accounts.
6. Check system health status.

---

## Documentation

Detailed documentation is available in the `docs/` directory:

| Document | Description |
|---|---|
| `docs/architecture.md` | System architecture and design decisions |
| `docs/data_flow.md` | End-to-end data flow documentation |
| `docs/ml_pipeline.md` | ML training, evaluation, and prediction pipeline |
| `docs/model_card.md` | Model card with performance metrics and limitations |
| `docs/security.md` | Security architecture and controls |
| `docs/privacy.md` | Privacy considerations and data handling |
| `docs/testing.md` | Testing strategy and coverage |
| `docs/user_guide.md` | Patient user guide |
| `docs/admin_guide.md` | Administrator guide |
| `docs/reviewer_guide.md` | Professional reviewer guide |
| `docs/frontend_architecture.md` | React frontend architecture |

---

## Known Limitations

1. **Dataset size** -- Limited to the Cleveland Heart Disease dataset (303 samples). Not validated on diverse or large-scale populations.
2. **Model performance** -- ROC-AUC scores range from 0.43 to 0.61. This is an academic prototype, not a clinical-grade prediction system.
3. **Lifestyle NLP** -- Rule-based approach with a predefined lexicon. It is not a production-grade NLP system.
4. **Clinical validation** -- No clinical validation has been performed. Predictions are experimental estimates only.
5. **Population bias** -- Training data may not represent all demographics equally.
6. **Database** -- SQLite is used for simplicity. Not suitable for high-concurrency production deployments.

---

## Clinical Disclaimer

HeartGuard is an academic and research prototype. It is not a medical diagnostic system and has not been clinically validated. Model predictions are experimental estimates based on the provided data and must not replace evaluation or advice from a qualified healthcare professional.

Do not enter real patient information into a public or demo deployment.

If you or someone nearby is experiencing severe symptoms, seek immediate emergency medical attention.

---

## License

This project is for academic and research purposes only.
