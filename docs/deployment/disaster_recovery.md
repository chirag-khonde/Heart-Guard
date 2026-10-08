# HeartGuard Disaster Recovery Guide

## Failure Scenarios and Recovery

### 1. Application Crash / Process Failure

**Detection:** Health check returns non-zero exit code

**Recovery:**
```bash
# If using systemd
sudo systemctl restart heartguard

# If using Docker
docker restart heartguard

# If manual
streamlit run app.py &
```

**RTO:** < 1 minute
**RPO:** 0 (no data loss)

### 2. Database Corruption

**Detection:** Health check reports database errors

**Recovery:**
```bash
# Stop application
# Restore database from backup
cp backups/auth_YYYYMMDD.db data/auth/heartguard_auth.db
cp backups/audit_YYYYMMDD.db data/security/audit.db
cp backups/assessments_YYYYMMDD.db data/assessments/assessments.db
# Restart application
```

**RTO:** < 5 minutes
**RPO:** Up to 1 day (based on backup frequency)

### 3. Model Artifact Failure

**Detection:** Health check reports missing or corrupted model files

**Recovery:**
```bash
# Identify failed model from health check output
# Restore from backup
cp /backup/models/random_forest.pkl models/random_forest.pkl
# Verify integrity
python scripts/health_check.py --full
# Restart if needed
```

**RTO:** < 2 minutes
**RPO:** 0 (model files are static)

### 4. Storage Full

**Detection:** Application errors on file operations, health check reports storage issues

**Recovery:**
```bash
# Clear temporary files
find data/tmp -type f -mtime +1 -delete

# Clear old logs (keep last 5)
cd logs && ls -t heartguard.log.* | tail -n +6 | xargs rm

# Check disk usage
df -h
```

**RTO:** < 1 minute
**RPO:** 0

### 5. External API (Twilio) Failure

**Detection:** Alert delivery failures in logs

**Recovery:**
- Application continues in demo mode
- Alerts are automatically disabled when Twilio is unavailable
- No action required; monitor for Twilio service restoration

**RTO:** N/A (graceful degradation)
**RPO:** N/A

### 6. Complete Server Failure

**Detection:** All health checks fail

**Recovery:**
1. Provision new server with Python 3.12
2. Clone repository
3. Restore backups:
   - Databases from `backups/` directory
   - Model artifacts from backup storage
   - `.env` file from secure storage
4. Install dependencies: `pip install -r requirements.txt`
5. Create admin account
6. Verify health: `python scripts/health_check.py --full`
7. Start application

**RTO:** < 30 minutes
**RPO:** Up to 1 day

## Backup Locations

| Component | Backup Location | Frequency |
|---|---|---|
| Databases | `backups/` directory | Daily |
| Model artifacts | Deployment-specific storage | On change |
| Configuration (`.env`) | Secure secret storage | On change |
| Source code | Git repository | On commit |

## Testing Recovery

### Database Restore Test

```bash
# 1. Create test backup
cp data/auth/heartguard_auth.db /tmp/test_backup.db

# 2. Simulate corruption
echo "corrupt" >> data/auth/heartguard_auth.db

# 3. Verify health check detects it
python scripts/health_check.py --full

# 4. Restore
cp /tmp/test_backup.db data/auth/heartguard_auth.db

# 5. Verify recovery
python scripts/health_check.py --full
```

### Model Restore Test

```bash
# 1. Backup
cp models/random_forest.pkl /tmp/rf_backup.pkl

# 2. Simulate missing
rm models/random_forest.pkl

# 3. Verify detection
python scripts/health_check.py --readiness

# 4. Restore
cp /tmp/rf_backup.pkl models/random_forest.pkl

# 5. Verify recovery
python scripts/health_check.py --full
```

## Contact

For production incidents, follow the organization's incident response procedure documented in `docs/security/incident_response.md`.
