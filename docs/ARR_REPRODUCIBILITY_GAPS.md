# ARR Reproducibility Gaps

**Companion to:** `ARR_CODEBASE_AUDIT.md`, `ARR_EXPERIMENT_PLAN.md`, `ARR_HARDWARE_ASSESSMENT.md`  
**Date:** 2026-10-20  
**Rule:** Gaps are documented; nothing invented to fill them.

---

## 1. Critical gaps (block clean reproduction)

| ID | Gap | Evidence | Impact | Remediation |
|----|-----|----------|--------|-------------|
| G-README | No README | Repo root listing | Newcomers cannot run pipeline | Write README pointing to scripts + this docs set |
| G-DEPS | No `requirements.txt` / lock / `pyproject.toml` | Glob search empty | Version drift (`transformers` 5.x typing patches already in `analysis.py` L374–379, L484–485) | Export from original `.venv` or reconstruct from overnight notes |
| G-VENV | Project `.venv` missing on audit machine | `ls .venv` fails; scripts hardcode `.venv/bin/python` | Cannot run SHAP/analysis locally | Recreate venv; document Python 3.12 |
| G-CKPT | Fine-tuned DeBERTa checkpoint missing | `models/` absent; gitignored (`.gitignore` L52–53) | Cannot reproduce DeBERTa inference/SHAP without retrain or external artifact | Restore from GitHub Release / Drive; else retrain with seed 42 |
| G-BASIL-RAW | Raw BASIL corpus missing | `preprocess_basil.py` expects `../BASIL`; path absent | No gold span offsets for E3; cannot regenerate CSV from source | Clone official BASIL; pin commit hash |
| G-SPAN | Sentence CSV has no span text/offsets | `basil_sentences.csv` columns; `sentence_features` drops span bodies (`preprocess_basil.py` L59–85) | Human–SHAP alignment blocked | Extend preprocessor to emit `spans.jsonl` with offsets |
| G-TAX | Em/Eval catch-all undocumented in paper | `categorize_word` L199; paper L491 TODO | Headline 90–96% claim not linguistically interpretable | E1 + paper taxonomy section |

---

## 2. High gaps (threaten scientific claims or partial repro)

| ID | Gap | Evidence | Impact | Remediation |
|----|-----|----------|--------|-------------|
| G-BG | Paper describes test-set SHAP background; code does not | `paper.tex` L415–419 vs `shap.maskers.Text(tokenizer)` in `analysis.py` L527 | Reviewer reproducibility score risk; method mismatch | Fix paper text to match code **or** re-run with documented background (costly) |
| G-PAIR | BABE SHAP samples are model-specific | Overlap all3 = 59 texts | “Same mechanism” magnitude comparisons confounded | Paired analyses (E4); optional new shared sample SHAP |
| G-DEB-STRATA | DeBERTa BASIL SHAP only magnitude strata | `basil_shap_generate.py` L316–328; analyze `SUFFIXES` L30 | Uneven 3-model story (reviewer k62P) | Extend shared FP/FN strata **or** scope paper claims to BD↔DR for those tables |
| G-AGG | Three aggregators diverge | `analysis.py` L257; `basil_shap_generate.py` L86; `fix_deberta_word_aggregation.py` L31 | Cross-script inconsistency; DeBERTa space-mass loss | Unify aggregator; unit tests; document residual |
| G-SHAPVER | SHAP HTML API drift | Overnight L156–159 | Minor; caches OK | Pin `shap` version; fix save_html if needed |
| G-MCNEMAR | McNemar only in notebook | `model_performance_comparison.ipynb` | Hard to re-run stats in CI | Port to `scripts/arr_mcnemar.py` |
| G-HUB-CASE | Model ID casing inconsistency | `DA-RoBERTa-BABE-FT` vs `da-roberta-babe-ft` in docs | Load failures | Canonical ID in one config module |

---

## 3. Medium gaps

| ID | Gap | Notes |
|----|-----|-------|
| G-SEED-MIX | Training seed 42 vs analysis seed 7 | Document both; do not conflate |
| G-TAX-ORIGIN | Emotional lexicon looks SHAP-derived | Document provenance; freeze before E1 validation |
| G-FN-APPEND | FN records appended by separate script | Provenance OK if seeds logged; ensure no duplicate texts (audit: 0 dups) |
| G-NOTEBOOKS | Parallel logic in notebooks vs scripts | Prefer scripts as source of truth |
| G-FIG6-HARDCODE | `babe_fig6_confound` paths / 2-model panels | Update for 3 models carefully |
| G-TEST-THRESH | Analyses lock t=0.5 | Address via E5; keep as sensitivity |

