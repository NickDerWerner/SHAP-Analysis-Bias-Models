# ARR Codebase Audit

**Repository:** SHAP-Analysis-Bias-Models  
**Paper:** *Explaining News Bias Detection: A Comparative SHAP Analysis of Transformer Model Decision Mechanisms*  
**Audit date:** 2026-10-20  
**Scope:** Repository inventory + scientific audit (Steps 1–2). No caches, results, or conclusions were modified.

**Legend:** **Verified** = confirmed in source/artifacts; **Assumption** = inferred but not proven; **Missing** = code/artifact absent.

---

## 1. Repository inventory

### 1.1 Layout and entry points

| Path | Role |
|------|------|
| `analysis.py` | Primary BABE SHAP pipeline (TP/FP/TN sampling + SHAP) |
| `babe_shap_fn.py` | Appends FN SHAP records to BABE caches |
| `basil_shap_generate.py` | BASIL SHAP generation (resumable JSONL) |
| `basil_shap_analyze.py` | Fast analysis over BASIL SHAP caches |
| `basil_eval.py` | Shared BASIL join + view definitions + model registry |
| `run_inference.py` | Full-corpus BASIL probability inference |
| `finetune_deberta_babe.py` | Fine-tune `microsoft/deberta-base` on BABE |
| `preprocess_basil.py` | Flatten raw BASIL → `basil_sentences.csv` |
| `babe_fig6_confound.py` | Matched-pool / taxonomy / bootstrap (Figure 6 confound) |
| `threshold_sweep.py`, `compute_metrics.py` | BASIL metrics / threshold tables |
| `scripts/*` | Figure regeneration, Mann–Whitney, DeBERTa fix, parity checks |
| `analysis.ipynb`, `research_analysis.ipynb`, `model_performance_comparison.ipynb`, `generate_figure1.ipynb` | Interactive / historical analysis |
| `docs/references/paper.tex` | Manuscript (line-numbered source of truth for revision) |
| `docs/references/ARR_Reviews.txt` | ARR May 2026 reviews + supervisor notes |

**Missing (Critical for reproducibility):**
- No `README.md`
- No `requirements.txt` / `environment.yml` / `pyproject.toml` / lockfile
- No project `.venv` on this machine (scripts assume `.venv/bin/python`)
- No `models/` directory (gitignored; DeBERTa checkpoint absent locally)

### 1.2 Models: load and configuration

| Suffix | Identifier | Registry |
|--------|------------|----------|
| `biasdetector` (empty BABE suffix) | `himel7/bias-detector` | `basil_eval.py` L30–34; `analysis.py` default L443 |
| `daroberta` | `mediabiasgroup/DA-RoBERTa-BABE-FT` | `basil_eval.py` L32; note Hub casing vs `da-roberta-babe-ft` in `MODEL_COMPARISON_SETUP.md` |
| `deberta` | `./models/deberta-base-babe-ft` | `basil_eval.py` L33; trained by `finetune_deberta_babe.py` (`MODEL_ID = "microsoft/deberta-base"`, L40) |

**DeBERTa training hyperparameters (Verified — `finetune_deberta_babe.py`):**
- Epochs 3, batch 16, lr 2e-5, weight decay 0.01, warmup 0.1, max length 256, seed 42
- 10% stratified val split from BABE train; best checkpoint by `f1_macro`
- Labels: `{0: Non-biased, 1: Biased}` (L132–133)
- Data: HF `mediabiasgroup/BABE` train/test parquet via `hf_hub_download` (L45–47, L52–54)
- MPS fallback env set (L109); DeBERTa-v3 abandoned due to MPS NaN (`OVERNIGHT_RUN_SUMMARY.md`)

**Device selection inconsistency (Verified):**
- `run_inference.py` L34–39: prefers **MPS → CUDA → CPU**
- `analysis.py` L470, `basil_shap_generate.py` L487: **CUDA if available else CPU** (no MPS)
- Implication on Apple Silicon: SHAP generation runs on CPU even when MPS works for inference

### 1.3 Datasets and labels

| Dataset | Source in code | Labels / views |
|---------|----------------|----------------|
| BABE | HF `mediabiasgroup/BABE`, split `test` (`analysis.py` L446–447, L483) | Binary via `normalize_label_values` (L112–143); threshold 0.5 (L501) |
| BASIL | Preprocessed `basil_sentences.csv` (7,984 rows) | Sentence-level `biased`, `has_lex`, `has_inf`, `has_both_types`, `quote_status` (`preprocess_basil.py` L11–28, L59–85) |
| BASIL views | `basil_eval.view_filters` L64–72 | full, lex-only, inf-only, both-types, quote-excluded, quote-only |

