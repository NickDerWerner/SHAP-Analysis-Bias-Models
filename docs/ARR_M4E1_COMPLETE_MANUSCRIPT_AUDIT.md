# ARR M4E-1 — Complete Manuscript Scientific and Submission Audit

**Date:** 2026-11-16  
**Manuscript (read-only):** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** Audit only — **no LaTeX edits**.  
**Status:** Complete.

---

## 1. Executive assessment

Core scientific revision (M4A–M4D) succeeded for the **main-text spine**: Abstract, Introduction, Methodology, Results, Discussion, Conclusion, and Limitations now share the same four-RQ framing (perturbation sensitivity; gold-span alignment + coverage; human IAA + SHAP–human; paired descriptive overlap) and largely avoid Em/Ev dominance, same-mechanism, magnitude-as-calibration, and independent-pathway theses.

The manuscript is **not submission-ready**. Remaining blockers are concentrated outside that spine:

1. **Appendix prose still asserts the old thesis** (calibration-not-mechanism; independent detection pathways; “similar content categories”).
2. **Related Work / Positioning still frames encoders as the “backbone of modern bias detection” and ends on mechanism-vs-calibration** (T05/T06 open).
3. **Broken figure paths** (`latex/…` while files live in the Overleaf root).
4. **Title still claims “Decision Mechanisms.”**
5. **Ethics checklist items** (consent/IRB/pay/licenses) unresolved (T29).
6. **Compilation UNVERIFIED** (no local engine); technical path bugs would fail Overleaf builds until fixed.

**Verdict:** Conditionally strong main text; **critical consistency debt in Appendix + Related Work + assets**. First corrective module should be a **small Abstract precision fix + figure-path repair**, then **Appendix reconciliation** (highest scientific contradiction risk).

---

## 2. Critical scientific inconsistencies

Classification key: **supported** · **qualified** · **outdated** · **contradicted** · **unresolved**

| ID | Location | Claim / pattern | Class | Notes |
|----|----------|-----------------|-------|-------|
| C1 | Appendix `\label{app:auprc_strata}` (~L1814–1819) | Lex/inf lifts “support the bias-type **independence** interpretation”; “two **detection pathways** … statistically independent” | **Contradicted** | Main Results (T26 / M4B-5) and Conclusion explicitly reject pathway/mechanism readings of the same arithmetic |
| C2 | Appendix `\label{app:max_shap}` (~L1757–1783) | “**calibration-not-mechanism** reading made quantitative”; “TN gap that anchors the **calibration interpretation** in the main text”; “cross-corpus **calibration signature**” | **Contradicted** | Main text retired magnitude-as-calibration; Limitations forbids reading mean \|SHAP\| as calibration |
| C3 | Appendix vocab confound (~L1696–1703) | Corrected analysis “demonstrates that both models **attend to similar content categories** under matched pools” | **Outdated** | Em/Ev category Results removed (M4B-5); matched-pool now a vocabulary control only (`sec:word_patterns`) |
| C4 | Appendix FP examples (~L1869–1870) | DR pattern “consistent with the **calibration gap** characterized in `sec:shap_mag`” | **Contradicted** | `sec:shap_mag` now descriptive magnitudes only |
| C5 | Related Work `\subsection{Transformer Models…}` (~L294–295) | Encoders “form the **backbone of modern bias detection** systems” | **Outdated** | AC + xw7D: scope to encoders; cite decoder LLMs |
| C6 | Related Work `\subsection{Positioning}` (~L352–360) | Gap framed as comparative SHAP; ends “**detection mechanism or calibration**”; “to our knowledge, no prior…” | **Outdated** / **unresolved** | Conflicts with Intro/Discussion; “first/no prior” unverified; still promises mechanism/calibration story |
| C7 | Title (L84) | “…Transformer Model **Decision Mechanisms**” | **Outdated** | Overstates recoverability of mechanisms; M4D-2 proposed replacements (not applied) |
| C8 | Results `\section{…Significance}` (~L1352–1361) | Shared FP **7.3×** independence baseline | **Qualified** | Text now says $t{=}0.5$ only, not mechanism; still dense and easy to misread as old thesis |
| C9 | Results both-type recall (~L1367–1377) | Union-of-recalls within 2–3 pts of both-type | **Qualified** | Explicitly **not** pathways; retain only with that negation (or move to appendix as arithmetic note) |
| C10 | Methods taxonomy retirement (~L618–625) | Em/Ev catch-all described then retired | **Supported** (as correction) | Correct disclosure; must not be re-read as a positive result |
| C11 | Main Results / Discussion / Abstract / Conclusion Em/Ev / same-mechanism as positive claims | — | **Supported absence** | No positive Em/Ev dominance or same-mechanism claims found in Abstract–Conclusion spine |
| C12 | Intro figure caption (~L231) | Mentions “calibration” only as what the example is **not** | **Supported** (qualified negation) | OK |
| C13 | Conclusion (~L1475) | “no formal **predictive-calibration** analysis” | **Supported** (limitation) | OK; do not confuse with appendix’s positive calibration thesis |
| C14 | DeBERTa faithfulness / strong human Deb | Not claimed in Abstract/Conclusion | **Supported absence** | Deb human rows remain exploratory in Results ($n{\leq}10$) |
| C15 | Stale comment after Intro contributions (~L286) | “Abstract/Conclusion TODOs remain” | **Outdated** (comment only) | M4D-2 resolved T01/T27; comment frozen because Intro not re-touched |

