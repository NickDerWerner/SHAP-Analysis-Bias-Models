# ARR M4E-5c — PDF Layout, Table, and Citation Repair

**Date:** 2026-11-16  
**Baseline PDF (author Overleaf):** `docs/revisedPaper.pdf` (copy of `Downloads/revisedPaper.pdf`, 2026-11-16) — **18 pages**; main content through ~p14; References from ~p15.  
**Local verification PDF:** `docs/revisedPaper_M4E5c_local.pdf` (tectonic compile of fixed sources) — **19 pages**; main content through ~p14; References from p15.  
**Sources edited:** `/Users/go52nom/Downloads/overleaf_latex/{acl_latex.tex,revision_macros.tex}`  
**Scientific content:** unchanged (no number/RQ/Ethics edits).

---

## 1. Page-by-page defect inventory (baseline `revisedPaper.pdf`)

| Page | Content (approx.) | Defects |
|-----:|-------------------|---------|
| 1 | Title, Abstract, Intro start | Anonymous title OK; no table overflow |
| 2 | Fig 1, RQs/contribs, Related Work 2.1–2.2 | Unresolved cite `(????)` for decoder-LLM cluster |
| 3 | Related Work 2.3–2.4, Methods start | Unresolved cites `(?DeYoung…)`, `(??)`, `(?)` for Jacovi/Atanasova cluster |
| 4 | Models, SHAP framework, Fig 2 | **Two yellow `\revnote`s** (Data protocol; Models) |
| 5 | Sampling + Analysis Framework; **Table 1 overflow** into gutter | Eval-population table column-width / single-column overflow |
| 6–7 | Faithfulness/gold/human Methods | Clean relative to known issues |
| 8 | Classification metrics; Results start | Yellow `\revnote`s (Magnitude confidence; Overall performance) |
| 9 | **Tables 3–4 collide** across columns | Faithfulness + gold-span overflow; captions crushed |
| 10 | Human Table 5 tight; Figs 3–4; yellow TODO | Table 5 near gutter; Fig 3–4 axis labels small; TODO visible |
| 11–12 | Magnitude/similarity/word surfaces | Yellow TODOs (global word lists; stats) |
| 13–14 | Discussion / Limitations / Ethics | Yellow Ethics `\revnote` (procedural disclosures) |
| 15–18 | References + Appendix | Six M4E-3 refs **missing** from bibliography body (Jacovi, Atanasova, Lin, Trhlík, Mujahid, Menzner); DeYoung/Dhaini present |

---

## 2. Table-by-table findings

| Label | Baseline problem | Correction applied | Numbers changed? |
|-------|------------------|--------------------|------------------|
| `tab:eval_populations` (Table 1) | Single-column `tabular` too wide; bleeds into gutter | → `table*` + `tabularx{\textwidth}` with fixed-width cols for Analysis/Data/Models and `X` for `$n$/design` | No |
| `tab:performance` (Table 2) | Fits; dense but readable | None | — |
| `tab:faithfulness` (Table 3) | Single-column overflow; collides with Table 4 | → `table*`; centered `llcccc`; slightly larger `\tabcolsep` | No |
| `tab:gold_span` (Table 4) | Collides with Table 3; caption width crushed | → `table*` (stacked full-width with Table 3) | No |
| `tab:shap_human` (Table 5) | Tight to gutter | Kept single-column; reduced `\tabcolsep` to 2.5pt; `llcrr` | No |
| `tab:shap_magnitudes` / Jaccard / appendix tables | No baseline overflow flagged | None | — |

**Local verify:** Table 1 on p6 full-width; Tables 3–4 stacked full-width on p10 (no side-by-side collision); Table 5 left column beside Fig 3.

---

## 3. Citations — diagnosis and resolution

### Symptom (baseline PDF)
- §2.1: `(????)` for `\cite{lin-etal-2025-investigating,trhlik-stenetorp-2024-quantifying,mujahid-etal-2025-profiling,menzner-leidner-2024-improved}`
- §2.3: `(?DeYoung et al., 2020)`, `(??)`, `(?)` for multi-cites involving `jacovi-goldberg-2020-towards` / `atanasova-etal-2020-diagnostic` (DeYoung alone resolved → classic “missing sibling key” natbib pattern)

### Source audit
- All six M4E-3 keys **present** in `custom.bib` (no duplicates; brace balance 0).
- All cite keys in `acl_latex.tex` **match** bib keys (no typos).
- `\bibliography{custom}` + `acl.sty` `\bibliographystyle{acl_natbib}` configuration is correct.
- **No replacement references invented.**

### Root cause
Author Overleaf PDF bibliography **did not contain** the six new entries (confirmed by scanning References pages). Local keys were already correct → stale/incomplete BibTeX `.bbl` on Overleaf (bib file not synced and/or BibTeX not re-run after `custom.bib` update), not bad citation keys.

