# Vocab-size confound check — outcome

**Outcome: C**

- K sensitivity: DA-RoBERTa FP F/T ranges [4.0, 15.0]% across K∈[25, 50, 100, 200, 500]; K=100 (13.0%) is mid-range, not inflated by vocab exhaustion (K=200 → 15.0%).
- Threshold-based control (n_selected=39 for DA-RoBERTa FP): DA-RoBERTa FP F/T = 5.1% vs bias-detector FP F/T = 6.9% → gap inverts.
- Proportional-K: top 5% → DA=0.0% / BD=3.0%; top 10% → DA=4.0% / BD=4.5%; top 20% → DA=8.0% / BD=4.5%; top 30% → DA=10.7% / BD=6.6%
- Bootstrap at K=100: DA-RoBERTa FP F/T 95% CI [11.0, 24.0] vs bias-detector FP F/T point estimate 4.0% — excludes.
- DA-RoBERTa within-model: TP F/T at K=100 = 0.0% vs FP F/T at K=100 = 13.0% (gap = +13.0 pt).
- **Decisive**: under the threshold-based (attribution-strength) control, the F/T gap collapses or inverts. The original 13% number is what you get when you fix K and let the comparison pool size differ — but when you fix the per-feature attribution bar, DA-RoBERTa does NOT attribute more to function words than bias-detector does.

## BASIL Figure 6 recommendation

Restructure Figure 6 on BASIL as 'feature-pool composition' with explicit vocab-size matching (proportional-K). Alternatively, drop the F/T claim entirely and reframe panel (d) as 'DA-RoBERTa FP attributions do not concentrate on framing vocab' rather than 'they shift to function words'.

## Verification

### K=100 reproduction vs published numbers

| model | pred_class | category | got (%) | target (%) | Δ |
|---|---|---|---:|---:|---:|
| biasdetector | TP | Emotional/Evaluative | 94.0 | 93 | +1.0 |
| biasdetector | FP | Emotional/Evaluative | 92.0 | 91 | +1.0 |
| biasdetector | FP | Framing/Reporting Verbs | 3.0 | 4 | -1.0 |
| biasdetector | FP | Function/Temporal Words | 4.0 | 4 | +0.0 |
| daroberta | TP | Emotional/Evaluative | 93.0 | 93 | +0.0 |
| daroberta | TP | Framing/Reporting Verbs | 5.0 | 5 | +0.0 |
| daroberta | FP | Emotional/Evaluative | 82.0 | 82 | +0.0 |
| daroberta | FP | Framing/Reporting Verbs | 5.0 | 5 | +0.0 |
| daroberta | FP | Function/Temporal Words | 13.0 | 13 | +0.0 |

### Vocab stats (premise check)

- bias-detector FP unique types: **660** (n=37 samples)
- DA-RoBERTa FP unique types: **249** (n=12 samples)
- ratio (DA-RoBERTa / bias-detector): **0.38**
  - Ratio in [0.2, 0.5] — Ax3B's premise (≈1/3) is supported.

### Bootstrap CI widths (sanity)

- bias-detector FP F/T CI width: **7.00** pts
- DA-RoBERTa FP F/T CI width: **13.00** pts
  - DA-RoBERTa CI wider as expected.

## Decision table — DA-RoBERTa FP Function/Temporal proportion under every control

| Condition | DA-RoBERTa FP F/T (%) | n_selected / K |
|---|---:|---:|
| K=25 | 4.0 | effective_K=25 |
| K=50 | 8.0 | effective_K=50 |
| K=100 *(uncorrected)* | 13.0 | effective_K=100 |
| K=200 | 15.0 | effective_K=200 |
| K=500 | 13.7 | effective_K=249 |
| Proportional-K at top 5% of vocab | 0.0 | n_selected=12 |
| Proportional-K at top 10% of vocab | 4.0 | n_selected=25 |
| Proportional-K at top 20% of vocab | 8.0 | n_selected=50 |
| Proportional-K at top 30% of vocab | 10.7 | n_selected=75 |
| Threshold ≥ 0.0406 (p75 of pooled mean_abs_shap) | 5.1 | n_selected=39 |
| **Bootstrap mean** (K=100, B=1000) | 17.5 | 95% CI [11.0, 24.0] |

**Comparison baselines (K=100):**
- DA-RoBERTa TP F/T: **0.0%** (within-model baseline)
- bias-detector FP F/T: **4.0%** (cross-model baseline)