### Abstract precision (propose only; do not edit yet)

**Issue:**  
> “Masking … lowers $P(\mathrm{biased})$ by about ${-}0.33$ (BD) and ${-}0.29$ (DR) …---more than random or low-$|$SHAP$|$ controls.”

Verified numbers (M2B / M4B-1): signed $A_{\mathrm{pos}}$ ΔP at $k{=}2$ is **−0.327 / −0.293**. Control superiority is a **separate** contrast (high-\|SHAP\| vs random paired \|ΔP\| ≈ **+0.223 / +0.222**). The em-dash can be misread as if −0.33/−0.29 *are* the deltas vs random.

**Proposed Abstract sentence (exact replacement candidate):**

```text
On paired BASIL sentences ($n{=}200$; BD/DR), masking the highest-positive
SHAP words ($k{=}2$) changes $P(\mathrm{biased})$ by about ${-}0.33$ (BD)
and ${-}0.29$ (DR); absolute probability changes exceed random and
low-$|$SHAP$|$ controls.
```

**Coverage wording:**  
“the apparent lexical--informational gap **disappears**” → prefer “is **not observed** / **closes** after coverage matching for BD/DR” so readers do not infer proven lex≡inf alignment or equivalence of evidence types.

**κ values:** ≈0.44 / ≈0.24 match 0.439 / 0.238 — **supported**.  
Human SHAP>random: **supported** for BD/DR cache∩; Abstract correctly scopes “available cache intersections” and does not claim strong Deb.

---

## 3. Numerical and methodological discrepancies

| Topic | Cross-section check | Finding |
|-------|---------------------|---------|
| Four RQs | Intro enumerate ↔ Abstract ↔ Methods protocols ↔ Results subsections ↔ Discussion paragraphs ↔ Conclusion First–Fourth | **Aligned** in main spine |
| Faithfulness scope | Methods + Results + Limitations: BD/DR, paired BASIL $n{=}200$; Deb excluded; TN $n{=}3$ | **Consistent** |
| Gold-span | Excess vs length-matched random; coverage match removes naive lex−inf gap BD/DR | **Consistent**; Abstract “disappears” slightly strong (see §2) |
| Human denominators | $n{=}120$ presence; type $n{=}119$; AnnB 26 yes∅spans excluded from span/SHAP; SHAP∩ BD34/DR42/Deb12 | **Consistent** across Results/Limitations/Ethics |
| Paired similarity | BASIL BD–DR $n{=}371$; shared FP 112 / FN 104; Jaccard@20 definition corrected (not “81% of top-20”) | **Consistent**; BABE/BASIL all-3 $n{=}59/60$ exploratory |
| Attribution metrics | Reporting sum aggregation; M2B offset-aware masking separate | Methods OK; **Appendix aggregation section duplicates** and may drift from DeBERTa-repair / offset notes |
| Threshold | $t{=}0.5$ for cells/caches; AUPRC + sweep disclosed; no validation-threshold re-strata | **Qualified**; xw7D residual remains |
| Unpaired as paired | BABE caches disclosed unpaired except text-hash ∩ | **Supported** in Methods/Results |
| Architecture-driven Deb claims | Main text: secondary where caches permit | **Supported**; Appendix still implies equal three-model calibration story |
| Phrase-level | Deferred in Limitations | **Unresolved** as experiment; **disclosed** |

