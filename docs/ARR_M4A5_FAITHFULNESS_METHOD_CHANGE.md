# M4A-5 Change Record — Perturbation-Based Attribution Sensitivity (Methods)

**Date:** 2026-11-13  
**File:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** New Methodology subsection only — `\subsection{Perturbation-Based Attribution Sensitivity}` (`\label{sec:faithfulness_protocol}`), inserted after Analysis Framework TODOs and before Statistical Significance Testing.  
**Not edited:** Abstract, Intro, Related Work, Results, Discussion, Conclusion, existing appendices.

---

## TODOs

| ID | Action |
|----|--------|
| **T15** Faithfulness protocol | **Methods resolved** — `\revnote` removed; M2B protocol documented. **Results still pending** (M4B-1): numerical ΔP / CIs / tables must not be claimed from this subsection alone. |

---

## Insertion context (before → after)

**Before:** Analysis Framework ended with taxonomy + similarity `\revnote`s, then immediately `\subsection{Statistical Significance Testing}`, with an intervening faithfulness `\revnote` asking for a top 10/20/30\% perturbation study.

**After:** That faithfulness `\revnote` is replaced by `\subsection{Perturbation-Based Attribution Sensitivity}` describing the **actual** M2B fixed-budget masking protocol. Taxonomy and similarity `\revnote`s retained.

---

## Evidence map (every substantive claim)

| Claim in TeX | Source |
|--------------|--------|
| Attribution-guided sensitivity framing; not internal reasoning | Scientific objective; `ARR_M2B_FAITHFULNESS_REPORT.md` §5 |
| Models: `himel7/bias-detector`, `mediabiasgroup/DA-RoBERTa-BABE-FT` | `faithfulness_eval.py` `MODELS`; results CSV models |
| DeBERTa excluded | No DeBERTa in `MODELS` / `faithfulness_results.csv` |
| $n{=}200$ paired BASIL sentences; same text + same TP/FP/TN/FN cell | `build_paired_pools` + `sample_medium`; CSV unique IDs = 200/model |
| Threshold $0.5$ for cell labels | Cache `pred` / manuscript Evaluation Metrics; consistency docs |
| Seed $7$; target equal 50/cell then fill shortfalls | `SEED=7`, `sample_medium` ideal `target//4` then remainder |
| Realized TP 85 / FP 60 / FN 52 / TN 3 | `sample_medium` notes; report; CSV stratum counts |
| TN underpowered / unequal strata | Only 3 shared TNs in intersection |
| Offset-aware whitespace alignment; special tokens skipped | `offset_alignment.py` (`SPECIAL`, `source_word_spans`, `align_record`) |
| Empty surfaces excluded; repeated spans left-to-right | `select_source_words` strip filter; cursor placement in align |
| Budgets $k\in\{1,2,3\}$ | `BUDGETS = (1, 2, 3)` |
| Conditions A_pos, B_neg, C_abs, D_random, E_lowabs | `CONDITIONS`; `select_source_words` |
| A/B fallback to signed ranking if <k strict ± | `select_source_words` A/B branches |
| Random: 3 seeded draws; averaged per sentence before bootstrap | `N_RANDOM_REPEATS=3`; `summarize` groups then `np.mean` |
| Replace with tokenizer `<mask>` (not delete) | `apply_mask_offsets`; CSV `mask_token` all `<mask>` |
| Incomplete budgets excluded | `complete_budget` gate; all kept rows `complete_budget=1` |
| Expected ΔP sign for A (−) / B (+) | `direction_ok` definition in `faithfulness_eval.py` |
| Metrics: orig/pert $P$, $\Delta P$, $\|\Delta P\|$, logit margin, direction, flips | result row fields |
| Sentence-level bootstrap CIs; paired A/B/C−random, C−lowabs | `bootstrap_mean_ci` (`n_boot=2000`); `paired_contrast` section |
| Mask OOD / not human-interpretable reasoning | Report §5; Limitations deferred for expansion (T28) |

**Not claimed:** top 10/20/30\% budgets; balanced strata; DeBERTa M2B; TN adequacy; sufficiency subsample as main protocol; result magnitudes.

---

## Consistency with M4A-1 / M4A-2

- M4A-1: Explainer + Text masker; this subsection tests **post-hoc masking of source words**, not the SHAP masker background myth.  
- M4A-2: Reporting aggregation vs **perturbation alignment** distinction reused (“offset-aware procedure above”).

---

## Downstream edits still required

| Module | Need |
|--------|------|
| **M4B-1** | Insert faithfulness Results (tables/CIs from `outputs/arr_m2b/`); cross-ref `\ref{sec:faithfulness_protocol}` |
| **M4C-1 / T28** | Limitations: mask OOD, TN $n{=}3$, RoBERTa-only, sensitivity ≠ reasoning |
| Intro/Abstract | Later: faithfulness≠plausibility framing (not this module) |

Numbering: new Methodology subsection shifts subsequent Methodology subsection numbers; Results section numbering unchanged. No other `\label`s renamed. Forward Results cross-ref intentionally omitted (no Results content edit).

---

## Compile status

**UNVERIFIED** — no `pdflatex`/`latexmk`/`xelatex` on PATH in this environment.

---

## Diff hygiene

Manuscript changes confined to replacing the T15 faithfulness `\revnote` with the new subsection (+ resolution comment). No Results/Intro/Abstract edits.
