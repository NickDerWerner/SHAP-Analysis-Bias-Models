# M4A-2 Change Record — Word-Level Attribution Aggregation

**Date:** 2026-11-13  
**File:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** `\subsection{Word-Level Attribution Aggregation}` only (incl. figure caption inside it)  
**TODO:** T11 — resolved for auditable reporting/DeBERTa/M2B distinction; phrase-level deferred  

---

## Original (abbrev.)

- Claimed aggregation from “model-specific tokenizer and SHAP **TextExplainer**.”  
- Implied normalization “prevent[s] spurious attributions” and “retain[s] faithfulness.”  
- Sum “preserving the additive property” without distinguishing paths.  
- No DeBERTa repair disclosure; no M2B offset pipeline distinction.  
- Yellow `\revnote{TODO P0 | Word attribution mapping}{...}`.

---

## Revised scientific content

| Statement in new prose | Evidence |
|------------------------|----------|
| Explanation units from Text masker; not assumed identical to all classifier internals | M4A-1; `shap.maskers.Text`; shap token formats in `basil_shap_generate.py` docstring |
| RoBERTa-family grouping: whitespace / Ġ/▁ + heuristics; skip specials; **sum** mapped units | `aggregate_subword_shap_to_words` in `basil_shap_generate.py` L86–191 |
| Sum conserves mapped-unit mass only; heuristics not error-free | Same; no claim of perfect alignment |
| DeBERTa pre-fix marker bug; char-span repair; `.bak`; in-place cache rewrite | `scripts/fix_deberta_word_aggregation.py` |
| Current Deb caches ≡ charspan fix; alnum align OK | `ARR_M1_VALIDATION_REPORT.md` Task C; `run_deberta_integrity.py` |
| Charspan excludes whitespace-character mass from word totals; additive derived files for strict Σ | `scripts/arr_m1/word_aggregation.py`; M1 report |
| Magnitude lineage = repaired caches, not `.bak` | M1 reliability verdict |
| Perturbation masking uses separate offset-aware alignment | `scripts/arr_m2/offset_alignment.py`; `ARR_M2B_FAITHFULNESS_REPORT.md` |
| No phrase-level atomic units | Explicit limitation; matches reviewer concern |

**Not claimed:** perfect conservation under charspan; semantic cross-tokenizer equivalence; that reporting aggregation alone yields mask spans.

---

## Appendix vs main text

| Detail | Where |
|--------|-------|
| Heuristic split rules (camelCase, endings, etc.) | Existing appendix “Word-Level Attribution Aggregation in Detail” (not edited in M4A-2) + code |
| Full DeBERTa debugging narrative | Main text: short correction paragraph only |
| Additive JSONL paths | Code/`outputs/arr_m1/deberta_integrity/` — cite in repro later if needed |

**Recommended later (not this module):** refresh appendix so it matches Explainer+Text terminology and mentions DeBERTa repair + offset alignment (requires separate approval to edit appendix).

---

## Compatibility with M4A-1

Uses `\texttt{shap.Explainer}` / Text masker; no test-set background; no “TextExplainer.”

---

## Diff scope

- `acl_latex.tex`: this subsection + caption only.  
- Docs: `ARR_M4_REVISION_STATE.md`, `ARR_M4_TODO_AUDIT.md`, this file.