---

## 4. Related Work gaps (T05 / T06)

### Adequacy by theme

| Theme | Present? | Assessment |
|-------|----------|------------|
| SHAP vs other attributions (LIME, attention debate) | Partial | LIME + attention faithfulness cites present; little on integrated gradients / other feature attributions |
| Perturbation-based explanation evaluation | Partial | Haug baselines; Rong ROAD; EvalxNLP — good, but Positioning still old |
| Plausibility vs faithfulness | Partial | EvalxNLP mentions both; paper’s own sensitivity≠plausibility distinction not mirrored in Related Work framing |
| Human-rationale alignment | Weak | ERASER cited; little on human rationale / bias-span annotation challenges beyond datasets |
| Media bias detection + annotation | Partial | BABE, bias-detector, DA-RoBERTa; BASIL cited elsewhere |
| Encoder vs decoder LLM bias detection | **Missing** | T05 revnote lists Lin 2025; Trhlík & Stenetorp 2024; Mujahid 2025; Menzner & Leidner 2024 — **not in `custom.bib` / not cited** |

### Material missing literature (verification required)

Do **not** invent bibliographic details. Add only after key verification:

1. Lin et al., COLING 2025 — LLM bias detection vs human perception (**verify**)  
2. Trhlík & Stenetorp, EMNLP 2024 — generative media bias (**verify**)  
3. Mujahid et al., ACL 2025 — LLM media factuality/bias profiling (**verify**)  
4. Menzner & Leidner, NLDB 2024 — LLM bias detection/subcategorization (**verify**)

Optional (only if space and purpose clear): one canonical faithfulness survey / Jacovi & Goldberg style “faithfulness myths” pointer — **requires verification**; EvalxNLP already covers much of the evaluation framing.

### Required Related Work edits (conceptual; not performed)

- Qualify “backbone of modern…” → encoder classifiers studied here; decoder LLMs exist and are out of scope.  
- Rewrite Positioning to match four RQs / multi-check evaluation; **delete** mechanism-or-calibration punchline.  
- Soften or remove unverified “to our knowledge, no prior…”  

---

## 5. Appendix reconciliation plan (T30)

| Appendix block | Action | Rationale |
|----------------|--------|-----------|
| Vocab-pool confound (`app:vocab_confound`) | **Keep + revise** | Still useful as methodology correction; rewrite implication paragraph so it does **not** claim matched-pool “similar content categories” / Em/Ev rehab; point to BASIL lex/inf + human evidence instead |
| Max \|SHAP\| (`app:max_shap`) | **Revise heavily** or **remove interpretive paragraphs** | Tables may stay as descriptive max-vs-mean; delete calibration-not-mechanism / TN calibration-signature prose |
| AUPRC strata (`app:auprc_strata`) | **Revise** | Keep table as discrimination-by-stratum; **remove** independence/pathway interpretation (C1) |
| Token-level examples (AppendixA/B + FP prose) | **Revise** | Keep illustrative examples (reviewer request); strip calibration-gap cross-refs; improve fonts/captions later |
| Word-level aggregation detail | **Relocate/condense** into Methods or shorten to delta-only vs `sec:word_aggregation` | Avoid dual contradictory aggregation stories; ensure DeBERTa repair + M2B offset notes survive |
| Orphan assets (`figure3_word_category_composition.png`, etc.) | **Do not reintroduce** | Em/Ev composition figures obsolete |

