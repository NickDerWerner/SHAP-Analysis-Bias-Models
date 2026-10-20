# ARR Hardware Assessment

**Machine audited:** MacBook Air (Apple M1), macOS 14.4.1  
**Date:** 2026-10-20  
**Policy:** Inexpensive benchmarks only; no full SHAP regeneration; no training; no large Hub downloads initiated by this audit.

---

## 1. System profile (Verified)

| Item | Value |
|------|-------|
| Model | MacBook Air |
| Chip | Apple M1 (arm64) |
| CPU | 8 cores (4 performance + 4 efficiency) |
| RAM / unified memory | **8 GB** (`hw.memsize` = 8589934592) |
| Free RAM at audit | ≈ **84 MB** free pages (heavy memory pressure) |
| Python (system) | 3.12.13 (`/opt/homebrew/opt/python@3.12`) |
| Project `.venv` | **Absent** |
| PyTorch (system) | 2.11.0 |
| MPS | `torch.backends.mps.is_available()` = **True**, built True |
| CUDA | **False** |

### Installed vs missing (system Python)

| Package | Status |
|---------|--------|
| `torch` | Present |
| `numpy` | Present |
| `transformers` | 5.4.0 |
| `shap` | **Missing** |
| `datasets` | **Missing** |
| `sklearn` / `pandas` / `matplotlib` / `scipy` | **Missing** |

Scripts historically expect `.venv/bin/python` (`OVERNIGHT_RUN_SUMMARY.md`, many headers). That environment is not on this machine.

### Hugging Face local cache

- Hub cache ≈ 2.1 GB  
- Present: `models--himel7--bias-detector`  
- **Absent:** DA-RoBERTa-BABE-FT, `microsoft/deberta-base`, local fine-tune `models/deberta-base-babe-ft/`

---

## 2. Code device paths

| Script | Device logic | macOS behavior |
|--------|--------------|----------------|
| `run_inference.py` L34–39 | MPS → CUDA → CPU | **Uses MPS** |
| `finetune_deberta_babe.py` | Trainer default + `PYTORCH_ENABLE_MPS_FALLBACK` | MPS training (v1 OK; v3 NaN) |
| `analysis.py` L470 | CUDA else **CPU** | **CPU SHAP** (no MPS) |
| `basil_shap_generate.py` L487 | CUDA else **CPU** | **CPU SHAP** |
| `babe_shap_fn.py` | Same pattern as generate (CPU on Mac) | CPU |

**CUDA-specific code:** only `torch.cuda.empty_cache()` after BASIL SHAP (`basil_shap_generate.py` L449–450). Safe on Mac (branch not taken).

**Recommendation:** For future pilots, optionally add MPS to SHAP scripts **only after** verifying `shap` + transformers stability on MPS; default remains CPU for attribution fidelity matching released caches.

---

## 3. Inexpensive benchmarks run

| Benchmark | Result | Uncertainty |
|-----------|--------|-------------|
| Load all BABE SHAP JSONL (976 records) | **0.037 s** | Low |
| Load all BASIL SHAP JSONL (2087 records) | **0.076 s** | Low |
| CPU 2048×2048 matmul (5-iter mean) | **23.4 ms/iter** | Microbenchmark only |
| MPS 2048×2048 matmul (5-iter mean) | **21.3 ms/iter** | Microbenchmark only; not model throughput |
| RoBERTa-class weight footprint (order-of-magnitude) | ~0.5 GB fp32 params | Does not include activations, SHAP, tokenizer, Python |

**Not run (would download or OOM risk):** single-model Hub load, 20-sentence perturbation, 5–10 sentence SHAP generation.

### Historical timings from repo docs (external evidence; not remeasured)

| Workload | Reported | Source |
|----------|----------|--------|
| DeBERTa-base fine-tune (BABE) | ~6 min MPS | `OVERNIGHT_RUN_SUMMARY.md` |
| BASIL inference 7,984 sents | ~34 s MPS | same |
| BABE SHAP ~237 examples (DeBERTa) | ~62 min **CPU** | same |
| Append 100 FN SHAP | ~28 min CPU | same |
| BASIL DeBERTa magnitude 400 sents | ~87.7 min CPU | same |

**Uncertainty:** These timings were on the same class of Apple Silicon workflow but possibly different free-RAM / torch / shap versions. Treat as ±30–50% until re-piloted on this 8 GB Air under a clean venv.

---

## 4. Memory feasibility on 8 GB unified

