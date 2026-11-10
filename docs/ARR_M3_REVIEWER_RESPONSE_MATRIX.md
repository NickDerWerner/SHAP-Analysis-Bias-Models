# ARR M3 — Reviewer / Professor Response Matrix

Statuses: **Resolved** / **Partly resolved** / **Unresolved** / **Deferred (disclosed)**

---

## Meta-review (AC dgcp)

| Concern | Status | Evidence / plan |
|---------|--------|-----------------|
| Scope related work to encoders; add decoder LLM citations | **Partly** | Rewrite-only; no new LLM experiments |
| Define taxonomy; SHAP background; token→word; BASIL lex/inf; cautious “attend to” | **Resolved** (evidence) / rewrite pending | M1 taxonomy + Other; M2B alignment; M1 spans; claim ledger |
| Core conclusions not artifacts of confidence/threshold | **Partly** | M2D prob bands; M2B strata; full model-specific thresholds still light |
| Address MqgQ/xw7D/k62P substantively; shorten abstract; examples | **Partly** | Analyses done; manuscript rewrite not started |

---

## Reviewer MqgQ

| Concern | Status | Notes |
|---------|--------|-------|
| BASIL lexical vs informational use/justification | **Resolved** | Analyzed separately; informational caveats (M2C–M3) |
| Span- vs sentence-level annotation handling | **Resolved** | Documented span→sentence; human spans at char offsets |
| What “generalization” means (perf vs attribution) | **Unresolved** (wording) | Clarify in rewrite: attribution patterns + paired errors, not zero-shot LLM gen |
| Sampling / why not all instances | **Partly** | M2C used all eligible caches; human study is stratified 120 |
| Phrase-level attributions | **Deferred** | Disclose limitation; word-level only |
| Abstract length / figures / examples | **Unresolved** (writing) | Blueprint lists concrete examples from M2D/M3 |

---

## Reviewer xw7D

| Concern | Status | Notes |
|---------|--------|-------|
| Encoder-only related work; “backbone of modern” overclaim | **Partly** | Cite decoder LLMs; scope claims |
| SHAP faithfulness untested | **Resolved** | M2B perturbation sensitivity |
| Magnitude ≈ confidence; SHAP redundant for calibration | **Partly** | Soften calibration narrative; keep faithfulness + plausibility as SHAP-specific value |
| Shared 0.5 threshold for TP/FP/TN/FN | **Partly** | Prob-band analyses; optional model-specific thresholds still open |
| Taxonomy undefined | **Resolved** | Retract Em/Ev; document Other + BASIL types |
| Normalization / background underspecified | **Partly** | Offset alignment documented; background still must be written from generation logs |
| Reproducibility score 1 concerns | **Partly** | Caches + scripts + tests; shap pin / background still gaps |

---

## Reviewer k62P

| Concern | Status | Notes |
|---------|--------|-------|
| Taxonomy never defined; Em/Ev backbone | **Resolved** | M1 invalidation; remove as main claim |
| Narrow scope / uneven DeBERTa | **Partly** | Explicit two-model primary design |
| Dense writing / abstract ratios | **Unresolved** (writing) | Rewrite blueprint |

---

## Professor Kasneci

| Concern | Status | Notes |
|---------|--------|-------|
| Faithfulness analysis | **Resolved** | M2B |
| Manual labels vs SHAP | **Resolved** (with limits) | M3 annA/annB; missingness on B; limited cache∩sample |
| Disentangle tokens vs semantic evidence (paraphrase) | **Deferred** | Future work; paired comparisons only for now |
| Model differences: cues vs architecture | **Partly** | Paired DR>BD lexical excess; no paraphrase causal design |
| Define Em/Ev etc.; why Emotional large; dummy category | **Resolved** | Catch-all → Other; Em/Ev retracted |

---

## Unresolved reviewer objections (must address in text even if not with new experiments)

1. Background dataset for SHAP TextExplainer (exact set).  
2. Decoder-LLM related work + scoped claims.  
3. Soften/remove “same mechanism / calibration” as primary thesis.  
4. Threshold sensitivity beyond 0.5 (at least discuss; ideally one robustness check if cheap).  
5. Writing: abstract, figures, terminology (inferential vs informational).  
6. Phrase-level / multi-word expressions.

**Not blockers for starting rewrite** if deferred items are honestly limited.
