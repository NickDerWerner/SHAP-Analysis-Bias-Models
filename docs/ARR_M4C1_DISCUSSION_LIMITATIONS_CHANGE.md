# ARR M4C-1 — Discussion and Limitations

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** New `\section{Discussion}`; full rewrite of `\section{Limitations}`.  
**Not edited:** Results, Methods, Abstract, Intro, Related Work, Conclusion, Ethics, Appendices.

---

## Structural change

| Before | After |
|--------|-------|
| No Discussion (Results → Conclusion) | `\section{Discussion}` `\label{sec:discussion}` before Conclusion |
| Short Limitations (~282 words) with calibration-vs-mechanism + revision aside | Rewritten `\label{sec:limitations}` (~411 words) |
| T28 `\revnote` present | **Removed** (resolved) |

**Word counts (approx., comments stripped):**  
- Discussion: **0 → 489** (new)  
- Limitations: **282 → 411** (+129)  
- Combined Discussion+Limitations block: **282 → 900**

---

## Discussion — interpretations introduced

Mapped to validated Results (no new numbers invented beyond those already in M4B):

| Theme | Interpretation | Anchors |
|-------|----------------|---------|
| A. Sensitivity | High-\|SHAP\| masking > controls ⇒ attribution-guided **sensitivity**, not causal fidelity / internal reasoning | `sec:faithfulness_results`; TN n=3 |
| B. Plausibility | Lexical gold excess > random; inf weaker; coverage match removes BD/DR lex−inf gap; sentence-local SHAP poor for long informational spans | `sec:gold_span_results` |
| B/C. Humans | Moderate presence κ, weak type κ; yes∅spans; cache∩ limits; human ≠ model ground truth | `sec:human_results` |
| C. Overlap | High paired Jaccard on shared FP = descriptive token overlap, not mechanism identity | `sec:paired_similarity` |
| Taxonomy | Em/Ev dominance retired; use BASIL lex/inf + humans | `sec:word_patterns` |
| Contribution | Multi-check protocol with denominators; BD–DR primary | Claim ledger short list |

**Explicitly rejected in Discussion:** causal explanation fidelity; shared internal mechanisms; Em/Ev dominance as a finding; magnitude-as-calibration.

---

## Limitations — strengthened content

| Cluster | Items added/strengthened |
|---------|---------------------------|
| Data/labels | BABE vs BASIL label mismatch; span→binary; BABE–BASIL overlap **UNVERIFIED**; cache selection @ t=0.5; both-types n=44; encoder-only |
| SHAP/masking | Mask OOD; BD/DR-only faithfulness; TN n=3; aggregation/whitespace; no phrase atoms; no alt explainers; discourse/info bias |
| Humans | n=120, 2 annotators; κ type weak; 26 yes∅spans classified; SHAP∩ 34/42/12; Deb exploratory |
| Stats/repro | Small n; no global multiplicity correction; threshold sensitivity; no ECE/Brier; Deb uneven coverage; incomplete Hub pins; Em/Ev not rehabilitated via p75 |

**Removed from old Limitations:** calibration-vs-mechanism future-work framing; “history” aside about TP≈FP revision as a narrative of paper changes (substance kept only as cross-corpus magnitude caveat in Results, not as Limitations revision diary).

---

## Unsupported claims removed (this module)

- Limitations: “whether calibration-vs-mechanism extends to decoder LLMs…”  
- Limitations: implying faithfulness was not assessed (contradicted M2B) — replaced with scoped sensitivity disclosure.  
- No restoration of Em/Ev dominance or same-mechanism as positive claims.

**Still present elsewhere (out of scope):** Conclusion Abstract/Intro Em/Ev + calibration language (T01/T27).

---

## TODOs

| ID | Status |
|----|--------|
| **T28** Limitations | **Resolved** |
| T23 Limitations disclosure (yes∅spans, cache∩) | **Addressed in Limitations** |
| T29 Ethics/repro | **Open** (deferred) |
| T01/T27 Abstract/Conclusion | **Open** |

---

## Verification

- Diff confined to Discussion insert + Limitations rewrite.  
- Cross-refs: faithfulness, gold-span, human, paired, shap_mag, word_patterns, eval_populations, vocab_confound.  
- Compile: **UNVERIFIED**.
