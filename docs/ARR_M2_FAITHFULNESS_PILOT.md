# ARR M2A — SHAP Faithfulness Pilot Report

**Date:** 2026-10-20  
**Machine:** MacBook Air M1, 8 GB, MPS  
**Env:** project `.venv` (`requirements-arr-m2.txt`)  
**Code:** `scripts/arr_m2/faithfulness_pilot.py`, `scripts/arr_m2/perturbations.py`  
**Outputs:** `outputs/arr_m2/` (does not overwrite M1 or original caches)  
**Models:** `himel7/bias-detector`, `mediabiasgroup/DA-RoBERTa-BABE-FT` (DeBERTa excluded)

---

## Stop-condition answers

### 1. Do live predictions reproduce cached probabilities?

**Yes.** Unperturbed MPS inference matched cached `prob_pos` for all 18 pilot sentences × 2 models (36/36) within tolerance `|Δp| ≤ 1e-3`.

| Model | Within tol | Max \|Δp\| | Mean \|Δp\| |
|-------|------------|-----------|-------------|
| biasdetector | 18/18 | 2e-6 | ≈0 |
| daroberta | 18/18 | 1e-6 | ≈0 |

Artifact: `outputs/arr_m2/repro_check.csv`.

### 2. Do SHAP-selected words cause larger / directionally consistent score changes than controls?

**Mostly yes for positive and absolute SHAP; mixed for negative SHAP.**

Primary results (probability space, **budget=2**, all strata, n=18 sentences):

| Model | Condition | Mean ΔP(biased) | 95% bootstrap CI | Direction rate\* | Mean \|ΔP\| |
|-------|-----------|----------------:|------------------|------------------|------------:|
| BD | A_pos (high +SHAP) | **−0.169** | [−0.299, −0.059] | 0.89 | — |
| BD | B_neg (high −SHAP) | **+0.044** | [+0.004, +0.112] | 0.39 | — |
| BD | C_abs | −0.134 | [−0.271, −0.016] | — | 0.161 |
| BD | D_random | +0.002 | [−0.032, +0.048] | — | 0.036 |
| BD | E_lowabs | −0.002 | [−0.011, +0.006] | — | 0.011 |
| DR | A_pos | **−0.180** | [−0.282, −0.097] | 1.00 | — |
| DR | B_neg | **+0.050** | [+0.019, +0.087] | 0.78 | — |
| DR | C_abs | −0.163 | [−0.270, −0.075] | — | 0.179 |
| DR | D_random | −0.035 | [−0.063, −0.009] | — | 0.046 |
| DR | E_lowabs | −0.000 | [−0.010, +0.009] | — | 0.014 |

\*Direction: A expects ΔP&lt;0; B expects ΔP&gt;0.

**Paired contrasts (budget=2):** removing top-+SHAP words reduces P(biased) more than random (A−random CI excludes 0 for both models). Top-|SHAP| causes larger \|ΔP\| than low-|SHAP| and than random (C−lowabs and C−random CIs exclude 0).

**Do not claim universal faithfulness:** BD B_neg direction rate is only 0.39 (many “negative” removals do not increase P). Aggregate A/C effects are clear; B is weaker and stratum-dependent.

Figure: `outputs/arr_m2/faithfulness_pilot_figure.png` / `.pdf`.

### 3. Differences between the two models

- Both show clear **A_pos** and **C_abs** effects vs controls.  
- **DA-RoBERTa** has cleaner **B_neg** directionality (0.78 vs 0.39 at budget=2).  
- Absolute effect sizes are similar (A_pos mean ΔP ≈ −0.17 BD vs −0.18 DR).  
- Random masks slightly decrease P for DR (CI below 0) but are near-zero for BD — treat random as a control, not a null of exactly zero.

### 4. Sensitivity to masking budget

Paired A−random mean becomes more negative as budget grows (BD: −0.08 / −0.17 / −0.22 for budgets 1/2/3; DR: −0.09 / −0.15 / −0.16). C−lowabs similarly increases. **Budget 2–3** give clearer separation; budget 1 is noisier (some CIs include 0).

### 5. Runtime and memory

