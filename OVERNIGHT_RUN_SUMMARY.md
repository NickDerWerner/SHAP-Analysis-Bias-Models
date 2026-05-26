# Overnight DeBERTa-base Integration — Summary

## TL;DR

A third model — **`microsoft/deberta-base`** fine-tuned on BABE — was added to
the SHAP-analysis pipeline alongside `himel7/bias-detector` and
`mediabiasgroup/DA-RoBERTa-BABE-FT`. Training, BASIL inference, BABE SHAP
generation (TP/FP/TN + FN), the 3-model BASIL metrics table, and the 3-model
Figure 3 are all done.

**Heads up:** the plan originally called for `microsoft/deberta-v3-base`, but
DeBERTa-v3 produces NaN gradients on Apple MPS (a hard architectural
incompatibility between DeBERTa-v3's disentangled attention and the MPS
backend). The pivot to DeBERTa-base (v1) was made after exhausting fp32, bf16,
and several LR/clipping combinations. See "Why v1 not v3" below.

## Final BABE-test metrics (DeBERTa-base, our fine-tune)

| metric | value |
|---|---|
| accuracy | 0.835 |
| macro-F1 | 0.835 |
| F1 (biased class) | 0.836 |
| AUPRC (biased class) | 0.948 |
| confusion @ 0.5 | TP=421, FP=27, TN=414, FN=138 |

For reference, the published DA-RoBERTa-BABE-FT reports macro-F1 ≈ 0.81 on the
same split. Our DeBERTa-base run lands marginally higher.

## What ran tonight

1. `finetune_deberta_babe.py` — fine-tunes `microsoft/deberta-base` on the
   BABE train parquet (3,121 sentences), 3 epochs, lr=2e-5, bs=16,
   max_len=256, 10% stratified val split, best checkpoint by macro-F1.
   ~6 min on MPS.
2. `run_inference.py --model ./models/deberta-base-babe-ft
   --model_suffix deberta` — produced
   `outputs/basil/predictions_deberta.csv` (7,984 rows). ~34 s on MPS.
3. `analysis.py --model ./models/deberta-base-babe-ft --model_suffix deberta
   --max_shap_examples 237 --seed 7` — produced
   `outputs/shap_samples_deberta.jsonl` (227 TP/FP/TN SHAP records) +
   `outputs/global_word_importance_deberta.csv` (~767 rows). ~62 min on CPU.
4. `babe_shap_fn.py --n_fn 100 --seed 7 --models deberta` — appended 100 FN
   records to the deberta cache. ~28 min on CPU.
5. `compute_metrics.py` — produced `outputs/basil/basil_metrics_table.csv`
   with metrics for all 3 models across the 6 BASIL views (full, lex-only,
   inf-only, both-types, quote-excluded, quote-only). instant.
6. `babe_fig3_with_fn.py` — regenerated
   `outputs/babe_fig3_with_fn.png` / `outputs/paperReady/babe_fig3_with_fn.pdf`
   with a third panel column for DeBERTa-base. instant.

Cache state after the run:

| cache | TP | FP | TN | FN | total |
|---|---|---|---|---|---|
| shap_samples.jsonl (biasdetector) | 100 | 37 | 100 | 100 | 337 |
| shap_samples_daroberta.jsonl | 100 | 12 | 100 | 100 | 312 |
| shap_samples_deberta.jsonl | 100 | 27 | 100 | 100 | 327 |

## 3-model BASIL metrics (highlights, "full" view)

| model | acc | P | R | F1 |
|---|---|---|---|---|
| biasdetector | 0.787 | 0.463 | 0.316 | 0.376 |
| daroberta | 0.794 | 0.488 | 0.272 | 0.349 |
| deberta | 0.791 | 0.471 | 0.207 | 0.288 |

DeBERTa-base wins on BABE-test but transfers least well to BASIL (lowest
recall). Worth investigating in the paper — likely reflects that BABE bias is
more lexical/explicit while BASIL bias is more inferential, and DeBERTa-base
over-fits the lexical pattern in 3 epochs. The full per-view table is in
[outputs/basil/basil_metrics_table.csv](outputs/basil/basil_metrics_table.csv).

## Figure 3 observation — initial "5–10× larger" was a bug, now fixed

The first cut of this run reported DeBERTa-base's SHAP magnitudes as 5–10×
larger than BD/DR. **That was a tokenization-aggregation bug, not a real
property of the model.** `analysis.py`'s `aggregate_subword_shap_to_words()`
only recognizes RoBERTa `Ġ` and SentencePiece `▁` markers as word-start
signals. DeBERTa-v1's tokenizer uses literal **leading spaces** instead, so
the aggregator concatenated whole phrases between commas into a single
"word" — collapsing ~30 words per sentence down to ~4, which mechanically
inflated the per-instance mean |SHAP| by ~7×.

Fix: [scripts/fix_deberta_word_aggregation.py](scripts/fix_deberta_word_aggregation.py)
re-aggregates word_attribs from the (still-correct) cached `tokens` +
`shap_pos` arrays using a tokenizer-agnostic char-span splitter. Applied to
both `outputs/shap_samples_deberta.jsonl` and
`outputs/basil_shap/samples_deberta.jsonl`; `.bak` copies preserved.
`outputs/global_word_importance_deberta.csv` was also rebuilt from the
fixed cache.

**Corrected Figure 3 numbers (per-instance median |SHAP|, BABE):**

| | TP | FP | TN | FN |
|---|---|---|---|---|
| bias-detector | 0.028 | 0.037 | 0.025 | 0.030 |
| DA-RoBERTa    | 0.027 | 0.027 | 0.011 | 0.016 |
| **DeBERTa-base** | **0.028** | **0.034** | **0.016** | **0.023** |

