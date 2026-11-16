# M4A-8b Change Record — Sampling & Evaluation-Population Consolidation

**Date:** 2026-11-15  
**File:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** `\subsection{Stratified Sampling Strategy}`, `Table~\ref{tab:eval_populations}` (+ caption), `\subsection{Analysis Framework}`  
**Not edited:** Faithfulness, gold-span, human, stats, metrics, aggregation, Dataset, Results, appendices.

---

## Word counts (≈ prose tokens)

| Unit | Before | After | Δ |
|------|-------:|------:|--:|
| Stratified Sampling Strategy (incl. table text) | ≈410 | ≈361 | **−49** |
| Analysis Framework | ≈190 | ≈200 | **+10** |
| Methodology total | ≈3133 | ≈3094 | **≈−39** |

Full 1900–2200 target **not** complete. Analysis Framework gained brief pairing/calibration caveats (scientific clarity > raw cut).

---

## Scientific distinctions preserved (verified)

| Fact | Source |
|------|--------|
| $t{=}0.5$ TP/FP/TN/FN | caches; consistency check |
| BABE full 1000; BASIL 7984 | metrics / CSV |
| BABE SHAP 337 / 312 / 327 unpaired | `shap_samples*.jsonl`; M1 coverage |
| BABE ∩ DR 127; all3 59 | `babe_coverage.csv` |
| BASIL 850 / 837 / 400; not flat 100/cell for BD/DR | caches; `basil_shap_generate.py` |
| BD∩DR 371; all3 60 | `basil_coverage.csv` |
| Faithfulness paired 200, TN=3 | M2B (detail in §faithfulness) |
| Gold-span eligible positives | table points to §; M2C 475/467/200 |
| Human blind 120; SHAP∩ 34/42/12 **separate** | caption + M3R |
| Seed 7 | sampling scripts |
| No magnitude=calibration; no shared-mechanism claim | Analysis Framework |
| Matched-pool p75 retained | Analysis Framework + appendix |

---

## Table changes

- Four columns: Analysis / Data / Models / $n$ design.  
- Caption defines BD, DR, Deb; defines paired; clarifies SHAP∩ ≠ 120.  
- Removed long cell prose; cell-level faithfulness strata left to Section~\ref{sec:faithfulness_protocol}.

---

## Removed / deferred (not deleted from research record)

| Detail | Disposition |
|--------|-------------|
| Explicit BABE per-cell tuples (100/37/100/100 etc.) | Deferred appendix / recoverable from caches; prose notes FP scarcity |
| Named BASIL strata list (magnitude_*, bias_type_*, fp_shared, …) | **Pending appendix** |
| Downstream “protocols appear in …” duplicate pointer ¶ | Folded into table caption + one sentence |

---

## TODOs

| ID | Action |
|----|--------|
| T12 | Already resolved (M4A-7); retained |
| T13, T14 | **Unchanged** (still in Analysis Framework; deferred to M4A-8d/e) |

Surrounding Analysis Framework prose no longer endorses Em/Ev as validated or SHAP magnitude as calibration.

---

## Verification

- Key numbers present in edited chunk: 337, 312, 327, 850, 837, 400, 200, TN=3, 120, 34/42/12, 371, 127, 59.  
- Brace balance 0.  
- Compile: **UNVERIFIED**.  
- Diff scope: Sampling + table + Analysis Framework only.

---

## Next recommended module

**M4A-8c** — Stats/Metrics cross-ref cleanup (or **M4A-8d** T13 retraction if conceptual clarity is prioritized).