| Metric | Value |
|--------|------:|
| Device | **MPS** |
| Wall time (pilot) | **61.5 s** |
| Peak RSS | **528 MB** |
| Model load | BD 12.7 s; DR 33.4 s (Hub) |
| Pure inference | 9.5 s for 576 forwards |
| Est. 200 sentences\* | ~0.04 h (~2.5 min) |
| Est. 1000 sentences\* | ~0.16 h (~10 min) |

\*Linear extrapolation from pilot forwards + setup; **±50% uncertainty** (thermal/MPS). 8 GB Mac is **adequate** for this design if models are loaded sequentially.

### 6. Ready to scale?

**Conditionally yes for a medium scale (≈100–200 sentences) on this Mac**, after addressing the alignment issue below. Not blocked by memory/runtime. **Do not scale to 1000+ or claim paper-ready faithfulness until:**

1. Word↔text alignment failures are reduced (token-level masking redesign), and  
2. Shared TN coverage is improved (or TN claims are scoped to n=3), and  
3. Stratum-wise tables are powered (especially TN).

### 7. Methodological issues requiring redesign

1. **Shared TN shortfall (sampling design):** Only **3** BD∩DR shared TN sentences exist in SHAP caches (requested 5). Pilot used all 3; **n_pilot=18**, not 20. Alternative (not run): append-only SHAP for additional shared-TN keys from full BASIL predictions.  
2. **Word_attribs ↔ whitespace alignment failures:** 93/540 rows underfilled (`n_applied < budget`) due to SHAP word strings with curly quotes, glued punct (`100FALSE!!!`, `Hunt!””`), or truncated merges (`compoundin`). **0 over-budget** events. Fully-applied subset (447/540) shows the same qualitative pattern, slightly stronger A_pos effects.  
   **Redesign:** select mask targets from token-level `tokens`+`shap_pos` and apply tokenizer-native masking, or repair word reconstruction before selection.  
3. **Deletion/mask OOD:** Replacing with `<mask>` is not a causal intervention in the training distribution; interpret as **sensitivity**, not proof of reasoning.  
4. **Gold labels unused for target selection** (as required); strata defined from joint predictions.

---

## Protocol (exact)

### Environment
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-arr-m2.txt
.venv/bin/python scripts/arr_m2/faithfulness_pilot.py --device auto
.venv/bin/python -m unittest tests.test_faithfulness_perturbations -v
```

### Sample
- Seed **7**.  
- Shared BASIL sentences with SHAP in **both** caches and **identical** text + same confusion cell.  
- Targets: 5 TP / 5 FP / 5 TN / 5 FN → realized **5/5/3/5**.  
- Manifest: `outputs/arr_m2/sampling_manifest.csv`, notes in `sampling_notes.json`.

### Perturbations
| Code | Selection |
|------|-----------|
| A_pos | Highest signed SHAP (biased class) |
| B_neg | Most negative signed SHAP |
| C_abs | Highest \|SHAP\| |
| D_random | Random words, matched count (seeded) |
| E_lowabs | Lowest \|SHAP\| |

Budgets **1, 2, 3** words. Mask token = tokenizer `mask_token` (`<mask>` for both RoBERTa models). Location via whitespace-token matching (`perturbations.py`). Metrics recorded in probability and logit-margin spaces separately.

### Stratum note (A_pos, budget=2)
Effects strongest on TP/FP; weaker on FN/TN (small n for TN). Do not claim faithfulness from aggregates alone if TN/FN remain weak after scale-up.

---

## Deliverable checklist

| Path | Status |
|------|--------|
| `scripts/arr_m2/faithfulness_pilot.py` | Done |
| `scripts/arr_m2/perturbations.py` | Done |
| `tests/test_faithfulness_perturbations.py` | 11/11 passed |
| `outputs/arr_m2/faithfulness_pilot_results.csv` | 540 rows |
| `outputs/arr_m2/faithfulness_pilot_summary.csv` | Done |
| `outputs/arr_m2/faithfulness_pilot_figure.png/.pdf` | Done |
| `requirements-arr-m2.txt` | Done |
| `docs/ARR_M2_FAITHFULNESS_PILOT.md` | This file |

**Not started:** full-scale faithfulness, human annotation (E3), DeBERTa.
