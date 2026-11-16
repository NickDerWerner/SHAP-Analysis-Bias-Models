# M4A-1 Change Record — SHAP-Based Interpretability Framework

**Date:** 2026-11-13  
**File:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** `\subsection{SHAP-Based Interpretability Framework}` only  
**TODO:** T10 (`TODO TODO P0 -- SHAP methodology`) — resolved in prose; inline `\revnote` removed

---

## Original paragraph

```latex
We use SHAP \cite{lundberg2017unifiedapproachinterpretingmodel}, which 
assigns each feature an additive attribution based on Shapley values 
\cite{shapley1953}. We apply the SHAP library's TextExplainer with a 
Text masker, which handles tokenization and masking for transformer 
models and computes token-level attributions against a background 
dataset of test-set sentences. For each model, we construct a 
prediction function returning softmax probabilities and extract 
attributions for the positive (biased) class.
```

Plus yellow `\revnote{TODO TODO P0 -- SHAP methodology}{...}`.

---

## Revised paragraph

See current `acl_latex.tex` subsection (post-M4A-1): documents `shap.Explainer` + `shap.maskers.Text(tokenizer)`, softmax biased-class output, mask-token occlusion, explicit denial of a test-set background corpus, and a caution that attributions are not internal-reasoning evidence.

---

## Substantive changes → evidence

| Change | Source |
|--------|--------|
| `TextExplainer` → `shap.Explainer` | `analysis.py` L538; `basil_shap_generate.py` L374 |
| Text masker = `shap.maskers.Text(tokenizer)` | `analysis.py` L527; `basil_shap_generate.py` L373 |
| Remove “background dataset of test-set sentences” | No such argument in code; comment: masker replaces tokens with mask token (L526) |
| Softmax over logits → class probabilities | `build_predict_fn` / `softmax_np` in `basil_shap_generate.py` L64–79 |
| Positive (biased) class | `vals[:, positive_index]` / same in both generators |
| Not “internal reasoning / causal mechanisms” | Claim ledger; reviewer xw7D |

**Not claimed (unverified / unlogged):** pinned `shap` version; `max_evals`; named PartitionExplainer class; custom baseline sentence list.

---

## Downstream (not edited)

- Aggregation subsection still says “SHAP TextExplainer” (~former L442) → **M4A-2**.  
- Abstract/Intro may still imply methods myths elsewhere → later modules.
