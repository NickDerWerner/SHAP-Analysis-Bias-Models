# ARR M2B — Faithfulness Alignment Repair and Medium-Scale Evaluation

**Date:** 2026-10-20  
**Hardware:** MacBook Air M1, 8 GB unified memory, MPS  
**Env:** `.venv` / `requirements-arr-m2.txt`  
**Code:** `scripts/arr_m2/offset_alignment.py`, `scripts/arr_m2b/faithfulness_eval.py`  
**Tests:** `tests/test_offset_alignment.py` (8/8 passed, includes M2A failure regressions)  
**Outputs:** `outputs/arr_m2b/` (M1/M2A/original caches untouched)

---

## Stop-condition answers

### 1. Effective alignment coverage

| Phase | Sentence align OK | Complete-budget rate | Underfilled rows |
|-------|-------------------:|---------------------:|-----------------:|
| M2A regression (18×2) | **100%** (36/36) | **100%** | **0** |
| Medium (200×2) | **100%** (400/400) | **100%** (8400/8400 attempted complete kept) | **0** |

Token-level content location rate: **min = 1.0** across all audited rows (`alignment_audit.csv`).  
**Gate (≥99%):** **PASSED** before scaling.

### 2. Faithfulness results and effect sizes (medium, budget=2, n=200 paired sentences)

Probability space (sentence-level means; random averaged over 3 seeds; 95% bootstrap CI over sentences):

| Model | Condition | Mean ΔP | 95% CI | Dir. rate | Mean \|ΔP\| |
|-------|-----------|--------:|--------|----------:|-----------:|
| BD | A_pos | **−0.327** | [−0.369, −0.282] | 0.925 | 0.329 |
| BD | B_neg | **+0.054** | [+0.036, +0.073] | 0.680 | 0.071 |
| BD | C_abs | −0.246 | [−0.291, −0.198] | — | **0.294** |
| BD | D_random | −0.040 | [−0.055, −0.024] | — | 0.071 |
| BD | E_lowabs | −0.013 | [−0.021, −0.005] | — | 0.029 |
| DR | A_pos | **−0.293** | [−0.328, −0.258] | 0.945 | 0.295 |
| DR | B_neg | **+0.045** | [+0.032, +0.057] | 0.705 | 0.060 |
| DR | C_abs | −0.276 | [−0.314, −0.239] | — | **0.289** |
| DR | D_random | −0.041 | [−0.055, −0.028] | — | 0.067 |
| DR | E_lowabs | −0.010 | [−0.019, −0.002] | — | 0.035 |

Paired contrasts (budget=2; CI excludes 0 for all listed):

| Contrast | BD mean | DR mean |
|----------|--------:|--------:|
| A − random (signed) | −0.287 | −0.253 |
| B − random (signed) | +0.094 | +0.085 |
| C − random (\|ΔP\|) | +0.223 | +0.222 |
| C − lowabs (\|ΔP\|) | +0.266 | +0.254 |

Logit-margin analyses are in `faithfulness_summary.csv` (`mean_delta_logit` columns) — kept separate from probability space.

### 3. Does the main effect survive the larger sample?

**Yes.** High-+SHAP and high-|SHAP| removals reduce P(biased) with CIs far from zero; effects are **larger** than in the 18-sentence pilot (A_pos ≈ −0.17/−0.18 → −0.33/−0.29). High-|SHAP| ≫ random ≫ low-|SHAP| on absolute sensitivity. Ordering **A/C > controls** is stable across budgets 1–3.

### 4. Both models and all four prediction groups?

| Stratum | n | A_pos effect | Caveat |
|---------|--:|--------------|--------|
| TP | 85 | Strong (BD −0.41, DR −0.36; dir ≈0.99) | OK |
| FP | 60 | Strong (BD −0.46, DR −0.39; dir ≈0.97–1.0) | OK |
| FN | 52 | Weaker but same sign (≈ −0.07/−0.08; dir 0.75–0.87) | OK with smaller magnitude |
| TN | **3** | Near-zero / unstable | **Underpowered — do not claim TN faithfulness** |

Both encoder models show the same qualitative pattern. B_neg directionality is moderate (~0.68–0.71 overall), stronger on FN than on TP/FP.

### 5. Can we present this as evidence of SHAP faithfulness?

**Yes, with precise scope:**

- **Supported:** On BASIL paired TP/FP (and, more weakly, FN), masking words that carry high positive or high absolute SHAP for the biased class changes model scores **more**, and in the expected direction for A_pos, than random or low-|SHAP| controls — after offset-correct word localization.  
- **Not supported as universal causal proof:** mask-token interventions are OOD; B_neg is only partially consistent; TN evidence is insufficient; results are for two RoBERTa-family models only.  
- Prefer wording: *“attribution-guided sensitivity / necessity evidence”* rather than *“explanations of reasoning.”*