Broken main-text refs into appendix: `app:vocab_confound` is cited from Results/Limitations — keep label after revise. `app:auprc_strata` currently **unused** from main text — either cite once descriptively or accept unused.

---

## 6. Ethics checklist (T29) — author questions only

Verified protocol already in Ethics (blindness, schema, independence, yes∅spans policy). **Do not invent** answers. Authors must confirm:

1. Who were the annotators (roles/expertise)?  
2. Voluntary participation?  
3. Compensation (pay / credit / none)?  
4. Informed consent (written/oral; purpose disclosed)?  
5. IRB/ethics review: required / obtained / waived / not sought (institution)?  
6. Withdrawal rights after labeling?  
7. Any PII outside `annA`/`annB` study IDs?  
8. Public / restricted / private release plan for raw annotations?  
9. Licenses for BABE, BASIL, Hub models, code, and annotations?  
10. ARR checklist: update **D Human Subjects** from prior “No” (submission form showed D=No) now that a human annotation study is reported.

---

## 7. LaTeX technical findings

| Check | Result |
|-------|--------|
| Duplicate `\label`s | **None** |
| Undefined `\ref`s | **None** (active text) |
| Missing citation keys vs `custom.bib` | **None** among currently cited keys (28 cite / 33 bib) |
| Missing graphics | **`latex/figure1_redesign.pdf`**, **`latex/babe_fig3_with_fn.pdf`** — **MISSING** (`latex/` directory absent; files exist at Overleaf **root**) |
| Path inconsistency | Intro fig uses `latex/…`; BABE magnitude fig uses `latex/…`; BASIL magnitude uses root `basil_fig3_with_fn.pdf` |
| Unused labels | `app:auprc_strata`, `sec:ethics`, `sec:global_bias`, `sec:stats`, `tab:max_shap`, `tab:max_vs_mean_ratios` |
| Orphan image files (not included) | `figure3_word_category_composition.png`, `figure3_tp_fp_breakdown.png`, `figure1_shap_distributions_single.png`, `shap_decisions.png`, `Shap_bd.png`, `Shap_darft.png` |
| Open `\revnote`s | **10** (see § Remaining TODOs) |
| Compilation | **UNVERIFIED** (no `pdflatex`/`xelatex`/`latexmk` locally) |
| Bibliography placement | `\bibliography{custom}` before `\appendix` (common ACL); appendix citations resolve if bib processed |
| Section order | Discussion → **Conclusion** → Limitations → Ethics → bib → Appendix | Unusual vs many ACL papers (Limitations often before Conclusion); nonblocking but noticeable |
| Template | `\usepackage[review]{acl}` | OK for ARR review build |

---

## 8. Section-level length assessment

Approx. word counts (comments stripped; body text + tables prose):

| Section | Words | Page-pressure note |
|---------|------:|--------------------|
| Abstract | 177 | Within typical ACL abstract budget |
| Introduction | 627 | OK |
| Related Work | 512 | Needs rewrite more than cut |
| Methodology | 3406 | Heavy but largely necessary; aggregation appendix duplicates some content |
| Evaluation Results | 3850 | Primary pressure; Significance catalogue still long (T24) |
| Discussion | 522 | OK |
| Conclusion | 255 | OK |
| Limitations | 435 | OK |
| Ethical Considerations | 350 | OK pending T29 answers |
| **Main (pre-appendix)** | **~10.4k** | High for long ACL; Results+Methods dominate |
| Appendix (all) | ~2048 | **Cut/revise outdated interpretation** before cutting Methods statistics |

**Prioritize for space:** (1) Appendix interpretive paragraphs C1–C4; (2) condense standalone Significance catalogue into finding-local sentences; (3) optional magnitude table/figure redundancy (xw7D); (4) do **not** gut CI/denominator disclosures.

---

## 9. Reviewer-response coverage matrix

Statuses require evidence, not mere new prose.

### Meta-review (AC dgcp)