### Resolution
- No key renames required.
- Local tectonic compile regenerates `.bbl` with all six keys; Related Work cites resolve; References lists Jacovi, Atanasova, Luyang Lin, Trhlík, Mujahid, Menzner.
- **Author action:** sync `custom.bib` + TeX to Overleaf → **Recompile from scratch** (clear aux/bbl) so BibTeX rebuilds.

---

## 4. TODO-macro diagnosis (`\revnote`)

### Symptom
Yellow inline TODOs printed on baseline pp. 4, 8, 10–12, 14 despite `\usepackage[review]{acl}` and the M4E-5a attempt to gate on `\ifacl@anonymize`.

### Root cause
`\ifacl@anonymize` is an ACL **internal** name. Outside `\makeatletter`…`\makeatother`, TeX tokenizes it as `\ifacl` + `@anonymize` → **Undefined control sequence** (confirmed by tectonic: `acl_latex.tex:161: Undefined control sequence \ifacl`). Recovery left `\revnote` effectively always printing. Same bug also broke the PDF-metadata clear block at `\begin{document}`.

### Fix applied (`revision_macros.tex`)
- Independent `\newif\ifshowrevnotes` (**default false**).
- `\revnote` prints only when `\showrevnotestrue`.
- Does **not** depend on ACL `@`-names.
- All `\revnote{…}{…}` source records retained (scientific TODOs not marked completed).
- Author drafts: uncomment `%\showrevnotestrue`.
- `\makeatletter`…`\makeatother` wrapped around the remaining `\ifacl@anonymize` hypersetup block.

### Local verify
Zero `TODO` strings in `revisedPaper_M4E5c_local.pdf`.

---

## 5. Figure legibility assessment

| Figure | Assessment | Action |
|--------|------------|--------|
| Fig 1 (shared FP) | Legible in column | None |
| Fig 2 (pipeline) | Legible | None |
| **Fig 3–4** (BABE/BASIL magnitude boxplots) | Axis category labels and tick text are small at column width; readable at screen zoom, marginal in print | **No regeneration** this module |
| Fig 5 (top words) | Acceptable | None |
| Appendix A/B | Illustrative; fine | None |

**Needs separate approval if regenerating Figs 3–4:** enlarge axis/tick fonts; optionally widen to `figure*` — **do not change plotted data**.

---

## 6. Exact source edits

1. `revision_macros.tex` — replace `\ifacl@anonymize` gate with `\ifshowrevnotes` (default off).  
2. `acl_latex.tex` — `\makeatletter` around hypersetup anonymize block.  
3. `acl_latex.tex` — `tab:eval_populations` → `table*` + `tabularx`.  
4. `acl_latex.tex` — `tab:faithfulness` → `table*`.  
5. `acl_latex.tex` — `tab:gold_span` → `table*`.  
6. `acl_latex.tex` — `tab:shap_human` tighter `\tabcolsep` / column types.  
7. Comment updates for M4E-5c packaging note.

`custom.bib` / `acl.sty` unchanged (already correct).

---

## 7. Items requiring author approval

1. Confirm Overleaf recompile of synced sources (must clear aux/bbl).  
2. Accept `table*` placement of Tables 1/3/4 (pagination shift; local PDF now **19** pages).  
3. Optional: regenerate Figs 3–4 for larger labels (`figure*` candidate).  
4. Open scientific `\revnote`s remain in source (T08/T09/T17/T18/T21/T24/T29, etc.) — still pending content modules; only **visibility** fixed.  
5. Do **not** start eight-page restructuring in this module.

---

## 8. Remaining page-budget issues

| Metric | Baseline | After M4E-5c (local) |
|--------|----------|----------------------|
| Total PDF pages | 18 | 19 |
| Main content end | ~p14 | ~p14 |
| ARR limit | ≤8 content pages | **Still far over** — out of scope for M4E-5c |

Technical fixes can add a page (`table*` + float redistribution) even while removing TODO boxes. Compression / appendix moves are **not** part of this module.

---

## 9. Verification against newly compiled PDF

Local artifact: `docs/revisedPaper_M4E5c_local.pdf` (tectonic 0.15.0).

| Check | Result |
|-------|--------|
| Yellow TODOs | **Absent** |
| Related Work `???` cites | **Resolved** |
| Six new bib entries in References | **Present** |
| Table 1 overflow | **Fixed** (`table*`) |
| Tables 3–4 collision | **Fixed** (stacked `table*`) |
| Numerical values in tables | **Unchanged** |
| Author Overleaf PDF re-check | **Pending** author sync/compile |

Page crops: `docs/m4e5c_pdf_pages/` (baseline) and `docs/m4e5c_pdf_pages/fixed/` (post-fix).

---

## Stop

**M4E-5c complete.** Awaiting author Overleaf recompile confirmation and approval before any page-limit restructuring or figure regeneration.
