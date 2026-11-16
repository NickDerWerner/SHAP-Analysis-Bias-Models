# M4A-6 Change Record — BASIL Gold-Span & Human-Evidence Alignment (Methods)

**Date:** 2026-11-13  
**File:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** Two new Methodology subsections after `\label{sec:faithfulness_protocol}`, before Statistical Significance Testing.  
**Not edited:** Abstract, Intro, Related Work, Results (incl. T23 Results `\revnote`), Discussion, Conclusion, Limitations, appendices.

---

## Subsections added

| Label | Title |
|-------|--------|
| `\label{sec:gold_span_alignment}` | BASIL Gold-Span Attribution Alignment |
| `\label{sec:human_annotations}` | Independent Human Evidence Annotations |

---

## TODOs

| ID | Action |
|----|--------|
| **T23** (methods) | **Resolved** — gold-span + independent human protocols documented; coverage-matched caveat stated; no causal/lex≫inf claim |
| **T23** (Results `\revnote` at Results §) | **Retained** — still needs Results tables (M4B-2 / M4B-3) |
| Unrelated TODOs (taxonomy, similarity, threshold, confidence magnitude, etc.) | **Untouched** |

---

## Evidence map

### Gold-span (M2C / M2D)

| Claim | Source |
|-------|--------|
| Plausibility ≠ faithfulness | M2C §5; claim ledger |
| Gold from BASIL @ `4fdbc4f`; key join | M1 / M2C; M4A-3 |
| Multi-span union; lex_only / inf_only / both | `compute_sentence_metrics` ann_category |
| Eligible caches; 1 BD text mismatch excluded | `exclusion_log.csv`; `coverage.json` |
| BD 849/475; DR 837/467; Deb 400/200 | `coverage.json` |
| Offset alignment; ≥50% char overlap ⇒ gold word | `gold_word_thresh=0.5` |
| Abs mass vs positive mass | `abs_mass_in_gold`, `pos_mass_in_gold` |
| Top-5 P/R; AP when eligible | `TOP_K=5`; `ap_eligible` |
| 20 length-matched random draws; seed 7 | `N_BASELINE_DRAWS=20`; `random_length_matched_spans` |
| Coverage baseline; positional control | `abs_minus_coverage_baseline`; `positional_control_spans` |
| Excess = gold − mean random | `abs_minus_random_span` |
| Sentence bootstrap; paired BD−DR | `summarize` / paired sections |
| TP/FN & prob-band strata; coverage match ±5pp; OLS controls | M2D `robustness.py` / report |
| No intrinsic lex≫inf after coverage match | M2D stop answer 1 |

### Human annotations (M3 / M3R)

| Claim | Source |
|-------|--------|
| n=120; seed 7; 30×4 strata | `build_human_sample`; sample CSV `GOLD_category` |
| Blind (no SHAP/model/gold in annotator view) | Sample BLIND CSV / guide |
| Schema: presence, type, spans, needs_context, uncertainty | JSON keys; integrity |
| AnnB updated; AnnA unchanged | M3R hashes / change report |
| Not consensus gold | Scientific objective |
| HH κ presence/type; soft-F1/IoU | `hh_agreement_summary.json` (methods only; no scores in TeX) |
| SHAP–human: yes+spans ∩ cache; 20 random baselines | `shap_vs_human`; `N_BASELINE=20` |
| Cache∩sample BD34 / DR42 / Deb12 | `shap_sample_coverage.json` |
| AnnB 26 yes∅spans: keep presence/type; exclude span/SHAP | M3R policy / integrity |
| Invalid offsets fail checks (0 remaining) | Integrity report |

**Not claimed in TeX:** agreement κ values; excess mass means; lex≫inf superiority; fused human gold; full-sample SHAP–human; DeBERTa faithfulness.

---

## Consistency

- Cross-ref `\ref{sec:faithfulness_protocol}` separates sensitivity from plausibility.  
- Reuses M4A-2/M4A-5 offset-aware wording.  
- Dataset BASIL commit / span types already in M4A-3; not re-expanded here.

---

## Proposed appendix (not edited this module)

Optional appendix dump: full `gold_span_metrics` formulas, random-span placement algorithm, coverage-matching greedy procedure, human annotation guide excerpts, AnnB yes∅spans classification table.

---

## Downstream Results / Limitations still required

| Module | Need |
|--------|------|
| **M4B-2** | BASIL gold-span Results + coverage-matched caveat numbers |
| **M4B-3** | Human HH / human–BASIL / SHAP–human Results (M3R numbers) |
| **M4C-1 / T28** | Limitations: cache∩sample, yes∅spans, weak type IAA, informational context |
| Results T23 `\revnote` | Remove only after Results prose lands |

---

## Compile status

**UNVERIFIED** (no LaTeX engine on PATH).

---

## Diff hygiene

Manuscript changes: insert two Methodology subsections only (+ resolution comment). No Results/Intro/Abstract/Limitations edits.
