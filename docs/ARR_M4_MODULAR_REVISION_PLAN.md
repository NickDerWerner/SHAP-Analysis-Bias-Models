# ARR M4 — Modular Revision Plan

**Date:** 2026-11-13  
**Manuscript root:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Rule:** One small module per approval cycle. **No edits until author approves the named module.**  
**Phase order (proposal):** M4A Methods → M4B Results → M4C Discussion/Limitations → M4D Intro/Related → M4E Conclusion/Abstract → M4F figs/tables/refs/responses.

Priority: **scientific validity over style.**

---

## Recommended first module

### **M4A-1 — SHAP-Based Interpretability Framework** (`acl_latex.tex` ~L412–428)

**Why first:** Contains a **false methods statement** (test-set background) that undermines reproducibility and reviewer xw7D/AC trust. Fix is local, evidence-complete, and unlocks honest Results framing. Does not require rewriting Abstract/Intro first.

| Field | Content |
|-------|---------|
| Location | `\subsection{SHAP-Based Interpretability Framework}` L412–428 |
| TODOs | **T10** (modify intent) |
| Problem | Claims TextExplainer + attributions “against a background dataset of test-set sentences” — **not implemented** |
| Proposed edits | Replace with: `shap.Explainer` + `shap.maskers.Text(tokenizer)`; mask-token reference behavior; softmax biased-class output; seed 7 for analyses; disclose shap version unknown/unpinned if not recovered; cite Lundberg; **no invented background corpus** |
| Evidence | `analysis.py` L527–538; `basil_shap_generate.py` L373–374; `ARR_PRE_REWRITE_CONSISTENCY_CHECK.md` §1; `ARR_CODEBASE_AUDIT.md` §1.4 |
| Reviewer/professor | xw7D #5 background; AC methods clarity; Kasneci (enables trustworthy faithfulness section later) |
| Risk | Low if wording stays minimal; Medium if author wants exact historical shap pin (**UNVERIFIED** without logs) |
| Acceptance criteria | (1) No test-set background claim; (2) masker/output space correct; (3) T10 marked resolved with rationale; (4) no new unsupported claims; (5) LaTeX still includes `\revnote` until author okays removal |

**Downstream:** M4A-2 aggregation; M4A-5 faithfulness protocol subsection; later Abstract must not reintroduce background myth.

---

## Module catalog

### Phase M4A — Methodology

| Module | Location | TODOs | Problem | Proposed edits (summary) | Evidence | Reviewer | Risk | Acceptance |
|--------|----------|-------|---------|--------------------------|----------|----------|------|------------|
| **M4A-1** SHAP framework | L412–428 | T10 | False background | Correct Explainer/masker/output | Code + consistency | xw7D, AC | Low | Methods match code |
| **M4A-2** Word aggregation | L431–446 | T11 | Underspecified | Point to offset/sum algorithm; M2B tests; phrase-level = limitation | M2B tests, `offset_alignment` | xw7D | Low | Auditable description |
| **M4A-3** Task harmonization | ~L350–411 + new paras | T07 | BABE vs BASIL unclear | Sentence vs span; lex/inf definitions; union rule; counts | M1 BASIL; preprocess | MqgQ | Med | Worked example + counts |
| **M4A-4** Models & scope | ~L387–403 | T09 | DeBERTa uneven; missing IDs | Hub IDs; local DeBERTa path; primary BD/DR; secondary Deb | `basil_eval.py` | k62P | Med | No false 3-model symmetry |
| **M4A-5** Faithfulness protocol (new) | After SHAP methods | T15 (modify) | Missing despite M2B | Add M2B masking protocol (budgets, controls, TP/FP, TN n=3) | `ARR_M2B_*`, `outputs/arr_m2b/` | Kasneci, xw7D | Low | Sensitivity ≠ reasoning |
| **M4A-6** Plausibility protocol (new) | After A-5 | T23 (modify) | Missing M2C/D/M3R methods | Gold-span + human-span metrics, random baselines, coverage match, IAA policy | M2C/D/M3R | MqgQ, Kasneci | Med | Disclose yes∅spans, cache∩sample |
| **M4A-7** Taxonomy retraction | Replace Em/Ev methods | T13 (modify) | Catch-all | Document Other audit; stop Em/Ev as main taxonomy | M1 | k62P, Kasneci | Med | 90–96% retracted in methods |
| **M4A-8** Sampling & threshold disclosure | L448–513 | T12, T16, T17 | 100/cell; t=0.5 | Disclose seeds, strata, t=0.5; cite sweep/AUPRC; confidence bands | Caches; `arr_consistency/` | MqgQ, xw7D, AC | Med | No false pairing |
| **M4A-9** Data protocol (verify) | L379 | T08 | Overlap UNVERIFIED | Only after author/verify article overlap | M1 | — | High if guessed | No invented overlap claims |