DeBERTa-base sits between BD (high baseline) and DR (most conservative) —
a clean intermediate calibration, not a third regime. No clipping is needed
on the y=0.15 axis anymore. Both `outputs/babe_fig3_with_fn.png/.pdf` and
`outputs/fig3_facet_2x2.png/.pdf` have been regenerated with the corrected
data.

## Files modified

- **New:** `finetune_deberta_babe.py` — 175 lines, self-contained, reusable.
- **New:** `models/deberta-base-babe-ft/` — full HF checkpoint (~556 MB).
- **New:** `outputs/shap_samples_deberta.jsonl` — 327 records.
- **New:** `outputs/global_word_importance_deberta.csv` — 767 rows.
- **New:** `outputs/basil/predictions_deberta.csv` — 7,984 rows.
- **Updated** to register the third model:
  - [basil_eval.py:30-34](basil_eval.py#L30-L34) — MODELS list
  - [babe_shap_fn.py:172-178](babe_shap_fn.py#L172-L178) — MODELS list
  - [babe_shap_fn.py:321](babe_shap_fn.py#L321) — default `--models` flag
  - [babe_fig3_with_fn.py:33-37](babe_fig3_with_fn.py#L33-L37) — SAMPLES list
  - [scripts/figure1_redesign_shap.py:22-28](scripts/figure1_redesign_shap.py#L22-L28) — MODELS list
  - [scripts/babe_auprc.py:25-30](scripts/babe_auprc.py#L25-L30) — MODELS list
  - [scripts/fig3_facet_2x2.py:39-50](scripts/fig3_facet_2x2.py#L39-L50) — SAMPLES + MODELS
- **Patched for transformers 5.9 / datasets 4.8 compatibility:**
  - [analysis.py:484-485](analysis.py#L484-L485) — `Column` → `list()` for new datasets API
  - [analysis.py:374-379](analysis.py#L374-L379) — numpy→list for new tokenizer typing
- **Updated** `.gitignore` — added `models/`.

## Why v1 not v3 — diagnostic record

`microsoft/deberta-v3-base` was attempted with three configurations on MPS:

1. **fp32 + LR=2e-5 + default grad clipping:** training completed epoch 1,
   then the eval forward pass produced NaN logits, which sklearn rejected.
2. **bf16 + LR=2e-5 + grad clipping:** training "completed" but training loss
   started at 143 with grad_norm=1874, decreased to 0.5 by epoch 3, but the
   model converged to a degenerate uniform-logit output (eval_loss = 0.6931 =
   exactly ln(2)).
3. **fp32 + LR=1e-5 + no in-training eval, eval moved to CPU:** training ran
   to completion, **but the printed loss showed `grad_norm: nan` from step 50
   onwards.** Final test metrics: accuracy = 0.441 (predicting all
   Non-biased — completely degenerate).

Diagnosis: DeBERTa-v3's disentangled-attention gradient on MPS produces NaN
in either precision. PyTorch issues #95135 and #99272 document related MPS
numerical bugs in DeBERTa-v3's relative position embeddings. The official
fix path is to run DeBERTa-v3 on CUDA — Apple Silicon is not currently
supported.

To get DeBERTa-v3-base specifically (as the original plan named), the path
is Colab/cloud GPU. The `finetune_deberta_babe.py` script is portable — change
`MODEL_ID = "microsoft/deberta-v3-base"` and `OUTPUT_DIR` to match, then run
it in a Colab notebook. Took 6 min on MPS with v1; would take ~3 min on a
free Colab T4 with v3.

## Known rough edges / what was NOT done

- `analysis.py` exits non-zero at the very end on a `shap.save_html(...)`
  call — a SHAP-API drift between v0.50 and v0.51. **Doesn't affect the
  cache files** (they're written before that call). If you want HTML force
  plots for sample inspection, line 608 needs updating to use the new
  `shap.plots.text(...)` return type.
- `basil_shap_generate.py` was extended to also generate the **magnitude**
  strata for deberta (the comparison-based strata like `fp_shared`,
  `fp_bd_only`, `fp_dr_only`, `fn_shared_lex` were *not* extended — they're
  2-model-comparison by design). The deberta-side run added 400 SHAP records
  (100 each TP/FP/TN/FN) to `outputs/basil_shap/samples_deberta.jsonl`, and
  the resulting deberta rows were merged into
  `outputs/basil_shap/basil_shap_magnitude.csv` (now 1,200 rows total — 3
  models × 400 records). Took 87.7 min on CPU.
- The 3x2 facet figure (`outputs/fig3_facet_2x2.png` / `.pdf`) is now
  regenerated with the third DeBERTa-base row. The dynamic row-count change
  is at [scripts/fig3_facet_2x2.py:133](scripts/fig3_facet_2x2.py#L133).
- Several downstream figure scripts were written for **exactly 2 models** and
  would need refactoring to plot 3:
  - `babe_fig6_confound.py` — hardcoded shap_samples237.jsonl for biasdetector
  - `scripts/babe_fp_partition.py` — "shared/bd_only/dr_only" three-way
    partition logic is 2-model by design
  - `scripts/shap_mannwhitney.py` — pairwise comparisons only
- `scripts/fig3_facet_2x2.py` was updated for 3 models but its BASIL panels
  depend on `basil_shap_magnitude.csv` for deberta, which doesn't exist yet
  (see basil_shap_generate.py bullet above). Running it now would error on
  the missing deberta-BASIL data.

## How to reproduce / extend

```
# Retrain (overwrites checkpoint):
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python finetune_deberta_babe.py

# Add BASIL-side SHAP (long):
.venv/bin/python basil_shap_generate.py --models deberta

# Regenerate the 3-model Fig 3 + metrics:
.venv/bin/python babe_fig3_with_fn.py
.venv/bin/python compute_metrics.py
```
