# ARR M2D — Gold-Span Robustness, Error Analysis, and Human Study Prep

**Date:** 2026-10-20  
**Code:** `scripts/arr_m2d/`  
**Tests:** `tests/test_arr_m2d.py` (**11 passed**)  
**Outputs:** `outputs/arr_m2d/`  
**Inputs:** M2C `gold_span_alignment.csv`; M2B `medium_results.csv`; M1 gold spans; existing SHAP caches  

**Scope:** Stress-test M2C plausibility claims; qualitative illustrations; validate human-study materials; ship analysis code for real annotations.  
**Not done:** Simulated human labels; paraphrasing; SHAP regeneration; full manuscript rewrite.

---

## Stop-condition answers

### 1. Does the lexical-versus-informational alignment gap survive controls?

**No — not for bias-detector or DA-RoBERTa once gold-span coverage is matched or controlled.**

| Analysis | BD | DR | Interpretation |
|----------|----|----|----------------|
| Unmatched lex−inf excess | +0.052 [+0.029, +0.073] | +0.097 [+0.072, +0.124] | Apparent gap (M2C) |
| Coverage-matched (±5pp) lex−inf | **−0.017 [−0.071, +0.038]** n=44 | **−0.001 [−0.064, +0.064]** n=42 | Gap **gone** |
| OLS `is_lex` **with** coverage | +0.021 [−0.023, +0.062] | +0.005 [−0.050, +0.062] | Nonsignificant |
| OLS `is_lex` **without** coverage | +0.068 [+0.045, +0.090] | +0.114 [+0.086, +0.142] | Significant only without coverage |

Mean coverage: lex ≈ 0.09–0.10 vs inf ≈ 0.70. DeBERTa still shows a matched gap (+0.146, n=18) — underpowered; do not overclaim.

**Retain:** Lexical spans beat length-matched **random** baselines (M2C).  
**Revise:** Do **not** claim SHAP is intrinsically better at lexical than informational evidence after span-length is equated. The M2C “lex ≫ inf” headline was largely a **coverage confound**.

### 2. How strongly do confidence / correctness explain the gap?

**Strongly for confidence and TP vs FN; they do not resurrect a coverage-free lex>inf effect.**

**Predicted probability (BD, abs excess over random):**

| Band | lex_only | inf_only |
|------|----------|----------|
| P&lt;0.25 | +0.008 n.s. | +0.009 n.s. |
| P≥0.75 | **+0.160** | +0.044 |

Lexical alignment rises sharply with confidence; informational stays weak even at high P.

**Outcome (cluster bootstrap by `triplet_uuid`):**

| Stratum | BD | DR |
|---------|----|----|
| lex\|TP | +0.147 | +0.204 |
| lex\|FN | +0.018 | +0.066 |
| inf\|TP | +0.035 | +0.052 |
| inf\|FN | +0.012 n.s. | +0.002 n.s. |

FP/TN: gold-negative sentences have **no gold bias spans**, so gold-span plausibility is undefined; M2B already covers FP faithfulness separately.

**Faithfulness ∩ alignment (M2B A_pos ∩ M2C, n=137/model):** Spearman(|ΔP|, excess) ≈ **+0.45**. High-faith tertile has higher alignment — but qualitative cases still show high faith with poor/zero gold alignment when spans cover the whole sentence.

### 3. Are DA-RoBERTa’s paired advantages still supported?

**Yes for absolute-mass excess and ranking AP; mixed for positive-mass excess.**

Paired BD − DR (sentence-level bootstrap):

| Stratum | Metric | n | Mean (BD−DR) | 95% CI |
|---------|--------|--:|-------------:|--------|
| ALL | abs_minus_rand | 255 | −0.031 | [−0.044, −0.017] |
| lex_only | abs_minus_rand | 168 | −0.038 | [−0.056, −0.021] |
| inf_only | abs_minus_rand | 67 | −0.008 | [−0.031, +0.016] |
| ALL | ap_abs | 216 | −0.078 | [−0.119, −0.038] |
| ALL | pos_minus_rand | 255 | +0.008 | [−0.019, +0.032] |

