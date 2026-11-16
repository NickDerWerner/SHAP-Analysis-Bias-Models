# ARR M4E-4 — Reproducibility and Submission-Readiness Audit

**Date:** 2026-11-16  
**Manuscript (read-only):** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** Audit only — **no LaTeX, bib, title, figure, or experiment edits**.  
**Status:** Complete.

---

## 1. Executive summary

Scientific main-text revision (M4A–M4E-3) is largely coherent. The manuscript is **not ARR-submission-ready**.

**Primary blockers**

1. **Anonymity leaks** for two-way anonymized review: filled `\author{…}` (Ghosh, Werner, Kasneci) and a non-anonymized GitHub URL (`NickDerWerner/…`) in the Introduction.  
2. **Page budget unverified** and likely tight/over: ~10.4k main-body words + dense Results/Methods under an **8-page content** long-paper cap (Limitations/Ethics/refs/appendix excluded per ARR).  
3. **Human-study / license checklist gaps (T29)** incomplete relative to prior ARR form answers (D=N/A; B2 licenses=No).  
4. **Title still claims “Decision Mechanisms.”**  
5. **Eight open `\revnote`s** will appear as yellow TODOs under `\usepackage[review]{acl}`.

**Compilation:** **UNVERIFIED** (no local LaTeX engine). All current `\includegraphics` paths resolve on disk after M4E-2a.

---

## 2. Reproducibility matrix

Classes: **A** regenerable from available artifacts · **B** recomputable from caches (not fully regenerable) · **C** partial (missing provenance) · **D** unverified

| Experiment / reported values | Code | Data / version | Models | Env / seeds | Key inputs | Key outputs | Class | Notes |
|------------------------------|------|----------------|--------|-------------|------------|-------------|-------|-------|
| BABE/BASIL classification (F1, AUPRC, sweep) | `scripts/basil_eval.py`, `compute_metrics.py`, `threshold_sweep.py`, `babe_auprc.py` | BABE HF `mediabiasgroup/BABE` (test 1000); BASIL CSV matched to `launchnlp/BASIL` @ **`4fdbc4f`** | `himel7/bias-detector`; `mediabiasgroup/DA-RoBERTa-BABE-FT`; local `models/deberta-base-babe-ft` | `requirements-arr-m2.txt`; analysis seed **7**; Deb train seed **42** (documented historically) | Prediction CSVs under `outputs/basil/` | `auprc_table.csv`, `threshold_sweep_table.csv`, metrics tables | **B** (BD/DR); **C** (Deb) | Deb checkpoint **missing** locally (`models/` absent). Metrics recompute from stored predictions without Hub. |
| Original SHAP generation | `analysis.py`, `basil_shap_generate.py` | Same corpora | Same | **`shap` not in** `requirements-arr-m2.txt`; historical comment ~0.51-style; current venv often **without shap** | Tokenizers + models | `outputs/shap_samples*.jsonl`, `outputs/basil_shap/` | **C** | Text masker + Explainer documented in Methods; **no pinned shap version**; bit-identical regen unverified. |
| Word-level aggregation | `basil_shap_generate.py`, `scripts/fix_deberta_word_aggregation.py`, `scripts/arr_m1/word_aggregation.py` | SHAP JSONL caches | Deb repair path | Analysis seed 7 | Cached `tokens`/`shap_pos` | Repaired `word_attribs`; `outputs/arr_m1/deberta_integrity/` | **B** | Re-aggregation from caches is strong; original buggy Deb path archived as `.bak`. |
| M2B perturbation sensitivity | `scripts/arr_m2/*faithfulness*`, `offset_alignment.py` | Paired BASIL SHAP ∩ | BD/DR only | Seed **7**; device logged `mps` in `run_meta.json` | SHAP caches + models for forwards | `outputs/arr_m2b/medium_*.csv`, `run_meta.json` | **B** | Tables recomputable from CSVs; full regen needs Hub models + torch. Deb excluded by design. |
| M2C/M2D gold-span + coverage | `scripts/arr_m2c/*`, `arr_m2d/*` | BASIL spans @ `4fdbc4f` | Cache models | Seed 7; 20 random draws | Caches + span maps | `outputs/arr_m2c/`, `outputs/arr_m2d/` | **B** | Strong cache-based recomputation; raw BASIL clone still needed for from-scratch span rebuild. |
| M3R human IAA + SHAP–human | `scripts/arr_m3*` / M3R runners | Blind sample seed 7, n=120 | Cache ∩ only | Local κ impl.; MD5-stable baselines | `human_raw/annA|annB.json` (AnnB SHA `5d845836…`) | `outputs/arr_m3r/` | **A/B** | Derived stats regenerable from frozen JSON + caches; do **not** script-edit annotations. |
| M1 paired attribution similarity | `scripts/arr_m1/*paired*` | BABE/BASIL caches | BD–DR primary; all-3 limited | Seed 7 | SHAP JSONL | `outputs/arr_m1/paired/` | **B** | Jaccard/cosine from caches; no bootstrap CIs were computed for medians. |

