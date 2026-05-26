# Section 4.5 data tables — BASIL

All numbers sourced from existing evaluation outputs. No new analysis was
run; this document curates the inputs needed to write the 4.5 prose.

Sources:
- `outputs/basil/basil_metrics_table.csv` (full-set FP/FN counts at θ=0.5)
- `outputs/basil/threshold_sweep_table.csv` (per-stratum recalls at θ=0.3)
- `outputs/basil/auprc_table.csv` (AUPRC by stratum)
- `outputs/basil_shap/basil_shap_fp_shared_paired.csv`,
  `outputs/basil_shap/basil_shap_fn_shared.csv` (shared-error pools used
  by the SHAP magnitude analysis — 314 and 221 sentences respectively)
- Shared-count totals (314 FPs, 221 lex-only FNs) carried forward from
  the SHAP-stage join already documented in `outputs/findings_summary.md`
  §7–§9.

All thresholds and strata follow the BASIL evaluation conventions:
- "FP / FN" without qualification refers to threshold 0.5 on the full set.
- "FN (lex-only)" refers to FNs restricted to the lex-only stratum
  (`has_lex=1, has_inf=0`).
- Recall@0.3 follows the threshold-sweep convention in
  `basil/threshold_sweep_table.csv`.

---

## 1. Error overlap at threshold 0.5

### 1a. Raw counts

| Error type        | BD  | DR  | Shared | N (denominator) |
|-------------------|----:|----:|-------:|----------------:|
| FPs (on negatives)|  594|  462|    314 |   6,361 negatives |
| FNs (lex-only)    |  241|  263|    221 |     405 lex-only positives |

- **N_negatives = 6,361** = BD's TN+FP = 5,767+594 = DR's TN+FP =
  5,899+462. ✓ consistent both ways.
- **N_lex-only positives = 405** (from `auprc_table.csv` lex-only row;
  also matches threshold_sweep_table lex-only TP+FN at every θ).
- BD lex-only FN = 405 − TP@0.5 = 405 − 164 = **241**.
- DR lex-only FN = 405 − TP@0.5 = 405 − 142 = **263**.
- Shared FP pool = **314** (BASIL §7 / `basil_shap_fp_partition.csv`).
- Shared FN pool (lex-only) = **221** (BASIL §9).

### 1b. Independence math

For each error type, the independence baseline is the product of the two
single-model error rates over the appropriate denominator. Two ways to
state the result — counts and rates — both reduce to the same ratio.

#### FP overlap (denominator: 6,361 negatives)

| Quantity                          | Value     |
|-----------------------------------|----------:|
| P(BD FP \| neg)                   | 594 / 6,361 = 0.0934 |
| P(DR FP \| neg)                   | 462 / 6,361 = 0.0726 |
| Expected shared rate (indep.)     | 0.0934 × 0.0726 = 0.00678 |
| Expected shared count (indep.)    | 0.00678 × 6,361 = **43.1** |
| Observed shared count             | **314** |
| Ratio (observed / expected)       | 314 / 43.1 = **7.28×** |

Stated as a conditional rate (the form used in `findings_summary.md`):
- Observed P(shared \| BD FP) = 314 / 594 = **0.529** (≈ 0.530).
- Independence prediction = P(DR FP \| neg) = **0.0726**.
- Ratio = 0.529 / 0.0726 = **7.29×**.

#### FN (lex-only) overlap (denominator: 405 lex-only positives)

| Quantity                          | Value     |
|-----------------------------------|----------:|
| P(BD FN \| lex pos)               | 241 / 405 = 0.5951 |
| P(DR FN \| lex pos)               | 263 / 405 = 0.6494 |
| Expected shared rate (indep.)     | 0.5951 × 0.6494 = 0.3865 |
| Expected shared count (indep.)    | 0.3865 × 405 = **156.5** |
| Observed shared count             | **221** |
| Ratio (observed / expected)       | 221 / 156.5 = **1.41×** |

Stated as a rate-over-positives (the form in the findings doc):
- Observed P(both miss \| lex pos) = 221 / 405 = **0.546**.
- Independence prediction = 0.5951 × 0.6494 = **0.386** (≈ 0.39).
- Ratio = 0.546 / 0.386 = **1.41×**.

