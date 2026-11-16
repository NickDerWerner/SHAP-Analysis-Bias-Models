# ARR Pre-Rewrite Methodological Consistency Check

**Date:** 2026-11-13  
**Scope:** Consistency only — no new SHAP, no manuscript rewrite, no change to frozen scientific conclusions.  
**Companion outputs:** `outputs/arr_consistency/`

---

## 1. SHAP Text-masker configuration (verified against code)

| Setting | Implemented (authoritative) | Paper (~L415–420) | Action |
|---------|----------------------------|-------------------|--------|
| Entry point | `shap.Explainer(predict_fn, masker)` in `analysis.py` L527–538 and `basil_shap_generate.py` L373–374 | “TextExplainer” | Rewrite: say `shap.Explainer` / Partition+Text (SHAP API), not a nonexistent custom background TextExplainer setup |
| Masker | `shap.maskers.Text(tokenizer)` | Text masker — OK | Keep |
| Reference / “background” | **Mask-token occlusion defaults** of the Text masker; **no** sentence list / test-set corpus passed | “background dataset of test-set sentences” | **Misconception — correct in rewrite** |
| Output space | Softmax probabilities (`softmax_np` on logits); attributions for biased-class index | Softmax + positive class — OK | Keep; state explicitly |
| Aggregation | Sum of subword SHAP → words (BASIL whitespace-aware aggregator; M2B offset alignment for analyses) | Sum aggregation — OK | Cite M2B offset tests |
| `shap` pin | **Absent** from `requirements-arr-m2.txt`; code comments reference shap **0.51**-style tokens | Unspecified | Disclose generation-time version if known; else “caches only / version not pinned” |
| Seeds | Analysis / sampling / bootstrap seed **7** | — | Keep |

**Corrected documentation misconception:** Prior “must write the background sentence set” TODOs implied a corpus that was never implemented. Docs updated (`ARR_M3_REPRODUCIBILITY_CHECK.md`, blueprint, reviewer matrix, `ARR_REPRODUCIBILITY_GAPS.md` G-BG): **fix paper wording; do not invent a background corpus.**

---

## 2. Human-validation provenance (M3R)

| Check | Result |
|-------|--------|
| Authoritative AnnB path | `outputs/arr_m2d/human_raw/basil_blind_annotations_annB.json` |
| AnnB SHA-256 | `5d845836cb0d98ef4333a68510b74de068a4aaa0a4fa2cb800dcf4c2c0889619` |
| Recorded in | `outputs/arr_m3r/annotation_integrity.json`, `m3r_executive_numbers.json`, `ARR_M3R_ANNOTATION_CHANGE_REPORT.md` |
| File hash matches integrity record | **Yes** |
| Primary numeric outputs | `outputs/arr_m3r/` (not pre-M3R `outputs/arr_m3/`) |
| Pre-M3R preserved | `outputs/arr_m3_archive_pre_m3r/` |
| AnnA unchanged SHA-256 | `0e96e535b4db661b26eb6826e4706c1fc02505b07f89081536cc783a3cce3d5b` |

All reported M3R human metrics (HH, human–BASIL, SHAP–human) are derived from the updated AnnB file above.

---

## 3. Claim ledger & rewrite blueprint vs M3R numbers

| Quantity | M3R artifact | Ledger / blueprint |
|----------|--------------|--------------------|
| κ_present ≈ 0.44, n=120 | `hh_agreement_summary.json` | Claim ledger Retain + Revise rows — **aligned** |
| κ_type ≈ 0.24, n=119 | same | Aligned; still “weak / no strong type consensus” |
| AnnB yes∅spans = 26 | `m3r_executive_numbers.json` | Blueprint limitations + blockers — **aligned** |
| Clarification 32/55 resolved | `clarification_resolution_summary.json` | Ledger Remove row forbids “all 55 resolved” — **aligned** |
| SHAP∩sample BD34/DR42/Deb12 | `shap_sample_coverage.json` | Aligned |
| Verdict CONDITIONAL GO | `ARR_M3R_FINAL_DECISION_SUMMARY.md` | Blueprint stop section — **aligned** |

No ledger/blueprint edits required beyond the SHAP-background wording corrections already applied in this check.

---

## 4. Remaining unsafe paper claims (still in `paper.tex`; flagged for rewrite)

These are **draft text problems**, not new analysis findings:

