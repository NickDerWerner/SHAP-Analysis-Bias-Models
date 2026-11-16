# ARR M4E-6b — Supporting Results Relocation and RQ4 Compression

**Date:** 2026-11-16  
**Status:** Complete (author review). Option B partial execution.  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Baseline PDF:** `docs/revisedPaper_M4E5c_local.pdf` (19 pp; ≈12.6 content)  
**Post-edit PDF:** `docs/revisedPaper_M4E6b_local.pdf` (19 pp; ≈**10.5** content)

---

## 1. Before / after Results structure

### Before (main)
4.1 Overall performance · 4.2 Perturbation · 4.3 Gold-span · 4.4 Human · **4.5 Magnitude** · **4.6 Paired similarity** · **4.7 Word surfaces** · **4.8 Vocab note** · **4.9 Stats catalogue**

### After (main)
4.1–4.4 **unchanged** · **4.5 Magnitude bridge** (short) · **4.6 Paired similarity** (compressed + slim Table 7)

### After (appendix)
A Vocab confound **+** retired Em/Ev note (`sec:word_patterns`)  
B **Supplementary Attribution-Magnitude** (mean figs/table + MW + prior max analysis)  
C AUPRC strata  
D **Supplementary Statistical Comparisons** (`app:supp_stats` / `sec:significance`)  
E **High-Attribution Word Surfaces** (`fig:tbi`)  
F Token-level examples  
G Word-level aggregation detail  

(Lettering follows compile order; labels are stable.)

---

## 2. Relocations

| Item | From | To |
|------|------|----|
| Figs `smd_babe`, `smd_basil` | §4.5 | App B (`app:max_shap`) |
| Table `shap_magnitudes` | §4.5 | App B |
| Magnitude prose + MW tests | §4.5 / §4.9 | App B |
| Fig `tbi` + word-list prose | §4.7 | App E (`app:word_surfaces` / `sec:global_bias`) |
| Em/Ev residual note | §4.8 | App A (`sec:word_patterns`) |
| McNemar (BABE FPR) | §4.9 | App D — **disposition:** belongs with Table 2 / §4.1; §4.1 not edited (scope) |
| Shared-error counts; both-type union arithmetic | §4.9 | App D |
| BABE/BASIL all3 Jaccard rows; shared-error mean-\|SHAP\| ratios | §4.6 | App D (`tab:paired_sim_app`) |
| Optional magnitude / stats `\revnote`s | main | moved with content (still suppressed in review PDF) |

**Not relocated / protected:** Tables 2–5; §4.1–4.4 prose; primary BASIL paired medians in Table 7.

---

## 3. RQ4 before / after

**Before (~408 words + 4-row table):** full BABE/all3 discussion, mean-\|SHAP\| ratios, co-error pointer, Jaccard definition + mechanism caveats.

**After (~162 words + 3-row BASIL-only table):**

- Population: matched BASIL BD∩DR; Jaccard@20 as \|A∩B\|/\|A∪B\|; cosine of L1 \|SHAP\| bags.  
- Numbers (verified vs M4B-4 / M1): *n*=371; shared FP 112 → Jac 0.818 / cos 0.855; shared FN 104 → 0.727 / 0.781; all ∩ → 0.762 / 0.820.  
- Explicit non-mechanism caveat; secondary rows → App D.  
- No “% of top-20” wording; no CIs claimed.

---

## 4. Word / float accounting

| Metric | Approx. |
|--------|--------:|
| Results section words (main, after) | ~2201 |
| Prior Results mass (M4E-6a estimate) | ~3223 |
| **Net Results reduction** | **~1.0k words** |
| Appendix words (after) | ~2800 |
| Prior appendix (M4E-6a estimate) | ~1.5k |
| **Appendix growth** | **~1.3k words** |
| Main floats removed | Figs 3–5 (old numbering), Table 6 |
| Main floats retained (RQ) | Tables 2–5, Table 7 (slim), Fig 1 |

---

## 5. Verification

| Check | Result |
|-------|--------|
| §4.1–4.4 / Tables 2–5 untouched in intent | Yes (numbers still in PDF: ΔP 0.327/0.293; gold 0.080; human κ 0.439; P 0.924) |
| RQ1–3 intact | Yes |
| RQ4 adequately answered | Yes (primary BASIL medians + Table 7) |
| Labels / undefined refs | Log: **0** undefined refs |
| Em/Ev / calibration / mechanism claims | Not reintroduced |
| M1 number audit | Matches `ARR_M4B4_PAIRED_SIMILARITY_RESULTS_CHANGE.md` |
| Scope creep (Intro/Methods/Discussion/Ethics) | **No** prose edits there (refs may now resolve to appendix labels) |
| Review TODOs visible | None in PDF (`\showrevnotes` still false) |

---

## 6. Page budget

| | Baseline M4E-5c | After M4E-6b |
|--|----------------:|-------------:|
| Total PDF pages | 19 | **19** |
| Content (Abstract→Conclusion) | ≈12.6 | ≈**10.5** (Conclusion mid-p11; Limitations p12; Refs p13) |
| Estimated content pages saved | — | ≈**2.0–2.1** |
| Remaining to 8-page target | ≈4.5–5 | ≈**2.5–3** |

Savings are real on the **content** budget even though total PDF page count stayed 19 (appendix grew). Further cuts need **M4E-6c** (Methods) / **M4E-6d** (front/back prose).

---

## 7. Outstanding layout

- Tables 3–4 still `table*` (float pressure on p10).  
- Appendix magnitude section is long (mean + max).  
- McNemar not yet inlined into §4.1 (deferred by scope).  
- Discussion still says “Section …” for labels now living partly in appendix — acceptable; optional later wording pass.

---

## 8. Ready for author review?

**Yes — M4E-6b ready for review.**  
Do not start Methods compression until approved.
