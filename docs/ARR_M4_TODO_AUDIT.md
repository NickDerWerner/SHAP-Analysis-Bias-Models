# ARR M4 — Manuscript TODO Audit

**Date:** 2026-11-16 (M4E-5c visibility note)  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**TODO mechanism:** `\revnote{TITLE}{BODY}` via `revision_macros.tex`  
**M4E-5c:** `\revnote` is **default-off** (`\ifshowrevnotes`; author drafts use `\showrevnotestrue`). Review PDF must not print yellow boxes; **open scientific TODOs remain in source** and are not marked completed by suppression alone.  
**Total TODOs found (initial audit):** **30** `\revnote`s  
**Open `\revnote`s in source:** residual T08/T09/T17/T18/T21/T24/T29 (+ optional notes) — content still pending  
**Rule:** TODOs are proposed tasks, not scientific authority. Cross-checked against claim ledger, M3R, consistency check, ARR reviews, Kasneci notes.

**Classification key:**  
`Valid+pending` · `Needs modification` · `Requires verification` · `Obsolete` · `Out of scope` · `Partially addressed experimentally (text still pending)`

IDs `T01`–`T30` are audit identifiers (not in LaTeX). Line numbers refer to `acl_latex.tex` (may drift after inserts).

---

## Summary counts

| Class | n | IDs |
|-------|--:|-----|
| Valid and pending (edit manuscript) | 1 | T09 (residual revnote) |
| Already resolved (prose + note removed) | 19 | **T01**, **T10**, **T11**, **T07**, **T12**, **T13 methods**, **T14 methods**, **T15**, **T16 methods**, **T19 Results**, **T20**, **T22 Results**, **T23**, **T25 Results**, **T26 Results**, **T27**, **T28 Limitations**, **T02–T04 Intro** |
| Partially resolved (revnote retained) | 3 | **T08**, **T09**; **T17**/T19 optional M2D-band follow-up |
| Needs modification (TODO text outdated vs evidence) | 0 | — |
| Partially addressed experimentally; prose still pending | 2 | T17 optional bands; T25 full threshold re-analysis (out of scope) |
| Requires verification (evidence incomplete / author decision) | 5 | T08, T14, T18, T21, T24 |
| Out of scope for this revision (no new experiments) | 4 | T14 residual (JS/signed/random baselines), T16 ECE/Brier/AUROC, T20 all-3-model full re-sim, phrase-level |
| Obsolete as stated | 1 | T13 “define Em/Ev for main claim” — **Methods replaced by retirement (M4A-8d)**; Results still obsolete until M4B-5 |

**Resolved in TeX:** Methods; Results; Discussion/Limitations; Ethics partial; Introduction (M4D-1); **Abstract + Conclusion (M4D-2)**. Open: title change (author approval); Related Work T05/T06; T29 consent/IRB/licenses; T30 Appendix; optional magnitude bands.

---

## Per-TODO audit