| Claim pattern | Where (approx.) | Problem | Ledger status |
|---------------|-----------------|--------|---------------|
| 90–96% Emotional/Evaluative; models “attend to” same lexical content | Abstract L157; §results taxonomy | Coding artifact (M1 Other ~94%) | **Remove** |
| Same-mechanism / different-calibration | Abstract L161–164; Intro L254–269; magnitude §§ | Equates magnitude & overlap with shared reasoning / calibration | **Remove / revise** |
| Three calibration levels / TN calibration spectrum | Magnitude results ~L606–662 | Treats SHAP magnitude as calibration without confidence controls | **Revise / downgrade** |
| “background dataset of test-set sentences” | Methods L417–418 | **False vs code** | **Correct** |
| Unqualified lex ≫ inf from raw mass | (various) | Coverage confound (M2D) | **Revise** |

**Safe replacements already in ledger:** attribution-guided sensitivity; lexical plausibility above length-matched random; paired token overlap without “same mechanism”; coverage-matched lex−inf caveat.

---

## 5. Threshold 0.5 and TP/FP/TN/FN (cached predictions only)

**How 0.5 enters the pipeline:** stratified SHAP sampling and confusion labels use `pred = (prob_pos >= 0.5)` (`analysis.py` L501; BASIL prediction CSVs). Faithfulness (M2B) and many magnitude tables inherit those strata.

**Existing artifact:** `outputs/basil/threshold_sweep_table.csv` + `auprc_table.csv` (BD/DR).  
**This check added (no new SHAP):** `outputs/arr_consistency/basil_full_threshold_confusion.csv` (all three models), plus stratum reassignment tables for BABE/BASIL SHAP caches.

### BASIL full (n=7984) F1 at alternate thresholds

| Model | t=0.3 F1 | t=0.5 F1 | t=0.6 F1 | Note |
|-------|---------:|---------:|---------:|------|
| bias-detector | 0.404 | **0.376** | 0.355 | Operating point moves; ranking via AUPRC is threshold-free |
| DA-RoBERTa | 0.424 | **0.349** | 0.326 | Larger F1 swing than BD across 0.3–0.6 |
| DeBERTa | 0.323 | **0.288** | 0.270 | Same direction; absolute F1 lowest |

AUPRC (BD/DR, full view): BD ≈0.39, DR ≈0.41 (`auprc_table.csv`) — discrimination is not solely a 0.5 artifact.

### SHAP-cache label reassignment (same attributions; new threshold)

At t≠0.5, some cached sentences change TP/FP/TN/FN membership (e.g., BASIL BD TP 286→255 when t: 0.5→0.6). **Do not re-interpret faithfulness strata without stating they were sampled at 0.5.** Lightweight conclusion for rewrite: report t=0.5 as the analysis operating point; cite threshold sweep + AUPRC; do not claim mechanism findings are threshold-invariant without paired re-analysis (out of scope here).

---

## 6. Figures & statistical results — retain / replace / remove

| ID / result | Decision | Source artifact |
|-------------|----------|-----------------|
| Fig F1 faithfulness ΔP | **Retain** | `outputs/arr_m2b/figures/faithfulness_medium_budget2.pdf` |
| Fig F2 abs sensitivity | **Retain** | `outputs/arr_m2b/figures/abs_sensitivity_medium_budget2.pdf` |
| Fig P1 gold abs mass vs random | **Retain** | `outputs/arr_m2c/figures/abs_mass_vs_random.pdf` |
| Fig P2 excess lex vs inf | **Retain** (with coverage caveat in caption) | `outputs/arr_m2c/figures/excess_mass_lex_vs_inf.pdf` |
| Fig P3 coverage-matched lex−inf | **Retain** (primary lex/inf caveat figure) | `outputs/arr_m2d/figures/coverage_matched_lex_minus_inf.pdf` |
| Fig P4 alignment by prob band | **Retain** (confidence control) | `outputs/arr_m2d/figures/alignment_by_prob_band.pdf` |
| Fig P5 paired BD−DR | **Retain** | `outputs/arr_m2d/figures/paired_bd_minus_dr.pdf` |
| Fig Q1 qualitative examples | **Retain** (illustrative) | `outputs/arr_m2d/qualitative_examples.html` / `figures/examples/` |
| Paper Fig shap.png pipeline | **Retain** (update caption if methods corrected) | `docs/references/` / paper assets |
| Legacy Em/Ev category pie / 90–96% figures | **Remove / replace** | Replace with Tab T1 Other audit |
| Uncontrolled magnitude “three calibration levels” figs | **Replace / downgrade** | Use P4 + confidence-controlled tables; move raw magnitude to appendix if kept |
| Tab T1 taxonomy p75 Em/Ev vs Other | **Retain** (retraction evidence) | `outputs/arr_m1/taxonomy/headline_p75_comparison.csv` |
| Tab T2 faithfulness summary | **Retain** | `outputs/arr_m2b/faithfulness_summary.csv` |
| Tab T3 gold-span + matched | **Retain** | `outputs/arr_m2c/gold_span_summary.csv`, `outputs/arr_m2d/robustness_summary.csv` |
| Tab T4 human study | **Replace pre-M3R numbers** with **M3R** | `outputs/arr_m3r/*` |
| Tab T5 population / pairing n | **Retain / update human n** | Audits + coverage JSON |
| BASIL metrics @0.5 | **Retain** with threshold-sensitivity note | `outputs/basil/basil_metrics_table.csv`, `threshold_sweep_table.csv`, `arr_consistency/basil_full_threshold_confusion.csv` |
| AUPRC table | **Retain** (threshold-free) | `outputs/basil/auprc_table.csv` |
| Shared FP Jaccard (paired) | **Retain** with n | M1 pairing / paper tables (paired only) |
| TN faithfulness claims | **Remove** | n=3 |
| Unpaired architecture superiority | **Remove** | Confounded |
| SHAP–human full-120 generalization | **Remove** | Only cache∩sample |

