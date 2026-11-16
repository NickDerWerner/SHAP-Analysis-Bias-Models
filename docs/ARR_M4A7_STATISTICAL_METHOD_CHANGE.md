# M4A-7 Change Record — Sampling, Stats, and Evaluation Metrics

**Date:** 2026-11-13  
**File:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope only:**  
- `\subsection{Stratified Sampling Strategy}` `\label{sec:sampling}`  
- `\subsection{Analysis Framework}`  
- `\subsection{Statistical Significance Testing}` `\label{sec:stats}`  
- `\subsection{Evaluation Metrics}` `\label{sec:metrics}`  

**Not edited:** faithfulness / gold-span / human subsections; Results; Abstract; Intro; Related Work; Conclusion; Limitations; Ethics; appendices.

---

## TODOs

| ID | Action |
|----|--------|
| **T12** Sampling | **Resolved** — actual cache sizes, seed 7, unpaired BABE, multi-stratum BASIL, no reweighting; `\revnote` removed |
| **T16** Threshold / ECE / AUROC | **Methods resolved** — t=0.5 + AUPRC + sweep disclosure; **no** ECE/Brier/AUROC invented; old `\revnote` removed |
| **T17** Confidence control | **Narrowed** to Results-facing `\revnote{TODO P1 \| Magnitude confidence (Results)}`; methods state mean \|SHAP\| ≠ calibration |
| T13/T14 taxonomy & similarity | **Untouched** (still in Analysis Framework) |

Open `\revnote`s after edit: **24** (was 26; −T12 −T16; T17 replaced by one residual).

---

## Evidence map

| Claim | Source |
|-------|--------|
| t=0.5 cell defs | `analysis.py` pred; consistency check; caches `pred_vs_0.5_mismatch=0` |
| BABE full n=1000; BASIL n=7984 | Dataset section / metrics tables |
| Seed 7 | `analysis.py`, `basil_shap_generate.py`, M2*/M3* |
| BABE BD 337 (100/37/100/100), DR 312 (100/12/100/100), Deb 327 (100/27/100/100) | `outputs/shap_samples*.jsonl`; `ARR_CODEBASE_AUDIT` |
| BABE unpaired; ∩ DR 127; all3 59 | `outputs/arr_m1/paired/babe_coverage.csv` |
| BASIL multi-stratum caps → BD 850, DR 837; Deb magnitude 400 | `basil_shap_generate.py` `STRATA_CAPS` + caches |
| BD∩DR 371; all3 60 | `basil_coverage.csv` |
| M2B 200 TP85/FP60/FN52/TN3 | M4A-5 / M2B outputs |
| M2C all eligible positives | M2C coverage.json |
| Human 120 = 30×4 GOLD strata | `human_annotation_sample.csv` `GOLD_category` Counter |
| McNemar + continuity | Notebook; Dietterich cite; Results still has numbers |
| Mann–Whitney + rank-biserial on cache \|SHAP\| | `scripts/shap_mannwhitney.py` |
| Sentence bootstrap seed 7, n_boot≈2000 | M2B/M2C/M3 code |
| AUPRC BD/DR BABE+BASIL; no ECE/Brier/AUROC in methods | `babe_auprc.txt`, `basil/auprc_table.csv` |
| Threshold sweep (discrete t) | `threshold_sweep_table.csv`, `arr_consistency/basil_full_threshold_confusion.csv` (incl. Deb F1@t) |

---

## Human-sample verification (M4A-6 cross-check)

| Statement in M4A-6 | Verified? | Source |
|--------------------|-----------|--------|
| 120 sentences; seed 7; 30 lex / 30 inf / 30 both / 30 non-biased | **Yes** | `Counter(GOLD_category)` on `outputs/arr_m2c/human_annotation_sample.csv` |

**No M4A-6 correction required.**

---

## Cross-section contradictions (reported; not edited)

1. **Prior Sampling claim (fixed here):** “BASIL … 100 instances per cell” was **false** for BD/DR (multi-stratum union → 850/837). Corrected in M4A-7.  
2. **Results (unapproved):** Overall performance still says all three models retain AUPRC with lift 1.79–2.03×; checked `auprc_table.csv` has **BD/DR only** (no DeBERTa BASIL AUPRC row). **Flag for M4B** — do not invent Deb AUPRC in Methods.  
3. **Results calibration language** (“calibration rather than mechanism”) conflicts with Methods “mean \|SHAP\| ≠ calibration” — **M4B/M4C** must revise Results wording.  
4. Faithfulness / gold / human subsections: **no factual contradiction** with this module; left unchanged.

---

## Scientific corrections

- Explicit non-interchangeable populations + summary Table~\ref{tab:eval_populations}.  
- Corrected BASIL cache construction narrative.  
- Stated BABE SHAP unpaired by default.  
- Separated McNemar / Mann–Whitney / sentence bootstrap / κ by use case.  
- Removed calibration implication from metrics; refused ECE/Brier/AUROC invention.

---

## Page-budget note

Methodology section ≈ **3050 words** after M4A-5/6/7 inserts (rough split). ACL long-paper Methods risk **over-length**; author review should consider moving Table~\ref{tab:eval_populations} and detailed cache strata to an appendix if page pressure bites. M4A-7 itself added ~1 compact table + ~1 column of prose net of deletions.

---

## Compile status

**UNVERIFIED** (no LaTeX engine on PATH). Brace balance OK on edited chunks.

---

## Diff hygiene

Only the four approved subsections (+ new table inside Sampling). Faithfulness/gold/human blocks untouched.
