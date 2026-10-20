# ARR Experiment Plan

**Purpose:** Dependency-ordered roadmap for ARR revisions addressing reviews (MqgQ, xw7D, k62P), AC meta-review, and supervisor Kasneci notes.  
**Constraint:** Do not assert hypothesis confirmation before experiments run. Prefer modular CLI scripts. Preserve original caches.

Paper line numbers refer to `docs/references/paper.tex`.

---

## Dependency order (milestones)

```
M0 Env + artifacts restore
 └─► E1 Taxonomy + Other/Unassigned (+ manual validation)
      └─► E4 Confidence-controlled / normalized similarity  (mostly caches)
      └─► E5 Threshold robustness (predictions + val protocol)
           └─► E2 Faithfulness perturbations (needs models)
                └─► E3 Human evidence spans (needs raw BASIL + annotators)
                     └─► E6 Optional paraphrase / semantic vs surface (hard)
```

| Milestone | Acceptance criteria | Primary artifacts |
|-----------|---------------------|-------------------|
| M0 | Pinned env installs; DeBERTa checkpoint loadable; seed/config logged | `requirements.txt` / lock; `models/deberta-base-babe-ft/`; `docs/ENV_LOCK.md` |
| E1 | Other category implemented; % tables; ≥50 manual labels with agreement | `outputs/arr/taxonomy_*`; paper taxonomy subsection |
| E2 | Perturbation Δp with matched budgets + CIs on shared pilot set | `outputs/arr/faithfulness_*` |
| E3 | Blind span labels; IAA; SHAP↔span overlap metrics | `outputs/arr/human_spans_*` |
| E4 | Paired normalized similarity + confidence bins | `outputs/arr/similarity_*` |
| E5 | Val-selected thresholds + threshold-free groupings | `outputs/arr/threshold_*` |
| E6 | Optional; surface vs semantic overlap table | `outputs/arr/paraphrase_*` |

---

## E1. Taxonomy audit + Other/Unassigned

**RQ:** Does Emotional/Evaluative dominate because of residual catch-all assignment?  
**Reviewers:** k62P weakness 1; supervisor dummy category; AC “clarify and validate taxonomy”; `paper.tex` L491.

**Inputs:** Existing SHAP JSONL word_attribs; **no** test-label tuning of lexicon.

**Reuse:** `babe_fig6_confound.categorize_word` (L143–199); matched-pool `step3_matched_pools` (L321–365); `scripts/babe_fp_partition.py`.

**New code (CLI):**
- `scripts/arr_taxonomy_audit.py` — apply ordered rules + `Other/Unassigned`; emit confusion vs old labels; report % at all-tokens and p75 matched-pool.
- `scripts/arr_taxonomy_manual_sample.py` — stratified sample of top-|SHAP| words for blind human coding (Em/Eval, Explicit, Fr/Rep, Fu/Temp, Other, Ambiguous).

**Measurements:** Category % with/without catch-all; Cohen’s κ / raw agreement on manual set; sensitivity of Table 3/4 style results.

**Baselines:** Current catch-all taxonomy; corpus frequency baseline (category rates on all words in sampled sentences, not just top SHAP).

**Confounders:** Lexicon reverse-engineered from SHAP tops; English morphology (`-ful`/`-less` false positives); case/punct normalization.

**Validity checks:** Decision order frozen in config JSON; examples of each bucket; do not claim linguistic “mechanism” from residual bucket.

**Compute:** CPU only; minutes.

**Outputs / paper locations:**
- New Methodology subsection after Analysis Framework (~L474–491) defining rules.
- Recompute Table matched-pool (`~L708–755`, `\label{sec:word_patterns}`) and FP partition table (`~L773–792`).
- Abstract L157 and Conclusion L881–883: **revise percentages only after E1**.

**Complexity:** Low–medium. **Depends on:** M0 optional.

**From caches?** Yes (percentages). Manual validation needs humans.

---

## E2. SHAP perturbation faithfulness

**RQ:** Do high-|SHAP| tokens change model probability more than low-|SHAP| or random tokens at matched mask budgets?  
**Reviewers:** xw7D weakness 2; supervisor faithfulness; `paper.tex` L495.

**Inputs:** Prefer **paired** sentences present in ≥2 model caches; pilot N=20 then scale. Use stored `tokens`/`shap_pos`/`word_attribs` to choose mask sets; **re-infer** with model forward passes (mask or replace with mask token / delete).

**Reuse:** `build_predict_fn` pattern (`analysis.py` L368–391); tokenizer from each model.