---

## 7. DeBERTa checkpoint & unreproducible artifacts

| Item | Status |
|------|--------|
| Intended local path | `models/deberta-base-babe-ft` (`basil_eval.MODELS`, `scripts/figure1_redesign_shap.py`) |
| Present on this machine | **Missing** (`models/` absent) |
| Hub IDs (other models) | `himel7/bias-detector`; `mediabiasgroup/DA-RoBERTa-BABE-FT` |
| DeBERTa HF revision hash | **Not frozen** in-repo |
| Available DeBERTa artifacts | BABE `outputs/shap_samples_deberta.jsonl` (+`.bak`); BASIL `outputs/basil_shap/samples_deberta.jsonl`; M1 integrity under `outputs/arr_m1/deberta_integrity/` |
| Predictions CSV | `outputs/basil/predictions_deberta.csv` (usable for threshold tables) |
| M2B faithfulness | **Not run** for DeBERTa |

**Cannot bit-reproduce from available code+data alone:** DeBERTa inference/SHAP regeneration (checkpoint missing); exact SHAP regen for any model without pinned `shap`+torch+transformers used at generation time; raw BASIL respan export if raw corpus absent (span recovery already done in M1 from pinned BASIL commit for analyses that used it).

**Can analyze without regen:** all committed SHAP JSONL / M1–M3R tables / prediction CSVs.

---

## 8. Reproducibility & limitation statement (human study — for rewrite)

> Independent annotations cover a stratified 120-sentence BASIL sample (seed 7). Annotator A and the updated Annotator B file (`basil_blind_annotations_annB.json`, SHA-256 `5d845836…`) provide complete binary presence labels (120/120). Annotator B still has **26** `bias_present=yes` responses **without sentence-local evidence spans**, predominantly informational/both judgments marked as needing article context; these are retained for presence/type agreement, excluded from span and SHAP–human mass analyses, and are **not** imputed. Human–human agreement is moderate for binary bias (κ≈0.44) and **weak** for lexical/informational/both/none type (κ≈0.24); span soft-F1≈0.48. SHAP–human alignment uses existing caches only (bias-detector 34 / DA-RoBERTa 42 / DeBERTa 12 overlapping the sample) and shows excess absolute attribution mass over length-matched random spans where evaluable; results do **not** generalize to the full 120 without cache coverage. BASIL gold labels are a complementary evidence source, not an infallible standard. Pre-update AnnB statistics are archived under `outputs/arr_m3_archive_pre_m3r/` and are not the primary reporting basis.

---

## Verdict & blockers

**Rewrite readiness:** still **CONDITIONAL GO** (unchanged scientific conclusions).

### Genuine blockers to a credible rewrite start?
| Item | Blocks starting rewrite? | Blocks camera-ready? |
|------|-------------------------:|---------------------:|
| Paper still claims test-set SHAP background | No (fix while writing) | **Yes** if left uncorrected |
| Same-mechanism / Em/Ev / calibration prose still in draft | No (rewrite task) | **Yes** if left |
| Missing DeBERTa checkpoint | No (scope to caches) | Prefer restore for full repro package |
| Unpinned `shap` | No | Prefer pin / disclose |
| AnnB 26 yes∅spans | No if disclosed | No if disclosed |
| Threshold sensitivity not exhaustively re-run for M2B strata | No (discuss + cite sweep/AUPRC) | Prefer explicit t=0.5 disclosure |

**No analysis blocker** prevents starting the manuscript rewrite under the claim ledger.  
**Writing/repro honesty blockers** for submission: correct SHAP methods, retract Em/Ev & same-mechanism/calibration overclaims, use M3R human numbers, disclose human/cache limits.

---

*End of consistency check. Existing M1–M3R results preserved.*