| ID | Loc | Request (abbrev.) | Reviewer / Kasneci link | Still scientifically valid? | Evidence | Disposition |
|----|-----|-------------------|-------------------------|----------------------------|----------|-------------|
| **T01** | Abstract | Shorten; drop mechanism/calibration | AC, MqgQ, k62P | Yes | Claim ledger; M4B; **M4D-2** | **Resolved** (Em/Ev, same-mechanism, calibration, pathways removed) |
| **T02** | Intro figure | Qualify Cold War anecdote | xw7D | Caption qualified in M4D-1 | M4D-1 | **Resolved** |
| **T03** | Intro RQs | Faithfulness ≠ plausibility; span/human/paired | MqgQ, Kasneci | Four RQs match M4B | **M4D-1** | **Resolved** |
| **T04** | Intro contributions | Rewrite; downgrade same-mechanism | AC, xw7D, k62P | Four contributions match claim ledger | **M4D-1** | **Resolved** |
| **T05** | Related Work | Decoder LLM cites; encoder scope | xw7D, AC | Yes | Anthology/Springer verified; **M4E-3** | **Resolved** |
| **T06** | Related Work / Positioning | Faithfulness literature; no “first” claims | AC, Kasneci | Yes | Jacovi & Goldberg + Atanasova + EvalxNLP; **M4E-3** | **Resolved** |
| **T07** | Dataset/Models | BABE vs BASIL task harmonization | MqgQ | **Resolved M4A-3** | CSV + M1 + preprocess | **Already resolved** |
| **T08** | Dataset/Models | Train/val/test; overlap; no test taxonomy tuning | MqgQ, AC | **Partial M4A-3:** BABE-test/full-BASIL + no threshold-on-test stated; overlap still **UNVERIFIED** | M1; gaps | **Requires verification** (revnote kept) |
| **T09** | Dataset/Models | IDs, revisions, DeBERTa scope | k62P, AC | **Partial M4A-3:** Hub IDs, caches-only Deb, no SOTA, uneven inclusion; pins/hyperparams deferred | `basil_eval`; finetune script | **Partially resolved** (revnote kept) |
| **T10** | ~~L422~~ SHAP methods | Specify masker/background/output/version | xw7D, AC | **Resolved in M4A-1 (2026-11-13):** prose now matches `shap.Explainer` + `Text` masker + softmax biased class; false test-set background removed. **Deferred:** pinned shap version / unlogged explainer hyperparameters | Code + M4A-1 edit | **Already resolved** (prose); residual repro items deferred |
| **T11** | ~~Aggregation~~ | Auditable token→word | xw7D | **Resolved M4A-2:** reporting sum aggregation, Deb repair, M2B offset distinction. **Deferred:** phrase-level atomic units → Limitations | Code + M1 + M2B | **Already resolved** (prose); phrase-level deferred |
| **T12** | `\label{sec:sampling}` | All instances or confidence strata; no false pairing | MqgQ, xw7D | Disclosed actual caches + unpaired BABE; M2C uses all eligible | M4A-7 TeX + caches | **Resolved (M4A-7)** |
| **T13** | Analysis Framework | Define Em/Ev… / 90–98% | k62P, Kasneci, AC | Catch-all invalid; Methods retired | M1 + M4A-8d TeX | **Methods resolved**; **Results Em/Ev removed (M4B-5)**; **Abstract/Conclusion cleaned (M4D-2)**; appendix residual possible |
| **T14** | Analysis Framework ¶Paired attribution similarity | New vector similarity suite | AC | Jaccard@20 + cosine(\|SHAP\|) **implemented**; JS/signed/random **not** | M1 + M4A-8e TeX | **Methods resolved (implemented subset)**; extras **out of scope** |
| **T15** | `\label{sec:faithfulness_protocol}` + `\label{sec:faithfulness_results}` | Perturbation study | Kasneci, xw7D | M2B done | M2B + M4A-5 + **M4B-1** | **Methods + Results resolved** |
| **T16** | `\label{sec:metrics}` | AUROC, ECE, val thresholds | xw7D, AC | Methods: t=0.5 + AUPRC + sweep; **no** ECE/AUROC invented | M4A-7; auprc/sweep CSVs | **Methods resolved (M4A-7)**; ECE/AUROC **out of scope** unless claimed later |
| **T17** | Metrics → Results residual | Magnitude vs confidence | xw7D, AC | Methods ≠calibration; Results descriptive | M2D; M4B-5 | **Results calibration claim removed**; optional M2D-band `\revnote` remains |
| **T18** | Overall performance | Table 1 AUROC/Brier/CIs | xw7D | AUPRC provenance fixed; ECE out of scope | M4B-5 | **Narrowed optional** |
| **T19** | Magnitude results | Drop three calibration levels | xw7D | Done descriptively | M4B-5 | **Resolved** (optional bands left) |
| **T20** | `\label{sec:paired_similarity}` + `tab:paired_sim` | All 3 models same sentences | AC, k62P | Paired BD–DR primary; all-3 limited | M1 + **M4B-4** | **Results resolved**; forced all-3 redesign **out of scope** |
| **T21** | L681 Global indicators | Frequency, DeBERTa in fig, wording | xw7D, k62P | Writing + figure choice | Existing figs | **Requires verification** / pending edit |
| **T22** | Word-level patterns | Recompute after taxonomy validation | k62P, Kasneci | Em/Ev tables removed; retraction note | M1 + **M4B-5** | **Results resolved**; Other audit → appendix later |
| **T23** | `\label{sec:gold_span_results}` + `\label{sec:human_results}` | Gold mass, lex/inf, human IAA, SHAP–human | MqgQ, Kasneci | Experimentally **done** M2C/D + M3R | M4A-6 + **M4B-2** + **M4B-3** | **Methods + Results resolved**; Limitations/Ethics disclosure still open |
| **T24** | L813 Stats inference | Paired tests, multiplicity | xw7D | Partially done; section still catalogue-like | Existing stats sections | **Requires verification** during Results rewrite |
| **T25** | Error overlap | Thresholds/bins; weaken mechanism | xw7D | Results: $t{=}0.5$ + sensitivity disclosed | M4B-5 | **Results resolved**; full bin re-analysis out of scope |
| **T26** | Two-pathway claim | Remove/substantiate independence | xw7D-adjacent | Independence claim removed | M4B-5 | **Results resolved** |
| **T27** | Conclusion | Supported findings only | All | Yes | Claim ledger; M4B; **M4D-2** | **Resolved** (RQ answers; no Em/Ev / same-mechanism / calibration thesis) |
| **T28** | `\label{sec:limitations}` + new Discussion | Expand; remove revision-history aside | AC, xw7D | Done | M3R + M4B + **M4C-1** | **Resolved** |
| **T29** | `\label{sec:ethics}` | Licenses, checklist, human study | Checklist B2, D1–D3 | Protocol + HITL ethics **in TeX (M4C-2)**; consent/IRB/pay/recruit/licenses **unverified** | M3R + guides + **M4C-2** | **Partially resolved**; `\revnote{TODO P1 \| Human-study procedural disclosures}` retained |
| **T30** | Appendix | Fonts, update claims, examples | MqgQ, xw7D | Scientific contradictions **resolved M4E-2b**; fonts/visual polish deferred | M4E-2b + claim inventory | **Mostly resolved**; presentation residuals open |