| Concern | MS change | Evidence | Section | Residual | Status |
|---------|-----------|----------|---------|----------|--------|
| Scope RW; add decoder LLM cites | **Not done** | T05 open; no bib keys | Related Work | Still “backbone…” | **Unresolved** |
| Define taxonomy; SHAP bg; token→word; BASIL lex/inf; cautious “attend to” | Taxonomy retired; SHAP Explainer+Text; aggregation; BASIL lex/inf + human | M1, M4A-1/2/6/8d, M4B-2/3 | Methods/Results | Phrase-level deferred | **Mostly resolved** (main); appendix “attend to similar categories” undoes caution |
| Core conclusions not confidence/threshold artifacts | $t{=}0.5$ disclosed; sweep/AUPRC; M2D coverage; no full model-specific threshold re-strata | M2D, M4A-7, M4B-5 | Metrics/Results/Lim. | xw7D threshold artifact concern partially open | **Partially resolved** |
| Shorten abstract; figures; examples; address reviews | Abstract rewritten; examples limited; fonts still small | M4D-2 | Abstract/Appendix figs | Figure fonts/paths | **Partially resolved** |

### Reviewer MqgQ

| Concern | Change | Evidence | Section | Residual | Status |
|---------|--------|----------|---------|----------|--------|
| BASIL lex vs informational | Analyzed separately + coverage | M2C/D, M4B-2 | Gold-span Results | — | **Resolved** |
| Span vs sentence handling | Documented + yes∅spans | M4A-3/6, M3R, M4B-3 | Methods/Results/Lim. | — | **Resolved** |
| What “generalization” means | Intro/Methods: attribution/paired scope; Deb secondary | M4D-1, M4A-3 | Intro/Methods | RW Positioning still muddy | **Mostly resolved** |
| Sampling / not all instances | Cache disclosure; M2C all eligible; human 120 stratified | M4A-7/8b | Sampling table | — | **Resolved** |
| Phrase-level attributions | Limitation only | — | Limitations | No experiment | **Deferred (disclosed)** |
| Abstract length / figs / examples | Abstract shortened; appendix examples weak fonts | M4D-2 | Abstract/App | Fig quality | **Partially resolved** |

### Reviewer xw7D

| Concern | Change | Evidence | Section | Residual | Status |
|---------|--------|----------|---------|----------|--------|
| Encoder-only RW; “backbone” overclaim | **Not fixed** | T05 | Related Work | Decoder cites missing | **Unresolved** |
| SHAP faithfulness untested | Perturbation sensitivity added | M2B, M4A-5, M4B-1 | Faithfulness Meth/Res | Mask OOD; BD/DR only | **Resolved** (scoped) |
| Magnitude ≈ confidence; SHAP redundant for calibration | Calibration thesis removed from main | M4B-5, M4C-1, M4D | Mag/Disc/Lim | **Appendix still asserts calibration thesis** | **Partially resolved** |
| Shared 0.5 threshold | Disclosed + sweep; no full re-analysis | M4B-5 | Metrics/Sig. | Model-specific thresholds not done | **Partially resolved** |
| Taxonomy undefined | Retired Em/Ev | M4A-8d, M4B-5 | Methods/Results | Appendix vocab implication outdated | **Resolved** (main) |
| Aggregation / background | Corrected Text-masker; no test-set bg | M4A-1/2 | Methods | shap pin missing | **Mostly resolved** |
| Reproducibility score 1 | Methods improved; pins/licenses open | M4A, T29/T09 | Methods/Ethics | Hub hashes; licenses | **Partially resolved** |

### Reviewer k62P

| Concern | Change | Evidence | Section | Residual | Status |
|---------|--------|----------|---------|----------|--------|
| Taxonomy / Em/Ev backbone | Retracted | M1, M4B-5 | Methods/Results | — | **Resolved** |
| Narrow scope / uneven Deb | Explicit BD/DR primary | M4D-1, Methods | Intro/Methods | Still 3-model branding in places/title | **Partially resolved** |
| Dense writing / abstract ratios | Abstract cleaned | M4D-2 | Abstract | Results still dense; Significance catalogue | **Partially resolved** |