**Raw BASIL:** `preprocess_basil.py` expects `../BASIL/articles` + `../BASIL/annotations` (L8, L31–36). **Not present** on this machine. Phrase-level spans are collapsed to sentence flags; **character offsets are not stored** in `basil_sentences.csv`.

### 1.4 SHAP implementation (Verified)

| Aspect | Implementation | Location |
|--------|----------------|----------|
| Explainer | `shap.Explainer(predict_fn, masker)` (Partition explainer for Text masker) | `analysis.py` L527–538; `basil_shap_generate.py` L373–374 |
| Masker | `shap.maskers.Text(tokenizer)` — **no explicit background corpus passed** | same |
| Model output | Softmax **probabilities** over classes (`softmax_np` on logits) | `analysis.py` L106–109, L368–391 |
| Explained class | Column `positive_index` of probability vector | L555–558 |
| Background | Library default for `Text` masker (mask-token occlusion), **not** a “background dataset of test-set sentences” | Paper L415–419 **mismatches** code |
| Aggregation (BABE `analysis.py`) | `aggregate_subword_shap_to_words` — `Ġ`/`▁` + heuristic splits | L257–353 |
| Aggregation (BASIL / FN scripts) | Whitespace-aware copy (trailing/leading spaces) | `basil_shap_generate.py` L86–191 |
| DeBERTa post-hoc fix | Char-span reaggregation over tokens+`shap_pos` | `scripts/fix_deberta_word_aggregation.py` L31–65 |

**Paper vs code (High):** Paper claims TextExplainer + “background dataset of test-set sentences” (`paper.tex` L415–419). Code uses generic `shap.Explainer` + `Text(tokenizer)` with no background sample list.

### 1.5 Caches and outputs

| Artifact | Contents |
|----------|----------|
| `outputs/shap_samples.jsonl` | BABE bias-detector, 337 records (100/37/100/100 TP/FP/TN/FN) |
| `outputs/shap_samples_daroberta.jsonl` | 312 (100/12/100/100) |
| `outputs/shap_samples_deberta.jsonl` | 327 (100/27/100/100); `.bak` = pre-fix aggregation |
| `outputs/basil_shap/samples_{biasdetector,daroberta,deberta}.jsonl` | 850 / 837 / 400 records |
| `outputs/basil_shap/manifest.csv` | Stratum assignments with sentence keys |
| `outputs/basil/predictions_*.csv` | Full BASIL probs/preds for all 3 models |
| Record schema (BABE) | `text, gold, pred, prob_pos, tokens, shap_pos, word_attribs` |

Load timing (this machine): BABE caches ~0.04 s; BASIL caches ~0.08 s.

### 1.6 Linguistic categories

**Canonical function:** `categorize_word` in `babe_fig6_confound.py` L143–199 (also used by `basil_shap_analyze.py` L22; `scripts/babe_fp_partition.py`).

**Decision order (Verified):**
1. Explicit Bias Terms — substring match on small set (L146–151)
2. Framing/Reporting Verbs — exact membership (L153–163)
3. Function/Temporal Words — exact membership (L165–181)
4. Emotional/Evaluative — substring on small list **or** `-less`/`-ful` suffix (L183–197)
5. **Else → `Emotional/Evaluative`** (L199) ← catch-all

### 1.7 Top-K, matched-pool, shared-error, stats

