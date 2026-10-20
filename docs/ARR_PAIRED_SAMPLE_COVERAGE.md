# ARR Paired Sample Coverage (M1)

**Code:** `scripts/arr_m1/run_paired_alignment.py`  
**Outputs:** `outputs/arr_m1/paired/`  
**Canonical IDs:**
- BABE: `babe:` + SHA256(text)[:16]
- BASIL: `basil:{triplet_uuid}|{outlet_idx}|{sentence_idx}`

Original SHAP caches were **not** modified.

---

## 1. BABE coverage

| Set | n unique sentences |
|-----|--------------------:|
| biasdetector cache | 337 |
| daroberta | 312 |
| deberta | 327 |
| bd ∩ dr | (see id maps) |
| **all three models** | **59** |

### Same prediction cell for all three (among the 59)

| Cell | n |
|------|--:|
| TP | 7 |
| FP | 3 |
| TN | 4 |
| FN | 26 |

**Limitation:** Same-cell n &lt; 30 for TP/FP/TN — **insufficient** for claiming three-model cell-specific attribution effects on BABE without new shared sampling.

### Paired attribution similarity (all 59; mixed pred types)

| Pair | n | median Jaccard@20 | median cosine(|SHAP|) |
|------|--:|------------------:|----------------------:|
| BD–DR | 59 | 0.625 | 0.783 |
| BD–DeBERTa | 59 | 0.538 | 0.666 |
| DR–DeBERTa | 59 | 0.500 | 0.627 |

Artifacts: `babe_paired_all3.csv`, `babe_paired_similarity_summary.csv`, `babe_id_map.csv`.

**Rule:** Do not interpret differences between the full unpaired TP/FP pools (100/37 vs 100/12 vs 100/27) as architecture effects.

---

## 2. BASIL coverage

| Set | n |
|-----|--:|
| biasdetector cache | 850 |
| daroberta | 837 |
| deberta (magnitude only) | 400 |
| **bd ∩ dr** | **371** |
| **all three** | **60** |

### Designed paired subsets (BD ↔ DR)

| Subset | n | median Jaccard@20 | median cosine | median mean\|SHAP\| BD | median mean\|SHAP\| DR |
|--------|--:|------------------:|--------------:|----------------------:|----------------------:|
| bd∩dr all | 371 | 0.762 | 0.820 | 0.041 | 0.032 |
| shared FP (gold=0, both pred=1) | **112** | **0.818** | 0.855 | 0.050 | 0.039 |
| shared FN (gold=1, both pred=0) | **104** | 0.727 | 0.781 | 0.034 | 0.017 |

These support **two-model** paired claims. Paper’s ~0.81 shared-FP Jaccard is consistent with this recomputation (0.818 on n=112 cache intersection; manifest stratum used n=100).

DeBERTa lacks `fp_shared` / `fn_shared_lex` strata (`basil_shap_generate.py`), so three-model paired error analysis is limited to the 60-sentence magnitude overlap.

Artifacts: `basil_paired_bd_dr.csv`, `basil_pair_summary.csv`, `basil_paired_all3.csv`, `basil_strata_summary.csv`.

---

## 3. What can be retained in the paper

| Claim type | Retain? | Basis |
|------------|---------|-------|
| BD↔DR shared-FP token overlap (BASIL) | **Yes**, as paired | n=112, Jaccard≈0.82 |
| BD↔DR magnitude gap on shared FP/FN | **Yes**, paired | same |
| Three-model “same mechanism” on BABE cells | **No** as currently sampled | unpaired + tiny same-cell all3 |
| Three-model TN calibration spectrum | **Only with caveat** | needs confidence control (E4) and/or shared sentences |
| Category composition all3 | Use taxonomy v2; do not imply paired | pool-level only |

---

## 4. Shared-sentence SHAP regeneration protocol (not executed)

See `outputs/arr_m1/paired/shared_shap_regen_protocol.json`.

Summary:
1. Define shared sentence list S (seed=7) for cells of interest.  
2. Extend BASIL manifest so DeBERTa participates in `fp_shared` / `fn_shared` with **identical keys**.  
3. Append-only SHAP generation; never overwrite existing JSONL.  
4. Re-run this paired script.  
5. Budget ≈ 15–20 s/sentence/model on CPU (historical).

**M1 status:** protocol documented only; **not run**.