### Professor Kasneci

| Concern | Change | Evidence | Section | Residual | Status |
|---------|--------|----------|---------|----------|--------|
| Faithfulness analysis | Done | M2B | Faithfulness | — | **Resolved** |
| Manual labels vs SHAP | Done with limits | M3R, M4B-3 | Human Results | Cache∩; κ_type weak | **Resolved** (scoped) |
| Disentangle tokens vs semantics (paraphrase) | Not done | — | Future work | — | **Deferred** |
| Model diffs: cues vs architecture | Paired descriptive + DR>BD lexical excess | M2C/D, M4B-4 | Results | No paraphrase causal design | **Partially resolved** |
| Define Em/Ev; dummy/Other | Catch-all retracted | M1, M4A-8d | Methods | — | **Resolved** |

### Reviewer concerns not yet fully addressed

1. Decoder-LLM Related Work + drop “backbone” (AC, xw7D).  
2. Appendix still carries calibration / pathway / similar-categories claims (undoes xw7D/Kasneci fixes).  
3. Threshold robustness beyond disclosure (xw7D).  
4. Figure readability / paths (AC, MqgQ, xw7D).  
5. Title “Decision Mechanisms” (scientific framing).  
6. Ethics/licenses + Hub pins (checklist + xw7D repro).  
7. Phrase-level / paraphrase disentangling (deferred).  
8. Standalone statistical catalogue density (xw7D #11 / T24).

---

## 10. Prioritized correction sequence

| Priority | Module (proposed) | Why |
|--------:|-------------------|-----|
| **P0** | **M4E-2a — Asset + Abstract micro-fix** | Fix `latex/` figure paths; Abstract ΔP-vs-control wording; coverage “disappears” softener. Small, low risk, unblocks compile + precision. |
| **P0** | **M4E-2b — Appendix reconciliation (T30)** | Remove/rewrite C1–C4 contradictions; highest scientific consistency risk. |
| **P1** | **M4E-3 — Related Work T05/T06** | Decoder cites (after bib verification); rewrite Positioning; kill backbone/mechanism-calibration. |
| **P1** | **Title decision** | Author pick among M4D-2 options; apply only with approval. |
| **P1** | **T29 Ethics answers** | Author questionnaire → short Ethics/checklist update. |
| **P2** | Condense `sec:significance` into finding-local stats (T24) | Page budget + xw7D readability. |
| **P2** | Optional magnitude confidence bands (revnotes) | Only if claiming anything beyond descriptive \|SHAP\|. |
| **P2** | Presentation: figure fonts, abbreviation pass, orphan-asset cleanup | AC/MqgQ. |
| **P3** | Final compile on Overleaf + checklist pass | After P0–P1. |

### Remaining open `\revnote` TODOs (TeX)

| Loc | Note | Disposition |
|-----|------|-------------|
| Related Work | T05 decoder cites | Open |
| Related Work / Positioning | T06 faithfulness positioning / no “first” | Open |
| Dataset/Models | T08 overlap / splits | Open (partial) |
| Models | T09 pins / Deb hyperparams | Open (partial) |
| Results | Magnitude confidence (×2 near-duplicate) | Optional |
| Results | Overall performance AUROC/ECE optional | Optional |
| Results | Global word lists optional | Optional |
| Results | Statistical inference catalogue | Open |
| Ethics | T29 procedural disclosures | Open |
| Appendix | T30 presentation / claim updates | Open |

---

## 11. Stop condition confirmation

- **No LaTeX manuscript edits** in this module.  
- No Related Work rewrite, appendix edit, title change, Abstract edit, Ethics invention, new experiments, or submission actions performed.  
- Recommended **first small corrective module for author approval:** **M4E-2a (Abstract precision + figure-path repair)**, immediately followed by **M4E-2b (Appendix reconciliation)** once approved.

---

*Audit complete. Companion state update: `docs/ARR_M4_REVISION_STATE.md`.*
