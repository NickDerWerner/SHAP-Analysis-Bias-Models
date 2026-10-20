# ARR M2D — Manuscript Claim Ledger

Working contribution: **attribution faithfulness ≠ human-evidence plausibility**, evaluated on BASIL with lexical vs informational evidence types.

This ledger states what the revision may claim after M1–M2D. It is **not** a full paper rewrite.

---

## Retain

| Claim | Support | Caveat |
|-------|---------|--------|
| SHAP high-+ / high-\|SHAP\| token masks change P(biased) more than random/low-\|SHAP\| controls (BD, DR; BASIL paired TP/FP) | M2B | Call it attribution-guided **sensitivity / necessity**, not “faithful reasoning” |
| SHAP absolute mass overlaps BASIL **lexical** spans above length-matched random baselines | M2C + M2D | Stronger on TP and high P(biased) |
| On **paired** sentences, DR exceeds BD on \|SHAP\|–gold excess and ranking AP | M2C + M2D | Not for signed pos-mass excess; not for informational |
| BASIL Em/Eval-style Emotional/Evaluative taxonomy in the draft is invalid (~94% Other) | M1 | Replace taxonomy |
| Informational bias often needs article context; sentence-local SHAP is a limited target | M2C + M2D | Qualitative + coverage geometry |

---

## Replace / reword

| Old / tempting claim | Replace with |
|----------------------|--------------|
| “SHAP aligns better with lexical than informational bias” (unqualified) | “Lexical spans beat length-matched random baselines; raw lex>inf contrasts are **confounded by span coverage** (~10% vs ~70%). After coverage matching / regression control, lex−inf excess is **nonsignificant** for BD/DR.” |
| “Faithful SHAP explanations” | “Attribution-guided sensitivity (M2B) **and separately** human-evidence plausibility (M2C/D)” |
| Em/Eval word-type headlines | BASIL **lexical / informational** evidence types |
| Unpaired cross-model architecture stories | Paired-only comparisons with n reported |
| High raw mass-in-gold on informational spans as “alignment” | Always report vs coverage / random-span baselines |

---

## Remove / do not claim

| Claim | Why |
|-------|-----|
| Emotional/Evaluative dominance (90–96%) | M1 invalidation |
| SHAP recovers informational bias evidence well | Weak vs baselines; nonsignificant after coverage control (BD/DR) |
| Faithfulness proves human plausibility | Divergent constructs; counterexamples (full-span gold + high A_pos) |
| TN faithfulness | n=3 in M2B |
| Equivalence of lex and inf from nonsignificant matched tests | Absence of evidence ≠ evidence of absence |
| Human IAA / human↔SHAP results | Study not run |
| DeBERTa architecture superiority from unpaired caches | Small paired n; integrity caveats (M1) |

---

## Suggested results narrative (short)

1. **Faithfulness:** Masking high positive / high absolute SHAP words reduces bias probability more than controls (M2B).  
2. **Plausibility:** SHAP mass overlaps short BASIL lexical spans above chance; informational spans are long, so raw overlap is misleading.  
3. **Robustness:** Lex vs inf gap vanishes under coverage matching for BD/DR; confidence and TP status drive alignment magnitude.  
4. **Models:** On paired data, DR shows higher \|SHAP\|–lexical alignment than BD; both remain sensitive under perturbation.  
5. **Implication:** Use SHAP for model-sensitivity analysis; do not equate it with recovering BASIL informational annotations; validate human agreement in the pending blind study.

---

## Remaining before ARR resubmission

| Priority | Item |
|----------|------|
| P0 | Rewrite taxonomy + faithfulness/plausibility sections per this ledger |
| P0 | Fix methods text vs code for SHAP (background mismatch) |
| P0 | Run 2-annotator study; report κ + span soft-F1; optional SHAP↔new-human |
| P1 | Add M2B/M2C/M2D tables/figures (coverage-matched result is required honesty) |
| P1 | Limitations: mask OOD, TN n=3, informational context, coverage confound |
| P2 | Optional DeBERTa / regen / paraphrases — only after P0 |

---

## Figure/table pointers for the draft

- Faithfulness: `outputs/arr_m2b/figures/faithfulness_medium_budget2.pdf`  
- Plausibility vs random: `outputs/arr_m2c/figures/excess_mass_lex_vs_inf.pdf`  
- **Coverage-matched gap:** `outputs/arr_m2d/figures/coverage_matched_lex_minus_inf.pdf`  
- Confidence bands: `outputs/arr_m2d/figures/alignment_by_prob_band.pdf`  
- Paired DR>BD: `outputs/arr_m2d/figures/paired_bd_minus_dr.pdf`  
- Qualitative: `outputs/arr_m2d/qualitative_examples.html`
