# ARR M4D-1 — Introduction and Contributions Revision

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** `\section{Introduction}` only (through start of Related Work).  
**Status:** Complete (author review).

---

## Word counts (approx., comments stripped)

| | Words |
|--|------:|
| Before | 778 |
| After | ~590 |
| Δ | ≈ −188 |

---

## Revised research questions → Results anchors

| RQ | Answered in |
|----|-------------|
| 1. High-\|SHAP\| masking vs controls | `\ref{sec:faithfulness_results}` (M4B-1) |
| 2. Gold-span mass vs random + coverage | `\ref{sec:gold_span_results}` (M4B-2) |
| 3. Human IAA + SHAP–human | `\ref{sec:human_results}` (M4B-3) |
| 4. Paired attribution overlap | `\ref{sec:paired_similarity}` (M4B-4) |

---

## Revised contributions → evidence

| Contribution | Evidence |
|--------------|----------|
| 1. Perturbation sensitivity (BD/DR) | M2B / M4B-1 |
| 2. BASIL lex/inf + random + coverage match | M2C–M2D / M4B-2 |
| 3. Two-annotator study + SHAP–human | M3R / M4B-3 |
| 4. Paired descriptive overlap | M1 / M4B-4 |

---

## Removed from Introduction

- Emotional/Evaluative 90–98% / “similar lexical content” dominance  
- Same-mechanism / different-calibration thesis  
- Magnitude-as-calibration; “intermediate calibration level”  
- Independent lex/inf detection pathways (2.4 pt claim as mechanism)  
- Overclaiming three-model equal analysis as primary  
- Figure caption “Same evidence, different calibration”  
- Intro `\revnote`s (shared-example; RQs; contributions)

**Figure~1 retained** with qualified caption (illustrative paired FP; not causal/calibration proof).

---

## Remaining contradictions (not edited)

| Location | Issue |
|----------|-------|
| Abstract | Still Em/Ev 90–96%, Jaccard 81%, same-mechanism, pathways |
| Conclusion | Still Em/Ev 90–98%, calibration axis, same-mechanism |
| Related Work TODOs | Decoder LLM cites; faithfulness positioning (T05/T06) |

---

## TODOs

| ID | Status |
|----|--------|
| Intro RQs / contributions (T03/T04 audit) | **Resolved** |
| Shared-example Intro note (T02) | **Resolved** (qualified caption) |
| **T01** Abstract | **Open** |
| **T27** Conclusion | **Open** |

---

## Diff scope

Introduction only. No Abstract/Title/Related Work/Methods/Results/Discussion/Limitations/Ethics/Conclusion/Appendix edits.

---

## Compilation

**UNVERIFIED**.