**Rule applied:** numerical summaries alone ≠ full reproducibility. SHAP **regeneration** remains **C** until shap pin + model revisions + Deb checkpoint are recovered.

---

## 3. Model and SHAP provenance

| Item | Known | Missing / unverified |
|------|-------|----------------------|
| HF IDs | `himel7/bias-detector`; `mediabiasgroup/DA-RoBERTa-BABE-FT` | **Revision hashes not frozen** |
| DeBERTa | Fine-tuned from `microsoft/deberta-base` → intended path `models/deberta-base-babe-ft` | Checkpoint **absent** on audit machine; Hub upload status unverified |
| Training hyperparams | Partial in `finetune_deberta_babe.py` / docs | Full seed/val/selection criterion not in manuscript appendix (T09) |
| SHAP API | `shap.Explainer` + `shap.maskers.Text(tokenizer)`; softmax biased class; **no** test-set background | **Library version unpinned**; generation-time env ≠ current analysis venv |
| Seeds | Analysis/sampling/bootstrap **7**; Deb train historically **42** | Must not conflate |
| Stochastic eval | Sentence bootstrap ~2000 in analyses | Multiplicity not globally corrected (disclosed) |

Do **not** invent revision hashes or shap versions. Distinguish historical generation metadata from the currently installed `requirements-arr-m2.txt` stack (torch 2.14.1, transformers 5.20.2, …).

---

## 4. Ethics and artifact-release checklist (T29)

### Verifiable from records (already in Ethics/Methods)

- Two independent annotators; blind to model/SHAP/gold.  
- n=120; seed-7; 30×4 strata.  
- Shared written instructions / pack.  
- Study IDs `annA`/`annB` in analyzed JSON.  
- Yes∅spans policy disclosed.  
- HITL / misuse warnings present.

### Requires author confirmation (do not invent)

1. Recruitment / roles / expertise.  
2. Voluntary participation.  
3. Compensation.  
4. Informed consent (form/process).  
5. IRB/ethics: required / obtained / waived / **not sought** (institution).  
6. Withdrawal rights.  
7. Residual PII outside study IDs.  
8. Release plan for raw annotations (public / restricted / private).  
9. Licenses: BABE, BASIL, Hub models, code, annotations.  
10. ARR Responsible NLP checklist update: prior submission marked **D Human Subjects = No** and **B2 licenses = No** — must be reconciled with the reported human study.

---

## 5. LaTeX and bibliography findings

| Check | Result |
|-------|--------|
| `\includegraphics` paths | All **7** resolve at Overleaf root (M4E-2a fixed) |
| Undefined `\ref` | **None** (active text) |
| Duplicate `\label` | **None** |
| Missing cite keys vs `custom.bib` | **None** |
| Open `\revnote` | **8** (T08, T09, optional magnitude×2, optional overall perf, optional word lists, T24, T29) |
| Template | `\usepackage[review]{acl}` |
| Authors | **Present** (not anonymized) |
| GitHub URL in Intro | **Deanonymizing** |
| Bib before appendix | Yes (ARR-compatible) |
| Conclusion before Limitations | Yes — matches ARR “Limitations after conclusion” |
| Compilation | **UNVERIFIED** |

### Overleaf compile steps (when available)

1. Ensure project root contains `acl_latex.tex`, `custom.bib`, `acl.sty`, `revision_macros.tex`, and all figure assets.  
2. Compile with pdfLaTeX (or Overleaf default) **twice** for refs.  
3. Confirm page count of content through Conclusion (≤8).  
4. Confirm Limitations/Ethics start after Conclusion and are excluded from the 8-page count.  
5. Switch to anonymous author block + anonymized code link before ARR upload.  
6. Remove or comment `\revnote`s for clean review PDF (or keep only if intentionally signaling TODOs — not recommended for final ARR PDF).

---

## 6. Verified ARR submission requirements