Optional sufficiency subsample (keep top-20% |SHAP| words, mask rest vs random keep; n=40): high-abs keep preserves prediction more often (BD 0.80 vs 0.53; DR 0.70 vs 0.45) and yields smaller |ΔP| — consistent with, but not proof of, sufficiency (`sufficiency_subsample.csv`).

### 6. Ready for M2C (human-evidence alignment)?

**Yes, methodologically.** BASIL gold spans are recovered (M1); faithfulness sensitivity is established for TP/FP. M2C can proceed for **plausibility** (SHAP↔human/gold span overlap), clearly separated from faithfulness.

**Do not begin** paraphrasing, DeBERTa, retraining, or full SHAP regen without approval.

---

## Task 1 — Alignment repair

### Method
Source-authoritative whitespace words + greedy location of each SHAP token’s non-space content in the sentence (cursor + soft curly-quote normalization). Token SHAP is aggregated onto overlapping source spans by character overlap. Masking uses **exact character offsets**; incomplete budgets are **excluded** (never silent substitute).

### M2A failure categories covered by tests
Curly quotes / `““He`, `100FALSE!!!` merge, `him&` glue, repeated words, punct/excl, corrupt-span no-substitute, full M2A manifest sweep.

---

## Task 2 — M2A 18-sentence reproduction

- Alignment: **100%**; complete budgets: **100%** (was 93/540 underfilled).  
- High-SHAP vs control **ordering preserved**.  
- A_pos/C_abs signs unchanged; magnitudes somewhat larger (cleaner masks).  
- One sign flip: BD D_random mean +0.002 → −0.025 (near-zero control; not a claim reversal).  
- Compare table: `m2a_vs_m2b_regression_compare.csv`.

Runtime regression: **16.5 s** wall, MPS.

---

## Task 3 — Medium-scale sample

| Item | Value |
|------|-------|
| Target | 200 distinct BASIL sentences |
| Seed | 7 |
| Scope | **Paired only** (BD∩DR, same text, same cell) |
| Taken | TP 85, FP 60, FN 52, TN **3** |
| Available TN | 3 (documented shortfall) |

No unpaired results are labeled as cross-model paired comparisons.

Runtime medium: **140 s** wall; **8800** forwards; peak RSS **~480 MB**; inference **134 s**.

---

## Task 4 — Statistics (design choices)

- Bootstrap over **sentences**, not raw mask rows.  
- Random condition: mean over 3 repetitions before sentence-level stats.  
- Probability and logit-margin reported separately.  
- Stratum-wise tables reported; TN flagged underpowered.

---

## Recommended manuscript changes (`docs/references/paper.tex`)

| Topic | Approx. lines | Action |
|-------|---------------|--------|
| Soften “attends to / same mechanism” | L210–212, L230–255, L648–662 | Cite attribution-guided sensitivity; point to M2B |
| Faithfulness protocol TODO | L495 | Replace with M2B protocol + BASIL TP/FP results |
| SHAP background mismatch | L415–419 | Still fix text vs code (methods honesty) |
| Taxonomy 90–96% Em/Eval | L157, L881–883 | Already superseded by M1 Other analysis |
| Limitations | L900+ | Add: mask OOD, TN n=3, B_neg partial, encoder-only |
| New results subsection | after L559 or new § before Conclusion | Table/figure: ΔP by condition (budget 2); stratum TP/FP |

Figures for paper draft: `outputs/arr_m2b/figures/faithfulness_medium_budget2.pdf`, `abs_sensitivity_medium_budget2.pdf`.

---

## Limitations

1. Shared TN n=3 in SHAP caches.  
2. Mask-token perturbations are distributionally unnatural.  
3. DeBERTa not included.  
4. B_neg only moderately directional.  
5. FN effects smaller than TP/FP (expected if positives were missed).  
6. Sufficiency experiment is a small optional subsample.

---

## Artifact index

```
outputs/arr_m2b/
  faithfulness_results.csv      # medium (canonical)
  faithfulness_summary.csv
  alignment_audit.csv
  regression_*.csv
  m2a_vs_m2b_regression_compare.csv
  medium_sampling_manifest.csv
  sufficiency_subsample.csv
  run_meta.json
  figures/*.png|pdf
scripts/arr_m2/offset_alignment.py
scripts/arr_m2b/faithfulness_eval.py
tests/test_offset_alignment.py
docs/ARR_M2B_FAITHFULNESS_REPORT.md
```
