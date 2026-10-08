# HeartGuard — Project Handover Document

**Version:** 1.0.0  
**Date:** September 2026  
**Status:** Final Release

---

## 1. Project Overview

HeartGuard is an academic/research prototype for early heart disease risk prediction using Explainable AI. It provides a Streamlit-based web application with role-based access for patients, clinical reviewers, and administrators.

### Key Capabilities
- Multimodal heart disease risk prediction (clinical + lifestyle)
- SHAP-based explainability for every prediction
- NLP-powered lifestyle cardiovascular risk scoring
- Doctor review portal for clinical oversight
- Admin analytics, model monitoring, and data quality dashboards
- Emergency SMS alerts via Twilio (demo mode disabled)
- PDF report generation
- Comprehensive security (RBAC, IDOR protection, audit logging)

---

## 2. Setup

### Prerequisites
- Python 3.10+
- pip

### Installation
```bash
# Clone repository
git clone https://github.com/your-org/heartguard.git
cd heartguard

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Create admin user
python scripts/create_admin.py

# Train models (or use pre-trained artifacts in models/)
python scripts/train_models.py

# Start application
streamlit run app.py
```

---

## 3. Configuration

All configuration is in `config/settings.py` and `.env`.

### Required Environment Variables
| Variable | Purpose | Default |
|----------|---------|---------|
| `SECRET_KEY` | Session security | (must set in production) |
| `ENVIRONMENT` | deployment mode | `development` |
| `TWILIO_ACCOUNT_SID` | SMS alerts | (blank = demo mode) |
| `TWILIO_AUTH_TOKEN` | SMS alerts | (blank = demo mode) |

### Key Files
| File | Purpose |
|------|---------|
| `config/settings.py` | Centralized configuration |
| `.env.example` | Environment variable template |
| `models/model_manifest.json` | Model artifact checksums |
| `.streamlit/config.toml` | Streamlit theme configuration |

---

## 4. Architecture

### Databases (6 SQLite files)
| Database | Path | Purpose |
|----------|------|---------|
| Auth | `data/auth/heartguard_auth.db` | User accounts |
| Audit | `data/security/audit.db` | Security audit trail |
| Assessments | `data/assessments/assessments.db` | Risk assessments |
| Reviews | `data/assessments/reviews.db` | Doctor reviews |
| Recommendations | `data/assessments/recommendations.db` | Clinical recommendations |
| Alerts | `data/alerts/alerts.db` | Emergency alerts |

### Model Artifacts (in `models/`)
| File | Purpose |
|------|---------|
| `random_forest.pkl` | Primary classifier |
| `xgboost.pkl` | Ensemble member |
| `neural_network.pkl` | Ensemble member |
| `logistic_regression.pkl` | Baseline classifier |
| `preprocessor.pkl` | Feature preprocessing pipeline |
| `feature_names.json` | Feature name registry |
| `model_manifest.json` | Integrity checksums |

---

## 5. Model

### Training
```bash
python scripts/train_models.py
```

### Current Metrics (Test Set)
| Model | Accuracy | F1 | ROC-AUC |
|-------|----------|-----|---------|
| Random Forest | 0.5738 | 0.675 | 0.5381 |
| XGBoost | 0.5902 | 0.638 | 0.6078 |
| Neural Network | 0.5574 | 0.609 | 0.4978 |
| Logistic Regression | 0.4098 | 0.471 | 0.4357 |

### Dataset
- Cleveland Heart Disease (UCI ML Repository)
- 303 samples, 19 features
- Binary classification: heart disease present/absent

### Important Notes
- Models are for research/academic purposes only
- Not validated on diverse populations
- Requires clinical validation before any real-world use

---

## 6. Database

### Schema Management
- No formal migration framework
- Tables created automatically on first use
- Schema is stable since Phase 6

### Backup
See `docs/deployment/backup_strategy.md` for backup procedures.

---

## 7. Deployment

### Local Development
```bash
streamlit run app.py
```

### Docker
```bash
docker build -t heartguard .
docker run -p 8501:8501 heartguard
```

### Health Check
```bash
python scripts/health_check.py --readiness
```

See `docs/deployment/production_setup.md` for production deployment guide.

---

## 8. Testing

### Run All Tests
```bash
pytest -q
```

### Run Specific Test Suites
```bash
pytest tests/test_auth.py -q          # Authentication
pytest tests/test_security.py -q      # Security
pytest tests/test_prediction.py -q    # ML prediction
pytest tests/test_shap.py -q          # SHAP explainability
```

### Test Count
- 562 tests across 40+ test files
- All tests pass

---

## 9. Maintenance

### Updating Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Retraining Models
1. Collect/validate new data
2. Run `python scripts/train_models.py`
3. Evaluate new model against current
4. Review and approve
5. Replace model artifacts
6. Update `model_manifest.json` checksums
7. Monitor for drift

### Reviewing Monitoring
- Admin Dashboard: Risk distributions, prediction analytics
- Model Monitoring: Performance metrics over time
- Data Quality: Missing values, invalid values, schema changes

---

## 10. Troubleshooting

### Application Won't Start
1. Check Python version: `python --version`
2. Check dependencies: `pip install -r requirements.txt`
3. Check `.env` file exists
4. Check database directories exist

### Model Loading Fails
1. Verify `models/` directory contains `.pkl` files
2. Check `models/model_manifest.json` checksums
3. Retrain if artifacts corrupted: `python scripts/train_models.py`

### Database Errors
1. Check `data/` directory structure
2. Delete corrupted `.db` files (will recreate on next use)
3. Check disk space

### Test Failures
1. Run `pytest -q` to identify failing tests
2. Check for Windows PermissionError (use `shutil.rmtree(ignore_errors=True)`)
3. Check for missing NLTK data

---

## 11. Key Contacts

This is an academic project. For questions:
- Project documentation: `docs/`
- Architecture: `docs/architecture.md`
- Security: `docs/security.md`
- ML Pipeline: `docs/ml_pipeline.md`

---

## 12. Future Development

If extending HeartGuard:
1. Create a new branch
2. Follow existing code conventions
3. Add tests for new features
4. Update documentation
5. Do NOT modify clinical model architecture, weights, or thresholds without review
