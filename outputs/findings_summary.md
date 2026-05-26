# Findings summary — bias-detector vs DA-RoBERTa SHAP analysis

Consolidates every quantitative result produced across this analysis phase.
Each table is the same one used as input to the corresponding figure/PNG.
Source artifacts are linked next to every section so reviewers can verify.

**Headline thesis:** The two bias-classifier checkpoints, `himel7/bias-detector`
(BERT-base, fine-tuned on BABE) and `mediabiasgroup/DA-RoBERTa-BABE-FT`
(RoBERTa-base, domain-adapted then fine-tuned on BABE), use the *same
underlying attribution mechanism* but exhibit *different calibration*.
Same mechanism: the words they latch onto are largely the same and their
peak attributions are nearly identical. Different calibration: DA-RoBERTa
sits on a lower attribution magnitude floor across every prediction
category, which moves more sentences across the decision boundary.

---

## 1. Setup

| Item | Value |
|---|---|
| Models | `himel7/bias-detector` (BD), `mediabiasgroup/DA-RoBERTa-BABE-FT` (DR) |
| Datasets | BABE (1000 test sentences) and BASIL (7984 sentences) |
| Decision threshold | 0.5 |
| SHAP setup | `shap.maskers.Text(tokenizer)` + `shap.Explainer(predict_fn, masker)` |
| Word aggregation | `aggregate_subword_shap_to_words` (verbatim from `analysis.ipynb` cell 3, the version that produced the original BABE word-attribution cache) |
| Word-category scheme | Emotional/Evaluative, Explicit Bias Terms, Framing/Reporting Verbs, Function/Temporal Words (from `babe_fig6_confound.py:categorize_word`) |
| Random seed | 7 (deterministic, reproducible sampling) |

---

## 2. BABE Figure 6 confound check — *Outcome C*

**The original paper claim:** "DA-RoBERTa false positives shift attribution
toward function/temporal words" (13% F/T at top-K=100 vs bias-detector's 4%).

**What we found:** the 13% number is an artifact of fixed-K selection
under unequal vocabulary pool sizes. Under matched-pool / attribution-strength
controls the gap collapses or inverts. Source:
[outputs/babe_fig6_confound/item3_summary.md](outputs/babe_fig6_confound/item3_summary.md).

### Decision table — DA-RoBERTa FP Function/Temporal proportion under every control

| Condition | DA-RoBERTa FP F/T (%) | n_selected / K |
|---|---:|---:|
| K=25 | 4.0 | effective_K=25 |
| K=50 | 8.0 | effective_K=50 |
| K=100 *(uncorrected — original paper)* | **13.0** | effective_K=100 |
| K=200 | 15.0 | effective_K=200 |
| K=500 | 13.7 | effective_K=249 |
| Proportional-K at top 5% of vocab | 0.0 | n_selected=12 |
| Proportional-K at top 10% of vocab | 4.0 | n_selected=25 |
| Proportional-K at top 20% of vocab | 8.0 | n_selected=50 |
| Proportional-K at top 30% of vocab | 10.7 | n_selected=75 |
| Threshold ≥ 0.0406 (p75 of pooled mean_abs_shap) | 5.1 | n_selected=39 |
| Bootstrap mean (K=100, B=1000) | 17.5 | 95% CI [11.0, 24.0] |

**Baselines at K=100:** DA-RoBERTa TP F/T = 0.0% (within-model); bias-detector FP F/T = 4.0% (cross-model).

### Vocab premise check

| metric | bias-detector FP | DA-RoBERTa FP |
|---|---:|---:|
| unique word types | 660 | 249 |
| n samples | 37 | 12 |
| ratio DR/BD | — | 0.38 |

DA-RoBERTa's FP vocabulary is ~⅓ the size of bias-detector's, supporting
the premise that fixed-K hits vocabulary exhaustion on the smaller side.

**Implication for the paper:** the BABE-side framing-shift claim does not
survive matched-feature-pool selection. The BASIL replication must use
**threshold-based feature selection** (p75 of pooled `mean_abs_shap`)
rather than top-K, and any "DA-RoBERTa shifts to function words" claim
should be downgraded to "DA-RoBERTa FPs do not concentrate on framing
vocab" or dropped entirely. See `outputs/babe_fig6_confound/item3_summary.md`
for the proposed Figure 6 restructure.

---

## 3. BASIL Figure 3 counterpart — per-sentence mean |SHAP|