| Workload | Feasibility on this Mac | Notes |
|----------|-------------------------|-------|
| Load / analyze existing SHAP caches | **Yes** | Proven; peak ≪ 1 GB |
| Taxonomy / matched-pool / stats CLIs | **Yes** | CPU/pandas |
| Single encoder inference batch (bs≤8) | **Likely yes** with closed apps | ~0.5 GB weights + activations; 8 GB is tight |
| Perturbation pilot (20 sentences, 3 conditions, 3 models) | **Marginal–OK** | Prefer sequential model loads; unload between models |
| SHAP for 5–10 new sentences (one model) | **Possible but slow** on CPU; risk of swap thrash | Match overnight ~15–20 s/sent order-of-magnitude → ~2–3 min for 10 |
| Full SHAP regen (hundreds) | **Not recommended** on 8 GB Air | Multi-hour + memory pressure |
| DeBERTa-v3 train | **No** (MPS NaN) | Needs CUDA server |
| Parallel multi-model SHAP | **No** | Will OOM |

At audit time free RAM was ~84 MB — **close all browsers/IDEs extras** before any model load.

---

## 5. Safe pilot plan (next phase)

Execute only after M0 env restore. Log wall time + `ps` RSS peak for each.

### P1 — Cache load (done-class)
- Command: load three BABE + three BASIL JSONL; count records.  
- **Accept:** completes &lt; 1 s; no writes.

### P2 — Single-model inference (10 BASIL sentences)
- Load `himel7/bias-detector` from local HF cache (already present).  
- MPS forward, max_length 256, batch 1 then 4.  
- **Accept:** record ms/sent and peak RSS.  
- **Do not** download other models until P2 succeeds.

### P3 — Perturbation inference (20 sentences, one model)
- Use texts from `outputs/basil_shap/basil_shap_fp_shared_paired.csv` / JSONL.  
- Three mask conditions × 20 = 60 forwards (no SHAP).  
- **Accept:** timing table; Δp computed.

### P4 — SHAP micro (5 sentences) — **only if P2–P3 leave &gt; 2 GB headroom**
- `shap` Explainer on CPU for bias-detector only.  
- Compare token count / mean |SHAP| to cached record for same text if present.  
- **Accept:** finishes without swap lockup; log s/sent.

### P5 — Full cache integrity check
- Already partially done in audit; automate checksums of JSONL without mutation.

---

## 6. GPU server recommendation

| Need | Mac 8 GB M1 sufficient? | GPU server justified when… |
|------|-------------------------|----------------------------|
| E1 taxonomy | **Yes** | — |
| E4/E5 cache analyses | **Yes** | — |
| E2 pilot (≤20–50 sents) | **Probably** | Pilot &gt; ~2–3 h or repeated OOM |
| E2 full (hundreds × 3 models) | **No** | Wall-clock or memory |
| E3 annotation tooling | **Yes** | — |
| New full SHAP strata (DeBERTa shared FP, etc.) | **Painful** | &gt; ~2–3 h CPU estimate from overnight rates |
| DeBERTa-v3 training | **No** | Always (CUDA) |
| Optional E6 SHAP on paraphrases | Small N **yes** | Large N |

**Verdict:** Personal Mac is **sufficient for M0, E1, E4, E5, and small E2/E3 pilots**. Prefer a **CUDA GPU server** only if (a) expanding SHAP caches substantially, (b) requiring DeBERTa-v3, or (c) measured pilot shows &gt; few hours or repeated memory failure on 8 GB.

---

## 7. Peak memory / runtime estimates (full intended experiments)

| Experiment | Estimate basis | Peak mem (order) | Runtime (order) | Confidence |
|------------|----------------|------------------|-----------------|------------|
| E1 full | Cache scan | &lt; 2 GB | &lt; 30 min | High |
| E4/E5 | Cache + preds CSV | &lt; 2 GB | &lt; 1 h | High |
| E2 N=20 × 3 models | Inference only | ~2–4 GB sequential | 10–40 min | Medium |
| E2 N=200 × 3 | Inference | same if sequential | 2–8 h | Low–medium |
| New SHAP 100 sents × 1 model | Overnight ~15–20 s/sent CPU | ~2–4 GB | ~25–35 min / 100 | Medium (historical) |
| Retrain DeBERTa-base | Overnight 6 min MPS | high during train | ~5–15 min | Medium |

**Do not extrapolate** beyond these without P2–P4 measurements on the restored venv.

---

## 8. Action items before next phase

1. Recreate project `.venv`; install `shap`, `transformers`, `datasets`, `scikit-learn`, `pandas`, `scipy`, `matplotlib`, `torch` (MPS build).  
2. Pin versions to a lockfile.  
3. Restore `models/deberta-base-babe-ft` from release artifact (preferred) before Hub retrain.  
4. Free RAM (target &gt; 3 GB free) before model pilots.  
5. Prefer sequential single-model workflows on this Air.