---

## 4. What *can* be reproduced from artifacts present now

Without Hub downloads or checkpoints:

- Reload and reanalyze all existing SHAP JSONL / CSV tables (taxonomy Other audit, Jaccard recomputation, magnitude tables).
- BASIL classification metrics from `outputs/basil/predictions_*.csv` + `basil_sentences.csv` (`compute_metrics.py`, `threshold_sweep.py` need deps).
- DeBERTa pre/post aggregation comparison via `.bak` files.

With HF cache for bias-detector only:

- Inference pilots on that model (MPS).

Cannot without remediation:

- Exact DeBERTa predictions regeneration.
- DA-RoBERTa load (not in local Hub cache).
- Gold-span E3.
- Bit-identical SHAP regen without pinned `shap` + torch + transformers.

---

## 5. Provenance notes (caches)

| Cache | Seed | Construction | Post-processing |
|-------|------|--------------|-----------------|
| BABE bd/dr TP/FP/TN | 7 (`analysis.py`) | Stratified per model | — |
| BABE FN | 7 (`babe_shap_fn.py`) | Append by text dedupe | — |
| BABE deberta | 7; max_shap_examples 237 then FN | Overnight | **word_attribs rewritten** by fix script; tokens/shap_pos unchanged |
| BASIL bd/dr | seed 7 manifest | Multi-stratum | — |
| BASIL deberta | magnitude only, RNG appended last | Overnight | fix script applied; `.bak` kept |

**Integrity checks performed:**  
- DeBERTa fixed word_attribs ≡ `reaggregate(tokens, shap_pos)` for all 327 BABE rows.  
- Gold labels consistent on shared BABE texts across models.  
- No duplicate texts within each BABE cache.

---

## 6. Leakage & protocol gaps

| Topic | Status |
|-------|--------|
| BABE test used for SHAP sampling | Expected for evaluation; do not use for threshold selection (E5) |
| Taxonomy tuning on test top-words | Undocumented risk — freeze lexicon, validate manually |
| BASIL as external test | Assumed; verify no BABE article overlap if required by reviewers (`paper.tex` L379 TODO) |
| Background from test set | Claimed in paper, not coded — do not silently add test backgrounds without disclosure |

---

## 7. Prioritized remediation checklist

### P0 — before any new experiments
- [ ] Create `requirements.txt` (+ lock) from a known-good environment  
- [ ] Recreate `.venv`; verify `import shap, transformers, datasets, sklearn, pandas, scipy`  
- [ ] Restore `models/deberta-base-babe-ft` **or** plan timed retrain  
- [ ] Obtain BASIL raw data; record URL + commit  
- [ ] Add README with run order (inference → SHAP → analyze)  
- [ ] Freeze write-protect or snapshot `outputs/` before experiments  

### P1 — scientific honesty in revision
- [ ] Correct SHAP background description in `paper.tex` L415–419 to match code  
- [ ] Run E1 Other/Unassigned; revise 90–96% claims only after  
- [ ] Scope or extend DeBERTa shared-error analyses  
- [ ] Document unpaired vs paired sentence sets explicitly  

### P2 — engineering hygiene
- [ ] Unify word aggregation + unit tests (incl. DeBERTa leading-space tokens)  
- [ ] CLI McNemar + Mann–Whitney entrypoints  
- [ ] Single `configs/models.yaml` for Hub IDs / local paths / seeds  
- [ ] Optional MPS flag for SHAP (default off until validated)  

### Acceptance for “reproducible release”
1. Fresh machine: clone → `venv` → `pip install -r` → download models → run `compute_metrics.py` matches committed CSV within tolerance.  
2. SHAP smoke: 2 sentences/model match cached `prob_pos` within 1e-5; attributions qualitatively consistent (exact SHAP match may vary by library version — document).  
3. Paper methods paragraph matches implemented masker, output space, background, aggregation, seeds.

---

## 8. Decisions required from owner (non-blocking for E1 on caches)

See executive summary in chat; key forks:

1. Restore DeBERTa checkpoint vs retrain.  
2. Fix paper background wording vs expensive SHAP recompute with explicit background corpus.  
3. Scope shared-error claims to two RoBERTa models vs generate DeBERTa shared strata.  
4. BASIL source location / license for span export.  
5. Whether 8 GB Mac-only or budget a CUDA box for E2-full / new SHAP.
