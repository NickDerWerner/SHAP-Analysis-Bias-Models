# ARR M1 Validation Report — Methodological Repair

**Milestone:** M1 (taxonomy, pairing, DeBERTa integrity, BASIL spans)  
**Date:** 2026-10-20  
**Constraint honored:** No full SHAP regeneration; no retraining; original caches preserved.  
**Artifacts root:** `outputs/arr_m1/`  
**Companion docs:** `ARR_TAXONOMY_SPECIFICATION.md`, `ARR_PAIRED_SAMPLE_COVERAGE.md`, `ARR_BASIL_SPAN_ALIGNMENT.md`

---

## Executive answers (requested)

| # | Question | Answer |
|---|----------|--------|
| 1 | Is the revised taxonomy scientifically defensible? | **Conditionally yes as an algorithmic coding scheme** with frozen rules and an explicit Other bucket. It is **not yet human-validated** (manual sample prepared). It is defensible for *retracting* the catch-all Em/Eval claim. |
| 2 | What replaces the old 90–96% claim? | Under matched-pool **p75**, v2 yields **~94% Other/Unassigned** and only **~2–4% Emotional/Evaluative** (count). Attribution-weighted Em/Eval is ~3–11% on BABE p75. Report category mixes with Other; do **not** claim Em/Eval dominance. |
| 3 | Can three-model attribution comparison be retained? | **Only with strict pairing.** BABE all3 n=59 (same-cell TP/FP/TN too small). BASIL BD↔DR paired shared FP n=112 is solid; all3 n=60 only. Unpaired pool comparisons must be labeled non-causal / non-architecture. |
| 4 | Is DeBERTa aggregation reliable? | **Word–text alignment: yes** (327/327, 400/400). Stored word_attribs ≡ charspan fix. The “15–22% drop” is **whitespace character mass under charspan splitting**, also seen on RoBERTa caches under the same diagnostic — not unique silent loss of content tokens. Additive derived artifacts preserve Σ token SHAP. |
| 5 | Can BASIL spans be used for human alignment? | **Yes.** launchnlp/BASIL `@4fdbc4f` matches CSV **7984/7984**; **1723/1723** span offsets valid (478 lex, 1245 inf). |
| 6 | Ready for SHAP faithfulness experiment? | **Almost.** M1 blockers cleared for pilot design. Still need: project venv + at least one loadable model checkpoint before E2 runs. Taxonomy/pairing docs ready to scope the pilot sentence set. |

---

## Task A — Taxonomy (E1)

### Method
- Legacy vs v2 in `scripts/arr_m1/taxonomy.py`.  
- Distributions: all word occurrences vs p75 word-type selection (paper matched-pool style).  
- Count % and |SHAP|-weighted %.  
- Instance-level Other fraction with bootstrap 95% CI (B=1000, seed=7).

### Does ~63% Other persist under p75?

**Yes — and it increases.**

| Corpus | Model | Legacy Em/Eval % (p75 count) | V2 Em/Eval % | V2 Other % |
|--------|-------|-----------------------------:|-------------:|-----------:|
| BABE | biasdetector | 97.2 | 3.6 | **93.6** |
| BABE | daroberta | 97.7 | 2.8 | **94.8** |
| BABE | deberta | 97.3 | 3.5 | **93.8** |
| BASIL | biasdetector | 98.3 | 1.7 | **96.6** |
| BASIL | daroberta | 97.9 | 2.1 | **95.8** |
| BASIL | deberta | 96.6 | 2.2 | **94.3** |

All-occurrence Other (count) remains ~63% with instance-level means ≈ 63–65% (95% CIs width ~2 pp). See `taxonomy/headline_p75_comparison.csv`, `category_distributions.csv`.

### Interpretation
High-|SHAP| word types are mostly **content tokens outside the tiny Em/Eval lexicon**. Legacy “90–96% Emotional/Evaluative” was an artifact of residual catch-all (`return 'Emotional/Evaluative'`). **That claim must not be reused.**

### Validation sample
`taxonomy/manual_validation_sample.csv` — 86 items stratified by v2 category for human coding. **Not yet labeled.**

