# ARR Revision — Agent Handoff Context

**Purpose:** Continue this project on another machine/Cursor window without re-deriving history.  
**Last updated:** 2026-11-12  
**Branch (home machine):** `research/arr-revision` (tracks `origin/research/arr-revision`)  
**Repo:** SHAP-Analysis-Bias-Models (ARR May 2026 revision of news-bias SHAP paper)

---

## 1. One-paragraph status

M0–M2D analyses are done. M3 human validation was run on real annA/annB exports (120 items each). Raw JSON must **never** be modified. AnnB has 55 incomplete items (24 empty `bias_present`, 31 `yes` with no spans; **disjoint**). A blinded clarification pack exists; **clarification responses not yet collected**. Manuscript rewrite has **not** started. Frozen verdict: **CONDITIONAL GO** to rewrite after (or in parallel with careful disclosure of) AnnB clarification. Core scientific frame: **faithfulness ≠ human-evidence plausibility**; retract Em/Ev 90–96%; BASIL lex/inf + coverage-matched caveats.

---

## 2. Do / don’t (hard rules)

| Do | Don’t |
|----|-------|
| Preserve all caches, M1–M3 outputs, human raw JSON | Regenerate SHAP / retrain models |
| Treat annA/annB as immutable | Simulate, adjudicate, or LLM-fill missing labels |
| Merge clarifications into **derived** files only | Overwrite `basil_blind_annotations_annB.json` |
| Scope claims via claim ledger | Restore Emotional/Evaluative dominance claims |
| Paired comparisons only for cross-model effects | Infer architecture effects from unpaired caches |

---

## 3. Milestone map (completed)

| Milestone | What | Key docs / outputs |
|-----------|------|-------------------|
| M0 | Audit, plan, hardware, repro gaps | `docs/ARR_CODEBASE_AUDIT.md`, `ARR_EXPERIMENT_PLAN.md`, … |
| M1 | Taxonomy Other, pairing, DeBERTa integrity, BASIL spans @`4fdbc4f` | `docs/ARR_M1_VALIDATION_REPORT.md`, `outputs/arr_m1/` |
| M2A | Faithfulness pilot | `docs/ARR_M2_FAITHFULNESS_PILOT.md`, `outputs/arr_m2/` |
| M2B | Offset repair + 200-sentence faithfulness (BD, DR) | `docs/ARR_M2B_FAITHFULNESS_REPORT.md`, `outputs/arr_m2b/` |
| M2C | Gold-span plausibility vs BASIL | `docs/ARR_M2C_GOLD_SPAN_REPORT.md`, `outputs/arr_m2c/` |
| M2D | Robustness (coverage confound), qualitative, human prep | `docs/ARR_M2D_*.md`, `outputs/arr_m2d/` |
| M3 | Human validation + readiness audit + AnnB completeness | `docs/ARR_M3_*.md`, `outputs/arr_m3/` |

---

## 4. Critical findings (do not re-argue unless new data)

1. **Faithfulness (M2B):** High-+ / high-|SHAP| masks change P(biased) more than random/low-|SHAP| (BD, DR; TP/FP). Prefer wording *attribution-guided sensitivity*. TN n=3 → no TN claim.  
2. **Plausibility (M2C):** Lexical gold spans beat length-matched random; informational raw mass is high mainly because spans cover ~70% of the sentence.  
3. **Robustness (M2D):** Lex−inf gap **vanishes** under coverage matching for BD/DR. Unqualified “lex ≫ inf” is overstated.  
4. **Paired models:** DR > BD on paired |SHAP|–lexical excess (n=255).  
5. **Taxonomy (M1):** Em/Ev 90–96% was catch-all → ~94% Other at p75. Retract.  
6. **Humans (M3):** HH κ_present≈0.35, κ_type≈0.14; SHAP still beats random vs each annotator’s spans on **cache∩sample** (BD34/DR42/Deb12 of 120). AnnB incompleteness audited.  
7. **Rewrite verdict:** **CONDITIONAL GO** (`docs/ARR_M3_REWRITE_BLUEPRINT.md`).

---

## 5. Important paths

### Human annotations (immutable)
```
outputs/arr_m2d/human_raw/basil_blind_annotations_annA.json
outputs/arr_m2d/human_raw/basil_blind_annotations_annB.json
```

