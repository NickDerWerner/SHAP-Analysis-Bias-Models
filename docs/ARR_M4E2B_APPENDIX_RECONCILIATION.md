# ARR M4E-2b — Appendix Scientific Reconciliation (T30)

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** Appendix only (`\appendix` … `\end{document}`).  
**Prerequisite:** **M4E-2a already complete** (Abstract precision + figure paths); not re-edited here.  
**Status:** Complete (author review).

---

## 1. Complete appendix claim inventory

Classes: **A** supported retain · **B** qualify · **C** contradicted remove/rewrite · **D** unsupported remove · **E** outdated implementation · **F** unverifiable

| ID | Location | Claim (abbrev.) | Class | Evidence | Disposition |
|----|----------|-----------------|-------|----------|-------------|
| V1 | `app:vocab_confound` | Fixed-$K$ F/T 13% vs 4% artifactual under pool size | **A** | Prior sensitivity tables; M4A-8d / M4B-5 | **Retained** as methodological audit |
| V2 | same | Vocab sizes 660 vs 249; $n$ 37/12; ratio 0.38 | **A** | Table retained | **Retained** |
| V3 | same | Sweep / bootstrap F/T shares | **B** | Legacy F/T labels only | **Retained** with “legacy coding / not Results” qualification |
| V4 | Implication | Matched pools ⇒ models “attend to **similar content categories**” | **C** | Em/Ev retired; `sec:word_patterns` | **Removed**; point to BASIL lex/inf + human |
| M1 | `app:max_shap` tables | Median max \|SHAP\| by cell; FP/TP mean vs max ratios | **A** | Descriptive; consistent with `sec:shap_mag` | **Retained** (captions softened) |
| M2 | Interpretive | “**calibration-not-mechanism** reading made quantitative” | **C** | Claim ledger; M4B-5; Limitations | **Removed** |
| M3 | TN paragraph | TN gap “anchors **calibration interpretation**”; “**calibration signature**” | **C** | Same | **Rewritten** as descriptive magnitude gaps |
| M4 | FN | “sub-threshold detection” as calibration-ish | **B/C** | Speculative | **Qualified**: ordering kept; calibration reading denied |
| A1 | `tab:auprc_strata` | AUPRC/baseline/lift by stratum | **A** | `outputs/basil/auprc_table.csv` (rounded) | **Retained**; caption denies pathways |
| A2 | Prose | Lifts “support **bias-type independence**”; “two **detection pathways** … statistically independent” | **C** | M4B-5 T26; `sec:significance` non-independence | **Removed** |
| A3 | Both-types / quote lifts | Prevalence explains high lift; quote strata similar | **A** | Same CSV; $n_{\mathrm{pos}}{=}44$ | **Retained** |
| E1 | Token FP examples | Surface \|SHAP\| values; TP/FP recurrence | **B** | Qualitative BABE examples | **Retained**; softened causal “drives” language |
| E2 | DR example | “**calibration gap** characterized in `sec:shap_mag`” | **C** | Magnitude ≠ calibration | **Removed**; descriptive $P$ difference only |
| E3 | Figs AppendixA/B | Illustrative TP/TN heatmaps | **A** | Files exist at root | **Retained**; captions clarified |
| G1 | Aggregation appendix | Explainer/TextExplainer ambiguity; full additive conservation | **E** | M4A-1/2; Methods | **Rewritten** to match Methods |
| G2 | DeBERTa / offset paths | Missing or obsolete | **E** | M4A-2/8a | **Added** verified DeBERTa repair + offset vs reporting |
| G3 | Phrase-level atomic units | Implied completeness | **B** | Limitations | **Stated** not atomic |

---

## 2. Scientific corrections made

### `app:vocab_confound`
- Reframed as **methodological** pool-size audit.  
- F/T shares labeled **legacy** (not Em/Ev Results).  
- Removed “similar content categories” / mechanism rehab.  
- Implication now points to BASIL gold + human sections.

### `app:max_shap`
- Kept both tables and mean>max compression observation.  
- Removed calibration-not-mechanism / calibration-signature / TN-calibration-anchor language.  
- Explicit: no ECE/Brier; magnitudes are explanation properties.

### `app:auprc_strata`
- Kept table; numbers verified vs `auprc_table.csv`.  
- Removed independence / pathway interpretation.  
- Caption: “Descriptive ranking metrics only.”

