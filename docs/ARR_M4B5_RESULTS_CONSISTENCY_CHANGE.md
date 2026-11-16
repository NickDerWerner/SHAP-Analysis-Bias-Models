# ARR M4B-5 — Results Scientific Consistency Cleanup

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** Remaining Results subsections only (not M4B-1…M4B-4 bodies; not Abstract/Intro/Methods/Conclusion/Limitations/Ethics/Appendix).  
**Status:** Complete (author review of Results).

**Results word count (approx., comments stripped):** 4608 → **3683** (−925).

---

## Claim inventory (Results only)

| ID | Location | Claim (abbrev.) | Class | Evidence | Disposition |
|----|----------|-----------------|-------|----------|-------------|
| C1 | Overall perf. | Calibration rather than mechanism; AUPRC ⇒ all three; lift 1.79–2.03 as mechanism story | **D** | Methods; `auprc_table.csv`; consistency check | Rewrote; AUPRC provenance disclosed |
| C2 | `tab:performance` Deb BASIL AUPRC 0.364 | Present in table | **B** | Not in `auprc_table.csv`; in `DEBERTA_PAPER_PARITY.md` | **Retained** with caption provenance |
| C3 | Overall / T25 | F1 robust / threshold-invariant findings | **C/D** | Sweep F1 moves with $t$ | Disclosed sensitivity; no robustness claim |
| C4 | Magnitude § | Three calibration levels / TN calibration spectrum / magnitude=calibration | **D** | Claim ledger Remove/Revise; Methods | Rewrote as descriptive \|SHAP\| |
| C5 | `tab:shap_magnitudes` caption | Calibration spectrum | **D** | Same | Caption corrected; numbers kept |
| C6 | Magnitude figures | Descriptive TP/FP/TN/FN \|SHAP\| | **A** | Existing figs + MWU | **Preserved** |
| C7 | Global indicators | “Bias indicators”; Em/Ev language reliance | **C** | No gold-span support; Em/Ev invalid | Softened to high-\|SHAP\| surfaces |
| C8 | `fig:tbi` | Top-10 word plot | **B** | Useful descriptive | **Retained**; caption fixed |
| C9 | Word-level patterns tables | 90–97% Em/Ev dominance | **D** | M1 legacy residual; v2 Other ~94–97% | **Tables removed** |
| C10 | FP partition table | Em/Ev dominates every cell; calibration difference | **D** | Same | **Table removed** |
| C11 | Significance MWU | Intermediate calibration level | **D** | Magnitude ≠ calibration | Softened; stats kept |
| C12 | Error overlap @0.5 | Shared FP/FN counts | **A/B** | `section_4_5_data.md` | Kept; scoped to $t{=}0.5$ |
| C13 | Two-pathway independence | Lex/inf independent detection | **D** | Ledger; T26; arithmetic ≠ mechanism | Claim removed; recalls kept as descriptive |
| C14 | Deb pathway 0.432 vs 0.480 | Independence gap | **E** | Not in BD/DR sweep CSV rows used | **Removed** |
| C15 | M4B-1…M4B-4 subsections | Faithfulness / gold / human / paired sim | **A** | Prior modules | **Untouched** |

Classes: A supported · B qualify · C unsupported remove · D contradicted correct · E unverifiable.

---

## Edits made

### Overall Model Performance (`\\subsection{Overall Model Performance}`)
- Removed calibration-vs-mechanism framing.
- Disclosed $t{=}0.5$ F1 sensitivity (BD 0.404/0.376/0.355).
- AUPRC lifts stated for BD/DR; Deb AUPRC kept with source note.
- Narrowed T18 `\revnote`.

### SHAP Magnitude Patterns (`sec:shap_mag`)
- Lead: \|SHAP\| ≠ calibration/certainty/causal importance.
- Removed “alignment”/calibration-signature rhetoric.
- Table caption: magnitude ordering, not calibration spectrum.
- T19 Results: resolved (no three-calibration claim); optional M2D-band `\revnote` retained.

### High-Attribution Word Surfaces (`sec:global_bias`)
- Renamed from “Global Bias Indicators”.
- No Em/Ev mechanism claim; figure retained with descriptive caption.

### Matched-Pool Vocabulary Note (`sec:word_patterns`)
- **Removed** `tab:matched_pool_tpfp` and `tab:fp_partition` + all Em/Ev dominance prose.
- Short note: catch-all artifact; point to gold-span/human Results; vocab confound appendix kept.
- Label `sec:word_patterns` retained for Methods/Appendix cross-refs.

### Statistical Significance (`sec:significance`)
- MWU kept; calibration interpretation removed.
- Error overlap: $t{=}0.5$ only; no threshold-invariant claim (T25 Results).
- Pathways: descriptive recalls + explicit **non**-independence (T26).
- Removed T22/T25/T26 Results `\revnote`s (pathway/error/category).

---

## Tables / figures

| Asset | Action | Justification |
|-------|--------|---------------|
| `tab:performance` | Revised caption/prose | AUPRC provenance; no mechanism claim |
| `fig:smd_babe`, `fig:smd_basil`, `tab:shap_magnitudes` | Retained; caption fix | Valid descriptive magnitude |
| `fig:tbi` | Retained; caption fix | Surface-form list only |
| `tab:matched_pool_tpfp` | **Removed** | Invalid Em/Ev taxonomy |
| `tab:fp_partition` | **Removed** | Invalid Em/Ev taxonomy |
| M4B-1…4 tables | Untouched | Out of scope |

---

## Appendix candidates (not edited)

1. M1 `headline_p75_comparison.csv` legacy vs v2 (Other ~94–97%).  
2. Full threshold-sweep F1 table for all models.  
3. Deb AUPRC strata from `DEBERTA_PAPER_PARITY.md` §H.  
4. Vocab-confound appendix already present (`app:vocab_confound`).

---

## TODOs

| ID | Status after M4B-5 |
|----|-------------------|
| **T22** Results Em/Ev | **Resolved** |
| **T19** three calibration levels | **Resolved** (optional M2D-band follow-up left) |
| **T25** Results threshold scope | **Resolved** for Results disclosure; full re-analysis still out of scope |
| **T26** pathways | **Resolved** (claim removed) |
| T18 Overall (AUROC/ECE) | Narrowed optional |
| T01/T27 Abstract/Conclusion Em/Ev | **Open** (not Results) |
| Methods `\revnote` magnitude confidence | **Open** (Methodology out of scope this module) |
| Limitations/Ethics human disclosures | **Open** |

---

## Downstream contradictions still outside Results

- Abstract / Intro / Conclusion still claim 90–96% Em/Ev and same-mechanism/calibration.
- Appendix passages still use “calibration-not-mechanism” language.
- Methods Metrics still has a Results-pointing magnitude `\revnote`.

---

## Verification checklist

- [x] No Em/Ev **dominance claim** remains as a positive Results finding (only retraction note).  
- [x] No SHAP-magnitude-as-calibration claim in Results.  
- [x] No unsupported independent-pathways claim.  
- [x] BASIL AUPRC coverage disclosed.  
- [x] M4B-1…M4B-4 labels/tables intact.  
- [x] No live `\ref` to removed Em/Ev tables.  
- [ ] Compile: **UNVERIFIED** (no TeX engine).

---

## Compile

**UNVERIFIED**.