Source: [outputs/basil_shap/basil_shap_summary.md](outputs/basil_shap/basil_shap_summary.md)
section 2. Figure: [outputs/basil_shap/basil_fig3_counterpart.png](outputs/basil_shap/basil_fig3_counterpart.png).

Methodology: 100 sentences per (model, category) sampled deterministically
from the BASIL joined prediction frame; per-sentence
`mean_abs_shap = mean(|word_shap|)` over `word_attribs`. Y-axis cap 0.15
matches the original BABE Fig 3.

| model | category | n | median | mean | clipped (>0.15) |
|---|---|---|---:|---:|---:|
| bias-detector | TP | 100 | 0.0407 | 0.0484 | 2 |
| bias-detector | FP | 100 | 0.0553 | 0.0586 | 3 |
| bias-detector | TN | 100 | 0.0313 | 0.0359 | 0 |
| bias-detector | FN | 100 | 0.0315 | 0.0399 | 0 |
| DA-RoBERTa | TP | 100 | 0.0343 | 0.0417 | 1 |
| DA-RoBERTa | FP | 100 | 0.0432 | 0.0550 | 2 |
| DA-RoBERTa | TN | 100 | 0.0161 | 0.0216 | 0 |
| DA-RoBERTa | FN | 100 | 0.0213 | 0.0299 | 0 |

**Read:**
- **FP > TP in mean for both models.** When the model fires a false
  positive, more words across the sentence carry elevated attribution than
  when it fires a true positive — i.e. FP attribution is more *diffuse*,
  not less.
- **TN floor is the lowest, FN sits between TN and the positives.** FN ≈ TN
  for BD (0.0399 vs 0.0359) but FN > TN for DR (0.0299 vs 0.0216). The
  model didn't activate strongly on FN sentences even though a lex-only
  bias term was present.
- **DA-RoBERTa is uniformly lower across all four categories.** Mean ratios
  DR/BD: TP 0.86, FP 0.94, TN 0.60, FN 0.75. The compression is most
  severe at the negative end — exactly what the "different calibration"
  thesis predicts.

---

## 4. BASIL Figure 3 max counterpart — per-sentence max |SHAP|

Source: same summary, section 2b. Figure:
[outputs/basil_shap/basil_fig3_max_counterpart.png](outputs/basil_shap/basil_fig3_max_counterpart.png).

Per-sentence `max_abs_shap = max(|word_shap|)`. Y-axis cap 0.6 (higher
than mean because peaks reach ~0.5 on canonical bias words like
"pounced", "bombshell", "facetiously"). Clipping is minimal — 1–2
outliers in the positive categories only.

| model | category | n | median | mean | clipped (>0.6) |
|---|---|---|---:|---:|---:|
| bias-detector | TP | 100 | 0.2203 | 0.2350 | 1 |
| bias-detector | FP | 100 | 0.2418 | 0.2578 | 2 |
| bias-detector | TN | 100 | 0.1060 | 0.1255 | 0 |
| bias-detector | FN | 100 | 0.1345 | 0.1459 | 0 |
| DA-RoBERTa | TP | 100 | 0.1938 | 0.2197 | 1 |
| DA-RoBERTa | FP | 100 | 0.2306 | 0.2401 | 0 |
| DA-RoBERTa | TN | 100 | 0.0576 | 0.0791 | 0 |
| DA-RoBERTa | FN | 100 | 0.0937 | 0.1106 | 0 |

**Read (the headline result):**
- **TP ≈ FP in max within each model.** BD: TP 0.220 vs FP 0.242 (ratio 1.10).
  DR: TP 0.194 vs FP 0.231 (ratio 1.09). Peak attribution on a *correct*
  positive and a *wrong* positive is essentially identical — direct evidence
  for the "same mechanism" half of the thesis. The model latches onto a
  single high-weight word with the same conviction whether or not that
  word is genuinely bias-marking.
- **FP/TP gap is *smaller* in max than in mean.** Mean ratios were
  1.21 / 1.32; max ratios are 1.10 / 1.09. So FPs spread elevated
  attribution diffusely across the sentence (mean), but the peak is the same
  as a TP (max).
- **DA-RoBERTa < bias-detector across all four categories**, as in mean.
  Largest gap at the negative end: TN 0.058 vs 0.106 (DR 45% lower);
  FN 0.094 vs 0.134 (DR 30% lower).
