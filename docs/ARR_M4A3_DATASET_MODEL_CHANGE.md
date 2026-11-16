# M4A-3 Change Record — Dataset and Models

**Date:** 2026-11-13  
**File:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** `\subsection{Dataset and Models}` only  

---

## TODOs

| ID | Action |
|----|--------|
| **T07** BABE/BASIL harmonization | **Resolved** — sentence vs span, union rule, quotes, strata counts, prevalence |
| **T08** Data protocol | **Still pending** (narrowed) — BABE–BASIL overlap audit; fuller split documentation |
| **T09** Models | **Partially resolved** — Hub IDs, DeBERTa local path/caches, no SOTA, uneven inclusion; **pending** revision pins + fine-tune hyperparams (kept `\revnote`) |

---

## Evidence map (key numbers)

| Claim | Source |
|-------|--------|
| BABE HF `mediabiasgroup/BABE`; test split for SHAP/eval | `analysis.py` `--dataset` / `--split test` |
| BABE test 1000; 559 pos (55.9%) | Training-time confusion TP+FN=559 in `deberta_paper_parity.py` notes |
| HF release ≠ SG1/SG2 | Existing manuscript footnote; retained |
| BASIL `launchnlp/BASIL` @ `4fdbc4f`; 7984/7984 match | `ARR_BASIL_SPAN_ALIGNMENT.md` |
| 1723 spans; 478 lex / 1245 inf; offset==txt | Same + M1 |
| CSV: 7984 sent; 1623 pos (20.3%); 405/1174/44 lex/inf/both | `basil_sentences.csv` |
| 100 events; 297 `article_uuid` | CSV (not 300 — discrepancy vs Fan “300 articles” noted) |
| Union label; quotes retained | `preprocess_basil.py` `sentence_features` |
| Models: `himel7/bias-detector`, `mediabiasgroup/DA-RoBERTa-BABE-FT`, `microsoft/deberta-base` → `models/deberta-base-babe-ft` | `basil_eval.MODELS`; `finetune_deberta_babe.py` |
| DeBERTa BABE-test AUPRC 0.948 / macro-F1 0.835 | Prior manuscript + `deberta_paper_parity.py` AUPRC note; macro-F1 retained as training-time report |
| Max length 256 | `finetune_deberta_babe.py` / `analysis.py` |
| Missing local DeBERTa ckpt | Consistency check; `models/` absent |

---

## Scientific corrections

- Removed “state-of-the-art” model-selection claim.  
- Clarified tasks are **not** equivalent; no causal story for BASIL drops.  
- Stated uneven three-model coverage and caches-only DeBERTa when checkpoint missing.  
- Replaced vague “300 articles / ~20%” with verified CSV counts; noted 297 article UUIDs.  
- Documented BASIL commit + span validation.  

---

## Unresolved / appendix candidates

| Item | Status |
|------|--------|
| BABE↔BASIL article/topic overlap | **UNVERIFIED** (T08) |
| Hub revision SHAs | Unpinned (T09) |
| Full DeBERTa fine-tune hyperparams / seed / val protocol | Deferred to appendix/model card (T09) |
| Why 297 vs published 300 articles | Likely preprocess/title drops; appendix note recommended |

---

## Compatibility

Uses encoder-only scope consistent with later SHAP methods (M4A-1/2). No TextExplainer / background-corpus language.