**New code:** `scripts/arr_faithfulness_perturb.py`
- Conditions: top-p% |SHAP| words, bottom-p% |SHAP|, random (matched count), optional contiguous phrase of top tokens.
- Budgets: 10/20/30% of words (length-controlled).
- Metrics: Δp_biased, |Δlogit|, flip rate; bootstrap CIs; per-model tables.

**Baselines:** Random and low-attribution masks (matched cardinality).

**Confounders:** Masking strategy (delete vs `[MASK]` vs UNK); sentence length; confidence ceiling effects; SHAP computed in probability space.

**Validity:** Pre-register budgets; same sentences across conditions; do not use gold labels to choose which sentences to perturb (may stratify by pred type using existing preds).

**Compute:** Inference-heavy. Pilot 20×3 conditions×3 models ≈ hundreds of forwards — feasible on Mac MPS if checkpoint present; full hundreds of sentences → prefer GPU if wall-clock > few hours (see hardware doc).

**Outputs / paper:** New subsection under Methodology (after L495 TODO) + Results faithfulness table; soften “attends to / mechanism” language in L230–255, L648–662 if faithfulness is weak.

**Complexity:** Medium. **Depends on:** M0 models; optionally E4 sentence IDs.

**From caches?** Mask **selection** yes; **scores** require inference.

---

## E3. Human-labeled evidence spans

**RQ:** Do high-SHAP regions overlap human-identified bias evidence, stratified by BASIL lex vs informational?  
**Reviewers:** MqgQ span vs sentence; AC BASIL labels; supervisor manual labels; `paper.tex` L802.

**Inputs:** Raw BASIL phrase-level annotations (must re-acquire); SHAP word_attribs with character alignment; stratified sample (lex-only / inf-only / both).

**Reuse:** `preprocess_basil.group_spans_by_sentence` logic (L47–56) once corpus present; extend to retain span text + offsets if present in JSON.

**New code:**
- `scripts/arr_basil_span_export.py` — export sentence + gold spans + model top-|SHAP| highlights for annotation UI/CSV.
- `scripts/arr_span_agreement.py` — IAA; token/span overlap (precision@k, attribution mass in gold span).

**Protocol:** Blind annotation (hide model); ≥2 annotators on overlap set; separate “human evidence” from BASIL gold when comparing SHAP to each.

**Measurements:** Token F1 / IoU vs gold; % positive SHAP mass inside gold spans; by bias type.

**Confounders:** Span-to-sentence projection; quote spans; multi-span sentences; SHAP word boundaries ≠ annotator spans.

**Validity:** Report agreement; distinguish **plausibility** (human) from **faithfulness** (E2).

**Compute:** Low CPU; human time dominant.

**Outputs / paper:** Results subsection near L802; examples appendix (~L1176).

**Complexity:** Medium–high (data + annotation). **Depends on:** raw BASIL (gap); E1 optional for category of human tags.

**From caches?** SHAP side yes; gold spans **no** until corpus restored.

---

## E4. Normalized cross-model attribution similarity + confidence control

**RQ:** Conditional on similar confidence, how similar are attributions? Is magnitude gap only a score-scale effect?  
**Reviewers:** xw7D weakness 3–4; AC confidence; `paper.tex` L493, L513, L568.

**Inputs:** Caches with `prob_pos` + `word_attribs`. Prefer BASIL `fp_shared` paired BD↔DR; BABE text intersection; expand DeBERTa shared strata if needed (new SHAP — optional phase).

**Reuse:** Jaccard in `basil_shap_analyze.median_pairwise_jaccard`; magnitude CSVs.

**New code:** `scripts/arr_attribution_similarity.py`
- Align words by normalized surface form on same sentence.
- Vectors: signed SHAP and |SHAP| / Σ|SHAP| (unit simplex).
- Metrics: cosine, Jaccard@k, L1; bin by |p_i − p_j| or matched probability quantiles.
- Regression: mean|SHAP| ~ f(prob) within model; residual magnitude comparison across models.

**Baselines:** Random word alignment; shuffle SHAP; different-sentence pairing.

**Confounders:** Tokenizer mismatch; unpaired BABE samples; DeBERTa missing shared strata.

**Validity:** Predefine bins; report n per bin; do not invent pairing across different texts.

**Compute:** CPU minutes on caches; optional new SHAP for DeBERTa shared FPs (hours on CPU).

**Outputs / paper:** Methodology L493; revise magnitude Results L559–662 and Table 2 if gaps shrink under confidence control.

**Complexity:** Medium. **Depends on:** E1 not required; M0 for new SHAP only.

**From caches?** **Mostly yes** for BD↔DR BASIL shared; limited for 3-model BABE.

---

## E5. Threshold robustness

**RQ:** Do TP/FP/TN/FN attribution patterns hold under validation-selected thresholds and threshold-free groupings?  
**Reviewers:** xw7D weakness 4; AC thresholds; `paper.tex` L512.

