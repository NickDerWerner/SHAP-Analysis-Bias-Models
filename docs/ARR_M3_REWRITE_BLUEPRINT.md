# ARR M3 — Manuscript Rewrite Blueprint

**Do not rewrite in this milestone.** This is the frozen plan for the next step.  
**Source manuscript:** `docs/references/paper.tex` (line refs approximate).  
**Verdict:** **CONDITIONAL GO** to begin rewriting.

---

## Section-by-section plan

| Section (paper.tex) | Action |
|---------------------|--------|
| **Abstract** (~L156–167) | Cut to ~150–200 words. Drop Em/Ev 90–96% and dense ratios. State: faithfulness (masking) + plausibility (BASIL lex + human study) + paired model comparison. One limitation (informational/context). |
| **Introduction** (~L173–270) | Reframe contribution around faithfulness≠plausibility. Remove same-mechanism/Emotional dominance. Soften calibration thesis. |
| **Related Work** (~L275–348) | Add decoder-LLM bias-detection citations (xw7D list). Scope “encoders in this study.” Add faithfulness evaluation literature. |
| **Methodology — models/data** (~L350–411) | Keep BABE/BASIL; clarify sentence vs span labels; BASIL lex/inf definitions. |
| **Methodology — SHAP** (~L412–450) | Fill TODOs: background set, masker, output space, library version, offset aggregation (cite M2B). |
| **Methodology — taxonomy** | **Replace** Em/Ev/Expl/Fr/Fu coding with: (i) Other/unassigned lexicon audit (M1), (ii) BASIL lex/inf for evidence alignment. |
| **Methodology — new** | Add faithfulness protocol (M2B); gold-span + human-span metrics + baselines (M2C–M3); pairing rules. |
| **Results — overlap/errors** | Keep paired Jaccard / shared FP with n; no unpaired architecture stories. |
| **Results — magnitude/calibration** | Downgrade; report with confidence controls or move to appendix. |
| **Results — faithfulness** | New primary subsection (M2B tables/figures). |
| **Results — plausibility** | BASIL lex/inf with coverage-matched caveat (M2D); human IAA + SHAP–human (M3). |
| **Discussion** | Mechanism claims → sensitivity + partial lexical plausibility. Informational needs context. |
| **Limitations** (~L900+) | Mask OOD; TN n=3; Deb uneven; human missingness (annB); cache∩sample; no paraphrase; encoder-only. |
| **Ethics / artifacts** | Human annotators section (D1–D3); licenses B2. |

---

## Final figures & tables (data sources)

| ID | Content | Source |
|----|---------|--------|
| Fig F1 | Faithfulness ΔP by condition (budget 2) | `outputs/arr_m2b/figures/faithfulness_medium_budget2.pdf` |
| Fig F2 | Abs sensitivity vs controls | `outputs/arr_m2b/figures/abs_sensitivity_medium_budget2.pdf` |
| Fig P1 | Gold abs mass vs random by cat | `outputs/arr_m2c/figures/abs_mass_vs_random.pdf` |
| Fig P2 | Excess mass lex vs inf | `outputs/arr_m2c/figures/excess_mass_lex_vs_inf.pdf` |
| Fig P3 | Coverage-matched lex−inf | `outputs/arr_m2d/figures/coverage_matched_lex_minus_inf.pdf` |
| Fig P4 | Alignment by prob band | `outputs/arr_m2d/figures/alignment_by_prob_band.pdf` |
| Fig P5 | Paired BD−DR | `outputs/arr_m2d/figures/paired_bd_minus_dr.pdf` |
| Fig Q1 | Qualitative SHAP vs gold | `outputs/arr_m2d/qualitative_examples.html` / `figures/examples/` |
| Tab T1 | Taxonomy p75 Em/Ev vs Other | `outputs/arr_m1/taxonomy/headline_p75_comparison.csv` |
| Tab T2 | Faithfulness summary | `outputs/arr_m2b/faithfulness_summary.csv` |
| Tab T3 | Gold-span summary + matched | `outputs/arr_m2c/gold_span_summary.csv`, `outputs/arr_m2d/robustness_summary.csv` |
| Tab T4 | Human–human + human–BASIL + SHAP–human | `outputs/arr_m3/*.json|csv` |
| Tab T5 | Population / pairing n | This audit + `coverage.json` files |

---

## Genuine blockers before camera-ready

| Blocker | Blocks rewrite start? | Blocks submission? |
|---------|----------------------:|-------------------:|
| Abstract/methods wording unfinished | No | Yes |
| SHAP background set not written | No (can draft with TODO then fill) | Yes |
| annB 31 yes-without-spans | No (disclose) | No if disclosed |
| Limited SHAP∩human sample | No (scope claim) | No if scoped |
| Paraphrase experiment absent | No | No (future work) |
| Model-specific decision thresholds | No | Prefer at least discussion |
| `shap` package pin missing | No | Prefer fix for repro package |

**No analysis blocker prevents starting the rewrite.** Submission needs background documentation + claim-aligned text.

---

## Recommended rewrite order

1. Claim-aligned abstract + intro contributions.  
2. Methods: SHAP protocol, faithfulness, plausibility, taxonomy retraction.  
3. Results: F1–F2 then P1–P5 then T4 human study.  
4. Related work + limitations + ethics.  
5. Figure polish and abbreviation cleanup.

---

## Stop condition — GO / CONDITIONAL GO / NO-GO

### **CONDITIONAL GO**

**May begin manuscript revision now**, under these conditions:

1. Use the claim ledger (Retain/Revise/Remove/Add) as the only claim source.  
2. Disclose human missingness, cache∩sample limits, and coverage confound.  
3. Do not invent paraphrase/LLM results or adjudicate/fuse annA+annB into synthetic gold.  
4. Fill SHAP background / package pins before submission (can draft in parallel).  

**Not NO-GO:** Core faithfulness + lexical plausibility + taxonomy retraction are evidence-ready.  
**Not unconditional GO:** Writing/repro documentation and soft calibration/mechanism cleanup remain required for a credible ARR resubmission.
