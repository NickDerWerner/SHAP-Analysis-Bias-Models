# ARR M4B-2 — BASIL Gold-Span Attribution Alignment Results

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** Results only — new subsection + one table after faithfulness Results.  
**Status:** Complete (author review). No new experiments.

---

## What changed

| Item | Detail |
|------|--------|
| New subsection | `\subsection{BASIL Gold-Span Attribution Alignment}` `\label{sec:gold_span_results}` |
| New table | `Table~\ref{tab:gold_span}` — lex/inf excess \|SHAP\| vs length-matched random |
| Insertion point | Immediately after `\label{tab:faithfulness}` / before `\subsection{SHAP Magnitude Patterns}` |
| Em/Ev Results | **Not edited**; flagged for later taxonomy cleanup |
| Human Results | **Not written**; T23 Results `\revnote` narrowed to M4B-3 |

---

## Primary evidence (verified)

| Artifact | Path |
|----------|------|
| M2C summary | `outputs/arr_m2c/gold_span_summary.csv` |
| M2D summary | `outputs/arr_m2d/robustness_summary.csv` |
| Reports | `docs/ARR_M2C_GOLD_SPAN_REPORT.md`, `docs/ARR_M2D_ROBUSTNESS_REPORT.md` |
| Methods cross-ref | `\ref{sec:gold_span_alignment}` (M4A-6) |

---

## Number → source map

### Eligible gold-positive populations

| Model | n | Source |
|-------|--:|--------|
| BD | 475 | `coverage,biasdetector,ALL_POSITIVE` |
| DR | 467 | `coverage,daroberta,ALL_POSITIVE` |
| Deb | 200 | `coverage,deberta,ALL_POSITIVE` |

### Table `\ref{tab:gold_span}` (`abs_minus_rand_span`)

| Model | Type | n | Mean | 95% CI | CSV rows |
|-------|------|--:|-----:|--------|----------|
| BD | lex_only | 223 | +0.080 | [+0.063, +0.097] | `metric,biasdetector,lex_only,...,abs_minus_rand_span` |
| BD | inf_only | 229 | +0.028 | [+0.015, +0.042] | same, `inf_only` |
| DR | lex_only | 227 | +0.133 | [+0.114, +0.152] | `daroberta,lex_only` |
| DR | inf_only | 214 | +0.035 | [+0.017, +0.055] | `daroberta,inf_only` |
| Deb | lex_only | 55 | +0.141 | [+0.101, +0.184] | `deberta,lex_only` |
| Deb | inf_only | 138 | +0.017 | [−0.002, +0.037] | `deberta,inf_only` (CI includes 0) |

Rounding: means to 3 dp; CI endpoints to 3 dp from CSV bootstrap bounds.

### Signed positive-class excess (prose only; lexical)

| Model | Type | Mean `pos_minus_rand_span` | Notes |
|-------|------|---------------------------:|-------|
| BD | lex | +0.241 [+0.212, +0.275] | Stated as “likewise positive” |
| DR | lex | +0.257 [+0.231, +0.284] | Same |
| Deb | lex | +0.282 [+0.211, +0.359] | Same |

### Coverage (~character fraction)

| Type | BD mean coverage | DR | Deb |
|------|-----------------:|---:|----:|
| lex_only | 0.094 | 0.100 | 0.104 |
| inf_only | 0.697 | 0.709 | 0.702 |

Prose: “roughly 10% vs ~70%”.

### Coverage-matched lex−inf (`abs_minus_rand`, ±5 pp)

| Model | n | Mean gap | 95% CI | Source |
|-------|--:|--------:|--------|--------|
| BD | 44 | −0.017 | [−0.071, +0.038] | `coverage_matched,biasdetector,...` |
| DR | 42 | −0.001 | [−0.064, +0.064] | `coverage_matched,daroberta,...` |
| Deb | 18 | +0.146 | [+0.069, +0.224] | Reported as underpowered residual only |

### Positional / coverage baselines (interpretation)

| Contrast | Finding | Source metric |
|----------|---------|---------------|
| BD/DR lexical vs positional | Excess remains positive | `abs_minus_positional` lex_only |
| BD informational vs coverage | CI includes 0 (+0.010 [−0.003, +0.024]) | `abs_minus_coverage` inf_only |
| DR informational vs coverage | Small positive (+0.025 [+0.007, +0.045]) | same |

### Paired BD−DR (sign = BD − DR)

| Stratum | n | Metric | Mean | 95% CI | Source |
|---------|--:|--------|-----:|--------|--------|
| ALL shared | 255 | abs_minus_rand | −0.031 | [−0.044, −0.017] | M2C `paired_diff` / M2D `paired_model` |
| lex_only | 168 | abs_minus_rand | −0.038 | [−0.056, −0.021] | M2D (matches M2C closely) |
| inf_only | 67 | abs_minus_rand | −0.008 | [−0.031, +0.016] | CI includes 0 |
| ALL | 255 | pos_minus_rand | +0.008 | [−0.019, +0.032] | No signed difference |

DeBERTa paired: BD−Deb n=83; DR−Deb n=65 — disclosed, not interpreted as architecture effects.

### Both-type cells (not emphasized)

BD 23 / DR 26 / Deb 7.

---

## Scientific framing (enforced)

- Plausibility / evidence alignment ≠ causal faithfulness.  
- Complementary to M4B-1 masking, not independent confirmation.  
- BASIL spans = corpus rationales, not model ground truth.  
- No intrinsic lex ≫ inf claim after coverage matching (BD/DR).  
- Sentence is the resampling unit; spans within a sentence are unioned (Methods).

---

## Appendix candidates (not edited now)

From M2D, better suited to appendix / later Results if space allows:

1. TP vs FN stratification of excess (TP ≫ FN for lexical).  
2. Probability-band gradients.  
3. Regression controls (`coef_is_lex` nonsignificant once coverage entered).  
4. Faithfulness∩alignment Spearman ≈ 0.45 (n=137) + qualitative counterexamples.  
5. Article-cluster bootstrap CIs (near identical to sentence bootstrap).  
6. Multi-span vs single-span strata.  
7. Coverage-matched figure `figures/coverage_matched_lex_minus_inf.*`.  
8. Paired BD−DR figure `figures/paired_bd_minus_dr.*`.

---

## TODOs

| ID | Action |
|----|--------|
| T23 gold-span Results | **Resolved** (subsection + table; old `\revnote` replaced) |
| T23 human Results | **Open** — narrowed `\revnote{TODO P1 \| Independent human-span Results}` → M4B-3 |
| T13/T22 Em/Ev Results | **Open** — flagged only |

---

## Diff scope check

Intended edits confined to:

1. New Results subsection + table after faithfulness.  
2. Narrowed human-span `\revnote` near former T23 Results location.  
3. Em/Ev FLAG comment update on SHAP Magnitude Patterns.

No Methodology / Abstract / Intro / Discussion / Conclusion / Limitations / Ethics / Appendix edits.

---

## Compilation

**UNVERIFIED** — no `pdflatex` / `xelatex` / `latexmk` on PATH in this environment.