- **The calibration gap FN→TP is ~0.10 SHAP for both models.** BD: 0.134 → 0.235.
  DR: 0.094 → 0.194. Equal absolute gap, but DR starts lower — which is why
  DR misses proportionally more.

---

## 5. BABE Figure 3 (mean) with FN — cross-corpus replication

Source: regenerated from [outputs/shap_samples.jsonl](outputs/shap_samples.jsonl)
(337 records: 100 TP, 37 FP, 100 TN, 100 FN) and
[outputs/shap_samples_daroberta.jsonl](outputs/shap_samples_daroberta.jsonl)
(312 records: 100 TP, 12 FP, 100 TN, 100 FN). FN partitions added by
`babe_shap_fn.py` (100 sampled per model, seed=7); the TP/FP/TN partitions
are the originals from the BABE pipeline (`analysis.py`). Figure:
[outputs/babe_fig3_with_fn.png](outputs/babe_fig3_with_fn.png).

Methodology mirrors §3 — per-sentence `mean_abs_shap` over `word_attribs`.
Y-axis cap 0.15 matched to BASIL Fig 3 for direct visual comparison.

| model | category | n | median | mean | clipped (>0.15) |
|---|---|---|---:|---:|---:|
| bias-detector | TP | 100 | 0.0280 | 0.0362 | 0 |
| bias-detector | FP | 37 | 0.0368 | 0.0447 | 0 |
| bias-detector | TN | 100 | 0.0254 | 0.0324 | 0 |
| bias-detector | FN | 100 | 0.0300 | 0.0351 | 0 |
| DA-RoBERTa | TP | 100 | 0.0274 | 0.0335 | 0 |
| DA-RoBERTa | FP | 12 | 0.0270 | 0.0310 | 0 |
| DA-RoBERTa | TN | 100 | 0.0106 | 0.0146 | 0 |
| DA-RoBERTa | FN | 100 | 0.0157 | 0.0212 | 0 |

**Note on n:** BABE FP samples are not 100 — the original BABE pipeline
used all available FPs in the test split (37 BD, 12 DR). BASIL had ample
FPs and capped at 100. The small-FP caveat from §2 applies here too.

**Read — cross-corpus consistency:**
- **DA-RoBERTa < bias-detector across all four categories** on BABE,
  replicating the BASIL pattern in §3. Mean ratios DR/BD: TP 0.93, FP 0.69,
  TN 0.45, FN 0.60. The calibration gap is not a BASIL artifact.
- **The negative-end compression is *more* severe on BABE than BASIL.**
  TN ratio 0.45 (BABE) vs 0.60 (BASIL); FN ratio 0.60 (BABE) vs 0.75 (BASIL).
  DR's lower attribution floor is stronger on its training-domain test set.
- **FN > TN for both models on BABE** (BD 0.0351 vs 0.0324; DR 0.0212 vs
  0.0146). On BASIL, the same FN > TN held for DR but FN ≈ TN for BD; the
  BABE evidence makes the FN > TN pattern look more robust. Cross-corpus
  read: when the model misses a positive, it still attributes slightly
  more across the sentence than when the input is genuinely negative —
  there *is* a signal it half-noticed.
- **FP > TP in mean for BD** (0.045 vs 0.036, consistent with BASIL) but
  **inverted for DR** (0.031 vs 0.034). The DR inversion sits on n=12 FP
  samples and is not statistically meaningful; the BD result aligns with
  BASIL.
- Overall magnitudes are systematically *lower* on BABE than BASIL across
  every category (BD TP mean 0.036 on BABE vs 0.048 on BASIL). Likely a
  sentence-length / domain effect; flagged for awareness, not relevant to
  the calibration claim.

**What this adds to the calibration thesis:** the BD > DR magnitude gap
*replicates on BABE*, including on the evaluation set the models were
trained against. The negative-end pattern (DR much lower on TN and FN)
is more pronounced on BABE than BASIL. Same calibration story, two
independent corpora.

---

## 6. Hypothesis A — bias-type independence at SHAP level

**Question:** does the model attribute differently to lexical-bias TPs vs
informational-bias TPs? Source: section 3 of `basil_shap_summary.md`.