### Limitation
Lexicon provenance may itself reflect earlier SHAP tops; human validation and a corpus-frequency baseline (planned in E1 completion) remain required before strong linguistic claims.

---

## Task B — Cross-model alignment

### BABE
- Canonical ID = hash(text).  
- Intersection all3 = **59**.  
- Same-cell all3: TP 7, FP 3, TN 4, FN 26.  
- Paired similarity (n=59): median Jaccard@20 BD–DR 0.63; BD–Deb 0.54; DR–Deb 0.50.

### BASIL
- Canonical ID = triplet|outlet|sentence.  
- bd∩dr = **371**; all3 = **60** (DeBERTa magnitude-only).  
- Shared FP = **112**, median Jaccard@20 = **0.818** (consistent with paper ~0.81 on n=100 stratum).  
- Shared FN = **104**, Jaccard 0.727.

### Regeneration protocol
Documented in `paired/shared_shap_regen_protocol.json` — **not executed** in M1.

---

## Task C — DeBERTa integrity

### Findings
| Cache | Stored ≡ charspan fix | Alnum align to source | Median \|space mass\|/\|token sum\| (charspan diagnostic) |
|-------|----------------------:|----------------------:|----------------------------------------------------------:|
| babe deberta (current) | 327/327 | 327/327 | 0.149 |
| babe deberta `.bak` | 0/327 (pre-fix words) | 327/327 on tokens | 0.149 (same tokens) |
| basil deberta | 400/400 | 400/400 | 0.149 |
| babe bd / dr (reference) | 0 (different aggregator) | 337/337, 312/312 | 0.174 / 0.199 |

- **Whitespace mass** = portion of each token’s SHAP allocated to space characters when SHAP is divided across the token string. It is **not** evidence that content-token SHAP was discarded from the model explanation.  
- **Additive** reaggregation (`word_aggregation.reaggregate_additive`) yields residual ≈ 0 (machine epsilon); derived JSONL written under `deberta_integrity/*_word_attribs_additive.jsonl` without touching originals.  
- Unit tests: `tests/test_word_aggregation.py` — **8/8 passed**.

### Reliability verdict
For ranking words and paired Jaccard on surface forms, **current DeBERTa word_attribs are usable**. For strict additivity to Σ token SHAP, prefer **additive** derived files. Paper magnitude tables based on post-fix means remain the correct lineage vs `.bak`.

---

## Task D — BASIL gold spans

| Check | Result |
|-------|--------|
| Matching release | launchnlp/BASIL `4fdbc4f…` |
| Sentence exact match | 7984/7984 |
| Span offset == txt | 1723/1723 |
| lex / inf | 478 / 1245 |
| License file in clone | Absent — do not redistribute; see span doc |

Usable for E3 human-alignment analysis.

---

## Artifact index

```
outputs/arr_m1/
  taxonomy/
    category_distributions.csv
    headline_p75_comparison.csv
    p75_word_type_assignments.csv
    manual_validation_sample.csv
    run_meta.json
  paired/
    babe_*.csv  basil_*.csv
    shared_shap_regen_protocol.json
    run_meta.json
  deberta_integrity/
    integrity_summary.csv
    integrity_examples.csv
    *_word_attribs_additive.jsonl
    run_meta.json
  basil_spans/
    gold_spans.csv
    shap_cache_span_coverage.csv
    alignment_report.json
    run_meta.json
tests/test_word_aggregation.py
scripts/arr_m1/{taxonomy,word_aggregation,run_*}.py
```

---

## Readiness for next milestone (E2 faithfulness)

| Prerequisite | Status |
|--------------|--------|
| Taxonomy rules documented | Done |
| Paired sentence IDs for pilot | Done (prefer BASIL shared FP / BABE all3) |
| BASIL spans for optional plausibility side analysis | Done |
| Model env (shap, venv, checkpoints) | **Outstanding** (see hardware/repro gaps) |
| Full SHAP regen | Not required for pilot if using cached sentences + fresh forward masks |

**Recommendation:** Begin E2 as a **20-sentence pilot** on BASIL shared-FP IDs once the venv and `himel7/bias-detector` (cached) load successfully — after owner confirms. Do not scale until pilot timings exist.
