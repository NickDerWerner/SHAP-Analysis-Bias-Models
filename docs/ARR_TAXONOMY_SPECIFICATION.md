# ARR Taxonomy Specification (M1)

**Version:** v2 (Other/Unassigned)  
**Code:** `scripts/arr_m1/taxonomy.py`  
**Audit outputs:** `outputs/arr_m1/taxonomy/`  
**Status:** Spec frozen for M1; manual labels in `manual_validation_sample.csv` are blank pending human review.

---

## 1. Purpose

Define an auditable, reproducible assignment of words to linguistic categories for SHAP attribution analysis, replacing the legacy residual catch-all that mapped every unmatched word to Emotional/Evaluative.

---

## 2. Categories (v2)

| Category | Short | Definition |
|----------|-------|------------|
| Explicit Bias Terms | Explicit | Identity-/prejudice-denoting lexical items from a closed substring list |
| Framing/Reporting Verbs | Fr/Rep | Closed set of reporting/framing lemmas (exact match after normalize) |
| Function/Temporal Words | Fu/Temp | Closed function-word and temporal-word lists (exact match) |
| Emotional/Evaluative | Em/Eval | Closed evaluative lexicon (substring) **or** `*less` / `*ful` with length > 4 |
| Other/Unassigned | Other | Residual after all rules — content words, names, topical nouns, etc. |

Legacy v1 used the same first four rules but returned Emotional/Evaluative for the residual.

---

## 3. Normalization

```
normalize(w) = lower(strip punctuation set . , ! ? ; : " ' ( ) [ ] { })
```

Identical to `babe_fig6_confound.normalize_word` / taxonomy `normalize_word`.

---

## 4. Precedence (first match wins)

1. Explicit Bias Terms — `any(term in word for term in EXPLICIT_BIAS_TERMS)`  
2. Framing/Reporting Verbs — `word in FRAMING_VERBS`  
3. Function/Temporal Words — `word in FUNCTION_WORDS or TEMPORAL_WORDS`  
4. Emotional/Evaluative — substring in `EMOTIONAL_EVALUATIVE_TERMS`  
5. Emotional/Evaluative — suffix `-less` or `-ful` with `len > 4`  
6. **Other/Unassigned** — otherwise  

Full lists: `scripts/arr_m1/taxonomy.py`.

---

## 5. Examples

| Category | Examples |
|----------|----------|
| Explicit | racist, xenophobic, stereotype |
| Fr/Rep | claimed, alleged, said |
| Fu/Temp | the, and, yesterday, years |
| Em/Eval | fierce, misleading, heartless, wonderful |
| Other | Obama, policy, Cuba, economy, Democrats |

---

## 6. What this taxonomy is / is not

**Is:** A transparent, lexicon-based coding scheme for reproducing paper tables and diagnosing catch-all inflation.

**Is not:** A validated linguistic ontology of media bias; not context-sensitive; not equivalent to human span labels (see BASIL lex/inf). Substring matching for Explicit/EmEval can over-fire (e.g., nested stems).

---

## 7. Manual validation protocol

File: `outputs/arr_m1/taxonomy/manual_validation_sample.csv` (86 rows; seed=7).

- Stratified by v2 category (up to 20/bucket; Explicit has only 6 types available in pool).
- Columns: `category_v2`, `rule`, `category_legacy`, blank `manual_category`.
- Annotators should assign one of the five v2 labels (or Ambiguous) **without** treating model SHAP as ground truth.
- Target: Cohen’s κ on double-annotated subset before updating paper percentages.

Until manual review is complete, treat v2 percentages as **algorithmic**, not human-validated.

---

## 8. Reproduction

```bash
python3 scripts/arr_m1/run_taxonomy_audit.py
python3 -m unittest tests.test_word_aggregation.TestTaxonomyOther
```