| model | bias_type | n | median mean_abs_shap |
|---|---|---:|---:|
| bias-detector | lex_only | 100 | 0.0411 |
| bias-detector | inf_only | 100 | 0.0413 |
| bias-detector | both | 23 | 0.0251 |
| DA-RoBERTa | lex_only | 100 | 0.0337 |
| DA-RoBERTa | inf_only | 100 | 0.0374 |
| DA-RoBERTa | both | 25 | 0.0243 |

**Top-20 word-vocabulary Jaccard between lex-only and inf-only:**

| model | Jaccard | |lex vocab| | |inf vocab| |
|---|---:|---:|---:|
| bias-detector | 0.138 | 1050 | 1018 |
| DA-RoBERTa | 0.139 | 987 | 993 |

**Read:**
- Per-sentence magnitudes are nearly identical between lex-only and inf-only TPs
  (BD: 0.0411 vs 0.0413; DR: 0.0337 vs 0.0374) — bias *type* is invisible at
  the magnitude level. Models do not "work harder" on one type vs the other.
- Top-20 vocabularies overlap only ~14% — the *words* the model attributes
  to differ between lex-only and inf-only TPs, but the *amount of attribution*
  does not.
- The `both` stratum looks lower (~0.025) but n=23–25 is too small to weight
  heavily; it is also likely a length confound (multi-bias-type sentences
  tend to be longer, diluting per-word means).

---

## 7. Hypothesis B — same mechanism, different calibration (FP three-way partition)

Source: section 4 of `basil_shap_summary.md`. Methodology:
threshold-based feature selection (the matched-pool fix from outcome C).
Pool all `mean_abs_shap` values across {shared FPs × {BD, DR}, BD-only
FPs × BD, DR-only FPs × DR} → compute p75 → keep words above threshold
per (partition, model).

**Threshold** = 0.0614.

**Category proportions among threshold-selected words:**

| partition | model | Emotional/Evaluative | Explicit Bias Terms | Framing/Reporting Verbs | Function/Temporal Words |
|---|---|---:|---:|---:|---:|
| bd_only | biasdetector | 0.944 | 0.000 | 0.019 | 0.037 |
| dr_only | daroberta | 0.913 | 0.004 | 0.026 | 0.057 |
| shared | biasdetector | 0.944 | 0.003 | 0.025 | 0.028 |
| shared | daroberta | 0.962 | 0.004 | 0.017 | 0.017 |

**Selected-word counts:**

| partition | model | n_selected_words |
|---|---|---:|
| bd_only | biasdetector | 323 |
| dr_only | daroberta | 229 |
| shared | biasdetector | 323 |
| shared | daroberta | 236 |

**Read:**
- Across every (partition × model) cell, **Emotional/Evaluative dominates
  at 91–96%**. Whether the FP is shared, BD-only, or DR-only, the
  threshold-selected words are overwhelmingly the same category.
- DR's Function/Temporal proportion in `dr_only` is 5.7% vs BD's 3.7%
  in `bd_only` — a 2-point gap, not the 9-point gap implied by the
  original BABE K=100 number.
