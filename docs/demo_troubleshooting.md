# HeartGuard — Demo Troubleshooting Guide

**Version:** 1.0.0  
**Date:** September 2026

---

## Common Issues & Solutions

### 1. Application Won't Start

**Symptom:** `streamlit run app.py` fails or hangs

**Solutions:**
```bash
# Check Python version
python --version  # Should be 3.10+

# Reinstall dependencies
pip install -r requirements.txt

# Check for port conflict
streamlit run app.py --server.port 8502

# Clear Streamlit cache
streamlit cache clear
```

### 2. Database Errors

**Symptom:** `sqlite3.OperationalError` or missing database files

**Solutions:**
```bash
# Ensure data directories exist
mkdir -p data/auth data/security data/assessments data/alerts data/tmp

# Delete corrupted databases (will recreate)
del data\auth\heartguard_auth.db
del data\security\audit.db
# etc.

# Re-run application to recreate databases
streamlit run app.py
```

### 3. Model Loading Fails

**Symptom:** `FileNotFoundError` or `pickle` errors when loading models

**Solutions:**
```bash
# Verify model artifacts exist
dir models\*.pkl

# Retrain models if corrupted
python scripts/train_models.py

# Check model manifest
type models\model_manifest.json
```

### 4. NLTK Data Missing

**Symptom:** `LookupError: Resource punkt not found`

**Solutions:**
```bash
# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

### 5. Streamlit Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'streamlit'`

**Solutions:**
```bash
# Activate virtual environment
.venv\Scripts\activate

# Reinstall Streamlit
pip install streamlit
```

### 6. PermissionError on Windows

**Symptom:** `PermissionError: [WinError 32]` when deleting temp files

**Solutions:**
- Close any running Streamlit instances
- Close any file explorers open in the project directory
- Restart terminal
- This is a Windows-specific issue and doesn't affect functionality

### 7. Port Already in Use

**Symptom:** `OSError: [WinError 10048]` or port 8501 already in use

**Solutions:**
```bash
# Use different port
streamlit run app.py --server.port 8502

# Or kill existing process
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

### 8. Login Fails

**Symptom:** Cannot log in with created admin credentials

**Solutions:**
```bash
# Recreate admin user
python scripts/create_admin.py

# Check auth database
python -c "import sqlite3; conn = sqlite3.connect('data/auth/heartguard_auth.db'); print(conn.execute('SELECT email, role FROM users').fetchall())"
```

### 9. Tests Fail

**Symptom:** `pytest` shows failures

**Solutions:**
```bash
# Run tests with verbose output
pytest -v

# Run specific failing test
pytest tests/test_failing.py -v

# Check for Windows PermissionError (common)
# Tests use shutil.rmtree(ignore_errors=True) to handle this
```

### 10. Report Generation Fails

**Symptom:** PDF report not generated or errors during generation

**Solutions:**
```bash
# Ensure reports directory exists
mkdir -p reports\generated

# Check report directory permissions
# Ensure matplotlib is installed
pip install matplotlib
```

---

## Pre-Demo Checklist

### 5 Minutes Before
- [ ] Close all unnecessary applications
- [ ] Open terminal in project directory
- [ ] Activate virtual environment
- [ ] Start application: `streamlit run app.py`
- [ ] Verify it loads in browser

### 1 Minute Before
- [ ] Clear browser cache (Ctrl+Shift+Delete)
- [ ] Open browser to http://localhost:8501
- [ ] Verify login page appears
- [ ] Have admin credentials ready

### During Demo
- [ ] Keep terminal visible (for error messages)
- [ ] Have backup plan if something fails
- [ ] Explain what's happening if there's a delay

---

## Emergency Recovery

### If Application Crashes
1. Close browser tab
2. Press Ctrl+C in terminal to stop Streamlit
3. Restart: `streamlit run app.py`
4. Reopen browser

### If Database Corrupted
1. Stop application
2. Delete corrupted `.db` file
3. Restart application (will recreate)
4. Re-create admin user if auth DB was deleted

### If Model Corrupted
1. Stop application
2. Retrain: `python scripts/train_models.py`
3. Restart application

### If All Else Fails
1. Close everything
2. Delete all `.db` files in `data/`
3. Delete `models/*.pkl` files
4. Retrain models: `python scripts/train_models.py`
5. Restart application
6. Re-create admin: `python scripts/create_admin.py`

---

## Demo Data Safety

- **Only use synthetic/demo data** during demonstrations
- **Never enter real patient information**
- **Default credentials are safe for demo:**
  - Admin: created via `scripts/create_admin.py`
  - Demo mode disables SMS alerts

---

## Browser Compatibility

### Recommended
- Google Chrome (latest)
- Mozilla Firefox (latest)
- Microsoft Edge (latest)

### Avoid
- Internet Explorer (not supported)
- Very old browser versions

### If Page Doesn't Load
1. Hard refresh: Ctrl+Shift+R
2. Clear cache: Ctrl+Shift+Delete
3. Try different browser
4. Check localhost:8501 is accessible
