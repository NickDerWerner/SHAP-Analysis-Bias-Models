# ARR M4 — Initial Scientific Risk Audit

**Date:** 2026-11-13  
**Manuscript:** `overleaf_latex/acl_latex.tex`  
**Evidence hierarchy:** M0–M3R artifacts + claim ledger > original reviews > manuscript/TODOs > background knowledge  

---

## 1. Workspace facts

| Item | Path / status |
|------|----------------|
| Experiment repo | `ExplainingBias/SHAP-Analysis-Bias-Models/` |
| Overleaf project (this machine) | `/Users/go52nom/Downloads/overleaf_latex/` (also Cursor workspace root) |
| Main TeX | **`acl_latex.tex`** (monolithic; `\input{revision_macros}`) |
| Bib | `custom.bib` |
| Compile locally | **`pdflatex` not installed** → compile status **UNVERIFIED** on this machine |

---

## 2. Five most serious manuscript risks

| Rank | Risk | Where | Why it threatens validity | Evidence |
|-----:|------|-------|---------------------------|----------|
| 1 | **Em/Ev 90–96% + “attend to same lexical content” as core finding** | Abstract L157; Word-Level Patterns ~L719+; Conclusion | Category is catch-all Other; dominance is coding artifact | M1; claim ledger **Remove** |
| 2 | **“Same mechanism / different calibration” thesis** | Abstract L161–165; Intro L254–269; Magnitude ~L647–662; Conclusion | Equates token overlap & SHAP magnitude with shared reasoning and calibration; rejected by xw7D; magnitude≠calibration | Claim ledger; consistency check; xw7D #2–3 |
| 3 | **False SHAP background (“test-set sentences”)** | Methods L415–418 | Factual methods error; reproducibility score risk | Code: `shap.maskers.Text(tokenizer)` only |
| 4 | **Missing faithfulness≠plausibility narrative; no M2B/M2C/M3R in Results** | Methods/Results structure | Kasneci + xw7D required faithfulness; paper still implies SHAP=reasoning without reporting completed tests | M2B–M3R exist but not integrated |
| 5 | **Unqualified lex≫inf / informational recovery; two-pathway independence** | Results / Conclusion L866 note | Coverage confound (M2D); independence claim weak (n=44) | M2D; T26 |

Additional serious (6–8): unpaired/three-model overclaim; t=0.5 strata without disclosure; human-study checklist still “no annotators” while M3R exists.

---

## 3. Claim ledger vs current manuscript prose

| Ledger action | Manuscript status |
|---------------|-------------------|
| Retain: attribution sensitivity (M2B) | **Absent** as primary result |
| Retain: lexical > random (M2C/D) | **Absent / incomplete** |
| Retain: paired DR≥BD lexical excess | **Absent** as stated |
| Retain: human SHAP>random (M3R) | **Absent** |
| Remove: Em/Ev 90–96% | **Still present** (abstract + results) |
| Remove: same-mechanism causal language | **Still present** |
| Revise: magnitude≠calibration | **Still asserts calibration levels** |
| Correct: SHAP background | **Still wrong** |
| Add: coverage-matched lex−inf caveat | **Missing** |
| Add: taxonomy retraction | **Missing** (TODO T13 still oriented to defining Em/Ev) |

---

## 4. What is already scientifically usable / preserve

Do **not** discard without cause:

- Cross-corpus BABE + BASIL motivation and label-philosophy contrast (needs clearer harmonization text).  
- Vocabulary-pool-size confound appendix (keep; stop framing as live “earlier finding” confusion in main text).  
- Paired error-overlap / Jaccard **when n and pairing are explicit**.  
- AUPRC and threshold-awareness fragments (expand disclosure, don’t invent ECE).  
- Word-aggregation *idea* (detail must match M2B/code).  
- Limitations seed paragraphs (must be expanded, not deleted).  
- Concrete qualitative examples machinery (replace weak Cold War framing).

---

## 5. Writing-quality risks (secondary to validity)

- Overlong abstract wall of ratios (MqgQ, k62P).  
- Dense Results catalogue; stand-alone “Statistical Significance Testing” section (xw7D).  
- Inconsistent “inferential” vs “informational” (xw7D).  
- Tiny figure fonts (MqgQ, xw7D).  
- Abbreviations Em/Ev etc. undefined (k62P).  

These matter for Findings acceptance but **must not** drive claim inflation.

---

## 6. Open scientific questions (author decisions)

1. **AUROC / ECE / Brier:** Compute from cached probs for Table 1, or drop calibration metrics entirely and remove calibration thesis?  
2. **New similarity metrics (T14):** Keep Jaccard-only or add vector similarities from existing paired caches (no new SHAP)?  
3. **DeBERTa:** Restore checkpoint for repro package vs permanently secondary/caches-only?  
4. **Ethics checklist:** Update D1–D3 for M3R annotators (payment/consent details may be **UNVERIFIED** — author must supply).  
5. **Phrase-level attributions:** Disclose limitation only (recommended) vs new experiment (out of scope unless approved)?  
6. **Title:** Keep until narrative settled (per instructions).

---

## 7. Compile / tooling

- Local `pdflatex`: **not found** → manuscript compile **UNVERIFIED** here.  
- Overleaf likely compiles (project has `acl.sty`, figures, bib); confirm on Overleaf after first edit module.

---

*End of risk audit. No manuscript edits performed.*
