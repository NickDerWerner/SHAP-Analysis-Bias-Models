# ARR M3 — Annotator B Completeness Audit

**Date:** 2026-11-10  
**Source (immutable):** `outputs/arr_m2d/human_raw/basil_blind_annotations_annB.json`  
**SHA-256:** recorded in `outputs/arr_m3/annB_clarification_items.json` → `source_sha256`  
**Original file modified?** **No**

Clarification pack (versioned):  
- `outputs/arr_m3/annB_clarification_items.json` (= `annB_clarification_items_v1.json`)  
- `outputs/arr_m3/annB_clarification_items.csv` (= `annB_clarification_items_v1.csv`)  
- Merge rules stub: `outputs/arr_m3/annB_clarification_merge_procedure.json`

---

## 1. Missing bias-presence labels (Annotator B)

**Definition:** `bias_present` is an empty string after strip (key present; value `""`). Not JSON `null`.

| Statistic | Value |
|-----------|------:|
| Count | **24** / 120 |
| IDs | H013, H026, H029, H034, H036, H042, H045, H049, H051, H059, H064, H068, H069, H070, H072, H076, H079, H080, H086, H100, H102, H104, H106, H113 |

**Co-occurring fields (pattern):**

| Field | Pattern on these 24 |
|-------|---------------------|
| `bias_type` | empty (23); `none` (1) |
| `spans` | empty (all) |
| `needs_context` | **yes** (23); empty (1) |
| `uncertainty` | high 9 / med 7 / low 4 / empty 4 |

**Interpretation:** Not a schema/null export bug. The UI initializes `bias_present: ''` and only requires annotator ID on export (`annotate.html`). These look like **incomplete responses**: context/uncertainty often filled, presence/type left blank—consistent with “need article context / unsure” without committing yes/no.

---

## 2. Biased (`yes`) but no evidence spans

**Definition:** `bias_present` ∈ {yes} and `spans` is `[]`.

| Statistic | Value |
|-----------|------:|
| Count | **31** / 120 |
| IDs | H004, H007, H010, H020, H030, H032, H054, H055, H062, H063, H066, H071, H075, H077, H089, H090, H096, H097, H101, H103, H105, H107, H108, H109, H112, H114, H115, H116, H117, H118, H119 |

**Co-occurring fields:**

| Field | Pattern |
|-------|---------|
| `bias_type` | informational **24**; both 4; lexical 3 |
| `needs_context` | **yes 24**; empty 4; no 2; unsure 1 |
| `uncertainty` | mostly empty (29) |

**Interpretation:** Dominated by **informational + needs_context=yes** with no sentence-local span. Likely intentional “bias present but not locally spannable” or skipped span capture—not a UTF-16/offset failure (no claimed span text to validate).

---

## 3. Overlap of the two sets

| Set | n |
|-----|--:|
| Missing presence | 24 |
| Yes without spans | 31 |
| **Intersection** | **0** |
| Union (clarification items) | **55** |

The two incompleteness modes are **disjoint**.

---

## 4. Cause assessment (form / null / skip / incomplete)

| Hypothesis | Supported? | Evidence |
|------------|------------|----------|
| Missing JSON keys / null fields | **No** | All 120 rows have `bias_present` as `str`; empties are `""` |
| Export schema drop | **No** | Same schema as annA; annA has 0 empty presence |
| UI required-field enforcement | **No** | Only annotator ID required before export; selects default to `""` |
| Deliberate skip / incomplete | **Yes (primary)** | Missing-presence cluster: context/uncertainty filled, presence empty |
| Informational/context without local span | **Yes (primary for yes∅spans)** | 24/31 informational + needs_context=yes |
| Technical span offset bugs | **No** | No spans recorded to mismatch |

---

## 5. Guide requirements (spans, uncertainty, context)

Sources: `human_annotation/guide.md`, `docs/ARR_M2C_HUMAN_ANNOTATION_GUIDE.md`.

| Guide rule | Stated? | Implication for these items |
|------------|---------|------------------------------|
| Bias present yes/no required | Yes (task list) | Empty presence = incomplete vs guide |
| Evidence spans “that justify the judgment (empty if none)” | Yes | “Empty if none” is explicit for **no** bias; for **yes**, spans are the justification—yes+empty is incomplete relative to intent |
| If present = no → spans empty, type none | Yes | N/A for yes∅spans set |
| Needs article context yes/no/unsure | Yes | Supported; used heavily by B |
| Uncertainty low/med/high | Yes | Supported; used on missing-presence set |
| “Cannot decide without article → needs context=yes; still give best sentence-local type” | Yes | Encourages a type even when context needed—does **not** authorize blank presence or yes without any local evidence note |

**Gap:** Guide does not explicitly offer “yes, but no identifiable sentence-local evidence” as a first-class option. Clarification form adds that option neutrally.

---

## 6–9. Clarification artifact (blinded)

`annB_clarification_items_v1` contains **55** items. Each includes only:

- `sentence_text`
- original annB response (presence, type, spans, context, uncertainty, comments)
- `issue_flags` and neutral clarification questions
- blank `clarification_responses` (not filled)

**Excluded:** Annotator A, BASIL `GOLD_*`, SHAP, model predictions, disagreement flags.

**Allowed answers:** `cannot_determine`, `no_identifiable_sentence_local_evidence`, and for span issues `change_bias_present_to_no` / `needs_article_context_only`—without pre-selecting any.

No judgments were changed or inferred.

---

## 10. Merge procedure (do not overwrite originals)

### Principles

1. **Never** modify `basil_blind_annotations_annB.json`.  
2. Store returned clarifications as a **new** file, e.g.  
   `outputs/arr_m3/annB_clarification_responses_v1.json`  
   keyed by `clarification_id` / `item_id`.  
3. Build a **derived** analysis file, e.g.  
   `outputs/arr_m3/annB_merged_for_analysis_v1.json`  
   = original record + optional `clarified_*` overlay fields + `clarification_version`.  
4. Keep provenance: `source_sha256`, clarification file hash, merge timestamp.

### Overlay rules (when responses arrive)

| Original issue | Merge rule |
|----------------|------------|
| Missing presence | If clarify_bias_present ∈ {yes,no}, set `clarified_bias_present`; if `cannot_determine`, leave primary empty and flag `still_indeterminate` |
| Yes without spans | If `will_add_sentence_local_spans` + valid offsets, set `clarified_spans`; if `no_identifiable_sentence_local_evidence`, keep present=yes, spans empty, flag `no_local_evidence`; if `change_bias_present_to_no`, set clarified present=no; never silently invent spans |
| Type/context | Only overwrite via `clarified_*` when annotator provides a non-`keep_original` value |

### Pre- vs post-clarification reporting

Report **both**:

1. **Pre-clarification (current M3):** complete-case κ; exclude empty presence; exclude yes∅spans from span/SHAP analyses (as already done).  
2. **Post-clarification:** same metrics on merged derived file; add sensitivity table:  
   - complete-case only  
   - `cannot_determine` excluded vs coded as disagreement  
   - yes+`no_local_evidence` included in presence κ but excluded from span F1  

Do **not** replace pre-clarification numbers; show them side-by-side.

---

## Stop

Clarification items identified (**55**). No simulated completions. Await annB clarification responses before re-running agreement.
