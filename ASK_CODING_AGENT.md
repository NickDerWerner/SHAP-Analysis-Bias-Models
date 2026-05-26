# What to ask the coding agent for

Three small things from your BABE SHAP analysis output:

## 1. For the bias-detector FP paragraph

- Top 5–8 words by mean |SHAP| across the 37 FP instances
- Each word's mean |SHAP| value (positive or negative direction)
- Mean confidence on FP predictions
- The "illegal" comparison: mean |SHAP| in TPs vs FPs (you already have 0.349 and 0.140 from the current text, but verify they still match)

## 2. For the DA-RoBERTa-BABE-FT FP paragraph

- Top 5–8 words by mean |SHAP| across the 12 FP instances
- Each word's mean |SHAP|
- Mean confidence on FP predictions
- The "claims" comparison: appears in both TPs (as claimed/claiming/claim) and FPs — verify this still holds

## 3. Optional but useful — quick consistency check

- Confirm the mean |SHAP| per instance on FPs is still around 0.0354 (bd) and 0.0215 (dr) — these are the headline FP magnitude numbers
- These should match what's reported in §4.2 / Table 2
