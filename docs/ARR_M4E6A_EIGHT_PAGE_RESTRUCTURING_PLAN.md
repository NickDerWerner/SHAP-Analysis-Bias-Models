# ARR M4E-6a — Eight-Page Main-Paper Restructuring Plan

**Date:** 2026-11-16  
**Status:** **AUDIT / PROPOSAL ONLY** — no LaTeX, figure, bib, or experiment edits.  
**PDF audited:** `docs/revisedPaper_M4E5c_local.pdf` (tectonic; post–M4E-5c)  
**Source (read-only):** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Policy:** [ARR CFP](https://aclrollingreview.org/cfp) — long papers ≤ **8 content pages**; unlimited space **after Conclusion** for required **Limitations** and optional **Ethical Considerations**; unlimited **References**; **Appendices** after references, uncapped, but reviewers need not read them. Main-text floats must fit inside the 8 content pages.

---

## 1. Current rendered page breakdown

| PDF pages | Role | Counts toward 8? |
|----------:|------|------------------|
| **1–12** | Abstract → Intro → Related Work → Methods → Results → start of Discussion | **Yes** |
| **13** (through Conclusion) | Conclusion | **Yes** |
| **13** (from Limitations) | Limitations | **No** (post-Conclusion) |
| **14** | Ethical Considerations | **No** |
| **15–~16 mid** | References | **No** |
| **~16 mid–19** | Appendices A–E | **No** |

**Totals**

| Quantity | Value |
|----------|------:|
| Total PDF pages | **19** |
| Approximate **main-content** pages (Abstract→Conclusion) | **≈ 12.6** (pp. 1–12 full + Conclusion portion of p13) |
| Non-content (Lim/Ethics/Refs/App) | **≈ 6.4** |
| ARR long-paper allowance | **8** content pages |
| **Required reduction** | **≈ 4.5–5.0 content pages** (conservative; exact only after recompile) |
| Eight-page limit currently satisfied? | **No** |

**Float-heavy content pages (drive over-budget):**  
p2 Fig 1; p4 Fig 2; p6 Table 1 (`table*`); p8 Table 2; p10 Tables 3–5 + Fig 3; p11 Fig 4 + Table 6; p12 Table 7 + Fig 5.

Do **not** treat 19 total pages as 19 content pages.

---

## 2. Section-level word and space estimates

Word counts are approximate prose tokens from TeX with macros/`\revnote` stripped (not rendered lines). Space is from the M4E-5c PDF.

| Section | ≈ words | ≈ PDF locus | Importance | Class (proposed) |
|---------|--------:|-------------|------------|------------------|
| Abstract | ~190 | p1 | Essential | **COMPRESS** lightly |
| §1 Introduction (+ Fig 1) | ~520 + fig | p1–2 | Essential framing + RQs | **COMPRESS** |
| §2 Related Work (2.1–2.4) | ~470 | p2–3 | Needed positioning | **COMPRESS** |
| §3.1 Dataset & Models | ~510 | p3–4 | Essential | **COMPRESS** |
| §3.2 SHAP framework | ~135 | p4 | Essential | **KEEP** (short already) |
| §3.3 Word aggregation (+ Fig 2) | ~365 + fig | p4–5 | Needed at high level | **COMPRESS** / detail **MOVE** |
| §3.4 Sampling (+ Table 1*) | ~330 + float | p5–6 | Essential distinctions | **COMPRESS**; Table 1 keep or compact |
| §3.5 Analysis Framework | ~290 | p5–6 | Overlaps Results caveats | **COMPRESS** heavily |
| §3.6 Faithfulness protocol | ~325 | p6–7 | RQ1 Methods | **COMPRESS** |
| §3.7 Gold-span protocol | ~305 | p6–7 | RQ2 Methods | **COMPRESS** |
| §3.8 Human protocol | ~250 | p7 | RQ3 Methods | **COMPRESS** |
| §3.9 Stats methods | ~175 | p7 | Secondary | **MOVE** |
| §3.10 Evaluation Metrics | ~150 | p7–8 | Partial overlap w/ 4.1 | **COMPRESS** / merge |
| §4.1 Overall performance (+ T2) | ~330 + tab | p8 | Context for caches | **KEEP** (trim prose) |
| §4.2 Perturbation (RQ1, T3*) | ~510 + tab | p8–10 | **Core** | **KEEP** |
| §4.3 Gold-span (RQ2, T4*) | ~480 + tab | p9–10 | **Core** | **KEEP** |
| §4.4 Human (RQ3, T5) | ~455 + tab | p9–10 | **Core** | **KEEP** |
| §4.5 Magnitude (+ F3–4, T6) | ~515 + 2 figs + tab | p10–11 | Supporting | **MOVE** (keep 2–3 sentences in main) |
| §4.6 Paired similarity (RQ4, T7) | ~410 + tab | p11–12 | Supporting contribution | **COMPRESS** (do not delete) |
| §4.7 Word surfaces (+ F5) | ~85 + fig | p12 | Descriptive | **MOVE** |
| §4.8 Matched-pool vocab note | ~65 | p12 | Caveat / legacy | **MOVE** |
| §4.9 Statistical significance | ~380 | p12 | Catalogue; duplicates | **MOVE** (fold key tests into 4.2–4.4) |
| §5 Discussion | ~470 | p12–13 | Interpretation | **COMPRESS** (cut number repeats) |
| §6 Conclusion | ~235 | p13 | Essential short close | **COMPRESS** lightly |
| Limitations | ~400 | p13–14 | Required; uncapped | **KEEP** (no new results) |
| Ethical Considerations | ~275 | p14 | Optional; uncapped | **KEEP** (T29 still open) |
| References | — | p15–16 | Uncapped | — |
| App A–E (existing) | ~1.5k + floats | p16–19 | Supplementary | **KEEP**; extend for moved material |

**Main-prose mass (Abstract→Conclusion, excl. Lim/Ethics):** order **~7.5–8.0k words** plus large floats → ~12.6 content pages.

---

## 3. Main-paper content hierarchy

**Must remain in the 8-page body (protected)**

1. **RQ1** — Attribution-guided masking: protocol gist + primary ΔP / CIs / *n* / controls (Table 3 or equivalent).  
2. **RQ2** — BASIL gold-span excess + coverage-matched caveat + key *n*/CIs (Table 4).  
3. **RQ3** — Human κ + SHAP–human excess on cache∩sample (Table 5) + yes∅span caveat.  
4. **RQ4 (supporting)** — Short paired Jaccard/cosine statement + compact Table 7 or one inline median row; not a full section.  
5. Minimal **task/model/SHAP/sampling** definitions so Results are interpretable without mandatory appendix reading.  
6. **Limitations** (post-Conclusion) with sampling, SHAP, TN=*n*3, Deb scope, overlap UNVERIFIED, human-study bounds.

**May leave the 8-page body (appendix / heavy compress)**

- Magnitude boxplots & median table (4.5).  
- Top-word figure & matched-pool vocab note (4.7–4.8).  
- Standalone stats catalogue (3.9 / 4.9).  
- Aggregation algorithm detail / Fig 2 if one sentence + appendix pointer remains.  
- Long Analysis Framework / metrics duplication.  
- Extended RW decoder-LLM survey detail (keep 1–2 cites + scope sentence).

---

## 4. Keep / Compress / Move / Remove matrix

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Abstract | COMPRESS | Drop repeated numbers already in Results/Conclusion |
| Intro RQs + contributions | COMPRESS | Keep 4 RQs; shorten anecdotes/contrib list |
| Fig 1 | KEEP | Motivates pairing; small |
| Related Work | COMPRESS | Merge 2.1–2.4 into ~0.5–0.75 page |
| §3.1 Datasets/Models | COMPRESS | Keep IDs, BABE/BASIL roles, Deb unevenness |
| §3.2 SHAP config | KEEP | Short; reproducibility critical |
| §3.3 Aggregation + Fig 2 | COMPRESS / MOVE detail | One rule sentence in main; App E already exists |
| Table 1 eval populations | KEEP (prefer) / COMPRESS design | High clarity; consider single-column compact or non-`table*` to cut float waste |
| §3.5 Analysis Framework | COMPRESS | Duplicate caveats → Limitations |
| §3.6–3.8 protocols | COMPRESS | Keep populations, metrics, controls; move procedural minutiae |
| §3.9 Stats methods | MOVE | Appendix “Inference” |
| §3.10 Metrics | COMPRESS | Merge into §3.1/4.1 |
| §4.1 + Table 2 | KEEP | Threshold/AUPRC context |
| §4.2–4.4 + Tables 3–5 | KEEP | Core RQs |
| §4.5 + Figs 3–4 + Table 6 | MOVE | Supporting; 2–3 sentence pointer |
| §4.6 + Table 7 | COMPRESS | Retain RQ4; ~⅓ length |
| §4.7 + Fig 5 | MOVE | Descriptive |
| §4.8 | MOVE | Legacy taxonomy sensitivity |
| §4.9 | MOVE | Integrate 2–3 key *p*/tests into 4.2–4.4 |
| Discussion | COMPRESS | One para per RQ; no full number reprise |
| Conclusion | COMPRESS | Findings list once |
| Limitations / Ethics | KEEP | Policy + scientific honesty |
| App A–E | KEEP + extend | Absorb moved Results/Methods |
| Em/Ev / unsupported claims | REMOVE only if any residual | Already cleaned; do not cut real findings |

**No REMOVE of legitimate RQ1–4 findings merely for space.**

---

## 5. Table and figure disposition

| Float | RQ link | Main 8-page? | Note |
|-------|---------|--------------|------|
| Fig 1 shared FP | Motivation | **Keep** | Column fig |
| Fig 2 pipeline | Methods | **Move or drop** | App E covers aggregation |
| Table 1 populations | All | **Keep** (compact) | `table*` costs ~⅓–½ page; prefer tighter single-column or shorter caption |
| Table 2 performance | Context | **Keep** | |
| Table 3 faithfulness | RQ1 | **Keep** | Prefer non-`table*` if fits; else keep `table*` |
| Table 4 gold-span | RQ2 | **Keep** | Same |
| Table 5 SHAP–human | RQ3 | **Keep** | |
| Figs 3–4 magnitude | Supporting | **Move** | Large space; labels already marginal |
| Table 6 magnitudes | Supporting | **Move** | |
| Table 7 paired sim | RQ4 | **Keep** (compact) | |
| Fig 5 top words | Supporting | **Move** | |
| App tables/figs A–D | Supp | Stay in appendix | Extend rather than duplicate |

**Minimum main-float set for Option B:** Fig 1, Tables 1–5, Table 7 (possibly merged/shrunk). Optional: keep Table 2 as half-width.

---

## 6. Options

### Option A — Conservative restructuring

**Moves:** §4.7–4.8 + Fig 5; §4.9 catalogue; §3.9; Fig 2 detail.  
**Compresses:** RW, Discussion, Methods protocols (~20–30%), §4.5 kept but **without** Figs 3–4 (table or 3 sentences only), §4.6 mildly shortened.  
**Keeps:** Full §4.2–4.4 with tables; most Methods narrative; Table 1 as `table*`.

| Estimate | Value |
|----------|------:|
| Words cut from main | ~1.2–1.8k |
| Floats relocated | Fig 2?, Fig 5, maybe Figs 3–4 |
| Likely content pages after | **≈ 9.5–11** |
| Hits 8 pages? | **Unlikely** without further cuts |
| Scientific risk | Low |
| Reviewer risk | Low–medium (still over → desk-reject risk remains) |

### Option B — Eight-page-oriented restructuring (**recommended**)

**Moves:** §4.5 (figs+table) entirely; §4.7–4.9; §3.9; aggregation minutiae / Fig 2; long Analysis Framework bullets.  
**Compresses:** Intro; RW to ~¾ page; Methods §3.1/3.4–3.8 to protocol digests + Table 1; §4.6 to short RQ4 paragraph + Table 7; Discussion to ≤¾ page; Conclusion ≤½ page.  
**Keeps in main:** RQ1–3 Methods digests + Results + Tables 2–5; compact Table 1; Fig 1; compressed RQ4; Limitations/Ethics unchanged in role.

| Estimate | Value |
|----------|------:|
| Words cut/moved from main | ~2.5–3.5k |
| Floats relocated | Figs 2–5, Table 6 (+ optional slim Table 1) |
| Likely content pages after | **≈ 7.5–8.5** (must verify by compile) |
| Hits 8 pages? | **Plausible**; may need one follow-up trim module |
| Scientific risk | Medium if Methods over-trimmed — mitigate with appendix + explicit pointers |
| Reviewer risk | Medium: appendix-dependent details; mitigated if RQ protocols stay self-contained |

**Recommendation:** **Option B.** Option A does not clear desk-reject page risk. Option B protects RQ1–3 numbers/CIs/*n* and keeps RQ4 as a short supporting result.

---

## 7. Estimated page savings (conservative, pre-recompile)

| Change bundle | ≈ pages saved | Risk |
|---------------|--------------:|------|
| Move §4.5 + Figs 3–4 + Table 6 | 1.0–1.5 | Low |
| Move §4.7–4.9 + Fig 5; fold key tests into 4.2–4.4 | 0.7–1.0 | Low |
| Compress Methods + move §3.9 / Fig 2 detail | 1.0–1.5 | Medium |
| Compress RW + Intro + Discussion/Conclusion redundancy | 0.7–1.0 | Low |
| Retune Table 1/`table*` float pressure | 0.2–0.5 | Low |
| **Option B total (non-additive)** | **≈ 4.0–5.0** | — |

Exact page count **only** after approved edits + recompile. Do not claim fixed savings beforehand.

---

## 8. Scientific risks and reviewer-coverage effects

| Risk | Mitigation |
|------|------------|
| Reviewers skip appendix → miss magnitude/FP>TP story | Keep 2–3 main-text sentences + Limitations pointer |
| Methods too thin → reproducibility complaints (xw7D) | Keep SHAP masker/output, sampling cells, protocol *n*/budgets/controls in main |
| RQ4 looks abandoned | Retain contribution sentence + Table 7 |
| Desk reject for “key claims only in appendix” | Never move primary ΔP / gold excess / human κ out of main |
| Limitations used to stash new results | Forbidden by ARR; only interpret main findings |
| Over-compress Ethics before T29 answers | Keep section; fill T29 later without expanding content pages |

---

## 9. Proposed appendix organization

| Appendix | Content |
|----------|---------|
| **A** (existing) | Vocabulary-pool confound — keep; absorb §4.8 pointer |
| **B** (existing) | Max \|SHAP\| — keep; absorb §4.5 magnitude figs/table |
| **C** (existing) | AUPRC strata — keep |
| **D** (existing) | Token-level examples — keep |
| **E** (existing) | Aggregation detail — keep; absorb Fig 2 / §3.3 detail |
| **F (new)** | Full faithfulness/gold/human protocol expansions (moved Methods minutiae) |
| **G (new)** | Paired-similarity extras + extended stats (from §4.9 / §3.9) |
| **H (new, optional)** | Reproducibility card: seeds, cache paths, Deb scope, unpinned shap note (from M4E-4) |

Avoid duplicating analyses already in A–E; **move** then **point**, do not copy.

---

## 10. Recommended implementation sequence

Small independently reviewable modules (do **not** start until approved):

| Order | Module | Scope | Est. save | Stop |
|------:|--------|-------|-----------|------|
| 1 | **M4E-6b** Supporting-Results relocation | Move §4.5, 4.7–4.9 (+ floats) to App B/A/G; leave 2–3 magnitude sentences + fold key tests into §4.2–4.4; compress §4.6 | ~1.5–2.5 pp | Compile; confirm RQ1–3 tables/numbers untouched |
| 2 | **M4E-6c** Methods digest | Compress §3.1, 3.3–3.8; move §3.9 + aggregation detail; retune Table 1 | ~1.0–1.5 pp | Main still self-contained for RQ protocols |
| 3 | **M4E-6d** Front/back prose | Compress Intro, RW, Discussion, Conclusion (no new claims) | ~0.7–1.0 pp | RQs/contributions still match claim ledger |
| 4 | **M4E-6e** Float pagination pass | `table*` vs column; caption length; verify ≤8 content pages | residual | **pubcheck-style page count**; stop if ≤8 |
| 5 | Later | Ethics T29 answers; optional Fig 3–4 regen in appendix | — | Separate approvals |

Prioritize **6b** first: largest float+prose savings without touching primary RQ tables.

---

## 11. First concrete editing module (needs approval)

### **M4E-6b — Relocate supporting Results (magnitude / surfaces / stats catalogue); compress RQ4**

| Field | Content |
|-------|---------|
| Exact subsections | `\subsection{SHAP Magnitude Patterns}` (§4.5); `\subsection{High-Attribution Word Surfaces}` (§4.7); `\subsection{Matched-Pool Vocabulary Note}` (§4.8); `\subsection{Statistical Significance Testing}` (§4.9 Results); light trim of `\subsection{Paired Cross-Model Attribution Similarity}` (§4.6) |
| Floats | Move `fig:smd_babe`, `fig:smd_basil`, `tab:shap_magnitudes`, `fig:tbi` → Appendix B (and A for vocab note). **Keep** `tab:paired_sim` in main (compressed caption/prose). |
| Retain in main | (i) 2–3 sentences: magnitude is descriptive, not calibration; optional one FP>TP clause + App pointer; (ii) RQ4: Jaccard/cosine medians on shared FP/FN + Table 7; (iii) any *critical* paired tests currently only in §4.9 that underpin §4.2–4.4 claims — fold **into** those subsections, do not drop |
| Move | Full §4.5/4.7/4.8/4.9 bodies; magnitude figures/tables; top-word figure |
| Do **not** touch | Tables 2–5 numerical cells; §4.2–4.4 primary CIs/*n*; Limitations substance; Ethics; bibliography keys |
| Dependencies | Appendix B/A labels; Discussion sentences that re-cite magnitude/word lists must retarget appendix |
| Verification | Diff tables 2–5 vs evidence CSVs; PDF: content-page count estimate; no `???` refs; RQ1–3 prose still has effect sizes |
| Stop | After compile + short verification note; **no** Methods rewrite in the same module |

**Acceptance criteria:** Primary RQ1–3 findings and Tables 3–5 unchanged; RQ4 still present; supporting floats gone from content pages; new appendix pointers valid.

---

## 12. Stop condition (this module)

M4E-6a produces **this plan only**.  
**No** manuscript edits, float moves, or experiments executed here.  
Restructuring is **not** marked completed in revision state.

---

## Report summary (for author)

| Item | Finding |
|------|---------|
| Main-content pages | **≈ 12.6** (of 19 PDF pages) |
| Required reduction | **≈ 4.5–5 content pages** |
| Highest-impact saves | Move magnitude figs/tables; move §4.7–4.9; compress Methods; cut Discussion/RW redundancy; reduce `table*` pressure |
| Core protected | RQ1–3 protocols + Results + Tables 2–5; short RQ4 + Table 7; Limitations |
| Recommended option | **B (eight-page-oriented)** |
| First edit module | **M4E-6b** (supporting Results relocation) — awaiting approval |
