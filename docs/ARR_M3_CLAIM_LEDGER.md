# ARR M3 — Claim Ledger (Retain / Revise / Remove / Add)

Evidence base frozen after M0–M3. Human raw JSON unmodified.

---

## Retain

| Claim | Evidence |
|-------|----------|
| SHAP high-attribution words are prediction-sensitive under masking (BD, DR; BASIL TP/FP) | M2B |
| Models show substantial top-token overlap on paired shared errors | M1 pairing / paper Jaccard (paired only) |
| SHAP \|mass\| in BASIL **lexical** spans exceeds length-matched random | M2C–M2D |
| On paired sentences, DR > BD on \|SHAP\|–lexical excess / AP | M2C–M2D |
| SHAP \|mass\| in **new human** evidence spans exceeds random (cache∩sample) | M3 |
| Em/Ev “90–96%” is invalid under reproducible coding with Other | M1 |
| Encoder-only scope; decoder LLMs out of scope | Meta-review + paper TODO |

## Revise

| Old claim | Revised claim |
|-----------|---------------|
| Same linguistic mechanism / Emotional dominance | Models show overlapping high-attribution **tokens** on paired data; category story uses BASIL **lex/inf** + explicit Other — not Em/Ev |
| Lex ≫ inf SHAP alignment | Lexical beats random; lex−inf gap **does not survive coverage matching** (BD/DR) |
| Faithful explanations | Attribution-guided **sensitivity** (faithfulness) **≠** human-evidence **plausibility** |
| Magnitude differences = calibration insight needing SHAP | Report magnitude with **confidence controls**; do not claim SHAP is necessary for calibration |
| Three models equally analyzed | Two-model primary (BD, DR); DeBERTa secondary where caches permit |
| BASIL gold as sole human truth | BASIL + independent annotators; disclose IAA and dual disagreements |

## Remove

| Claim | Reason |
|-------|--------|
| 90–96% Emotional/Evaluative | Catch-all residual |
| SHAP recovers informational bias well | Weak after length control |
| TN faithfulness | n=3 |
| Unpaired architecture superiority | Confounded |
| Strong human consensus on lex/inf type | κ_type=0.14 |
| Mechanism claims implying causal reasoning from SHAP alone | Reviewer xw7D |

## Add

| New contribution | Support |
|------------------|---------|
| Explicit faithfulness vs plausibility distinction | M2B + M2C/D + M3 |
| Coverage-matched robustness of lex/inf gap | M2D |
| Blind two-annotator study + SHAP vs human spans | M3 (with missingness) |
| Reproducible taxonomy retraction + BASIL span recovery | M1 |
| Offset-correct word aggregation + tests | M2B |

---

## Final defensible paper contributions (short list)

1. **Faithfulness:** Attribution-guided masking shows SHAP-highlighted words influence BD/DR bias probabilities beyond controls.  
2. **Plausibility:** SHAP overlaps short lexical evidence (BASIL and new humans) above length-matched chance; informational / long spans are poor sentence-local targets.  
3. **Comparative:** On paired data, models share much attribution mass but differ in alignment strength (DR ≥ BD on lexical excess); do not overclaim “same mechanism.”  
4. **Methodological correction:** Prior Em/Ev dominance was a coding artifact; evaluation uses transparent categories and baselines.

---

## GO assessment

**CONDITIONAL GO** for manuscript rewrite — see stop section in `ARR_M3_REWRITE_BLUEPRINT.md`.