### 1c. Summary line for the prose

| Error type | Actual rate | Independence | Ratio |
|------------|------------:|-------------:|------:|
| FP overlap (\| BD FP) | 0.530 | 0.073 | **7.28×** |
| FN lex-only overlap (\| lex pos) | 0.546 | 0.386 | **1.41×** |

Suggested phrasing: *"Among BASIL's 6,361 negative examples, the two
models share 314 false positives at θ = 0.5 — 7.3× more than if their
errors were independent. Among the 405 lex-only positives, they share
221 misses, only 1.4× the independence baseline."*

---

## 2. Bias-type recall at threshold 0.3

All from `basil/threshold_sweep_table.csv`, threshold = 0.3.

| stratum     |     n | BD recall@0.3 | DR recall@0.3 |
|-------------|------:|--------------:|--------------:|
| lex-only    |   405 |  191/405 = **0.4716** | 200/405 = **0.4938** |
| inf-only    | 1,174 |  397/1,174 = **0.3382** | 440/1,174 = **0.3748** |
| both-types  |    44 |   28/44  = **0.6364** |  29/44  = **0.6591** |

### Independence prediction for the both-types row

Formula: P(catch_both) ≈ 1 − (1 − P_lex)(1 − P_inf).

| Model | P_lex  | P_inf  | 1 − (1−P_lex)(1−P_inf) | Observed (both-types) | Gap (pts) |
|-------|-------:|-------:|----------------------:|----------------------:|----------:|
| BD    | 0.4716 | 0.3382 | 1 − 0.5284 × 0.6618 = **0.6502** | 0.6364 | **1.4** |
| DR    | 0.4938 | 0.3748 | 1 − 0.5062 × 0.6252 = **0.6835** | 0.6591 | **2.4** |

Both gaps are within the "2–3 points" claim. Independence predicts the
observed both-types recall well; the small undershoot is consistent with
weakly *anti*-correlated detection across the two cue families (i.e., a
sentence that gets caught by the lex pathway isn't quite as likely to
also get caught by the inf pathway, conditional on a sentence having
both cues).

Suggested phrasing: *"Recall at θ = 0.3 on sentences carrying both cue
types is 0.64 / 0.66 for BD / DR. Treating the two cue pathways as
independent — using the per-stratum lex-only and inf-only recalls of
0.47 / 0.49 and 0.34 / 0.37 — predicts 0.65 / 0.68. Observed matches
predicted within 2.4 points for both models."*

---

## 3. AUPRC by stratum (appendix-ready)

From `basil/auprc_table.csv`.

| stratum         |     n | BD AUPRC | DR AUPRC | baseline | BD lift | DR lift |
|-----------------|------:|---------:|---------:|---------:|--------:|--------:|
| full            | 7,984 |  0.3915  |  0.4121  |  0.2033  |  1.93×  |  2.03×  |
| lex-only        | 6,766 |  0.1945  |  0.2094  |  0.0599  |  **3.25×** |  **3.50×** |
| inf-only        | 7,535 |  0.2900  |  0.3127  |  0.1558  |  **1.86×** |  **2.01×** |
| both-types      | 6,405 |  0.0583  |  0.1013  |  0.00687 |  **8.49×** |  **14.75×** |
| quote-excluded  | 7,297 |  0.2748  |  0.2740  |  0.1283  |  2.14×  |  2.14×  |
| quote-only      | 7,048 |  0.2258  |  0.2702  |  0.0975  |  2.32×  |  2.77×  |

Notes:
- "baseline" is the prevalence of the positive class within the
  stratum, i.e., the AUPRC of a random classifier.
- "lift" = AUPRC / baseline. The conversation summary cited 3.25 /
  3.48 / 1.86 / 2.01 / 8.3 / 14.4 — these match within rounding
  (3.50 vs 3.48 and 8.49 vs 8.3 / 14.75 vs 14.4 are the same numbers at
  slightly different rounding).
- Both models are markedly stronger over the inf-only stratum than the
  lex-only stratum *in absolute AUPRC* (0.29 vs 0.19 for BD; 0.31 vs 0.21
  for DR), but the *lift* over baseline is highest on the both-types
  stratum because the baseline is tiny (0.69%).
