# ARR M4B-3 — Independent Human Annotation and SHAP–Human Alignment Results

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** Results only — new subsection + one SHAP–human table after gold-span Results.  
**Status:** Complete (author review). No new experiments; annotations untouched.

---

## Annotation files used (authoritative)

| Annotator | Path | SHA-256 (from `m3r_executive_numbers.json`) |
|-----------|------|-----------------------------------------------|
| AnnA | `outputs/arr_m2d/human_raw/basil_blind_annotations_annA.json` | `0e96e535…` |
| AnnB (post-M3R) | `outputs/arr_m2d/human_raw/basil_blind_annotations_annB.json` | `5d845836…` |

**Not used:** `outputs/arr_m3_archive_pre_m3r/` (pre-M3R snapshot).

Final aggregates: `outputs/arr_m3r/` (`hh_agreement_summary.json`, `human_vs_basil_summary.json`, `shap_vs_human_summary.csv`, `m3r_executive_numbers.json`, `annB_yes_without_spans_classification.csv`, `annotation_integrity.json`).

---

## What changed

| Item | Detail |
|------|--------|
| New subsection | `\subsection{Independent Human Annotations and SHAP--Human Alignment}` `\label{sec:human_results}` |
| New table | `Table~\ref{tab:shap_human}` — excess \|SHAP\| vs human spans by annotator×model |
| Insertion | After `\label{tab:gold_span}`; before `\subsection{SHAP Magnitude Patterns}` |
| T23 Results `\revnote` | Removed (gold + human Results both present) |
| Em/Ev / other Results | Untouched |

---

## Number → source map

### Human–human agreement (`hh_agreement_summary.json` / `m3r_executive_numbers.json`)

| Quantity | n | Value | Notes |
|----------|--:|------:|-------|
| Binary raw agreement | 120 | 0.733 | CI [0.650, 0.808] |
| Binary Cohen's κ | 120 | 0.439 | complete-case |
| Type raw agreement | 119 | 0.437 | one incomplete type pair |
| Type Cohen's κ | 119 | 0.238 | weak |
| Char soft-F1 | 120 | 0.476 [0.395, 0.555] | both-empty ⇒ F1=1 |
| Char IoU (appendix cand.) | 120 | 0.437 [0.357, 0.519] | not in main table |
| Token F1 (appendix cand.) | 120 | 0.472 | not in main table |

Confusion (presence): YY 60, YN 7, NY 25, NN 28.

### Completeness / yes∅spans (`annotation_integrity.json`, classification CSV)

| Annotator | yes | yes+spans | yes∅spans |
|-----------|----:|----------:|----------:|
| AnnA | 67 | 67 | 0 |
| AnnB | 85 | 59 | 26 |

AnnB yes∅spans classes (n=26):

| Class | n | Treatment in paper |
|-------|--:|--------------------|
| informational/both + needs_context (nonlocalizable candidate) | 19 | Keep in presence/type; exclude from span/SHAP |
| informational yes∅spans (context ≠ yes) | 5 | Same |
| lexical yes∅spans (incomplete) | 2 | Same; not all labeled nonlocalizable |

### Human–BASIL (`human_vs_basil_summary.json`)

| Annotator | n | Bin agree | κ_bin | Type agree | κ_type |
|-----------|--:|----------:|------:|-----------:|-------:|
| AnnA | 120 | 0.625 | 0.204 | 0.445 | 0.261 |
| AnnB | 120 | 0.758 | 0.389 | 0.442 | 0.256 |

### SHAP–human (`shap_vs_human_summary.csv`, subset=`annotator_all`, metric=`abs_minus_rand`, type=`ALL_POSITIVE`)

Cache∩sample (`shap_sample_coverage.json`): BD 34 / DR 42 / Deb 12.

| Ann. | Model | Evaluable n | Mean excess | 95% CI |
|------|-------|------------:|------------:|--------|
| A | BD | 26 | +0.117 | [+0.049, +0.185] |
| A | DR | 32 | +0.183 | [+0.119, +0.247] |
| A | Deb | 10 | +0.199 | [+0.120, +0.276] |
| B | BD | 28 | +0.134 | [+0.082, +0.193] |
| B | DR | 34 | +0.182 | [+0.125, +0.244] |
| B | Deb | 7 | +0.169 | [+0.064, +0.288] |

Evaluable n = yes + ≥1 valid local span ∩ cache (yes∅spans excluded).

Paired BD−DR abs excess (appendix candidate): AnnA n=23, −0.044 [−0.092, +0.007]; AnnB n=26, −0.044 [−0.073, −0.014].

---

## Framing enforced

- Three questions kept separate (presence/type IAA; span overlap; SHAP–human excess).  
- Complementary to `\ref{sec:gold_span_results}`, not a fused validation.  
- No “human-grounded proof” / “verified reasoning” language.  
- Deb rows exploratory ($n{\leq}10$).  
- Empty spans ≠ zero SHAP–human alignment.

---

## Appendix candidates (not edited now)

1. Full HH confusion matrices.  
2. Needs-context / uncertainty κ (n=27; underpowered).  
3. Char IoU / token F1 CIs.  
4. Lexical vs informational span F1 when both agree on type.  
5. Human–BASIL dual-disagreement ID list (`both_humans_disagree_basil.csv`).  
6. Paired BD−DR SHAP–human diffs.  
7. `both_humans_agree` SHAP subset (smaller n).  
8. Clarification-pack resolution counts (32 resolved / 23 persisted).  
9. Item-level AnnB change diagnostics.

---

## TODOs

| ID | Action |
|----|--------|
| T23 Results (human) | **Resolved** |
| T23 overall Results | **Resolved** (gold M4B-2 + human M4B-3) |
| Limitations / Ethics | **Open** — yes∅spans, cache∩sample, weak type IAA, human-study checklist |
| T22 Em/Ev | **Open** |

---

## Compilation

**UNVERIFIED** — no TeX engine on PATH.
