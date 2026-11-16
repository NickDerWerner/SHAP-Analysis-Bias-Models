# ARR M4E-6c — Methodology Compression

**Date:** 2026-11-16  
**Status:** Complete (author review).  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Baseline PDF:** `docs/revisedPaper_M4E6b_local.pdf` (19 pp; ≈10.5 content)  
**Post-edit PDF:** `docs/revisedPaper_M4E6c_local.pdf` (17 pp; ≈**8.2** content)

---

## 1. Methodology outline

### Before
3.1 Dataset and Models · 3.2 SHAP Framework · 3.3 Word Aggregation (+ Fig 2) · 3.4 Sampling (+ Table 1*) · 3.5 Analysis Framework · 3.6 Faithfulness · 3.7 Gold-span · 3.8 Human · 3.9 Stats · 3.10 Metrics

### After
3.1 Dataset and Models · 3.2 SHAP and Word-Level Aggregation · 3.3 Evaluation Populations and Sampling (+ Table 1* + paired-similarity paragraph) · 3.4 Faithfulness · 3.5 Gold-span · 3.6 Human · 3.7 Inference and Metrics (merged)

---

## 2. Word counts

| Block | Before (approx.) | After |
|-------|-----------------:|------:|
| Full Methodology (main) | ~2830 | **~968** |
| **Main words removed** | | **~1860** |
| New `app:method_details` | — | ~550 |
| Fig 2 moved into `app:word_aggregation` | main | appendix |

---

## 3. Relocation map

| Original | Receiving appendix | Preserved meaning |
|----------|--------------------|-------------------|
| BABE HF/SG note; BASIL CSV match; span `text[start:end]=txt`; quote flags | `app:method_details` | Provenance |
| Deb path, train-time AUPRC/F1, caches-only | `app:method_details` | Checkpoint caveat |
| Per-model cache construction (337/312/327; 850/837/400; overlaps) | `app:method_details` | Sampling detail (Table 1 still in main) |
| Aggregation heuristics; DeBERTa repair; Fig 2 | `app:word_aggregation` | Reporting vs offset paths |
| Faithfulness fallbacks, logit-margin, 3 random draws | `app:method_details` | Implementation |
| Gold join keys; secondary P/R/AP; positional/regression controls; cache 849/475… | `app:method_details` | Implementation |
| AnnB file update; integrity; human–BASIL categorical | `app:method_details` | Implementation |
| Long Analysis Framework / Em/Ev paragraph | Cut + pointer to App A | Taxonomy retired |
| Separate §3.9–3.10 | Merged §3.7; MW/McNemar → App D pointer | Uncertainty conventions |

---

## 4. Scientific-preservation checklist

| Required element | In main? |
|------------------|----------|
| BABE/BASIL definitions + union binary + non-comparability | Yes |
| BD/DR/Deb scope; no invented pins | Yes |
| Explainer + Text masker; biased-class; no test background | Yes |
| Sum aggregation; offset path ≠ reporting; Deb caveat | Yes |
| Table 1 populations; $t{=}0.5$; paired vs unpaired; TN$=$3 | Yes |
| Faithfulness $n{=}200$; A–E; $k\in\{1,2,3\}$; $\Delta P$/$\|\Delta P\|$; mask OOD | Yes |
| Gold mass; random baseline; coverage match; gold-positive $n$ | Yes (detail $n$ also in app) |
| Human $n{=}120$; tasks; $\kappa$; soft-F1; cache∩; **26 yes∅spans** | Yes |
| Jaccard@20 + cosine; shared-ID pairing | Yes (§3.3 paragraph) |
| $t{=}0.5$ vs AUPRC; sentence-level bootstrap; no false independence | Yes |

Results numbers unchanged (e.g. ΔP 0.327, Jac 0.818, $\kappa$ 0.439 present in PDF).

---

## 5. Cross-references

| Label | Status |
|-------|--------|
| `sec:word_aggregation`, `sec:sampling`, `sec:faithfulness_protocol`, `sec:gold_span_alignment`, `sec:human_annotations` | Kept on compressed subsections |
| `sec:stats` + `sec:metrics` | Both on merged §3.7 |
| `tab:eval_populations` | Kept |
| `fig:shap_pipeline` | Moved to appendix (one `\label`) |
| `app:method_details` | New |
| Log undefined refs | **0** |

Scope: **no** edits to Abstract/Intro/RW/Results/Discussion/Conclusion/Limitations/Ethics/bib.

---

## 6. PDF page-count comparison

| Metric | M4E-6b | M4E-6c |
|--------|-------:|-------:|
| Total PDF pages | 19 | **17** |
| Content (through Conclusion) | ≈10.5 | ≈**8.2** |
| Saved this module | — | ≈**2.3** content pages |
| ARR limit | 8 | 8 |
| **Remaining overrun** | ≈2.5–3 | ≈**0.2–0.3** |

**Verified detail:** Conclusion begins on p8 and **spills ~12 lines onto p9** immediately before Limitations. Under a strict reading, content is still **slightly over** eight pages until that overflow is pulled back (Discussion trim or float tweak — **not** done in M4E-6c).

---

## 7. Methodological risks introduced

| Risk | Mitigation |
|------|------------|
| Reviewers miss join keys / cache construction | Appendix pointers; Table 1 retained |
| Aggregation figure only in appendix | Short main definition + App |
| Merged stats section thinner | Primary CIs still defined; App D for MW/McNemar |
| Over-compression of Deb provenance | Main states caches-only + unpinned Hub; App has AUPRC/F1 |

---

## 8. Ready for author review?

**Yes.** Next optional module (not started): M4E-6d Discussion/RW compression or float pagination to clear the ~0.2–0.3 page Conclusion overflow.