| Analysis | Code | Notes |
|----------|------|-------|
| Top-K proportions | `babe_fig6_confound.top_k_proportions` L212–215; `step2_sensitivity` L252–266 | |
| Matched-pool / p75 | `step3_matched_pools` L321–365; FP partition in `basil_shap_analyze.build_fp_partition_csv`; `scripts/babe_fp_partition.py` L96–127 | |
| Shared FP Jaccard | `basil_shap_analyze.median_pairwise_jaccard` L122–138 | BD↔DR only |
| Mann–Whitney | `scripts/shap_mannwhitney.py` | |
| McNemar | **Only** `model_performance_comparison.ipynb` (~cell “McNemar's Test”) | No CLI module |
| Bootstrap CIs | `babe_fig6_confound.bootstrap_proportions` L370–384 | |

### 1.8 Regenerability

| Component | Regenerable from release? |
|-----------|---------------------------|
| BABE SHAP caches | Needs HF models + `shap` + BABE test; seed 7 documented |
| BASIL predictions | Needs models + `basil_sentences.csv` |
| DeBERTa checkpoint | **Missing locally**; retrain via `finetune_deberta_babe.py` (~6 min MPS historically) or restore from release artifact |
| BASIL gold spans | Needs raw BASIL clone; **not** recoverable from CSV alone |
| Exact package versions | **Missing** pin file |

---

## 2. Scientific audit (A–I)

### A. Emotional/Evaluative as catch-all — **Critical / Verified defect**

`categorize_word` returns `'Emotional/Evaluative'` for every residual token (`babe_fig6_confound.py` L199).

Audit estimate (all word_attribs; introduce explicit Other/Unassigned instead of final return):

| Cache | Current Em/Eval | True Em/Eval (list+suffix) | Would be Other |
|-------|-----------------|----------------------------|----------------|
| BABE bd | 64.9% | 0.5% | **64.3%** |
| BABE dr | 63.6% | 0.5% | **63.1%** |
| BABE deb | 63.2% | 0.6% | **62.6%** |
| BASIL bd/dr/deb | ~63% | ~0.3% | **~63%** |

Among **top-K by mean |SHAP|** (TP, BABE), current Em/Eval remains 93–100%, but with Other fallback Other is **30–91%** depending on K/model — i.e. the headline **90–96% Emotional/Evaluative** (`paper.tex` L157, L881–883) is largely an artifact of the default bucket.

### B. Token→word aggregation / additivity — **High / Verified mixed**

| Model / path | Status |
|--------------|--------|
| RoBERTa-family BABE/BASIL (whitespace-aware aggregator) | Summation of token SHAP into words; tokens often include trailing spaces (`'A '`, `'push '`) |
| DeBERTa pre-fix (`analysis.py` aggregator) | **Broken**: DeBERTa tokens use leading spaces (`' has'`); ignored → phrase collapse (~12.7 words/sent vs ~31 after fix) |
| DeBERTa post-fix (`fix_deberta_word_aggregation.py`) | Reaggregate matches stored word_attribs 327/327; alnum alignment to source text OK on sample; **whitespace characters absorb ~15–22% of |token SHAP| mass and are dropped from word sums** → word-sum ≠ token-sum |

Paper claims additivity preserved (`paper.tex` L442). For DeBERTa post-fix, additivity holds vs **non-space** char mass only, not full `shap_pos`.

**Paper numbers vs fix:** Overnight summary + `outputs/DEBERTA_PAPER_PARITY.md` report post-fix medians (TP≈0.028). Pre-fix bak medians ≈0.17. **Current paper magnitude claims for DeBERTa are post-correction.**

### C. Classification vs SHAP output space — **Low / Verified consistent**

Inference and SHAP both use softmax probabilities; SHAP explains the positive-class probability (`build_predict_fn`). Thresholding at 0.5 uses the same `prob_pos`. No logit-space SHAP found.

### D. Same sentences vs model-dependent samples — **Critical / Verified for BABE magnitude**

BABE caches are **independently stratified per model** (`analysis.py` `stratified_sample` L411–438). Unique-text overlap:

| Intersection | Count |
|--------------|-------|
| bd ∩ dr ∩ deb | **59** |
| TP ∩all3 | 7 |
| FP ∩all3 | 3 |
| TN ∩all3 | 4 |
| FN ∩all3 | 26 |

Cross-model magnitude/category comparisons that treat pools as interchangeable are **not** paired on the same sentences (except analyses that explicitly intersect texts, e.g. BABE FP partition by text in `scripts/babe_fp_partition.py` L54–67, and BASIL `fp_shared` / `fn_shared_lex` in `basil_shap_generate.py` L293–306).

### E. Three-model consistency — **High / Verified gaps**

| Analysis | DeBERTa included? |
|----------|-------------------|
| BABE SHAP caches / Fig 3 facet | Yes |
| BASIL magnitude CSV (1200 rows) | Yes (400) |
| BASIL `fp_shared` / `fn_shared_lex` / bias_type strata | **No** — generate only magnitude for deberta (`basil_shap_generate.py` L316–328; overnight L161–165) |
| `basil_shap_analyze.SUFFIXES` | **Only** `biasdetector`, `daroberta` (L30) |
| Fig 6 / BABE FP partition taxonomy | BD+DR primarily |
| McNemar notebook | Historically two-model |

Reviewer k62P’s note that DeBERTa is unevenly included is **code-accurate**.

### F. Caches for confidence-controlled comparisons — **Medium / Partially ready**

- `prob_pos` present on every SHAP record → confidence binning / matching **possible without recomputing SHAP** for cached sentences.
- Cross-model **paired** confidence matching needs overlapping texts; BABE triple overlap is small (59). BASIL shared-FP pairs exist for BD↔DR (100). DeBERTa lacks shared-FP SHAP strata.
- Empirical corr(prob, mean|SHAP|): bd 0.12, dr 0.42, deb 0.26 — magnitude is related to confidence but not a deterministic identity (addresses reviewer concern partially).

### G. BASIL gold lexical/informational spans — **Critical / Missing locally**

- CSV retains type flags and span **counts**, not offsets/text of spans (`preprocess_basil.py` L59–85).
- Raw corpus path `../BASIL` absent → **cannot** run gold-span alignment (E3) without re-acquiring BASIL.
- Span `id` field is sentence index (`p0`, …), not character offset (L47–56). Assumption: original JSON likely contains span surface forms; need corpus to confirm offset fields.

### H. Leakage — **Medium / Potential risk**

| Risk | Assessment |
|------|------------|
| SHAP on BABE **test**; DeBERTa trained on BABE train with internal val | OK if test never used for threshold/taxonomy tuning |
| Paper/code use test predictions at t=0.5 for TP/FP definitions | Standard for reporting; **must not** use test labels to pick validation thresholds (ARR plan) |
| Background claimed as “test-set sentences” | Not implemented; if later added from test, document carefully |
| Taxonomy lexicons built by inspecting model top words | **Potential circularity** (list in L183–190 looks SHAP-derived); not documented |

### I. Do claimed metrics match code? — **High / Mixed**

| Claim | Code support |
|-------|--------------|
| Matched-pool p75 category % | Yes (`babe_fig6_confound`, FP partition scripts) |
| Shared FP top-20 Jaccard ~0.81 | Yes (`basil_shap_summary.md` L96–97; analyze L122–138) |
| Mann–Whitney magnitudes | Yes (`scripts/shap_mannwhitney.py`) |
| McNemar | Notebook only; not a reproducible CLI |
| 90–96% Em/Eval | Numerically produced by catch-all taxonomy — **methodologically invalid as linguistic claim** |
| “Background of test sentences” | **Not implemented** |
| Three calibration levels on TN | Uses model-specific sampled sets + post-fix DeBERTa; directionally in caches but confounded by unpaired sampling + confidence |

---

## 3. Severity register (headline risks)

| ID | Issue | Severity | Type |
|----|-------|----------|------|
| T1 | Em/Eval catch-all drives 90–96% claim | **Critical** | Verified defect |
| S1 | BABE cross-model analyses mostly unpaired sentences | **Critical** | Verified defect |
| B1 | Paper background-dataset description ≠ code | **High** | Verified discrepancy |
| D1 | DeBERTa word aggregation: fixed for means, residual mass on spaces | **High** | Verified defect (partial) |
| M1 | DeBERTa excluded from shared-error / analyze SUFFIXES | **High** | Verified gap |
| G1 | Raw BASIL + span offsets unavailable | **Critical** (for E3) | Missing artifact |
| R1 | No env pin; no local DeBERTa checkpoint; no README | **Critical** (repro) | Missing |
| C1 | Confidence–magnitude confounding of “calibration” narrative | **High** | Potential risk (reviewer-aligned) |
| A1 | Divergent aggregators (`analysis.py` vs `basil_shap_generate.py`) | **Medium** | Verified defect |
| L1 | Taxonomy may be reverse-engineered from SHAP tops | **Medium** | Potential risk |
| K1 | McNemar only in notebook | **Medium** | Gap |
| V1 | `.venv` / deps missing on audit machine | **High** (ops) | Missing |

---

## 4. Prioritized checklist (acceptance criteria)

1. **Freeze artifacts:** Do not overwrite `outputs/**/*.jsonl` or predictions; copy-on-write for any reanalysis.  
2. **Document taxonomy decision list + Other estimate** (this audit) → implement E1 without mutating published CSVs until validated.  
3. **Restore env:** recreate `.venv`, pin versions, restore DeBERTa checkpoint from release or retrain with logged seed.  
4. **Acquire raw BASIL** for span experiment; keep CSV as sentence view.  
5. **Paired-sentence analysis path** for E4 before new SHAP.  
6. **Faithfulness pilot (E2)** on 20 sentences before full run.

See also: `ARR_EXPERIMENT_PLAN.md`, `ARR_HARDWARE_ASSESSMENT.md`, `ARR_REPRODUCIBILITY_GAPS.md`.