---

## High-priority TODO conflicts with evidence

1. **T10** — **resolved in M4A-1**; deferred only shap library pin / unlogged hyperparameters.  
2. **T13/T22** — Methods + Results Em/Ev removed; Intro cleaned (M4D-1); **Abstract/Conclusion cleaned (M4D-2)**.  
3. **T15** — fully resolved.  
4. **T19/T25/T26** — **Results resolved in M4B-5**.  
5. **T20/T23** — Results resolved (M4B-2…M4B-4).  
6. **T01/T27** — **Resolved in M4D-2**. Title change still needs separate approval. Ethics T29 consent/IRB/licenses still need author answers. Related Work T05/T06 and Appendix T30 remain.

---

## Resolution protocol (for later modules)

- Do **not** delete `\revnote` silently.  
- When a module is approved and implemented, either:  
  - comment the revnote with `% RESOLVED M4x | rationale | date`, or  
  - replace with `\revnote{RESOLVED …}{…}` temporarily then remove before camera-ready.  
- Record resolution in `ARR_M4_REVISION_STATE.md`.

---

*Audit living document. Last module: **M4E-6c** Methodology compression (`ARR_M4E6C_METHODOLOGY_COMPRESSION.md`) — Methods ~2830→~968 words; technical detail in `app:method_details` / aggregation app; T08/T09 `\revnote`s retained. Content ≈8.2 / 8 (Conclusion spills onto p9). Next: author review; optional M4E-6d overflow trim; Ethics T29 still open.*