**Inputs:** BABE train/val from training recipe; BASIL `predictions_*.csv` (full probs). **Forbidden:** choosing thresholds on BABE test or BASIL using analysis labels for tuning.

**Reuse:** `threshold_sweep.py` (discrete sweep + AUPRC); `basil_eval.view_filters`.

**New code:** `scripts/arr_threshold_protocol.py`
- Select t* on **BABE validation** only (F1-max or fixed FPR).
- Apply t* and t=0.5 to redefine confusion cells; recompute magnitude stats from **existing** SHAP where pred labels change membership (document cells that leave/enter).
- Threshold-free: gold × probability quantile bins; AUROC + AUPRC.

**Measurements:** Cell sizes; median mean|SHAP| by cell; McNemar under each t (CLI port from notebook).

**Confounders:** Domain shift BASIL; small FP sets (DR has 12 FPs on BABE at 0.5).

**Validity:** Log selection criterion; never peek at test for t*.

**Compute:** CPU; seconds–minutes. Re-SHAP only if new cells lack attributions.

**Outputs / paper:** Evaluation Metrics L502–512; sensitivity appendix; revise claims at L506, L553.

**Complexity:** Low–medium. **Depends on:** M0 for val split reproducibility; caches for SHAP cells.

**From caches?** Metrics yes; SHAP reassignment partial.

---

## E6. Optional: lexical paraphrase vs semantic evidence (supervisor challenge)

**RQ:** Is cross-model overlap due to surface tokens or shared semantic evidence?  
**Reviewers:** supervisor “disentangle tokens from semantic evidence.”

**Design (sketch):** For shared-FP sentences, generate paraphrases that (a) preserve bias-bearing meaning with different lexicalization, (b) preserve top surface tokens with neutralized meaning. Compare prediction + top-|SHAP| overlap.

**Reuse:** Inference scripts; SHAP generate for small N.

**New code:** `scripts/arr_paraphrase_probe.py` + human check of paraphrase validity.

**Compute:** LLM paraphrase gen + SHAP on tens of sentences — Mac OK for N≤30; larger → GPU.

**Paper:** Discussion / Limitations (~L900) unless results are strong enough for Results.

**Complexity:** High. **Depends on:** E2/E4; human validation.

**From caches?** No for paraphrases.

---

## Experimental dependency matrix

| Experiment | Existing SHAP caches | Model inference | New SHAP | Annotations | Retrain |
|------------|----------------------|-----------------|----------|-------------|---------|
| E1 | Sufficient | No | No | Manual word labels | No |
| E2 | Mask selection | **Yes** | No (unless expand set) | No | No |
| E3 | SHAP side | No | Optional | **Yes + raw BASIL** | No |
| E4 | Mostly BD/DR | No | Optional (DeBERTa shared) | No | No |
| E5 | Partial | No (probs exist) | If new cells | No | No (unless val lost) |
| E6 | No | Yes | Yes (small) | Paraphrase QC | No |

---

## Implementation roadmap (executable)

1. **Week 0 — M0:** Recreate venv; pin deps from overnight machine if available; restore DeBERTa weights; clone BASIL; write `docs/ENV_LOCK.md`.  
   - **Accept:** `python -c "import shap,torch,transformers; ..." ` and `models/deberta-base-babe-ft` loads.
2. **Week 1 — E1:** CLI taxonomy audit + 50–100 word manual labels; draft paper taxonomy subsection (L491).  
   - **Accept:** Other % table; κ reported; no silent overwrite of old CSVs.
3. **Week 1–2 — E4 + E5:** Confidence-controlled similarity + val thresholds (cache-first).  
   - **Accept:** Tables with n per bin; t* selection log.
4. **Week 2 — E2 pilot:** 20 sentences × 3 mask types × models on Mac; decide GPU need.  
   - **Accept:** Δp table with CIs; pilot timing logged in hardware doc.
5. **Week 3 — E3:** Span export + annotation round 1.  
   - **Accept:** IAA ≥ pre-registered floor or discuss disagreement.
6. **Week 4 — Integrate paper:** Update abstract L157, methods L412–513, results L559–802, limitations L900; soften mechanism language pending E2.
7. **Optional E6** if time.

---

## What not to do

- Do not overwrite `outputs/shap_samples*.jsonl` or `outputs/basil_shap/samples_*.jsonl`.
- Do not tune thresholds or taxonomy on BABE test / BASIL labels.
- Do not claim “same mechanism” until E1+E2+E4 results are in.
- Do not retrain DeBERTa-v3 on MPS (known NaN); use CUDA if v3 required.
