# HeartGuard Testing Documentation

**Document Version:** 1.0.0  
**Phase:** 15 (Security, Privacy, Audit Logging & Compliance)  
**System Status:** Academic & Research Healthcare Demonstration Prototype

---

## 1. Test Strategy

HeartGuard uses **pytest** as its test framework with a comprehensive test suite covering unit tests, integration tests, security tests, and deployment smoke tests.

### Test Framework
- **Framework:** pytest
- **Configuration:** `pytest.ini`
- **Test Discovery:** `tests/test_*.py`
- **Fixtures:** Temporary SQLite databases for isolation
- **Warnings:** DeprecationWarning, FutureWarning, UserWarning suppressed

---

## 2. Test Types

### Unit Tests
- Individual function testing
- Isolated database operations
- Input validation logic
- Password hashing/verification
- Rate limiter behavior

### Integration Tests
- Multi-component workflows
- Database interactions across services
- Authentication flows end-to-end
- Assessment creation and retrieval

### Security Tests
- Authentication and authorization
- IDOR prevention
- Input validation and sanitization
- Audit logging
- Rate limiting
- Session management

### Deployment Tests
- Configuration validation
- Health checks
- Model loading
- Graceful failure handling
- Session isolation

---

## 3. Test Commands

### Run All Tests
```bash
pytest -q
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Specific Test File
```bash
pytest tests/test_security.py -v
```

### Run Specific Test Function
```bash
pytest tests/test_auth.py::test_hash_password_returns_string -v
```

### Run Tests by Keyword
```bash
pytest -k "password" -v
```

### Run Tests by Marker
```bash
pytest -m "not slow" -v
```

### Generate Coverage Report
```bash
pytest --cov=src --cov-report=html
```

---

## 4. Test Coverage Summary

### Total Tests: 562

### Test Files and Coverage

| Test File | Description | Approx. Tests |
|-----------|-------------|---------------|
| `test_security.py` | Input sanitization, validation, SQL injection, password security, audit logging, rate limiting | ~40 |
| `test_auth.py` | Registration, password hashing, login, logout, account state | ~25 |
| `test_authorization.py` | RBAC enforcement, role checks, IDOR prevention | ~20 |
| `test_security_phase15.py` | Phase 15 security controls | ~30 |
| `test_deployment.py` | Configuration, health checks, model loading, graceful failures | ~45 |
| `test_alerts.py` | Alert dispatch, idempotency, threshold enforcement | ~20 |
| `test_alert_security.py` | Alert security controls | ~15 |
| `test_alert_analytics.py` | Alert analytics and reporting | ~15 |
| `test_assessment_history.py` | Assessment persistence, retrieval, trends | ~25 |
| `test_analytics_authorization.py` | Analytics access control | ~15 |
| `test_dashboard_analytics.py` | Dashboard analytics functionality | ~20 |
| `test_dashboard_security.py` | Dashboard security controls | ~15 |
| `test_data_quality_monitoring.py` | Data quality checks | ~15 |
| `test_drift_detection.py` | Model drift detection | ~15 |
| `test_explainability_analytics.py` | Explainability features | ~15 |
| `test_insights.py` | AI insights functionality | ~20 |
| `test_lifestyle_analyzer.py` | Lifestyle NLP analysis | ~20 |
| `test_lifestyle.py` | Lifestyle data processing | ~15 |
| `test_model_monitoring.py` | Model monitoring | ~15 |
| `test_models.py` | Data models | ~15 |
| `test_monitoring_events.py` | Monitoring event tracking | ~15 |
| `test_multimodal_risk.py` | Multimodal risk engine | ~25 |
| `test_performance_metrics.py` | Performance measurement | ~15 |
| `test_pipeline.py` | Data pipeline | ~15 |
| `test_prediction_analytics.py` | Prediction analytics | ~15 |
| `test_prediction.py` | Prediction functionality | ~20 |
| `test_preprocessing.py` | Data preprocessing | ~15 |
| `test_recommendation_engine.py` | Recommendation generation | ~20 |
| `test_recommendation_rules.py` | Recommendation rules | ~15 |
| `test_recommendation_security.py` | Recommendation security | ~15 |
| `test_recommendation_validation.py` | Recommendation validation | ~15 |
| `test_report_generator.py` | Report generation | ~15 |
| `test_review_authorization.py` | Review access control | ~15 |
| `test_review_service.py` | Review service | ~15 |
| `test_risk_distribution.py` | Risk distribution | ~15 |
| `test_security_analytics.py` | Security analytics | ~15 |
| `test_shap.py` | SHAP explainability | ~15 |
| `test_ui_components.py` | UI component testing | ~15 |

---

## 5. Test Categories

### Authentication Tests (`test_auth.py`, `test_security.py`)
- Password hashing returns string, not plaintext
- Correct password verification
- Incorrect password rejection
- Empty password handling
- User registration flow
- Duplicate email rejection
- Admin user creation
- Authentication with non-existent email
- Authentication with wrong password

### Authorization Tests (`test_authorization.py`, `test_review_authorization.py`, `test_analytics_authorization.py`)
- Patient access to own data
- Patient denial of other patient's data
- Reviewer access to all assessments
- Admin access to all resources
- Role hierarchy enforcement

### IDOR Prevention Tests
- Assessment access verification
- Report access verification
- IDOR attempt logging

### Input Validation Tests (`test_security.py`)
- Email format validation
- Name validation
- Password strength validation
- Lifestyle text length validation
- XSS prevention (script tag removal)
- SMS content sanitization
- Path traversal prevention
- File upload validation

### Session Security Tests
- Session creation
- Session timeout
- Session clearing on logout
- Session fixation prevention

### Rate Limiting Tests (`test_security.py`)
- Login rate limiting
- Failed attempt tracking
- Cooldown lockout
- Attempt counter reset

### Audit Logging Tests (`test_security.py`)
- Event logging
- Event retrieval
- Detail sanitization
- IP address hashing

### File Security Tests
- Path traversal detection
- Safe path resolution
- File upload validation
- Report access control

### Deployment Tests (`test_deployment.py`)
- Environment variable loading
- Secret key configuration
- Debug mode default
- Database path validation
- Directory creation
- Model loading
- Graceful failure handling
- Session isolation

---

## 6. How to Run Specific Test Suites

### Security Tests Only
```bash
pytest tests/test_security.py tests/test_security_phase15.py tests/test_security_analytics.py tests/test_dashboard_security.py tests/test_alert_security.py -v
```

### Authentication & Authorization Tests
```bash
pytest tests/test_auth.py tests/test_authorization.py tests/test_review_authorization.py tests/test_analytics_authorization.py -v
```

### Analytics & Dashboard Tests
```bash
pytest tests/test_dashboard_analytics.py tests/test_analytics_authorization.py tests/test_prediction_analytics.py tests/test_explainability_analytics.py tests/test_alert_analytics.py tests/test_security_analytics.py -v
```

### Recommendation Tests
```bash
pytest tests/test_recommendation_engine.py tests/test_recommendation_rules.py tests/test_recommendation_security.py tests/test_recommendation_validation.py -v
```

### Deployment & Monitoring Tests
```bash
pytest tests/test_deployment.py tests/test_model_monitoring.py tests/test_monitoring_events.py tests/test_data_quality_monitoring.py tests/test_drift_detection.py -v
```

---

## 7. Known Test Limitations

### Database Isolation
- Tests use temporary SQLite databases (`tmp_path` fixture)
- No shared state between tests
- Database cleanup automatic via pytest fixtures

### Mocking Requirements
- Streamlit session state requires mocking
- External API calls (Twilio, LLM) mocked in tests
- Model loading may require test fixtures

### Performance Considerations
- SHAP explanations are CPU-intensive
- Some tests may be slow due to bcrypt hashing (12 rounds)
- Model loading tests require pre-trained models

### Coverage Gaps
- UI interaction testing limited (Streamlit rerun model)
- End-to-end browser testing not implemented
- Load/stress testing not included

---

## 8. CI/CD Integration

### Test Execution in CI
```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    pip install -r requirements.txt
    pytest -q --tb=short
```

### Pre-commit Hooks
```bash
# Run tests before commit
pytest -q --tb=short
```

### Coverage Reporting
```bash
# Generate coverage report
pytest --cov=src --cov-report=xml --cov-report=html
```

### Test Data Management
- All tests use isolated temporary databases
- No production data used in tests
- Test fixtures provide clean database state

---

## 9. Test Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
filterwarnings =
    ignore::DeprecationWarning
    ignore::FutureWarning
    ignore::UserWarning
```

### conftest.py
- Adds project root to Python path
- Provides shared fixtures for database isolation

---

## 10. Writing New Tests

### Test Naming Convention
- Test files: `test_<module>.py`
- Test functions: `test_<description>`
- Test classes: `Test<Description>`

### Fixture Usage
```python
@pytest.fixture()
def tmp_auth_db(tmp_path: Path) -> Path:
    """Provide a clean temporary auth SQLite database."""
    db_file = tmp_path / "test_auth.db"
    init_auth_db(db_file)
    return db_file
```

### Test Structure
```python
def test_password_hashing():
    """Test that password hashing works correctly."""
    hashed = hash_password("SecurePass1")
    assert isinstance(hashed, str)
    assert len(hashed) > 0
```