### Phase M4B — Results

| Module | Location | TODOs | Problem | Proposed edits | Evidence | Reviewer | Risk | Acceptance |
|--------|----------|-------|---------|----------------|----------|----------|------|------------|
| **M4B-1** Faithfulness results (new primary) | New § before/instead of magnitude primacy | T15 | Missing | F1/F2 + tables; BD/DR; no TN claim | `outputs/arr_m2b/` | Kasneci | Low | CIs + controls stated |
| **M4B-2** Plausibility BASIL | New / replace category-led story | T23 | Missing / wrong lex≫inf | P1–P3; coverage-matched caveat | M2C/D | MqgQ | Med | No unqualified lex≫inf |
| **M4B-3** Human study M3R | New | — | Absent | HH κ, SHAP–human, BASIL≠humans | `outputs/arr_m3r/` | Kasneci | Med | Exact M3R numbers + SHA note in repro |
| **M4B-4** Magnitude downgrade | L559–664 | T19, T17 | Calibration levels | Confidence-controlled; remove three calibration levels | M2D P4 | xw7D | Med | No magnitude=calibration |
| **M4B-5** Category results rewrite | L696–802 | T22 | Em/Ev dominance | Other audit table; not Em/Ev headlines | M1 | k62P | High (large) | 90–96% gone |
| **M4B-6** Paired overlap / errors | Shared FP/FN | T20, T25, T26 | Mechanism language | Paired n only; weaken two-pathway | M1; T26 | xw7D | Med | Descriptive not causal |
| **M4B-7** Overall performance | L514–557 | T18 | Table 1 gaps | Update only verified metrics | basil metrics | xw7D | Med | No fake AUROC |
| **M4B-8** Stats section slim | L804–866 | T24 | Catalogue | Move tests next to findings | — | xw7D | Low | Readable |

### Phase M4C — Discussion / Limitations / Ethics

| Module | TODOs | Focus | Evidence |
|--------|-------|-------|----------|
| **M4C-1** Limitations | T28 | Mask OOD; TN n=3; Deb; human yes∅spans; cache∩sample; no paraphrase; encoder-only; t=0.5 | M3R, consistency |
| **M4C-2** Ethics/repro | T29 | Licenses B2; human annotators D1–D3 (**author facts needed**) | Checklist |
| **M4C-3** Discussion (if present / fold into Conclusion) | — | Faithfulness≠plausibility; no mechanism overclaim | Ledger |

### Phase M4D — Introduction / Related Work

| Module | TODOs | Focus |
|--------|-------|-------|
| **M4D-1** Related work decoder LLMs | T05, T06 | Scope encoders; add cites (verify bib) |
| **M4D-2** Intro RQs + contributions | T03, T04 | Match ledger short list |
| **M4D-3** Shared example | T02 | Replace/qualify Cold War |

### Phase M4E — Conclusion / Abstract

| Module | TODOs | Focus |
|--------|-------|-------|
| **M4E-1** Conclusion | T27 | Supported findings only |
| **M4E-2** Abstract | T01 | ~150–200 words; no Em/Ev; no same-mechanism/calibration |

### Phase M4F — Presentation / responses

| Module | TODOs | Focus |
|--------|-------|-------|
| **M4F-1** Figures/tables swap | T30, blueprint fig list | Add F1–F2, P1–P5, T4 M3R; retire Em/Ev pies |
| **M4F-2** Reviewer response letter | — | Map to matrix; no invented objections |
| **M4F-3** Final consistency | — | Numbers vs `outputs/arr_*` |

---

## Proposed rewrite sequence (modules)

1. **M4A-1** SHAP methods correction ← **start here**  
2. M4A-2 Aggregation  
3. M4A-5 Faithfulness protocol  
4. M4A-6 Plausibility + human protocol  
5. M4A-7 Taxonomy retraction  
6. M4A-3 Task harmonization  
7. M4A-4 / M4A-8 Models + sampling/threshold  
8. M4B-1 → M4B-3 core new results  
9. M4B-4 → M4B-6 rewrite/downgrade old results  
10. M4C limitations/ethics  
11. M4D intro/related  
12. M4E conclusion/abstract  
13. M4F figures + responses + audit  

---

## Explicit non-goals (unless author re-opens)

- New SHAP generation / GPU experiments  
- Decoder LLM experiments  
- Phrase-level attribution system  
- Paraphrase disentangling study  
- Inventing human labels or fusing annA+annB gold  
- Editing `SHAP-Analysis-Bias-Models/docs/references/paper.tex` instead of Overleaf  

---

*Await author approval of **M4A-1** before any `acl_latex.tex` edit.*
