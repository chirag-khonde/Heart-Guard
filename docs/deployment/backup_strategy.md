# HeartGuard Backup Strategy

## Overview

HeartGuard uses SQLite databases and file-based storage. This document defines the backup strategy for production deployments.

## Backup Components

### 1. SQLite Databases

| Database | Path | Criticality |
|---|---|---|
| Auth DB | `data/auth/heartguard_auth.db` | High (user accounts) |
| Audit DB | `data/security/audit.db` | Medium (audit trail) |
| Assessments DB | `data/assessments/assessments.db` | High (patient data) |
| Reviews DB | `data/assessments/reviews.db` | Medium (doctor reviews) |
| Recommendations DB | `data/assessments/recommendations.db` | Medium |
| Alerts DB | `data/alerts/alerts.db` | Low (alert history) |

### 2. Model Artifacts

| Artifact | Path | Criticality |
|---|---|---|
| All `.pkl` files | `models/` | High |
| Feature names | `models/feature_names.json` | High |
| Manifest | `models/model_manifest.json` | Medium |
| Metadata | `models/model_metadata.json` | Medium |

### 3. Configuration

| Component | Path | Criticality |
|---|---|---|
| Environment file | `.env` | Critical |
| Application code | Git repository | High |

### 4. Generated Reports

| Component | Path | Criticality |
|---|---|---|
| PDF reports | `reports/generated/` | Medium |

## Backup Frequency

| Component | Frequency | Retention | Method |
|---|---|---|---|
| SQLite databases | Daily | 30 days | File copy |
| Model artifacts | On version change | Keep v1 and v2 | File copy |
| `.env` file | On change | Version controlled | Secure storage |
| Generated reports | Per retention policy | 30 days | Automatic cleanup |

## Backup Commands

### Database Backup

```bash
#!/bin/bash
# backup_databases.sh
BACKUP_DIR="backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

cp data/auth/heartguard_auth.db "$BACKUP_DIR/auth.db"
cp data/security/audit.db "$BACKUP_DIR/audit.db"
cp data/assessments/assessments.db "$BACKUP_DIR/assessments.db"
cp data/assessments/reviews.db "$BACKUP_DIR/reviews.db"
cp data/assessments/recommendations.db "$BACKUP_DIR/recommendations.db"
cp data/alerts/alerts.db "$BACKUP_DIR/alerts.db"

echo "Backup completed: $BACKUP_DIR"
```

### Model Backup

```bash
#!/bin/bash
# backup_models.sh
BACKUP_DIR="backups/models_$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

cp models/*.pkl "$BACKUP_DIR/"
cp models/*.json "$BACKUP_DIR/"

echo "Model backup completed: $BACKUP_DIR"
```

## Restore Procedure

### Database Restore

```bash
# Stop application first
# cp backups/YYYYMMDD/auth.db data/auth/heartguard_auth.db
# cp backups/YYYYMMDD/assessments.db data/assessments/assessments.db
# ... (repeat for each database)
# Restart application
```

### Model Restore

```bash
# cp backups/models_YYYYMMDD/*.pkl models/
# cp backups/models_YYYYMMDD/*.json models/
# Verify integrity
# python scripts/health_check.py --full
```

## Automated Backup (Cron Example)

```cron
# Daily database backup at 2 AM
0 2 * * * /path/to/backup_databases.sh

# Weekly model backup on Sunday at 3 AM
0 3 * * 0 /path/to/backup_models.sh
```

## Backup Verification

After each backup:
1. Verify file sizes are non-zero
2. Verify SQLite databases are readable: `sqlite3 backup.db "SELECT 1"`
3. Verify model files have valid checksums

## Restore Testing

Quarterly restore test procedure:
1. Provision test environment
2. Restore backups to test environment
3. Run `python scripts/health_check.py --full`
4. Verify application starts and functions correctly
5. Document test results

## Notes

- **Automated production backups require deployment-specific configuration.** The commands above are templates that should be adapted to your deployment environment.
- For cloud deployments, consider using platform-native backup services (AWS RDS snapshots, Azure Backup, etc.).
- For containerized deployments, use Docker volumes or persistent storage mounts.
