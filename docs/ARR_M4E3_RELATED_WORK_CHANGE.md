# ARR M4E-3 — Related Work and Research Positioning (T05/T06)

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Bibliography:** `/Users/go52nom/Downloads/overleaf_latex/custom.bib`  
**Scope:** `\section{Related Work}` + verified BibTeX additions only.  
**Status:** Complete (author review).

---

## 1. Original claim audit

| Claim | Problem | Disposition |
|-------|---------|-------------|
| Encoders “form the **backbone of modern bias detection**” | Overclaim (AC, xw7D) | **Removed** |
| Positioning ends on “**detection mechanism or calibration**” | Contradicts revised thesis | **Removed** |
| “To our knowledge, no prior…” comparative SHAP | Unverified novelty | **Removed** |
| Transformer subsection as architecture survey | Low relevance / space | **Merged** into media-bias encoder scope |
| Attention debate cited as if about SHAP | Risk of category error | **Kept**, explicitly separated from SHAP |
| ERASER / Haug / Rong / EvalxNLP present | Useful | **Retained** and reframed under faithfulness/plausibility |
| Decoder LLM media-bias work absent | Reviewer request | **Added** (4 verified papers) |
| Faithfulness ≠ plausibility under-specified | T06 | **Added** Jacovi & Goldberg; Atanasova diagnostic |

---

## 2. Revised structure

1. **Media Bias Detection** — BABE/BASIL; encoder detectors; scoped decoder LLM cites; no universal backbone.  
2. **Post-hoc Attribution and SHAP** — LIME/SHAP as post-hoc; config dependence; attention debate separate; baseline/perturbation caveats.  
3. **Faithfulness, Plausibility, and Human Evidence** — Jacovi & Goldberg; ERASER; Atanasova; EvalxNLP; human rationales ≠ causal gold.  
4. **Positioning** — four complementary checks matching Intro contributions; no mechanism-vs-calibration; no “first” claim.

Removed `\revnote`s T05 and T06 after substantive address.

---

## 3. Citation verification log

| Key | Venue / status | Claim supported in RW | Verified via |
|-----|----------------|------------------------|--------------|
| `lin-etal-2025-investigating` | COLING 2025 | LLM political-bias prediction / bias detection | ACL Anthology `2025.coling-main.709` (+PDF abstract) |
| `trhlik-stenetorp-2024-quantifying` | Findings EMNLP 2024 | LLMs as generators/classifiers for news political bias | Anthology `2024.findings-emnlp.255` + official `.bib` |
| `mujahid-etal-2025-profiling` | Findings ACL 2025 | LLM outlet-level factuality/bias profiling | Anthology `2025.findings-acl.45` + official `.bib` |
| `menzner-leidner-2024-improved` | NLDB 2024 (Springer LNCS 14762) | LLM/transformer bias detection & subcategorization (incl. BABE/BASIL eval in paper) | Springer DOI `10.1007/978-3-031-70239-6_13`; arXiv `2412.11835`; NLDB accepted list |
| `jacovi-goldberg-2020-towards` | ACL 2020 | Faithfulness vs plausibility; human judgment ≠ faithfulness | Anthology `2020.acl-main.386` + official `.bib` |
| `atanasova-etal-2020-diagnostic` | EMNLP 2020 | Diagnostic comparison of explainability methods; human salient regions | Anthology `2020.emnlp-main.263` + official `.bib` |

**Not added:** unverified or loosely related XAI survey expansions.  
**Retained (already in bib):** Lundberg/Lee; Ribeiro; Mosca; Haug; Rong; Dhaini EvalxNLP; DeYoung ERASER; Jain/Wiegreffe/Serrano; BABE/BASIL/Hamborg; Ghosh; Krieger; DeBERTa.

---

## 4. Reviewer concerns addressed

| Source | Concern | Status after M4E-3 |
|--------|---------|-------------------|
| AC / xw7D | Scope RW; add decoder LLM cites; drop “backbone” | **Resolved** |
| xw7D / Kasneci / T06 | Faithfulness literature; beyond descriptive SHAP ranking | **Resolved** (positioned as combined evaluation, not invention) |
| MqgQ | BASIL lex/inf context | **Supported** in RW dataset paragraph |
| Novelty overclaim | “To our knowledge / first” | **Removed** |

**Remaining (not RW):** title “Decision Mechanisms”; Ethics T29; Hub/shap pins; optional Significance condensation; appendix figure fonts.

---

## 5. Unresolved literature gaps

- No dedicated phrase-level / multi-word attribution method paper added (Limitation already discloses word-level only).  
- `powers2025` (GUS encoder vs decoder social-bias benchmark) remains in bib unused; optional later if space.  
- Broader LLM-explanation surveys intentionally omitted.

---

## 6. Word-count change (Related Work, comments stripped)

| | Words |
|--|------:|
| Before | ~512 |
| After | ~565 |
| Δ | +53 |

Modest increase justified by required decoder LLM coverage and faithfulness/plausibility positioning; architecture survey subsection removed.

---

## 7. Diff scope / compilation

| Edited | Unedited |
|--------|----------|
| `\section{Related Work}` | Title, Abstract, Intro, Methods, Results, Discussion, Conclusion, Limitations, Ethics, Appendix |
| `custom.bib` (+6 keys) | — |

**Compilation:** **UNVERIFIED** (no local LaTeX engine). All new cite keys present in `custom.bib`; no missing keys in Related Work.

---

## 8. T05 / T06 status

| ID | Status |
|----|--------|
| **T05** decoder LLM cites + encoder scope | **Resolved** |
| **T06** faithfulness positioning / no unverified “first” | **Resolved** |
