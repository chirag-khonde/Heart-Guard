# HeartGuard — Presentation Outline

**Title:** Early Heart Disease Risk Prediction with Explainable AI  
**Version:** 1.0.0  
**Duration:** 15-20 minutes

---

## Slide-by-Slide Outline

### Slide 1 — Title
- **HeartGuard: Early Heart Disease Risk Prediction with Explainable AI**
- Your name, institution, date
- Course/project identifier

### Slide 2 — Problem Statement
- Heart disease is leading cause of death globally
- Early detection improves outcomes
- Traditional screening relies on expert interpretation
- AI can assist but must be explainable for clinical trust

### Slide 3 — Motivation
- Need for transparent, interpretable AI in healthcare
- Black-box models insufficient for clinical decision support
- Patients and doctors need to understand WHY a prediction was made
- Regulatory and ethical requirements for explainability

### Slide 4 — Objectives
- Build multimodal heart disease risk predictor
- Integrate clinical and lifestyle data
- Provide SHAP-based explanations for every prediction
- Implement role-based access (Patient, Reviewer, Admin)
- Ensure security and privacy

### Slide 5 — Proposed Solution
- HeartGuard: Streamlit-based web application
- Ensemble ML models (Random Forest, XGBoost, Neural Network, Logistic Regression)
- SHAP explainability for transparent predictions
- NLP-based lifestyle risk scoring
- Doctor review portal for clinical oversight

### Slide 6 — System Architecture
```
Frontend (Streamlit) → Backend (Python) → ML Layer → Database (SQLite)
         ↓                    ↓               ↓              ↓
    15 Pages          Authentication      4 Models      6 Databases
    Responsive        Authorization       SHAP          Auth/Audit
    Accessible        Audit Logging       NLP           Assessments
```

### Slide 7 — Technology Stack
- **Frontend:** Streamlit, Altair, Matplotlib, SHAP
- **Backend:** Python 3.10+, SQLite
- **ML:** scikit-learn, XGBoost, TensorFlow/Keras, SHAP
- **NLP:** NLTK, custom lexicon
- **Security:** Bcrypt, RBAC, audit logging
- **Deployment:** Docker, GitHub Actions

### Slide 8 — Dataset
- Cleveland Heart Disease (UCI ML Repository)
- 303 samples, 19 features
- Binary classification: heart disease present/absent
- Features: age, sex, chest pain, blood pressure, cholesterol, ECG, heart rate, ST depression, vessels, thal

### Slide 9 — ML Pipeline
```
Data Loading → Preprocessing → Train/Test Split → Model Training → Evaluation → Deployment
       ↓              ↓              ↓                  ↓              ↓
   303 samples   19 features    80/20 split      4 models      Cross-validation
```

### Slide 10 — Model Evaluation
| Model | Accuracy | F1 | ROC-AUC |
|-------|----------|-----|---------|
| Random Forest | 0.574 | 0.675 | 0.538 |
| XGBoost | 0.590 | 0.638 | 0.608 |
| Neural Network | 0.557 | 0.609 | 0.498 |
| Logistic Regression | 0.410 | 0.471 | 0.436 |

- Note: Modest performance on small dataset
- Research prototype, not clinical-grade

### Slide 11 — Explainable AI (SHAP)
- SHAP (SHapley Additive exPlanations) values
- Shows contribution of each feature to prediction
- Patient-level explanations
- Global feature importance
- Visualization: waterfall plots, bar charts, force plots
- Why this matters: clinical trust, transparency, debugging

### Slide 12 — Application Workflow
1. Patient registers/logs in
2. Enters clinical data + lifestyle text
3. System predicts risk (ensemble)
4. SHAP explains prediction
5. Recommendations generated
6. Alerts sent if high risk
7. Doctor reviews assessment
8. Admin monitors analytics

### Slide 13 — Security & Privacy
- Bcrypt password hashing (12 rounds)
- Role-based access control (Patient, Reviewer, Admin)
- IDOR protection (data isolation)
- Audit logging (tamper-evident)
- Input validation (SQL injection, XSS prevention)
- Privacy filter (no PII in logs)
- Session timeout

### Slide 14 — Analytics & Monitoring
- Risk distribution analytics
- Prediction trend analytics
- Model performance monitoring
- Data drift detection (PSI, KS test, JS divergence)
- Data quality monitoring (missing values, schema)
- System health checks

### Slide 15 — Screenshots/Demo
- Login page
- Patient dashboard
- Risk assessment form
- Prediction results
- SHAP explanation
- Recommendations
- Doctor review portal
- Admin analytics

### Slide 16 — Results
- 562 tests passing
- 4 ML models trained and evaluated
- SHAP explanations for every prediction
- NLP lifestyle scoring operational
- RBAC with 3 roles
- 6 SQLite databases
- 15 application pages
- Comprehensive documentation

### Slide 17 — Limitations
- Small dataset (303 samples)
- Modest model performance
- Cleveland-specific population
- No external clinical validation
- Rule-based NLP (not production NLP)
- SQLite file-based storage
- Not a medical device

### Slide 18 — Future Scope
- Larger, more diverse datasets
- External clinical validation
- Production NLP integration
- Real-time monitoring dashboard
- Multi-language support
- Mobile application
- Integration with EHR systems
- Federated learning for privacy

### Slide 19 — Conclusion
- HeartGuard demonstrates AI-powered heart disease risk prediction
- SHAP provides transparent, explainable predictions
- Role-based access ensures appropriate data access
- Security and privacy enforced throughout
- Academic/research prototype for learning and demonstration

### Slide 20 — Q&A
- Open for questions
- Contact information
- GitHub repository link

---

## Presentation Tips

1. **Start with the problem** — make audience care before showing solution
2. **Live demo** if possible — show actual application
3. **Explain SHAP visually** — show actual waterfall plots
4. **Be honest about limitations** — shows maturity and understanding
5. **Practice timing** — 15-20 minutes + 5-10 min Q&A
6. **Prepare for questions** on model performance, security, clinical validity
