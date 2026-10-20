# ARR M2C — Gold-Span Alignment and SHAP Plausibility

**Date:** 2026-10-20  
**Hardware:** MacBook Air M1, 8 GB unified memory  
**Env:** `.venv` / `requirements-arr-m2.txt`  
**Code:** `scripts/arr_m2c/gold_span_metrics.py`, `scripts/arr_m2c/run_gold_span_alignment.py`  
**Inputs:** M1 `outputs/arr_m1/basil_spans/gold_spans.csv`; existing SHAP caches under `outputs/basil_shap/`  
**Outputs:** `outputs/arr_m2c/` (original caches and M1/M2A/M2B artifacts untouched)

**Scope:** Plausibility of SHAP word attributions vs BASIL human bias spans.  
**Not in scope:** New SHAP generation, semantic paraphrasing, or claiming the blind human study is complete.

---

## Stop-condition answers

### 1. Gold-alignment coverage

| Source | Count |
|--------|------:|
| BASIL gold spans (M1) | 1,723 |
| Unique positive sentences | **1,623** (96 multi-span) |
| Lexical / informational spans | 478 / 1,245 |

| Model | Cache | Analyzed | Positive aligned | lex_only | inf_only | both | non-biased in cache |
|-------|------:|---------:|-----------------:|---------:|---------:|-----:|--------------------:|
| bias-detector | 850 | 849 | **475** | 223 | 229 | 23 | 374 |
| DA-RoBERTa | 837 | 837 | **467** | 227 | 214 | 26 | 370 |
| DeBERTa | 400 | 400 | **200** | 55 | 138 | 7 | 200 |

Paired positive sentences: **bd∩dr = 255**, bd∩deb = 83, dr∩deb = 65, all three = 42.  
Exclusions: **1** (`biasdetector` text mismatch vs `basil_sentences.csv`).

Main analysis uses **every eligible cached positive explanation**, not a subsample of 100.

### 2. Does SHAP identify lexical evidence better than baselines?

**Yes.** Excess absolute attribution mass over length-matched random spans (`abs_minus_rand_span`), lex_only:

| Model | n | Mean excess | 95% CI |
|-------|--:|------------:|--------|
| bias-detector | 223 | +0.080 | [+0.063, +0.097] |
| DA-RoBERTa | 227 | +0.133 | [+0.114, +0.152] |
| DeBERTa | 55 | +0.141 | [+0.101, +0.184] |

Same pattern for positive-mass excess, top-k precision vs random words, and excess over span-coverage / positional controls (CIs exclude 0). Lexical spans are short (~9–10% char coverage), so raw mass is modest (~0.17–0.24) but **clearly above chance**.

### 3. Does SHAP identify informational evidence better than baselines?

**Weakly / often not after length control.** Informational spans cover ~70% of sentence characters, so raw `|SHAP|` mass in gold is high (~0.70–0.73) but nearly matched by random/coverage baselines.

| Model | n | Mean `abs_minus_rand` | 95% CI | Verdict |
|-------|--:|----------------------:|--------|---------|
| bias-detector | 229 | +0.028 | [+0.015, +0.042] | Small positive |
| DA-RoBERTa | 214 | +0.035 | [+0.017, +0.055] | Small positive |
| DeBERTa | 138 | +0.017 | [−0.002, +0.037] | **Not significant** |

`abs_minus_coverage` for BD inf_only CI includes 0. Do **not** treat high raw mass as alignment. Many informational annotations are poor sentence-local explanation targets (see §4 and `informational_context_flags.csv`).

### 4. Does one model align more closely on paired sentences?

**DA-RoBERTa > bias-detector** on the 255 shared positives (paired BD − DR):

| Metric | n | Mean diff (BD−DR) | 95% CI |
|--------|--:|------------------:|--------|
| abs_mass | 255 | −0.039 | [−0.052, −0.026] |
| abs_minus_rand | 255 | −0.033 | [−0.045, −0.020] |
| prec@k | 255 | −0.027 | [−0.046, −0.009] |
| AP(\|SHAP\|) | 216 | −0.078 | [−0.119, −0.038] |

Category split (abs_minus_rand): lex_only n=168, mean −0.041 [−0.058, −0.025]; inf_only n=67, mean −0.006 [−0.028, +0.016] (no paired difference).  
DeBERTa comparisons are smaller (n=65–83); unpaired abs_mass differences must **not** be read as architecture effects.

### 5. Do faithfulness and human plausibility diverge?

**Yes.** M2B showed strong attribution-guided sensitivity (faithfulness-style necessity) for both BD and DR on TP/FP. M2C shows only **moderate lexical plausibility** and **weak informational plausibility**. A model can be sensitive to its own high-SHAP tokens without those tokens matching BASIL evidence—especially informational spans. Treat faithfulness and human alignment as **separate claims**.

### 6. Is the independent annotation study ready?

**Materials ready; study not run.** Seed=7 sample of 120 (30 lex_only / 30 inf_only / 30 both / 30 non-biased). Blind CSV, gold-keyed analyst CSV, HTML offset-preserving form, and guide are in place. No LLM labels substituted. IAA pending two human annotators.

