# ARR M4D-2 — Abstract, Conclusion, and Title Assessment

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** `abstract` environment + `\section{Conclusion}` only.  
**Title:** Assessment and proposals only — **not edited**.  
**Status:** Complete (author review).

---

## LaTeX locations edited

| Region | Approx. lines (post-edit) | Change |
|--------|---------------------------|--------|
| `\begin{abstract}` … `\end{abstract}` | ~155–177 | Full rewrite; `\revnote{TODO P0 \| Abstract}` → `% RESOLVED M4D-2 \| T01` |
| Keywords | ~180–181 | Retuned to explanation-evaluation framing |
| `\section{Conclusion}` | ~1446–1481 | Full rewrite; `\revnote{TODO P0 \| Conclusion}` → `% RESOLVED M4D-2 \| T27` |
| `\title{...}` | L84 | **Unchanged** |

No edits to Introduction, Related Work, Methodology, Results, Discussion, Limitations, Ethics, Appendices, or References.

---

## Word counts (approx.; comments / LaTeX macros stripped)

| Block | Before | After | Δ |
|-------|-------:|------:|--:|
| Abstract | ~196 | ~177 | −19 |
| Conclusion | ~220 | ~255 | +35 |

Conclusion is slightly longer because it answers the four Intro RQs with section anchors; still compact relative to ACL page budget.

---

## Evidence mapping (Abstract / Conclusion → Results)

| Claim | Scope | Source |
|-------|-------|--------|
| A_pos $k{=}2$: ΔP ≈ −0.33 (BD), −0.29 (DR); > random / low-\|SHAP\| | Paired BASIL $n{=}200$; BD/DR only | `\ref{sec:faithfulness_results}` / M2B / M4B-1 (−0.327 / −0.293) |
| Lexical gold mass > length-matched random; coverage match removes naive lex−inf gap (BD/DR) | BASIL gold-span analyses | `\ref{sec:gold_span_results}` / M2C–M2D / M4B-2 |
| Binary κ≈0.44; type κ≈0.24; SHAP > random on human spans in cache∩ | Blind $n{=}120$; SHAP–human on BD/DR intersections | `\ref{sec:human_results}` / M3R / M4B-3 (κ 0.439 / 0.238) |
| Paired top-\|SHAP\| overlap on shared errors = descriptive Jaccard | Matched BD–DR inputs | `\ref{sec:paired_similarity}` / M1 / M4B-4 |
| Not internal reasoning / not shared mechanisms / no formal calibration | Framing + Limitations echo | Intro RQs; Discussion; Conclusion caveats |

**Not claimed:** DeBERTa faithfulness; strong DeBERTa human-validation; Em/Ev dominance; independent pathways; magnitude-as-calibration; SOTA classification.

---

## Removed unsupported claims

From Abstract and Conclusion:

- Emotional/Evaluative 90–96% / 90–98% dominance  
- Same-mechanism detection with calibration-level differences  
- Intermediate calibration point / TN calibration axis  
- Independent lexical vs.\ informational detection pathways (2.4 pp claim)  
- 7.2× / 1.4× error-overlap-as-mechanism framing  
- Architecture primarily affecting calibration rather than linguistic signals  
- “Stronger internal evidence” / causal fidelity language  

Preserved only as **negations** where needed (e.g., “no formal predictive-calibration analysis”; “not identical mechanisms”).

---

## Title assessment (no manuscript edit)

**Current title:**  
`Explaining News Bias Detection: A Comparative SHAP Analysis of Transformer Model Decision Mechanisms`

**Assessment:** Overstates recoverability of “decision mechanisms.” The revised paper evaluates explanation *properties* (sensitivity, span/human alignment, descriptive overlap), not mechanisms inside the models. “Comparative SHAP analysis” alone undersells the evaluation protocol and can read as a visualization study.

### Ranked alternatives

| Rank | Proposed title | Rationale |
|-----:|----------------|-----------|
| **1** | Evaluating SHAP Explanations for News Bias Detection: Prediction Sensitivity and Human Evidence Alignment | Precise; matches RQs 1–3; ACL-suitable; does not claim mechanisms |
| **2** | Beyond Heatmaps: Evaluating SHAP Attributions for Transformer News-Bias Classifiers | Concise gap framing; slightly vaguer on which checks |
| **3** | SHAP Explanations for News Bias Detection: Sensitivity, Evidence Alignment, and Cross-Model Overlap | Faithful to all four RQs; longer; “overlap” still needs “descriptive” reading in abstract |

**Recommendation:** Prefer **#1** if authors want a single replacement. Do **not** change `\title` until separate approval.

---

## Remaining manuscript-wide inconsistencies (out of M4D-2 scope)

| Location | Issue |
|----------|-------|
| Related Work TODOs (T05/T06) | Decoder cites / faithfulness positioning still open |
| Intro comment after contributions | Still says “Abstract/Conclusion TODOs remain” (stale comment; Intro frozen this module) |
| Appendix | Residual calibration / pathway narrative in appendix prose (T30) |
| Ethics T29 | Consent/IRB/pay/licenses still unverified |
| Section order | Conclusion currently precedes Limitations (pre-existing; not rearranged here) |

---

## TODOs

| ID | Status |
|----|--------|
| **T01** Abstract | **Resolved** |
| **T27** Conclusion | **Resolved** |
| Title change | **Open** (proposals only) |
| T05/T06 Related Work | Open |
| T29 Ethics residual | Open |
| T30 Appendix/presentation | Open |

---

## Compilation

**UNVERIFIED** — no `pdflatex` / `xelatex` / `latexmk` available in the local environment.

---

## Diff scope confirmation

Edits limited to Abstract (+ keywords) and Conclusion. Title line unchanged.
