# HeartGuard Production Setup Guide

## Overview

HeartGuard is a Streamlit-based multi-page web application for early heart disease risk prediction with explainable AI. This guide covers production deployment configuration.

## Architecture

```
                    USER (Browser)
                         │
                         ▼
                   HTTPS / DOMAIN
                         │
                         ▼
                 HEARTGUARD APP (Streamlit)
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
        DATABASE      ML MODELS    FILE STORAGE
        (SQLite)      (sklearn)    (reports/tmp)
           │             │             │
           └─────────────┼─────────────┘
                         ▼
                    LOGGING
                    (Rotating)
                         │
                         ▼
                    MONITORING
                   (Health Checks)
```

## Stack

| Component | Technology | Version |
|---|---|---|
| Language | Python | 3.12+ |
| Framework | Streamlit | >=1.30.0 |
| ML | scikit-learn, XGBoost, TensorFlow | See requirements.txt |
| Explainability | SHAP | >=0.43.0 |
| Database | SQLite | Built-in |
| PDF Reports | ReportLab | >=4.0.0 |
| Auth | bcrypt | >=4.0.0 |
| SMS Alerts | Twilio | >=8.10.0 |

## Python Version

Python 3.12 or later is required.

## Dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

See `.env.example` for all available configuration options.

### Production-Critical Variables

| Variable | Value | Notes |
|---|---|---|
| `ENVIRONMENT` | `production` | Enables production logging, blocks insecure config |
| `SECRET_KEY` | `<random-64-char-hex>` | Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DEBUG` | `false` | Must be disabled in production |
| `LOG_TO_FILE` | `true` | Enables rotating log files |
| `LOG_LEVEL` | `WARNING` | Appropriate for production |

## Database

HeartGuard uses SQLite databases stored in `data/`. On first startup, databases and schemas are created automatically.

### Limitations

- SQLite handles concurrent writes with a busy timeout (default 5s)
- For high-concurrency deployments, consider migrating to PostgreSQL
- Back up databases regularly (see Backup Strategy below)

### Backup Strategy

```bash
# Backup all SQLite databases
cp data/auth/heartguard_auth.db backups/auth_$(date +%Y%m%d).db
cp data/security/audit.db backups/audit_$(date +%Y%m%d).db
cp data/assessments/assessments.db backups/assessments_$(date +%Y%m%d).db
```

**Note:** Automated production backups require deployment-specific configuration.

## ML Models

Model artifacts are stored in `models/`. All artifacts are versioned with SHA-256 integrity checksums in `model_manifest.json`.

| Artifact | Purpose | Required |
|---|---|---|
| `random_forest.pkl` | Primary clinical classifier | Yes |
| `preprocessor.pkl` | Feature preprocessing pipeline | Yes |
| `feature_names.json` | Feature name mapping | Yes |
| `model_manifest.json` | Integrity checksums | Yes |
| `xgboost.pkl` | Ensemble member | No |
| `neural_network.pkl` | Ensemble member | No |
| `logistic_regression.pkl` | Baseline classifier | No |

### Model Versioning

Current version: v1 for all artifacts. See `models/model_manifest.json` for checksums.

### Model Rollback

To rollback to a previous model version:
1. Restore `.pkl` files from backup
2. Verify checksums: `python scripts/health_check.py --full`
3. Restart the application

## File Storage

| Directory | Purpose | Persistence |
|---|---|---|
| `reports/generated/` | PDF patient reports | Required for history |
| `data/tmp/` | Temporary files (24h retention) | Ephemeral OK |
| `logs/` | Rotating log files | Required for debugging |
| `models/` | ML model artifacts | Required |

## Startup Command

```bash
streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --browser.gatherUsageStats=false
```

## HTTPS

HTTPS termination should be handled by a reverse proxy (nginx, Caddy, cloud load balancer) in front of Streamlit.

### nginx Example

```nginx
server {
    listen 443 ssl;
    server_name heartguard.yourdomain.com;

    ssl_certificate /etc/ssl/certs/heartguard.crt;
    ssl_certificate_key /etc/ssl/private/heartguard.key;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Health Checks

| Endpoint | Purpose | Use Case |
|---|---|---|
| `python scripts/health_check.py --full` | Complete health status | Monitoring dashboard |
| `python scripts/health_check.py --liveness` | Process alive check | Docker/Kubernetes liveness |
| `python scripts/health_check.py --readiness` | Dependency check | Docker/Kubernetes readiness |

## Monitoring

### Application Metrics

Track via health check script output:
- Database connectivity (auth, audit, assessments, reviews)
- Model artifact availability and integrity
- Storage writability
- Configuration validity

### Resource Monitoring

Monitor system resources:
- CPU usage (TensorFlow/SHAP inference)
- Memory usage (model loading)
- Disk usage (SQLite databases, logs, reports)

## Security

### Production Checklist

- [ ] SECRET_KEY is a strong random value
- [ ] DEBUG=false
- [ ] HTTPS enabled via reverse proxy
- [ ] Admin accounts created via CLI scripts only
- [ ] Audit logging enabled
- [ ] File upload restrictions in place
- [ ] Rate limiting active
- [ ] No sensitive data in logs
- [ ] No secrets in source code

### Security Headers

Configured in `config/security.py`:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Content-Security-Policy: configured

## Disaster Recovery

See `docs/deployment/disaster_recovery.md` for detailed procedures.

### Quick Recovery

| Failure | Action |
|---|---|
| Application crash | Restart process / Docker container |
| Database corruption | Restore from backup |
| Model corruption | Restore models from backup |
| Storage full | Clear `data/tmp/`, rotate logs |
| External API failure | Alerts disabled gracefully (demo mode) |