Source: [ACL Rolling Review CFP](https://aclrollingreview.org/cfp) (fetched 2026-11-16) and ACLPUB formatting guidance.

| Requirement | Status vs this MS |
|-------------|-------------------|
| Long paper ≤ **8 content pages** | **At risk / UNVERIFIED** until PDF page count |
| Unlimited refs | OK |
| **Limitations required** after conclusion | Present |
| Ethical considerations optional (recommended) | Present |
| Appendix after references; not for core claims | Structure OK; appendix is supplementary |
| Two-way anonymized review | **Failing** (authors + GitHub) |
| Supplementary software/data anonymized | GitHub link not anonymized |
| Responsible NLP checklist accurate | **Out of date** vs human study / licenses |
| Main paper self-contained | Mostly yes after M4 rewrite |
| From Oct 2026: sustainable reviewing / service contributor rules | **Confirm for the specific cycle** before submitting; policy may apply |

Assumptions vs facts: exact future-cycle deadlines and service-contributor mechanics must be re-checked on the CFP for the intended submission month; the **8-page + Limitations + anonymity** rules above are confirmed on the live CFP.

---

## 7. Remaining scientific issues

| ID | Issue | Severity class |
|----|-------|----------------|
| Anonymity (authors + GitHub) | Desk-reject risk | **Submission blocker** |
| Page count >8 (suspected) | Desk-reject / forced cuts | **Submission blocker until measured** |
| Title “Decision Mechanisms” | Scientific overclaim | **Important** (author decision) |
| T29 ethics/licenses | Checklist integrity | **Important / blocker for honest checklist** |
| T09 model pins / Deb checkpoint | Repro score | **Important limitation** (disclose if unrestored) |
| T08 BABE–BASIL overlap | Unverified | **Manageable limitation** (already said UNVERIFIED) |
| T24 Significance catalogue | Density / readability | **Optional improvement** (also helps pages) |
| T30 figure fonts | Presentation | **Optional** |
| Optional magnitude-band notes | Not required after calibration retirement | **Deferred / optional** |
| SHAP version pin | Repro | **Important limitation** |
| Phrase-level / paraphrase | Reviewer wish | **Deferred future work** |

No new experiments are required for submission honesty if missing provenance is **disclosed** and anonymity/page/checklist issues are fixed.

---

## 8. Severity-ranked blockers

1. **Anonymize** author block; replace GitHub with Anonymous GitHub / supplementary zip.  
2. **Compile on Overleaf** and measure content pages; cut if >8 (prefer Significance condensation + redundant magnitude prose before gutting Methods CIs).  
3. **Author-complete T29** + update Responsible NLP checklist (human subjects; licenses).  
4. **Title decision** (recommended: *Evaluating SHAP Explanations for News Bias Detection: Prediction Sensitivity and Human Evidence Alignment*).  
5. Clear or hide **`\revnote`s** for the review PDF.  
6. Add a short **model/repro card** (Hub IDs; “revision unknown”; shap unpinned; Deb checkpoint availability) — appendix or Limitations one-liner if space.

---

## 9. Title assessment (no edit)

| Title | Fit |
|-------|-----|
| Current: “…**Decision Mechanisms**” | **Poor** — overstates recoverability of mechanisms; conflicts with Abstract/Conclusion |
| Proposed: “Evaluating SHAP Explanations for News Bias Detection: Prediction Sensitivity and Human Evidence Alignment” | **Good** — matches RQs 1–3; concise; ACL-suitable; slightly under-mentions paired overlap (acceptable in subtitle economy) |

Recommendation: adopt the proposed title on author approval (separate module).

---

## 10. Recommended minimal correction sequence

| Order | Module | Action |
|------:|--------|--------|
| **1** | **M4E-5a — Submission packaging** | Anonymize authors; anonymize code URL; remove/comment `\revnote`s for review PDF; optional title swap on approval |
| **2** | **M4E-5b — Page-budget pass** | Overleaf compile; if overlength, condense `sec:significance` (T24) and any residual repetition |
| **3** | **M4E-5c — Ethics/checklist answers** | Author questionnaire → Ethics + ARR form (T29); license sentences |
| **4** | **M4E-5d — Repro disclosure** | Model card / appendix table: IDs, missing revisions, shap unpinned, Deb path (T09) — **no invented hashes** |
| 5 | Final | Full Overleaf PDF + checklist + resubmission letter |

**First small corrective module for approval:** **M4E-5a (anonymization + title + revnote cleanup)**.

---

## 11. Remaining TODOs (TeX `\revnote`)

| Note | ID |
|------|-----|
| Data protocol / overlap | T08 |
| Model pins / Deb hyperparams | T09 |
| Magnitude confidence (×2) | Optional |
| Overall performance AUROC/ECE | Optional |
| Global word lists | Optional |
| Statistical inference catalogue | T24 |
| Human-study procedural disclosures | T29 |

---

## 12. Stop confirmation

- No manuscript edits in this module.  
- No bibliography/title/figure/experiment changes.  
- Next work requires explicit author approval (recommend M4E-5a).

*State updated in `docs/ARR_M4_REVISION_STATE.md`.*
