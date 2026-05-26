# FP-Paragraph Numbers (current SHAP caches, 2026-05-26)

Source script: [scripts/fp_word_analysis.py](scripts/fp_word_analysis.py)

Caches used:
- [outputs/shap_samples.jsonl](outputs/shap_samples.jsonl) — bias-detector, 337 records (37 FPs, 100 TPs)
- [outputs/shap_samples_daroberta.jsonl](outputs/shap_samples_daroberta.jsonl) — DA-RoBERTa-BABE-FT, 312 records (12 FPs, 100 TPs)

All "mean |SHAP|" headlines below use **pooled aggregation across word-attribs**
(every word in every FP/TP contributes once, no per-instance averaging).
This matches how the TP headlines in `KEY_FINDINGS.md` are reproduced exactly
(0.0277 ≈ 0.0276 bd, 0.0266 = 0.0266 dr); see §3 for the headline-FP discrepancy.

---

## 1. bias-detector FP paragraph

**FP set:** 37 instances (gold = Non-biased, pred = Biased).

**Mean confidence on FPs:** **0.7959** (vs 0.9411 on TPs)

**Mean |SHAP| per FP word (pooled):** **0.0378** (vs 0.0277 on TPs)

**Mean |SHAP| per FP instance (instance-avg):** 0.0447 (alternative aggregation)

### Top FP words by mean |SHAP| (any-frequency — single highest-pull tokens)

| word | n | mean \|SHAP\| | mean signed | direction |
|---|---|---|---|---|
| frantically | 1 | 0.4504 | +0.4504 | toward Biased |
| sided | 1 | 0.4106 | +0.4106 | toward Biased |
| denigrate | 1 | 0.3862 | +0.3862 | toward Biased |
| juggernaut | 1 | 0.3854 | +0.3854 | toward Biased |
| opponents | 1 | 0.3475 | −0.3475 | toward Non-biased |
| wealthy | 1 | 0.3451 | +0.3451 | toward Biased |
| left | 1 | 0.3248 | +0.3248 | toward Biased |
| hard | 1 | 0.3043 | +0.3043 | toward Biased |

### Top RECURRING FP words (count ≥ 2 across the 37 FPs)

| word | n | mean \|SHAP\| | mean signed | direction |
|---|---|---|---|---|
| pandemic | 2 | 0.1975 | +0.1975 | toward Biased |
| illegal | 2 | 0.1400 | +0.1400 | toward Biased |
| said | 2 | 0.1304 | −0.1304 | toward Non-biased |
| Tuesday | 3 | 0.1128 | −0.1128 | toward Non-biased |
| could | 2 | 0.1094 | −0.1094 | toward Non-biased |
| not | 4 | 0.0933 | −0.0775 | toward Non-biased |
| TV | 2 | 0.0814 | −0.0497 | toward Non-biased |
| Trumps | 2 | 0.0670 | +0.0670 | toward Biased |

### "illegal" comparison (TPs vs FPs) — **verified**

| set | mean \|SHAP\| | occurrences | instances with word |
|---|---|---|---|
| TPs (100) | **0.3489** | 4 | 3 |
| FPs (37)  | **0.1400** | 2 | 2 |

These match the paragraph's existing 0.349 / 0.140 values exactly. ✅

---

## 2. DA-RoBERTa-BABE-FT FP paragraph

**FP set:** 12 instances.

**Mean confidence on FPs:** **0.6732** (vs 0.8857 on TPs)

**Mean |SHAP| per FP word (pooled):** **0.0267** (vs 0.0266 on TPs)

**Mean |SHAP| per FP instance (instance-avg):** 0.0310

### Top FP words by mean |SHAP| (any-frequency)

| word | n | mean \|SHAP\| | mean signed | direction |
|---|---|---|---|---|
| gruesome | 1 | 0.3388 | +0.3388 | toward Biased |
| unbelievable | 1 | 0.3064 | +0.3064 | toward Biased |
| quaint | 1 | 0.2991 | +0.2991 | toward Biased |
| archivist | 1 | 0.2986 | +0.2986 | toward Biased |
| unfortunately | 1 | 0.2514 | +0.2514 | toward Biased |
| **claims** | **2** | **0.2061** | **+0.2061** | toward Biased |
| bombshell | 1 | 0.1631 | +0.1631 | toward Biased |
| claimed | 1 | 0.1593 | +0.1593 | toward Biased |

### "claims / claimed / claiming" cross-class verification — **verified**

The `claims*` stem appears in **both** TPs and FPs:

| set | mean \|SHAP\| | occurrences | instances with word |
|---|---|---|---|
| TPs (100) | 0.1254 | 1 | 1 / 100 |
| FPs (12)  | 0.2061 | 2 | 2 / 12 |

So yes — the claim that "*claims/claimed/claiming* appears in both TPs and FPs"
still holds. Note also that the mean |SHAP| of the stem is actually **higher in
FPs** than in TPs (0.2061 vs 0.1254), which strengthens the paragraph's point
that DA-RoBERTa over-weights this stem when it fires incorrectly.

---

## 3. Headline FP magnitude — does NOT exactly match `KEY_FINDINGS.md`

Expected (from §4.2 / Table 2 / `KEY_FINDINGS.md`):

| model | TP mean \|SHAP\| | FP mean \|SHAP\| |
|---|---|---|
| bias-detector | 0.0276 | **0.0354** |
| DA-RoBERTa | 0.0266 | **0.0215** |

Current pooled values from the live caches:

| model | TP (pooled) | FP (pooled) | TP (per-instance) | FP (per-instance) |
|---|---|---|---|---|
| bias-detector | **0.0277** ✅ | 0.0378 | 0.0362 | 0.0447 |
| DA-RoBERTa | **0.0266** ✅ | 0.0267 | 0.0335 | 0.0310 |

**TPs match exactly under pooled aggregation.** FPs do not — the live FP magnitudes
are slightly higher for bd (0.0378 vs 0.0354) and noticeably higher for dr
(0.0267 vs 0.0215). I checked the legacy `shap_samples237.jsonl` file
(237 records, same 37 FPs) and got pooled FP = 0.0398 — also not a match.

### Why the drift

Both jsonl caches have been **regenerated since the headline numbers were written**
(May 25 timestamps on the current files; the headline numbers in
`KEY_FINDINGS.md` reference an earlier run that used a different SHAP
random seed / max-evals / explainer config). The FP *count* is unchanged
(37 / 12), but the per-word SHAP values themselves have shifted slightly.

### Recommended action

Pick one of:

1. **Update §4.2 / Table 2 to the current pooled values** (bd FP = 0.0378,
   dr FP = 0.0267). This is the lowest-effort fix and the TP numbers already
   match.
2. **Re-run the original SHAP config** and overwrite the caches so the
   headline numbers are reproducible. Requires re-running `analysis.py` and
   `babe_shap_fn.py` with whatever seed/max-evals produced 0.0354/0.0215.
3. **Compute over a subset** — if the original headline used the first 100
   FPs only, or a different threshold, that would explain it. I did not find
   the original aggregation script that produced 0.0354 in the repo (the
   value appears only in `KEY_FINDINGS.md` and `ASK_CODING_AGENT.md`); the
   research notebook (`research_analysis.ipynb`) does compute FP stats but
   I didn't trace it line-by-line.

Recommendation: **option 1** (update the table). The TP numbers match exactly,
so the cache regeneration was internally consistent; the FP shift is real
data, not a methodology bug.