### Token examples (`app:token_examples`)
- Softened “same cue drives” → surface can appear in TP and FP.  
- Removed calibration-gap cross-ref.  
- Clarified illustrative / non-mechanistic purpose.  
- Captions updated (no design change to PNGs).

### Aggregation (`app:word_aggregation`)
- Aligned with Methods: `shap.Explainer` + `Text` masker; biased-class softmax; no test-set background.  
- Sum = mapped-unit conservation (not universal).  
- DeBERTa char-span repair + whitespace exclusion.  
- Distinct offset-aware perturbation / span-scoring path.  
- Phrase-level not atomic.

### `\revnote{TODO P2 | Appendix…}`
- **Removed** after substantive T30 corrections.  
- Deferred items noted in `% RESOLVED M4E-2b` comments: figure fonts; Hub/shap pins (T09/T29).

---

## 3. Tables / figures

| Asset | Action |
|-------|--------|
| `tab:vocab_stats`, `tab:vocab_sensitivity` | **Retained**; sensitivity caption revised |
| `tab:max_shap`, `tab:max_vs_mean_ratios` | **Retained**; captions descriptive |
| `tab:auprc_strata` | **Retained**; pathway disclaimer in caption |
| `fig:appendixA`, `fig:appendixB` | **Retained**; caption wording only |
| No appendix assets deleted | — |

---

## 4. Numerical verification

| Quantity | Source | Match |
|----------|--------|-------|
| Full/lex/inf/both/quote AUPRC & baselines | `outputs/basil/auprc_table.csv` | Yes (table rounded: e.g. full BD 0.3915→0.392, DR 0.4121→0.412) |
| Both-types $n_{\mathrm{pos}}{=}44$ | CSV `pos=44` | Yes |
| Stratum $n$ = pos + 6361 negatives | CSV | Yes |
| Max \|SHAP\| cell medians / FP/TP ratios | Prior appendix + `sec:shap_mag` narrative | Retained unchanged numerically |
| Vocab 660/249, F/T sweep | Prior appendix sensitivity | Retained unchanged |

---

## 5. Reproducibility: added vs still missing

**Added / clarified in appendix:** Explainer+Text; no test-set background; DeBERTa repair; offset vs reporting; AUPRC CSV provenance note.

**Still missing (do not invent; follow-ups):** pinned `shap` version; Hub revision hashes; Deb fine-tune hyperparams/seed; artifact licenses (T09/T29); figure font redesign.

---

## 6. Remaining cross-section contradictions (outside appendix scope)

| Item | Status |
|------|--------|
| Related Work “backbone” + mechanism/calibration Positioning (T05/T06) | **Open** (main text) |
| Title “Decision Mechanisms” | **Open** |
| Ethics T29 consent/IRB/licenses | **Open** |
| Results Significance catalogue density (T24) | **Open** |
| Main-text comment “Abstract/Conclusion TODOs remain” | Stale Intro comment (frozen) |
| Optional magnitude-band `\revnote`s in Results/Methods | Optional |

Appendix no longer reasserts pathway/calibration/Em/Ev dominance theses.

---

## 7. Word counts (appendix, comments stripped)

| | Words |
|--|------:|
| Before (M4E-1 estimate) | ~2048 |
| After | ~2042 |
| Δ | ≈ −6 (interpretation rewritten; tables kept) |

---

## 8. LaTeX verification

| Check | Result |
|-------|--------|
| Edit scope | Appendix only (pre-`\appendix` unchanged; M4E-2a Abstract/paths intact) |
| Duplicate labels | None |
| Appendix `\revnote`s | **0** (T30 presentation revnote resolved) |
| Figure files | `AppendixA.png`, `AppendixB.png` exist at root |
| Compilation | **UNVERIFIED** (no local engine) |

### Exact source range
- Replaced from `\appendix` through `\end{document}` (~former L1616–1899 → new appendix through ~L1947).

### New labels
- `app:token_examples`, `app:word_aggregation` (added for clarity; optional).

---

## 9. T30 status

| Component | Status |
|-----------|--------|
| Pathway / independence appendix claims | **Resolved** |
| Magnitude-as-calibration appendix claims | **Resolved** |
| Similar-categories / Em/Ev rehab | **Resolved** (legacy F/T audit isolated) |
| Aggregation alignment with Methods | **Resolved** |
| Keep vocab confound analysis | **Done** |
| Figure font sizes / visual polish | **Deferred** (presentation) |
| Validation examples from both corpora | Partial (BABE examples retained; BASIL examples not newly added) |

**T30 scientific contradictions: resolved.** Presentation residuals deferred.
