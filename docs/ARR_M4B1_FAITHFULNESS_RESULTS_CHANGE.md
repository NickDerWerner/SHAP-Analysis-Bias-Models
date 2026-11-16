# M4B-1 Change Record — Perturbation-Based Attribution Sensitivity Results

**Date:** 2026-11-16  
**File:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** New Results `\subsection{Perturbation-Based Attribution Sensitivity}` `\label{sec:faithfulness_results}` + `Table~\ref{tab:faithfulness}`, inserted after Overall Model Performance and before SHAP Magnitude Patterns.  
**Not edited:** Methodology, Abstract, Intro, Em/Ev Results body, Conclusion, Limitations, appendices.

---

## Evidence map (budget $k{=}2$, phase `medium`, $n{=}200$)

Source: `outputs/arr_m2b/faithfulness_summary.csv` (`section=delta_prob`, `stratum=ALL` unless noted).

| TeX claim | CSV fields |
|-----------|------------|
| BD A_pos ΔP −0.327 [−0.369,−0.282]; \|ΔP\| 0.329; dir 0.925 | biasdetector / A_pos / budget 2 |
| DR A_pos −0.293 [−0.328,−0.258]; 0.295; 0.945 | daroberta / A_pos / 2 |
| BD/DR B_neg +0.054/+0.045; dirs 0.680/0.705 | B_neg / 2 |
| BD/DR C_abs \|ΔP\| 0.294/0.289; random 0.071/0.067; lowabs 0.029/0.035 | C_abs, D_random, E_lowabs |
| Paired C−random \|ΔP\| +0.223/+0.222 | `paired_contrast` C_minus_random_abs / 2 |
| Paired C−lowabs +0.266/+0.254 | C_minus_lowabs_abs / 2 |
| A_pos budgets 1/2/3 BD −0.201/−0.327/−0.404; DR −0.190/−0.293/−0.345 | A_pos budgets |
| TP/FP/FN/TN n and A_pos means | `stratum`∈{TP,FP,FN,TN}, A_pos, budget 2 |
| Bootstrap unit = sentence; random reps pre-averaged | `faithfulness_eval.py` `summarize` |

Protocol cross-ref: `\ref{sec:faithfulness_protocol}`. DeBERTa excluded (matches Methods).

**Not reported:** sufficiency subsample; logit-margin table (available in CSV, omitted for page economy); formal monotonicity test.

---

## TODOs

| ID | Action |
|----|--------|
| **T15 Results** | **Resolved** by this subsection + table |
| Em/Ev Results (T22) | **Flagged only** — not rewritten |
| Gold-span / human Results | Pending M4B-2 / M4B-3 |

---

## Scientific framing

Attribution-guided **prediction sensitivity** under mask-token intervention; OOD caveat one sentence; TN $n{=}3$ no generalization; B_neg weaker than A_pos.

---

## Verification

- Signs match expected A_pos decrease / B_neg increase.  
- All table numbers rounded from CSV.  
- Diff: Results insert only.  
- Compile: **UNVERIFIED**.