### 7. What should replace Emotional/Evaluative taxonomy claims?

Replace Em/Eval (M1: ~94% “Other” at p75) with:

1. **BASIL lexical vs informational** as the primary evidence taxonomy for explanation evaluation.  
2. **Faithfulness** = perturbation sensitivity (M2B), not human agreement.  
3. **Plausibility** = gold-span / human-span alignment (M2C), reported **separately by bias type**, vs length-matched baselines.  
4. Explicit caveat that informational bias often needs **article context** and is not a fair sentence-local SHAP target.

---

## Method

### Join and exclusions

- Sentence key: `(triplet_uuid, outlet_idx, sentence_idx)` → `basil:…|…|…`.  
- Gold spans from M1 recovery (`launchnlp/BASIL` @ `4fdbc4f`). Multiple spans per sentence kept; metrics use the union of gold character masks.  
- Word↔char mapping: M2B `offset_alignment.align_record` (≥50% character overlap ⇒ gold word).  
- Exclusion log: text mismatch between cache and CSV (1 row).

### Metrics (positive annotated sentences)

| ID | Metric | Definition |
|----|--------|------------|
| A | Gold-span abs mass | Σ\|SHAP\|·overlap_frac / Σ\|SHAP\| |
| B | Positive mass | Σ max(SHAP,0)·overlap / Σ max(SHAP,0) |
| C | Top-k P/R | k=5 by \|SHAP\| vs gold words |
| D | Ranking | Average precision by \|SHAP\| (and signed); exclude if no gold or all-gold words |
| E | By category | lex_only / inf_only / both |

### Baselines (20 seeded draws per sentence, seed derived from `SEED=7`)

- Length-and-count-matched **random character spans**.  
- Random **word sets** matched to top-k size.  
- **Span-coverage** baseline (expected mass = char coverage under uniform attribution).  
- **Positional** control (same-length spans shifted to sentence start/end when feasible).

Primary contrast: `abs_minus_rand_span` (and analogs). Sentence-level means with 95% bootstrap CIs over sentences; paired diffs on shared IDs.

### Prediction strata

Caches are gold-positive–heavy (TP/FN only in this join). Alignment excess is **larger on TP than FN** (e.g. DR lex_only|TP +0.204 vs lex_only|FN +0.066). FN informational excess is near zero for all models.

---

## Results summary figures

- `outputs/arr_m2c/figures/abs_mass_vs_random.png` — SHAP vs length-matched random by model/category.  
- `outputs/arr_m2c/figures/excess_mass_lex_vs_inf.png` — excess mass lex vs inf with CIs.

### Both-type sentences

Small n (23–26 for BD/DR). Excess over random is positive (~0.12–0.14) but underpowered for strong claims; treated as an additional category only.

### Informational / contextual caveats

`informational_context_flags.csv` lists 80 BD informally weak cases (sorted by lowest excess over random) for qualitative review. Sentence-level classifiers and sentence-local SHAP **cannot** be expected to recover annotations that depend on omitted facts, framing across paragraphs, or outlet contrast. Weak informational alignment may reflect annotation scope as much as model or SHAP failure.

---

## Human validation prep (not executed)

| Artifact | Path |
|----------|------|
| Analyst sample (with GOLD_*) | `outputs/arr_m2c/human_annotation_sample.csv` |
| Blind annotator CSV | `outputs/arr_m2c/human_annotation_sample_BLIND.csv` |
| HTML form (offset capture) | `outputs/arr_m2c/human_annotation_interface.html` |
| Guide | `docs/ARR_M2C_HUMAN_ANNOTATION_GUIDE.md` |

Plan: two independent annotators on all 120 if feasible; compute span-level and category IAA after collection. **Do not** use LLM labels as substitutes.

---

## Files produced

| File | Role |
|------|------|
| `gold_span_alignment.csv` | Per (sentence, model) metrics + baselines |
| `gold_span_summary.csv` | Aggregate means/CIs, paired diffs, by_outcome |
| `coverage.json` | Model coverage + paired counts |
| `exclusion_log.csv` | Dropped rows |
| `informational_context_flags.csv` | Qualitative inf review set |
| `human_annotation_sample*.csv` / `.html` | Blind study materials |
| `figures/` | Alignment vs baseline plots |

---

## Limitations

- Cache coverage ≠ full BASIL; DeBERTa positive n=200 and both-type cells are thin.  
- Random baselines are span-geometry matched, not discourse matched.  
- AP excludes all-gold / no-gold edge cases (common when informational spans cover most tokens).  
- No new SHAP; conclusions are conditional on existing attribution quality.  
- Human study materials prepared only—agreement and human↔SHAP overlap not yet measured.

---

## Bottom line for the paper revision

SHAP attributions show **statistically reliable, length-corrected alignment with BASIL lexical spans**, stronger for DA-RoBERTa than bias-detector on paired sentences, and **much stronger on TP than FN**. Alignment with **informational** spans is weak once span length is controlled and should not be claimed as human plausibility. Faithfulness (M2B) must not be presented as evidence of human-evidence alignment. Emotional/Evaluative taxonomy claims remain invalidated (M1); report **lexical vs informational** evidence alignment with the caveats above.
