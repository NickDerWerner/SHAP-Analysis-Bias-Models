# M4A-8d Change Record — Retire Unsupported Linguistic Taxonomy (Methods)

**Date:** 2026-11-15  
**File:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** `\subsection{Analysis Framework}` only (taxonomy clarification; T13 Methods `\revnote` removed).  
**Not edited:** Results, Abstract, Intro, Related Work, Conclusion, Limitations, Ethics, appendices, other Methods subsections.

---

## Problem verified (implementation)

| Fact | Evidence |
|------|----------|
| Legacy residual → Emotional/Evaluative | `categorize_word_legacy` returns `"Emotional/Evaluative"` for unmatched tokens (`scripts/arr_m1/taxonomy.py`) |
| v2 residual → Other/Unassigned | `categorize_word_v2` |
| Legacy p75 Em/Ev ~96–98%; v2 Em/Ev ~2–4%, Other ~94–97% | `outputs/arr_m1/taxonomy/headline_p75_comparison.csv` |
| 90–96% Em/Ev claim invalid | M1 validation report; claim ledger **Remove** |
| BASIL lex/inf is a separate annotation framework | Dataset §; gold-span / human §§ |

Four-category scheme ≠ BASIL lexical/informational span types.

---

## Edit summary

**Removed:** `\revnote{TODO P0 | New taxonomy subsection}{Define Emotional/Evaluative…}` (which incorrectly implied Em/Ev would be redefined as the backbone method).

**Added:** One concise Methods clarification that the original four-way grouping is **not** retained as a primary analysis because of the residual catch-all, and that evidence-type evaluation uses BASIL lex/inf spans (cross-refs only; no protocol repeat).

**Retained:** Matched-pool p75 selection for vocabulary-size control (Appendix~\ref{app:vocab_confound}); calibration/mechanism caveats; T14 similarity `\revnote`.

**Not claimed:** Other dominance as a new finding; independent lex/inf pathways; shared mechanisms.

---

## T13 status

| Layer | Status |
|-------|--------|
| **Methodology** | **Resolved (M4A-8d)** |
| Results (`\revnote` T22 Category results; Em/Ev tables ~L986+) | **Pending** M4B-5 |
| Abstract (90–96% Em/Ev) | **Pending** M4E |
| Conclusion (same) | **Pending** M4E |
| Limitations / appendix Other audit dump | **Pending** M4C / appendix module |

---

## Downstream unsupported taxonomy references (do not edit this module)

| Location | Issue |
|----------|-------|
| Abstract ~L157 | 90–96% Emotional/Evaluative |
| Results Word-Level Patterns + tables | Em/Ev dominance narrative + matched-pool % tables |
| Conclusion ~L1163 | 90–98% Emotional/Evaluative |
| Appendix vocab confound | Function/Temporal sensitivity (may remain as sensitivity of *selection*, not Em/Ev claim) |

---

## Word count

| Unit | Approx. Δ |
|------|-----------|
| Analysis Framework | TODO removed (~40 words) + clarification (~70) → **net ≈ +30** |
| Methodology total | ≈3094 → ≈3125 (small increase; scientific clarity) |

Compression target unaffected in spirit; this module prioritizes claim validity over length.

---

## Proposed later (not done)

- Appendix: short Other/Unassigned audit table from M1 `headline_p75_comparison.csv`.  
- Results rewrite replacing Em/Ev tables (M4B-5).

---

## Verification

- Methodology no longer presents four-category Em/Ev as validated primary method.  
- BASIL lex/inf framework intact.  
- T14 untouched.  
- Compile: **UNVERIFIED**.  
- Diff limited to Analysis Framework.
