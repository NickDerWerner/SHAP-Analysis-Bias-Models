# ARR M3 — Human Validation Report

**Date:** 2026-11-10  
**Code:** `scripts/arr_m3/run_human_validation.py`  
**Raw annotations (unmodified):**  
- `outputs/arr_m2d/human_raw/basil_blind_annotations_annA.json`  
- `outputs/arr_m2d/human_raw/basil_blind_annotations_annB.json`  
**Outputs:** `outputs/arr_m3/`  
**Sample:** 120-item blind BASIL set (seed 7; 30 lex / 30 inf / 30 both / 30 non-biased)

---

## Stop-condition answers (Phase 1)

### 1. Human–human agreement

| Judgment | n (complete pairs) | Raw agree | 95% CI | Cohen’s κ |
|----------|-------------------:|----------:|--------|----------:|
| Bias present (yes/no) | 96 | 0.698 | [0.604, 0.792] | **0.350** |
| Bias type (4-way) | 96 | 0.354 | — | **0.144** |
| Needs article context | 23 | 0.478 | — | **0.153** |

Span agreement (all 120; both-empty ⇒ F1=1):

| Metric | Mean | 95% CI |
|--------|-----:|--------|
| Char soft-F1 (symmetric) | **0.473** | [0.388, 0.554] |
| Char IoU | ~0.42 | (see `hh_agreement_summary.json`) |
| Token F1 (whitespace) | ~0.49 | |

**Interpretation:** Fair binary agreement; **weak** type agreement. Lexical vs informational distinctions are hard for humans without article context. annB incomplete fields reduce usable pairs (see integrity).

### 2. SHAP–human agreement vs baselines

On sentences where the annotator marked bias **yes** with ≥1 valid span **and** a SHAP cache exists:

| Annotator | Model | n | Mean excess \|SHAP\| mass over length-matched random | 95% CI |
|-----------|-------|--:|-----------------------------------------------------:|--------|
| annA | bias-detector | 26 | **+0.121** | [+0.053, +0.191] |
| annA | DA-RoBERTa | 32 | **+0.174** | [+0.115, +0.235] |
| annA | DeBERTa | 10 | **+0.192** | [+0.112, +0.274] |
| annB | bias-detector | 22 | **+0.140** | [+0.079, +0.208] |
| annB | DA-RoBERTa | 23 | **+0.190** | [+0.113, +0.268] |
| annB | DeBERTa | 6 | **+0.177** | [+0.062, +0.295] |

Lexical-only human spans (where n≥12): excess ≈ +0.15–0.20 (CIs > 0).  
Both-type: mixed; informational-only cells underpowered in the SHAP∩sample intersection.

**Supplementary (both humans agree on present=yes and same type):** n≈7–10; excess still positive (DR ≈ +0.24–0.26) but small-n.

**Cache coverage of the 120-item sample:** BD 34, DR 42, DeBERTa 12. SHAP–human claims are **conditional on this intersection**, not the full 120.

### 3. Do BASIL gold-alignment findings replicate with new annotators?

**Partially, with important caveats.**

| Check | Result |
|-------|--------|
| SHAP excess over random vs **new human** spans | Yes — positive, CI excludes 0 (similar qualitative story to M2C lexical) |
| Humans agree with BASIL binary | Moderate (A κ=0.20; B κ=0.43) |
| Humans agree with BASIL type | Low–moderate (κ≈0.22–0.26) |
| Both humans disagree with BASIL binary | 13 sentences |
| Both disagree on type | 35 sentences |

Humans often mark BASIL informational items as `none` (especially annA: 18 cases). BASIL is **not** treated as infallible; independent humans and BASIL are related but distinct evidence sources.

### 4–7. See final M3 assessment in the claim ledger / stop section below and companion docs.

---

## Step 1 — Integrity

### Schema (both files)

List of 120 objects with keys:  
`annotator_id`, `item_id`, `canonical_id`, `bias_present`, `bias_type`, `spans` (`start`,`end`,`text`), `needs_context`, `uncertainty`, `comments`.

### Checks

| Check | annA | annB |
|-------|------|------|
| n items / unique IDs | 120 / 120 | 120 / 120 |
| Match sample IDs + canonical_id | OK | OK |
| Span text == `sentence[start:end]` | **114/114 OK** | **64/64 OK** |
| Offset convention | Unicode code points; **0 non-BMP** chars ⇒ JS UTF-16 ≡ Python | same |
| Duplicate IDs | 0 | 0 |
| Issues | **none** | **31 `yes_without_spans`**, 1 `type_without_present` |
| Empty `bias_present` | 0 | **24** |
| Empty `needs_context` | 93 | 17 |

**Policy:** Missing labels excluded from κ/raw agreement denominators. `yes` without spans kept for presence/type stats but **excluded** from span and SHAP–human analyses. Source JSON **never modified**.

Artifacts: `annotation_integrity.json`, `annotation_integrity_issues.csv`.

---

## Step 2 — Human–human (detail)

**Missing handling:** Pairwise complete-case for categorical κ. Spans: empty∩empty = perfect agree; empty vs non-empty = F1 0.

Confusion (present, n=96): both-yes 50, both-no 17, A-yes/B-no 4, A-no/B-yes 25 (B more liberal on “yes”).

Type κ is low; many lexical↔both and informational↔none swaps. Context field sparsely filled (especially A) → underpowered.

---

## Step 3 — Human vs BASIL

| Annotator | n complete present | Bin agree | κ_bin | n complete type | Type agree | κ_type | Span F1 mean |
|-----------|-------------------:|----------:|------:|----------------:|-----------:|---------:|-------------:|
| annA | 120 | 0.625 | 0.204 | 119 | 0.445 | 0.261 | 0.393 |
| annB | 96 | 0.802 | 0.431 | 97 | 0.412 | 0.221 | 0.379 |

Both humans disagree with BASIL: 13 binary + 35 type cases (`both_humans_disagree_basil.csv`). Mix of genuine judgment differences (esp. informational / context-dependent) vs annotation strictness — not offset bugs (spans validated).

---

## Step 4 — SHAP vs human

Method (per annotator, no span fusion):

- Align SHAP words via M2B `offset_alignment`
- Abs / pos mass in human spans; AP where eligible
- 20 length-matched random-span baselines (seeded)
- Sentence-level bootstrap CIs
- Paired BD−DR where both caches exist

**Main finding:** SHAP places more absolute attribution mass in independently annotated human evidence spans than length-matched random spans (CIs exclude 0 for BD/DR on both annotators). This **replicates the M2C lexical plausibility pattern** against a new evidence source, with smaller n.

**Limitations:** Sparse cache∩sample; annB missing spans; DeBERTa n≤10; informational human types rare in intersection; no span adjudication / fusion.

---

## Concise interpretation

1. Independent humans show **modest** reliability on binary bias and **weak** agreement on lexical/informational type — so type-stratified human claims need caution.  
2. Despite that, SHAP **still** aligns with each annotator’s evidence spans above chance on available caches.  
3. BASIL and new humans are only partially aligned; use both as complementary, not identical, targets.  
4. Do **not** claim high human consensus on informational bias or that SHAP recovers BASIL informational spans well.

---

## Artifact index

```
outputs/arr_m3/
  annotation_integrity.json|.csv
  hh_agreement_summary.json
  hh_confusion.csv
  hh_span_by_item.csv
  human_vs_basil_*.csv|json
  both_humans_disagree_basil.csv
  shap_sample_coverage.json
  shap_vs_human_by_item.csv
  shap_vs_human_summary.csv
```
