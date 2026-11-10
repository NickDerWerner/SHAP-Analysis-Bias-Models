# ARR M3 — Reproducibility Check

**Constraint:** No SHAP regeneration; no retraining. Document what exists.

---

## 1. Environment (this machine / `.venv`)

| Component | Version / note |
|-----------|----------------|
| OS | macOS (darwin), Apple Silicon M1 8GB |
| Python | 3.12.13 |
| torch | 2.14.1 |
| transformers | 5.20.2 |
| numpy | 2.5.4 |
| pandas | 3.0.6 |
| matplotlib | (in requirements-arr-m2.txt) |
| scipy | 1.18.1 |
| **shap** | **Not installed in current `.venv`** — SHAP values consumed from **precomputed caches** |
| scikit-learn | Not installed (κ implemented locally) |

Pinned analysis deps: `requirements-arr-m2.txt`.  
**Gap:** Document the original SHAP generation environment (library version, Text masker settings) from prior logs/caches; current venv alone cannot regenerate attributions.

---

## 2. Models

| Model | Role | Availability |
|-------|------|----------------|
| bias-detector | Primary | Local / HF as used for caches |
| DA-RoBERTa-BABE-FT | Primary | Local / HF as used for caches |
| DeBERTa-base (BABE-FT) | Secondary | Checkpoint cited in paper; uneven cache coverage |

**Action for rewrite:** List exact HF repo IDs + commit/revision hashes and local cache digests in a model card appendix. Do not claim three-model symmetry where DeBERTa was excluded (M2B faithfulness).

---

## 3. Datasets

| Dataset | Version | Notes |
|---------|---------|-------|
| BASIL | `launchnlp/BASIL` @ `4fdbc4f` | M1: 7984/7984 sentence match; 1723 spans valid |
| BABE | As in original project CSVs | Licensing: follow dataset terms; paper checklist noted license discussion incomplete |
| Human sample | Seed 7, 120 items | `outputs/arr_m2c/human_annotation_sample.csv` (+ GOLD for analysts only) |
| Human annotations | annA, annB JSON | `outputs/arr_m2d/human_raw/` — immutable |

---

## 4. SHAP configuration (from code + reports)

| Setting | Documented value |
|---------|------------------|
| Explainer | SHAP TextExplainer + Text masker |
| Output space | Probability of biased class (faithfulness also reports logit margin separately) |
| Aggregation | Token → word via offset alignment (M2B); additive property for sum |
| Background / reference | Paper TODO: must state background sentence set explicitly in rewrite |
| Seeds | Analysis seed **7** (sampling, bootstrap, baselines) |

**Gaps (must fix in manuscript text):** exact background set, masker token, output space confirmation, library version used at generation time.

---

## 5. Token-to-word integrity

- M2B offset alignment: 100% complete budgets on medium eval; tests in `tests/test_offset_alignment.py`.  
- DeBERTa: word_attribs usable for ranking; whitespace mass is diagnostic, not silent content loss (M1).  
- Human span offsets: validated against source text; 0 non-BMP ⇒ no UTF-16 conversion needed.

---

## 6. Cached artifact provenance

| Artifact | Path | Regenerated in M3? |
|----------|------|--------------------:|
| BASIL SHAP JSONL | `outputs/basil_shap/` | No |
| M2B faithfulness | `outputs/arr_m2b/` | No |
| M2C gold alignment | `outputs/arr_m2c/` | No |
| M2D robustness | `outputs/arr_m2d/` | No |
| Human raw | `outputs/arr_m2d/human_raw/` | No (read-only) |
| M3 analysis | `outputs/arr_m3/` | Yes (derived only) |

---

## 7. Reproducibility blockers (rewrite-relevant)

| ID | Blocker | Severity | Mitigation |
|----|---------|----------|------------|
| R1 | `shap` absent from current venv / pin missing | Medium | Pin historical shap version; document that results use caches |
| R2 | Background set underspecified in paper.tex | High (reviewer) | Write exact protocol from generation scripts if recoverable |
| R3 | Model revision hashes not frozen in one place | Medium | Add `MODEL_CARD.md` / appendix table |
| R4 | BABE/BASIL license wording incomplete in checklist | Low–Med | Fix B2 in camera-ready |
| R5 | annB incomplete annotations | Medium (human study) | Report missingness; do not impute |
| R6 | Paraphrase disentangling not run | Low for core claims | Explicit future work |

**None of R1–R6 block starting a careful rewrite** if claims are scoped to cached evidence and missingness is disclosed.
