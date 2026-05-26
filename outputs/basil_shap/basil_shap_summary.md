# BASIL SHAP analysis — outcome summary

## 1. Sample sizes (unique sentences per (model, stratum))

| model | stratum | n_sentences |
|---|---|---|
| biasdetector | bias_type_both | 23 |
| biasdetector | bias_type_inf | 100 |
| biasdetector | bias_type_lex | 100 |
| biasdetector | fn_shared_lex | 100 |
| biasdetector | fp_bd_only | 100 |
| biasdetector | fp_shared | 100 |
| biasdetector | magnitude_FN | 100 |
| biasdetector | magnitude_FP | 100 |
| biasdetector | magnitude_TN | 100 |
| biasdetector | magnitude_TP | 100 |
| daroberta | bias_type_both | 25 |
| daroberta | bias_type_inf | 100 |
| daroberta | bias_type_lex | 100 |
| daroberta | fn_shared_lex | 100 |
| daroberta | fp_dr_only | 100 |
| daroberta | fp_shared | 100 |
| daroberta | magnitude_FN | 100 |
| daroberta | magnitude_FP | 100 |
| daroberta | magnitude_TN | 100 |
| daroberta | magnitude_TP | 100 |

## 2. SHAP magnitude by prediction type (BASIL Fig 3 counterpart)

Per-instance mean |SHAP| from `magnitude_TP/FP/TN` strata. These are the numbers underlying `basil_fig3_counterpart.png`. Clipped-outlier counts refer to the figure's y-axis cap (y=0.15, matched to the original BABE Fig 3).

| model | category | n | median | mean | clipped (>0.15) |
|---|---|---|---|---|---|
| bias-detector | TP | 100 | 0.0407 | 0.0484 | 2 |
| bias-detector | FP | 100 | 0.0553 | 0.0586 | 3 |
| bias-detector | TN | 100 | 0.0313 | 0.0359 | 0 |
| bias-detector | FN | 100 | 0.0315 | 0.0399 | 0 |
| DA-RoBERTa | TP | 100 | 0.0343 | 0.0417 | 1 |
| DA-RoBERTa | FP | 100 | 0.0432 | 0.0550 | 2 |
| DA-RoBERTa | TN | 100 | 0.0161 | 0.0216 | 0 |
| DA-RoBERTa | FN | 100 | 0.0213 | 0.0299 | 0 |

## 2b. Max |SHAP| by prediction type (BASIL Fig 3 max counterpart)

Per-instance max |SHAP| from `magnitude_TP/FP/TN/FN` strata. These are the numbers underlying `basil_fig3_max_counterpart.png`. Clipped-outlier counts refer to the figure's y-axis cap (y=0.6).

| model | category | n | median | mean | clipped (>0.6) |
|---|---|---|---|---|---|
| bias-detector | TP | 100 | 0.2203 | 0.2350 | 1 |
| bias-detector | FP | 100 | 0.2418 | 0.2578 | 2 |
| bias-detector | TN | 100 | 0.1060 | 0.1255 | 0 |
| bias-detector | FN | 100 | 0.1345 | 0.1459 | 0 |
| DA-RoBERTa | TP | 100 | 0.1938 | 0.2197 | 1 |
| DA-RoBERTa | FP | 100 | 0.2306 | 0.2401 | 0 |
| DA-RoBERTa | TN | 100 | 0.0576 | 0.0791 | 0 |
| DA-RoBERTa | FN | 100 | 0.0937 | 0.1106 | 0 |

## 3. Hypothesis A — bias-type independence at SHAP level

**biasdetector**
- lex_only: n=100, median mean_abs_shap = 0.0411
- inf_only: n=100, median mean_abs_shap = 0.0413
- both: n=23, median mean_abs_shap = 0.0251
- top-20 vocabulary Jaccard(lex_only, inf_only) = 0.138  (|lex|=1050, |inf|=1018)

**daroberta**
- lex_only: n=100, median mean_abs_shap = 0.0337
- inf_only: n=100, median mean_abs_shap = 0.0374
- both: n=25, median mean_abs_shap = 0.0243
- top-20 vocabulary Jaccard(lex_only, inf_only) = 0.139  (|lex|=987, |inf|=993)

## 4. Hypothesis B — same mechanism, different calibration (FP partition)

Threshold (p75 of pooled mean_abs_shap across all FP partitions × models): **0.0614**

**Category proportions among threshold-selected words:**

| partition | model | Emotional/Evaluative | Explicit Bias Terms | Framing/Reporting Verbs | Function/Temporal Words |
|---|---|---|---|---|---|
| bd_only | biasdetector | 0.944 | 0.000 | 0.019 | 0.037 |
| dr_only | daroberta | 0.913 | 0.004 | 0.026 | 0.057 |
| shared | biasdetector | 0.944 | 0.003 | 0.025 | 0.028 |
| shared | daroberta | 0.962 | 0.004 | 0.017 | 0.017 |

**Selected-word counts per (partition, model):**

| partition | model | n_selected_words |
|---|---|---|
| bd_only | biasdetector | 323 |
| dr_only | daroberta | 229 |
| shared | biasdetector | 323 |
| shared | daroberta | 236 |

## 5. FP paired mechanism check (shared FPs, both models)

- Median per-sentence Jaccard of top-20 tokens (BD ∩ DR / BD ∪ DR): **0.809** (n=100 sentences)
- Median per-sentence mean_abs_shap — BD: 0.0502, DR: 0.0378

## 6. FN paired calibration check (shared lex-only FNs, both models)

- Median per-sentence Jaccard of top-20 tokens (BD ∩ DR / BD ∪ DR): **0.721** (n=100 sentences)
- Median per-sentence mean_abs_shap — BD: 0.0340, DR: 0.0170

## 7. Sanity checks

- **Magnitude scale**: overall mean mean_abs_shap = 0.0414. In BABE range [0.02, 0.08]? **YES**
- **Cache integrity**: 0 manifest entries missing from JSONL caches

### Known-bias attribution spot check (3 random lex-only TPs per model)

**biasdetector**:
- 8dc7ccfe.../13: top3 = pounced|0.4926 | Following|-0.1507 | Romney|0.1186
- 9879bbc0.../1: top3 = heated|0.1205 | challenging|-0.1130 | Republicans|-0.1102
- 59f2f47c.../9: top3 = Cruz.””|-0.1449 | problem|0.1329 | 's|0.0399

**daroberta**:
- be026bd1.../0: top3 = bombshell|0.4761 | Donald’’|0.0749 | response|-0.0673
- a4f1d515.../0: top3 = forcefully|0.1722 | saying|0.0610 | revelations|0.0587
- 2153fb3e.../20: top3 = facetiously|0.2085 | Boehner|0.1173 | help:““’’|0.0533

## 8. Key numbers worth citing

(Pull from the tables and plots above once reviewed.)

## 9. Unexpected findings

(Note anything off-pattern after inspecting diagnostics/*.png.)