- The selected-word counts also confirm DA-RoBERTa's smaller effective FP
  vocabulary on BASIL (236 shared / 229 dr_only vs BD's 323 / 323),
  paralleling the BABE finding.

**The threshold-based methodology overturns the framing-shift claim on BASIL
just as it did on BABE.** Same mechanism (emotional/evaluative dominance),
different calibration (DR sees fewer words above threshold).

---

## 8. FP paired mechanism check (shared FPs, both models, BASIL)

Source: section 5 of `basil_shap_summary.md`. Paired analysis on BASIL.
n=100 shared-FP sentences randomly sampled (seed=7) from the full pool of
**314** BASIL sentences where both BD and DR fired a false positive.

| metric | value |
|---|---:|
| Median per-sentence Jaccard of top-20 tokens (BD ∩ DR / BD ∪ DR) | **0.809** |
| Median per-sentence mean_abs_shap — BD | 0.0502 |
| Median per-sentence mean_abs_shap — DR | 0.0378 |

**Read:** when both models fire an FP on the same sentence, their top-20
attributed-token sets have a median Jaccard overlap of 0.81 — they are
looking at substantially the same words. On these same sentences,
BD's per-sentence mean |SHAP| (median across the 100 paired sentences)
is ~33% higher than DR's (0.0502 vs 0.0378). The calibration gap shows
up on the matched sentence pairs too, not just across the unmatched
distributions.

---

## 9. FN paired calibration check (shared lex-only FNs, both models, BASIL)

Source: section 6 of `basil_shap_summary.md`. Paired analysis on BASIL.
n=100 sentences randomly sampled (seed=7) from the full pool of **221**
BASIL sentences where both models missed a *lex-only* bias
(gold=1, has_lex=1, has_inf=0, pred_BD=0, pred_DR=0). The lex-only filter
restricts the population to sentences whose only bias signal is a loaded
word (not informational/framing bias); behaviour on inf-only or
both-types missed sentences was not measured here.

| metric | value |
|---|---:|
| Median per-sentence Jaccard of top-20 tokens (BD ∩ DR / BD ∪ DR) | **0.721** |
| Median per-sentence mean_abs_shap — BD | 0.0340 |
| Median per-sentence mean_abs_shap — DR | 0.0170 |

**Read:**
- Top-20 attributed-token sets have a median Jaccard overlap of 0.72 on
  missed sentences — slightly lower than 0.81 on FPs but still high.
  The two models are mostly attending to the same tokens when they miss.
- DR's median per-sentence mean |SHAP| is **half** of BD's
  (0.0170 vs 0.0340) — the calibration gap is *largest* on lex-only
  FNs of all the categories sampled. When DR misses, it's missing more
  confidently (less attribution anywhere) than BD does.
- This is consistent with the FN row of the §3 magnitude table
  (means across the 100 magnitude_FN sentences: BD 0.0399, DR 0.0299).
  Caveat: §3's `magnitude_FN` stratum is unrestricted FN (any bias type),
  while this §9 pool is lex-only — they aren't the same sentences, but
  both show DR < BD on FNs.

---

## 10. Sanity checks & spot-checks

Source: section 7 of `basil_shap_summary.md`.

| check | result |
|---|---|
| Overall magnitude scale (mean of `mean_abs_shap`) | 0.0414 — within published BABE range [0.02, 0.08] ✓ |
| Cache integrity | 0 manifest entries missing from JSONL caches ✓ |

### Known-bias attribution spot check — top-3 attributed words on 3 random lex-only TPs

**bias-detector**:
- `8dc7ccfe.../13`: pounced (0.49) | Following (-0.15) | Romney (0.12)
- `9879bbc0.../1`: heated (0.12) | challenging (-0.11) | Republicans (-0.11)
- `59f2f47c.../9`: Cruz.'' (-0.14) | problem (0.13) | 's (0.04)

**DA-RoBERTa**:
- `be026bd1.../0`: bombshell (0.48) | Donald'' (0.07) | response (-0.07)
- `a4f1d515.../0`: forcefully (0.17) | saying (0.06) | revelations (0.06)
- `2153fb3e.../20`: facetiously (0.21) | Boehner (0.12) | help:""'' (0.05)

The top-attributed words ("pounced", "bombshell", "forcefully",
"facetiously") are canonically bias-loaded — confirms the pipeline isn't
silently attributing to junk.

---

## 11. Cross-cutting synthesis — the "same mechanism, different calibration" story

Threading all pieces of evidence together:

| Evidence | Same mechanism? | Different calibration? |
|---|:-:|:-:|
| §3 BASIL Fig 3 mean: DR lower in all 4 categories | — | ✓ |
| §4 BASIL Fig 3 max: TP ≈ FP within each model | ✓ | — |
| §4 BASIL Fig 3 max: DR lower in all 4 categories | — | ✓ |
| **§5 BABE Fig 3 mean: DR lower in all 4 categories** (cross-corpus replication) | — | ✓ |
| **§5 BABE Fig 3 mean: negative-end compression *stronger* on BABE than BASIL** | — | ✓ |
| §7 FP partition: Emotional/Evaluative dominant 91–96% across all partitions | ✓ | — |
| §7 FP partition: DR has fewer selected words at same threshold | — | ✓ |
| §8 FP paired (BASIL, n=100 of 314): median top-20 Jaccard 0.81 | ✓ | — |
| §8 FP paired (BASIL): BD median per-sentence mean \|SHAP\| 33% higher than DR's on the same sentences | — | ✓ |
| §9 FN paired (BASIL lex-only, n=100 of 221): median top-20 Jaccard 0.72 | ✓ | — |
| §9 FN paired (BASIL lex-only): DR median per-sentence mean \|SHAP\| is **half** of BD's on the same sentences | — | ✓ (most extreme) |

Both halves of the thesis are supported by *independent* lines of evidence
on BASIL **and** the calibration half replicates on BABE (§5). The
threshold-based methodology (rather than top-K) was necessary on BASIL
just as it was on BABE. The original "framing-shift" story (BABE Fig 6)
was an artifact of vocabulary-pool size; the calibration story is what
survives, and it survives on both corpora.

---

## 12. Generated artifacts

All paths relative to `SHAP Analysis Bias Models/`.

### BASIL SHAP

| Artifact | Path |
|---|---|
| Per-sentence SHAP records (BD) | `outputs/basil_shap/samples_biasdetector.jsonl` |
| Per-sentence SHAP records (DR) | `outputs/basil_shap/samples_daroberta.jsonl` |
| Sampling manifest | `outputs/basil_shap/manifest.csv` |
| Magnitude CSV (mean + max per sentence) | `outputs/basil_shap/basil_shap_magnitude.csv` |
| Bias-type CSV | `outputs/basil_shap/basil_shap_bias_type.csv` |
| FP three-way partition CSV | `outputs/basil_shap/basil_shap_fp_partition.csv` |
| FP shared paired CSV | `outputs/basil_shap/basil_shap_fp_shared_paired.csv` |
| FN shared paired CSV | `outputs/basil_shap/basil_shap_fn_shared.csv` |
| Summary md (per-section breakdown) | `outputs/basil_shap/basil_shap_summary.md` |
| **Fig 3 counterpart (mean)** | `outputs/basil_shap/basil_fig3_counterpart.png` |
| **Fig 3 counterpart (max)** | `outputs/basil_shap/basil_fig3_max_counterpart.png` |
| Diagnostic boxplot grid | `outputs/basil_shap/diagnostics/magnitude_boxplot.png` |
| Diagnostic by bias type | `outputs/basil_shap/diagnostics/magnitude_by_bias_type.png` |
| Diagnostic FP partition composition | `outputs/basil_shap/diagnostics/fp_partition_composition.png` |
| Diagnostic FP paired scatter | `outputs/basil_shap/diagnostics/fp_shared_paired.png` |
| Diagnostic FN paired scatter | `outputs/basil_shap/diagnostics/fn_shared_paired.png` |

### BABE Fig 6 confound

| Artifact | Path |
|---|---|
| Decision-table summary | `outputs/babe_fig6_confound/item3_summary.md` |
| Vocab-stats table | `outputs/babe_fig6_confound/vocab_stats_table.csv` |
| K-sensitivity figure | `outputs/babe_fig6_confound/fig6_sensitivity.png` |
| Matched-pools CSV | `outputs/babe_fig6_confound/fig6_matched_pools.csv` |
| Bootstrap CI figure | `outputs/babe_fig6_confound/fig6_bootstrap_ci.png` |
| Bootstrap CSV | `outputs/babe_fig6_confound/bootstrap_summary.csv` |

### BABE SHAP (TP/FP/TN/FN — FN partition added in this phase)

| Artifact | Path |
|---|---|
| BD records (337: 100 TP + 100 TN + 37 FP + 100 FN) | `outputs/shap_samples.jsonl` |
| DR records (312: 100 TP + 100 TN + 12 FP + 100 FN) | `outputs/shap_samples_daroberta.jsonl` |
| **BABE Fig 3 with FN** | `outputs/babe_fig3_with_fn.png` |
| FN generator script | `babe_shap_fn.py` |
| Figure script | `babe_fig3_with_fn.py` |

---

## 13. Caveats and known gaps

- **BABE n_FP is small** (37 BD, 12 DR). The vocab-confound decision-table
  numbers in §2 sit on these small samples; bootstrap CIs widen accordingly
  and are reported in `outputs/babe_fig6_confound/item3_summary.md`.
- **BASIL `both`-type stratum is small** (n=23 BD, n=25 DR). The slightly
  lower magnitude is likely a length confound, not a model property.
- **Decoder-family models are out of scope** of this phase. The
  same-mechanism / different-calibration thesis is supported across two
  encoder checkpoints (BERT-base, RoBERTa-base) but extending to modern
  decoders is a separate revision item.
- **Threshold-based selection at p75** was chosen to match the BABE
  outcome-C methodology. Alternative thresholds (p50, p90) produce
  qualitatively the same partition picture but shift the selected-word
  counts; the dominance of Emotional/Evaluative (>90%) is robust to this
  choice.