### AnnB clarification (awaiting responses)
```
docs/ARR_M3_ANNOTATION_COMPLETENESS_AUDIT.md
outputs/arr_m3/annB_clarification_items.json          # + _v1 twin
outputs/arr_m3/annB_clarification_items.csv
outputs/arr_m3/annB_clarification_merge_procedure.json
```
Expected next: `outputs/arr_m3/annB_clarification_responses_v1.json` → derived `annB_merged_for_analysis_v1.json` (do not overwrite raw).

### Website pack (annotator-facing only)
```
human_annotation/   # guide, onboarding, annotate.html, items.json/csv
```

### SHAP caches (do not regenerate)
```
outputs/basil_shap/samples_biasdetector.jsonl
outputs/basil_shap/samples_daroberta.jsonl
outputs/basil_shap/samples_deberta.jsonl
```

### Paper / reviews
```
docs/references/paper.tex
docs/references/ARR_Reviews.txt
```

### Env
```
.venv/
requirements-arr-m2.txt   # note: shap may be absent; analyses use caches
Seed for sampling/bootstrap/baselines: 7
```

### Analysis entrypoints
```
scripts/arr_m2b/faithfulness_eval.py
scripts/arr_m2c/run_gold_span_alignment.py
scripts/arr_m2d/run_m2d.py
scripts/arr_m2d/human_agreement.py
scripts/arr_m3/run_human_validation.py
```

---

## 6. What is next (priority order)

1. **Collect AnnB clarifications** for the 55 items (blind pack already built).  
2. **Merge** via procedure in completeness audit → re-run M3 agreement **pre vs post** side-by-side.  
3. **Manuscript rewrite** per `ARR_M3_CLAIM_LEDGER.md` + `ARR_M3_REWRITE_BLUEPRINT.md` + `ARR_M3_REVIEWER_RESPONSE_MATRIX.md`.  
4. Fill repro gaps for submission: SHAP background set text, `shap` pin, model revision hashes (see `ARR_M3_REPRODUCIBILITY_CHECK.md`).  
5. **Deferred / not now:** semantic paraphrasing, full SHAP regen, decoder LLM experiments, inventing human labels.

---

## 7. Sync checklist (workplace MacBook)

1. `git fetch && git checkout research/arr-revision && git pull`  
2. Confirm large artifacts present (SHAP JSONL, `outputs/arr_m*`, human_raw). If OneDrive/Git LFS: wait for sync.  
3. Recreate venv if needed: `python3 -m venv .venv && .venv/bin/pip install -r requirements-arr-m2.txt`  
4. Open this file + paste the prompt in §8 into a new Cursor Agent chat.  
5. Do **not** assume home-machine absolute paths (`/Users/rick/...`); use repo-relative paths.

---

## 8. Cursor takeover prompt (copy-paste)

```text
You are continuing the ARR revision project for SHAP-Analysis-Bias-Models.

Read first (in order):
1. docs/ARR_HANDOFF_CONTEXT.md
2. docs/ARR_M3_REWRITE_BLUEPRINT.md
3. docs/ARR_M3_CLAIM_LEDGER.md
4. docs/ARR_M3_ANNOTATION_COMPLETENESS_AUDIT.md
5. docs/ARR_M3_HUMAN_VALIDATION_REPORT.md

Hard rules:
- Never modify outputs/arr_m2d/human_raw/*.json
- Never regenerate SHAP or retrain models
- Never simulate / LLM-fill human annotations
- Never restore Emotional/Evaluative 90–96% claims
- Prefer paired comparisons; disclose small strata
- Merge AnnB clarifications only into derived versioned files

Current state:
- M0–M2D done; M3 human validation done with CONDITIONAL GO for rewrite
- AnnB needs clarification on 55 items (pack in outputs/arr_m3/annB_clarification_items.*)
- Clarification responses not yet in repo
- Manuscript not rewritten yet

Ask me what to do next if unclear. Likely next tasks:
(A) help process AnnB clarification responses when I provide them,
(B) start manuscript rewrite from the claim ledger / blueprint,
(C) something else I specify.

Confirm you read the handoff and summarize in ≤5 bullets before acting.
```

---

## 9. Quick command crib

```bash
# Human validation (already run; re-run only after merge)
.venv/bin/python scripts/arr_m3/run_human_validation.py

# Agreement helper (paths as args)
.venv/bin/python scripts/arr_m2d/human_agreement.py \
  --annotator-a outputs/arr_m2d/human_raw/basil_blind_annotations_annA.json \
  --annotator-b outputs/arr_m2d/human_raw/basil_blind_annotations_annB.json \
  --id-a annA --id-b annB
```

---

*End of handoff. Update this file when AnnB clarifications are merged or rewrite begins.*