DR remains better on paired **|SHAP|** alignment and AP; **signed** positive-mass excess does not differ. Informational paired difference remains nonsignificant.

### 4. Which qualitative examples best illustrate the findings?

See `outputs/arr_m2d/qualitative_examples.html` and `figures/examples/`. Illustrative only:

| Role | Example takeaway |
|------|------------------|
| `high_faith_high_align` / `good_lexical_align` | Ryan “knuckle-rapping” — short lexical span, high A_pos sensitivity, high excess (BD & DR) |
| `high_faith_poor_align` | “Her mind is shot - resign!” — full-sentence gold span ⇒ excess=0 by construction despite huge A_pos ΔP |
| `poor_informational_align` | Near-full quote span; SHAP below length-matched random |
| `model_disagreement_*` | “unrepresentative and unreliable” — DR excess +0.16 vs BD −0.34 (both FN, low P) |
| `near_full_span_coverage` | Lex+inf union covers entire sentence; mass-in-gold ≈ coverage baseline |

### 5. Are study materials ready for two real annotators?

**Yes.** Verification: **11/11 checks passed**. Pack at `outputs/arr_m2d/annotator_pack/` (blind CSV + patched HTML with required `annotator_id`). Onboarding: `docs/ARR_M2D_HUMAN_STUDY_INSTRUCTIONS.md`. Analysis pipeline ready; **do not run** until real JSON/CSV arrive.

### 6. Which manuscript claims can be retained / replaced / removed?

See `docs/ARR_M2D_PAPER_FINDINGS.md`.

### 7. What remains before a credible ARR resubmission?

1. Two human annotators complete the 120-item study; run `human_agreement.py`.  
2. Revise paper: Em/Eval → BASIL lex/inf; separate faithfulness vs plausibility; **coverage confound** on lex vs inf.  
3. Fix SHAP background vs code mismatch (M2B note).  
4. Optional: DeBERTa faithfulness / fuller SHAP regen — **not** required for the core claim.  
5. No paraphrasing milestone until human study + wording locked.

---

## Task A — Method notes

- Unit of inference: **sentence** (bootstrap). Cluster bootstrap by `triplet_uuid` for multi-sentence articles.  
- Coverage matching: greedy 1:1 lex↔inf within ±0.05 coverage (seed 7).  
- OLS: `excess ~ is_lex + coverage + length + n_spans + prob` with bootstrap CIs.  
- Metrics: abs/pos excess over random, AP, prec@k (from M2C columns).  
- Nonsignificant ≠ equivalence (explicitly).

### Multi-span sensitivity

Multi-span positives show **higher** excess than single-span (BD +0.098 vs +0.052); not a threat to the main pattern. Annotations within a sentence are unioned (M2C), not treated as independent rows.

---

## Task B — Artifacts

| Path | Content |
|------|---------|
| `qualitative_examples.csv/.json/.html` | Full text, gold spans, top SHAP, faith join |
| `figures/examples/*.png` | Side-by-side gold band vs SHAP heat |
| `figures/coverage_matched_*.png` | Matched lex−inf |
| `figures/alignment_by_prob_band.png` | P-band curves |
| `figures/paired_bd_minus_dr.png` | Paired model diffs |

---

## Task C/D — Human study

Verification JSON: `human_materials_verification.json`.  
Agreement runner: `scripts/arr_m2d/human_agreement.py` (κ for labels; character soft-F1/IoU for spans). Refuses missing files (exit 2).

---

## Bottom line

M2C’s **lexical-beats-random** and **DR>BD paired |SHAP| alignment** survive. The **lexical-beats-informational** contrast does **not** survive coverage matching for BD/DR and must be reframed as a span-geometry confound plus a confidence/TP effect. Faithfulness and plausibility remain distinct: correlated (~0.45) but separable, with clear counterexamples when gold spans are near-total.
