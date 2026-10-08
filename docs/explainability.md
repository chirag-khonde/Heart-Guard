# HeartGuard Explainability Module

## What is SHAP?

SHAP (SHapley Additive exPlanations) is a game-theoretic approach to explaining the output of machine learning models. It assigns each feature an importance value for a particular prediction, based on the concept of Shapley values from cooperative game theory.

## Why HeartGuard Uses SHAP

HeartGuard uses SHAP to provide transparent, interpretable explanations for its heart disease risk predictions. Rather than treating the ML model as a black box, SHAP reveals which clinical features contributed most to each prediction, enabling:

- **Transparency**: Users can see exactly why the model made a particular prediction
- **Trust**: Explanations are grounded in a mathematically rigorous framework
- **Debugging**: Researchers can verify that the model is using clinically meaningful features
- **Accountability**: Predictions are accompanied by evidence of feature contributions

## TreeExplainer

For tree-based models (XGBoost, Random Forest), HeartGuard uses SHAP's `TreeExplainer`. This is the most efficient and accurate SHAP explainer for tree models:

- Computes exact SHAP values (not approximations)
- Fast execution even on large datasets
- Handles feature interactions naturally
- Provides consistent, reliable explanations

When the best model is a tree-based model, TreeExplainer is used automatically. For non-tree models (e.g., Logistic Regression), the appropriate alternative explainer is used instead (e.g., LinearExplainer).

## Global Explanations

Global explanations answer: **"Which features are most influential to this model overall?"**

HeartGuard computes global feature importance by calculating the mean absolute SHAP value for each feature across the training dataset. Features are then ranked by this metric.

**Key metrics:**
- **Mean |SHAP Value|**: Average magnitude of a feature's contribution across all predictions
- **Rank**: Ordered importance from most to least influential

**Output files:**
- `reports/explainability/shap_global_importance.csv` — ranked feature importance
- `reports/figures/shap_global_importance.png` — bar chart visualization
- `reports/figures/shap_summary.png` — beeswarm plot showing value distributions

## Local Explanations

Local explanations answer: **"Which features most influenced this patient's model prediction?"**

For each patient, SHAP computes:
- **Base value**: The expected model output before considering individual features
- **SHAP values**: Per-feature contributions to the prediction
- **Model output**: The final prediction (probability or class)

**For each feature, the explanation shows:**
- Feature name and clinical label
- Patient's actual value
- SHAP contribution value
- Direction (increases/decreases risk)
- Absolute importance

## SHAP Values

A SHAP value represents the contribution of a feature to the prediction, measured in the model's output space:

- **Positive SHAP value**: The feature pushes the prediction toward higher risk (class 1)
- **Negative SHAP value**: The feature pushes the prediction toward lower risk (class 0)
- **Near-zero SHAP value**: The feature has minimal impact on this prediction

**Important**: SHAP values are NOT percentages. They represent contributions in the model's output space (log-odds for logistic regression, probability for calibrated models). A SHAP value of +0.3 does not mean "34% more disease risk."

## Base Value

The base value (also called the expected value) represents the model's average output across the training dataset. It is the starting point before any patient-specific features are considered:

- **Final prediction = Base value + Sum of all SHAP values**
- For logistic regression, the base value is the log-odds of the average prediction
- For tree models, it is the average prediction over the training data

## Waterfall Plot

The waterfall plot visualizes how each feature contributes to a single prediction:

```
Base value          0.30
├── Age             +0.15
├── Cholesterol     +0.22
├── Max Heart Rate  -0.12
├── ST Depression   +0.35
├── ...
└── Final output    0.75
```

The plot shows:
1. The base value at the top
2. Each feature's contribution as a red (positive) or blue (negative) bar
3. The cumulative result as the final model output

## Feature Importance

HeartGuard provides three levels of feature importance:

1. **Global importance**: Mean |SHAP| across all training samples — overall model behavior
2. **Local importance**: Individual SHAP values for a specific patient — prediction-specific
3. **Top risk factors**: Top 3 features contributing toward higher predicted risk

## Limitations

1. **Model behavior, not causation**: SHAP explains what the model learned, not what causes heart disease. A feature with high SHAP importance does not necessarily cause the condition.

2. **Approximation for complex models**: For neural networks and kernel-based explainers, SHAP values are approximations, not exact computations.

3. **Feature correlations**: When features are correlated, SHAP may distribute importance across correlated features in ways that are difficult to interpret.

4. **Training data dependence**: Explanations reflect the patterns in the training data. If the training data is biased or unrepresentative, the explanations will reflect those limitations.

5. **Individual predictions**: Local explanations apply to a single prediction. They should not be generalized to all patients with similar characteristics.
