# HeartGuard Deployment Runbook

## Prerequisites

- Python 3.12+
- 4 GB+ RAM (TensorFlow/SHAP requirement)
- 2 GB+ disk space
- Docker (optional, for containerized deployment)

## 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd HeartGuard

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with production values (see Environment Variables below)
```

## 2. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ENVIRONMENT` | Yes | `development` | `development`, `testing`, or `production` |
| `SECRET_KEY` | Yes (prod) | `heartguard-change-in-production` | Strong random string for token signing |
| `DEBUG` | Yes | `false` | Must be `false` in production |
| `APP_URL` | No | `http://localhost:8501` | Application public URL |
| `ALLOWED_ORIGINS` | No | `http://localhost:8501` | CORS allowed origins |
| `LOG_LEVEL` | No | `WARNING` (prod) | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_TO_FILE` | No | `true` (prod) | Enable rotating file logs |
| `ALERTS_ENABLED` | No | `false` | Enable Twilio SMS alerts |
| `TWILIO_ACCOUNT_SID` | If alerts | - | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | If alerts | - | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | If alerts | - | Twilio sender phone number |

## 3. Generate Production Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Set the output as `SECRET_KEY` in your `.env` file.

## 4. Database Setup

Databases are created automatically on first run. No manual migration needed.

SQLite databases created:
- `data/auth/heartguard_auth.db` — User accounts
- `data/security/audit.db` — Security audit trail
- `data/assessments/assessments.db` — Patient assessments
- `data/assessments/reviews.db` — Doctor reviews
- `data/assessments/recommendations.db` — Recommendations
- `data/alerts/alerts.db` — Emergency alerts

## 5. Create Admin Account

```bash
ADMIN_EMAIL=admin@yourdomain.com ADMIN_PASSWORD=YourSecurePass123 python scripts/create_admin.py
```

## 6. Create Reviewer Account

```bash
REVIEWER_EMAIL=doctor@yourdomain.com REVIEWER_PASSWORD=YourSecurePass123 python scripts/create_reviewer.py
```

## 7. Verify Model Artifacts

Ensure `models/` directory contains:
- `random_forest.pkl`
- `xgboost.pkl`
- `neural_network.pkl`
- `logistic_regression.pkl`
- `preprocessor.pkl`
- `feature_names.json`
- `model_manifest.json`
- `model_metadata.json`

## 8. Run Health Check

```bash
python scripts/health_check.py --full
```

Expected output: `"status": "healthy"`

## 9. Start Application

```bash
streamlit run app.py
```

## 10. Production Startup (Streamlit)

```bash
streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --browser.gatherUsageStats=false \
  --server.enableXsrfProtection=true \
  --server.enableCORS=false
```

## 11. Docker Deployment

```bash
# Build image
docker build -t heartguard:latest .

# Run container
docker run -d \
  --name heartguard \
  -p 8501:8501 \
  -e ENVIRONMENT=production \
  -e SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
  -e ALLOWED_ORIGINS=https://yourdomain.com \
  -v heartguard-data:/app/data \
  -v heartguard-logs:/app/logs \
  --restart unless-stopped \
  heartguard:latest
```

## 12. Verify Deployment

1. Open `http://your-server:8501`
2. Login with admin credentials
3. Create a test assessment
4. Verify SHAP explainability works
5. Check audit logs in Admin Dashboard
6. Run `python scripts/health_check.py --readiness`

## 13. Rollback Procedure

### Application Rollback
```bash
# Revert to previous commit
git checkout <previous-commit-hash>
pip install -r requirements.txt
# Restart application
```

### Model Rollback
```bash
# Restore previous model files from backup
cp /backup/models/random_forest.pkl models/random_forest.pkl
# Verify integrity
python scripts/health_check.py --full
```

### Database Rollback
```bash
# SQLite: Restore from backup copy
cp /backup/data/auth/heartguard_auth.db data/auth/heartguard_auth.db
```

## 14. Backup Strategy

| Component | Frequency | Retention | Method |
|---|---|---|---|
| SQLite databases | Daily | 30 days | File copy |
| Model artifacts | On change | Keep previous 2 versions | File copy |
| Configuration | On change | Version controlled | Git |
| Generated reports | Per retention policy | 30 days | Automatic cleanup |

**Note:** Automated production backups require deployment-specific configuration (cron jobs, cloud backup services, etc.).

## 15. Monitoring

Check application health:
```bash
# Full health check
python scripts/health_check.py --full

# Liveness only (for orchestrator)
python scripts/health_check.py --liveness

# Readiness (for load balancer)
python scripts/health_check.py --readiness
```

## 16. Troubleshooting

| Issue | Resolution |
|---|---|
| Startup blocked: insecure SECRET_KEY | Set a strong SECRET_KEY in production |
| Startup blocked: DEBUG=true | Set DEBUG=false in production |
| Model integrity error | Restore model from backup, retrain |
| Database locked | Check DB_BUSY_TIMEOUT_MS, reduce concurrent writes |
| Memory issues | Reduce Streamlit server workers, check TensorFlow memory |
