# M4A-8a Change Record — Aggregation Consolidation

**Date:** 2026-11-15  
**File:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Primary scope:** `\subsection{Word-Level Attribution Aggregation}` `\label{sec:word_aggregation}`  
**Minimal related edits:** one sentence each in faithfulness (word selection) and gold-span (word localization) for unambiguous cross-refs.  
**Not edited:** Appendix, Results, Abstract, Intro, Related Work, Conclusion, Limitations, Sampling, Dataset, SHAP framework body, Human annotations body.

---

## 1. Before / after

### Aggregation subsection

| | ≈ prose words |
|--|-------------:|
| Before (M4A-8 audit) | **518** |
| After | **≈438** |
| Δ Aggregation | **≈ −80** |

### Methodology total

| | ≈ prose words |
|--|-------------:|
| Before M4A-8a | ≈3214 |
| After M4A-8a | ≈3133 (recomputed) |
| Net Methodology Δ | **≈ −81** |

Full 1900–2200 target **not** claimed complete.

### Structural changes

- Added `\label{sec:word_aggregation}`.  
- DeBERTa ¶: ~8 sentences → **2** (issue + corrected mapping; validation + whitespace-mass caveat).  
- Removed `.bak`, in-place rewrite narrative, additive JSONL diagnostics, and “see appendix” claim (appendix not updated this module).  
- Perturbation alignment kept as canonical definition; notes reuse for gold/human mass scoring.  
- Faithfulness / gold-span: replaced “pipeline above” with `Section~\ref{sec:word_aggregation}`; retained experiment-specific rules (≥50\% gold overlap; special/empty/repeat handling; mask token).

---

## 2. Evidence for retained statements

| Statement | Evidence |
|-----------|----------|
| Explainer units ≠ necessarily classifier internals / orthographic words | M4A-1; Text masker tokens |
| RoBERTa grouping: whitespace / Ġ/▁ + heuristics; skip specials; **sum** | `basil_shap_generate.py` `aggregate_subword_shap_to_words` |
| Sum preserves mapped-unit attribution; not full-path conservation / causality | Same; M4A-2 |
| DeBERTa leading-space vs BPE markers → collapsed surfaces | `fix_deberta_word_aggregation.py` docstring |
| Char-span whitespace-split recompute from `tokens`+`shap_pos` | Same script `reaggregate` |
| Integrity: word lists align to source; usable for magnitude | `ARR_M1_VALIDATION_REPORT.md` Task C (327/327, 400/400) |
| Whitespace character mass excluded from word totals | M1 report; charspan procedure |
| Reporting ≠ faithfulness test | Explicit; claim ledger |
| Offset-aware masking distinct from reporting aggregation | `offset_alignment.py`; M2B |
| Gold/human mass uses same localization + ≥50\% word-in-gold | M2C `gold_word_thresh=0.5` |

---

## 3. Details removed (and why)

| Removed from main text | Why |
|------------------------|-----|
| `.bak` backups / in-place cache rewrite | Implementation history, not scientific procedure |
| Additive derived JSONL / strict Σ residual | Diagnostic; pending appendix |
| “Further implementation notes appear in the appendix” | Avoid pointing at outdated/unupdated appendix section |
| Long DeBERTa diagnostic comparison to RoBERTa under same charspan | Compressible; keep whitespace caveat only |

---

## 4. Pending appendix material (not written this module)

1. Full DeBERTa repair procedure (`.bak`, in-place rewrite).  
2. Additive reaggregation paths and residual checks (`arr_m1/word_aggregation.py`, `deberta_integrity/`).  
3. Refresh existing “Word-Level Attribution Aggregation in Detail” appendix so it matches Explainer+Text terminology and documents DeBERTa correction + offset alignment (separate approval).

---

## 5. Verification

| Check | Result |
|-------|--------|
| Essential facts 1–7 from approval prompt | Retained |
| No perfect-conservation claim | OK (whitespace exclusion stated) |
| No faithfulness-from-aggregation claim | OK |
| Labels `sec:word_aggregation`, `sec:faithfulness_protocol`, `sec:gold_span_alignment` | Present; forward refs OK |
| `.bak` in Aggregation | Absent |
| Unrelated TODOs | Untouched |
| Compile | **UNVERIFIED** (no engine) |
| Brace balance on Aggregation chunk | 0 |

---

## 6. Further duplication (deferred)

| Item | Module |
|------|--------|
| Sampling integer density / stratum laundry list | M4A-8b |
| Stats/Metrics κ and AUPRC repeats | M4A-8c |
| T13/T14 conceptual TODOs | M4A-8d/e |
| AnnB revision-history tone | M4A-8f |

---

## Diff hygiene

Only Aggregation rewrite + two short cross-ref sentences in Faithfulness and Gold-span. No appendix edit.
