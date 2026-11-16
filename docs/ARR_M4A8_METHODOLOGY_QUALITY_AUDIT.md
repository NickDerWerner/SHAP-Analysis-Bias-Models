# M4A-8 — Methodology Consolidation and Scientific Readability Audit

**Date:** 2026-11-15  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** Audit only — **no LaTeX edits in this module.**  
**Section audited:** `\section{Methodology}` through just before `\section{Evaluation Results}`.

Word counts below are approximate **prose tokens** after stripping comments and most LaTeX commands (table cells counted lightly via remaining text). Prior M4A-7 estimate (~3050) matches this pass within noise.

---

## 1. Subsection word counts

| Subsection | ≈ words | Share | Verdict |
|------------|--------:|------:|---------|
| Dataset and Models | 636 | 20% | Essential but compressible |
| SHAP-Based Interpretability Framework | 143 | 4% | Keep; already tight |
| Word-Level Attribution Aggregation | 518 | 16% | **Overweight** (esp. DeBERTa repair) |
| Stratified Sampling Strategy (+ population table) | 410 | 13% | Essential core; table keep/slim |
| Analysis Framework | 190 | 6% | Thin + stale TODOs; merge candidate |
| Perturbation-Based Attribution Sensitivity | 359 | 11% | Essential; slight trim |
| BASIL Gold-Span Attribution Alignment | 326 | 10% | Essential; formula/baseline trim |
| Independent Human Evidence Annotations | 258 | 8% | Essential; AnnB update wording trim |
| Statistical Significance Testing | 192 | 6% | Keep; cut κ duplication |
| Evaluation Metrics | 182 | 6% | Keep; cut cross-ref padding |
| **Total Methodology** | **≈3214** | 100% | **Too long for ACL Methods** |

**Recommended main-text target after consolidation:** **≈1900–2200 words** (~35–40% cut), with engineering provenance and full cache strata moved to appendix.  
Do **not** cut primary protocols for faithfulness, gold-span, or human annotation below what a careful reviewer needs to reproduce the claim structure.

Realistic ACL impact: current Methods alone is roughly **4+ column-pages** of dense prose; target Methods ≈ **2.5–3 pages** plus a short appendix subsection for aggregation/sampling detail.

---

## 2. Scientific completeness assessment

Can a careful NLP reader answer the following from Methods alone?

| Question | Status | Notes |
|----------|--------|-------|
| 1. Datasets and models | **Yes** | BABE HF test; BASIL commit + union label; three encoders; uneven coverage disclosed |
| 2. How SHAP is generated | **Mostly yes** | Explainer + Text masker + biased-class softmax; **missing** pinned `shap` version / explainer kwargs (already deferred) |
| 3. Attribution → words | **Yes, but heavy** | Reporting sum vs offset-aware masking distinguished; DeBERTa repair over-narrated |
| 4. Faithfulness measurement | **Yes** | Masking, budgets, A–E, ΔP, controls, TN n=3, BD/DR only |
| 5. Human-evidence / gold alignment | **Yes** | Abs/pos mass, random baselines, coverage match, paired BD−DR |
| 6. 120-sentence human study | **Yes** | Blind, schema, AnnB update, yes∅spans policy, cache∩sample |
| 7. Populations / pairing | **Yes** | Table + sampling prose; some numbers repeated downstream |
| 8. Stats / controls | **Yes** | McNemar, Mann–Whitney, bootstrap, κ; roles distinguished |

### Omissions (do not invent; disclose or defer)

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| Pinned `shap` / Hub revision / DeBERTa train hyperparams | Medium (repro) | Appendix / model card (T09); not main Methods bulk |
| BABE↔BASIL article/topic overlap | Medium | Keep T08; do not guess |
| Annotator recruitment, training, compensation | Medium (ethics) | Ethics/checklist (T29), not Methods compression |
| Exact article-level cluster-bootstrap procedure | Low | One sentence + appendix pointer if Results use it |
| Soft-F1 definition (formula) | Low | Appendix or cite standard char soft-F1 |

### Contradictions / confusion inside Methods

| Issue | Severity | Action |
|-------|----------|--------|
| “Offset-aware pipeline above” referenced from faithfulness/gold **before** readers may recall Aggregation ¶Perturbation | Low–Med | One shared short definition; delete later repeats |
| Analysis Framework still hosts **T13/T14** asking to *define* Em/Ev taxonomy and a *new* similarity suite — conflicts with claim ledger | **High (conceptual)** | Resolve via restructuring recommendation below; do not keep as if Em/Ev is planned backbone |
| Stats § re-defines κ / soft-F1 already in Human § | Low | Cross-ref only |
| Metrics § largely repeats threshold/AUPRC caveats from Sampling | Low | Merge or shorten |
| DeBERTa BABE-test AUPRC/macro-F1 in Models is fine; **Results** still overclaim all-three BASIL AUPRC (flagged M4A-7) | Med (cross-section) | Fix in M4B, not Methods |

No new unsupported empirical claims found in Methods that invent results; caveats about sensitivity≠reasoning and no intrinsic lex≫inf are appropriately methodological.

---

## 3. Readability problems (ranked by severity)

1. **Critical — Conceptual backlog in Analysis Framework.** Yellow TODOs still ask to define Emotional/Evaluative as a main taxonomy and to invent a broad new similarity metric suite. A reader scanning Methods will think Em/Ev is forthcoming. That is scientifically misleading relative to M1/ledger.  
2. **High — Aggregation § reads as engineering postmortem.** The DeBERTa `.bak` / whitespace-exclusion / additive reaggregation paragraph is hard for non-authors and duplicates the appendix.  
3. **High — Repetition of alignment.** Offset-aware mapping is explained in Aggregation, then restated in Faithfulness and Gold-span.  
4. **High — Length vs ACL budget.** ~3200 words of Methods before Results crowds out findings; reviewers will skim and miss population caveats.  
5. **Medium — Sampling paragraph packs too many integers.** Essential, but denser than a conference reader can absorb without the table; prose should lean on Table~\ref{tab:eval_populations}.  
6. **Medium — Dataset § is thorough but front-loaded.** Label harmonization + model caveats are good; some Hub/path prose can move.  
7. **Medium — “Updated Annotator B…” revision-history tone.** Methods should state the final protocol; file-replacement narrative fits Limitations/repro appendix.  
8. **Low — Notation.** $\sum |s_i| f_i$ is fine; “logit-margin” undefined in one word (logits of biased vs non-biased).  
9. **Low — Jargon stacking.** “attribution-guided prediction sensitivity,” “plausibility,” “cache∩sample” are justified but should appear with one plain-English gloss each (already mostly present).

Be critical: prior modular AI edits correctly fixed false claims (background corpus; 100/cell BASIL myth) but **accumulated defensive detail** and left obsolete TODOs visible—hurting readability more than a clean retraction paragraph would.

---

## 4. Paragraph-level compression plan

Classification key: **A** essential main text · **B** appendix · **C** redundant removable · **D** necessary but unclear (rewrite shorter).

### Dataset and Models (636 → ~420)

| Block | Class | Plan |
|-------|-------|------|
| BABE release + test split + no threshold tuning | A | Keep ~½ length |
| BASIL commit, 7984, lex/inf counts, union rule | A | Keep; drop CSV path trivia |
| Quote / span dump vs flags | B | Appendix |
| Label harmonization paragraph | A | Keep (1 short ¶) |
| Three models + uneven inclusion | A | Keep |
| Hub pins / missing ckpt / local path detail | B | Appendix (T09) |
| Preprocessing max-len 256 | A | One sentence |

### SHAP Framework (143 → ~120)

| Block | Class | Plan |
|-------|-------|------|
| Explainer + Text masker + no background corpus | A | Keep |
| Not internal reasoning | A | Keep one sentence |

### Word-Level Aggregation (518 → ~220 main + appendix)

| Block | Class | Plan |
|-------|-------|------|
| Why word-level / figure | A | Keep short |
| Reporting: sum units → words | A | Keep ~5–7 sentences |
| DeBERTa repair history (.bak, whitespace diagnostic, additive checks) | B | Move to appendix (already foreshadowed) |
| One sentence: “DeBERTa uses repaired word lists; see App.” | A | Replace long ¶ |
| Perturbation alignment definition | A | **Canonical** short ¶ here; others cross-ref |
| Phrase-level not atomic | A | One sentence (or Limitations) |

### Sampling (410 → ~280)

| Block | Class | Plan |
|-------|-------|------|
| Non-interchangeable populations; t=0.5 | A | Keep |
| BABE unpaired sizes | A | Keep compact list; rely on table |
| Full BASIL stratum laundry list | B/D | Main: “multi-stratum union, caps 100, deduped → 850/837”; strata names → appendix |
| Table~\ref{tab:eval_populations} | A | **Keep** (best navigation aid); optionally shorten cell text |
| Downstream pointer ¶ | C | Table caption already points |

### Analysis Framework (190 → ~80 or merge)

| Block | Class | Plan |
|-------|-------|------|
| Cache fields + magnitude aggregates | A | 3–4 sentences or fold into Sampling/Metrics |
| Matched-pool p75 | A | Keep (needed for vocabulary Results) |
| T13/T14 revnotes as currently worded | C (as tasks) | **Replace** with retraction/retention decisions (see §6); do not expand Em/Ev methods |

### Faithfulness (359 → ~300)

| Block | Class | Plan |
|-------|-------|------|
| Why + sensitivity≠reasoning | A | Keep |
| Population n=200 / strata / Deb excluded | A | Keep |
| Conditions A–E + mask token | A | Keep |
| Re-explain offset alignment | C | “as in §Aggregation” |
| Measurements list | A | Slight trim; defer OOD sentence to Limitations if duplicated |

### Gold-span (326 → ~260)

| Block | Class | Plan |
|-------|-------|------|
| Plausibility framing + join key | A | Keep; shorten commit repeat |
| Formula for abs mass | A | Keep one display or inline |
| Top-5 / AP | A | One sentence |
| 20 random + coverage + positional | A | Keep; “implementation in App.” for placement algorithm |
| Coverage-matched ±5pp + OLS controls | A | Keep (scientifically load-bearing) |
| Repeat “not causal / no intrinsic lex≫inf” | A | Keep one sentence |

### Human annotations (258 → ~210)

| Block | Class | Plan |
|-------|-------|------|
| 120 / 30×4 / blind schema | A | Keep |
| AnnB file-replacement narrative | B/C | “Final annotations: complete presence on 120; 26 yes without local spans” |
| κ / soft-F1 / SHAP–human / cache∩ | A | Keep |
| Duplicate “deferred to Results/Limitations” | C | One clause |

### Stats + Metrics (192+182 → ~250 combined)

| Block | Class | Plan |
|-------|-------|------|
| McNemar / Mann–Whitney roles | A | Keep |
| Bootstrap / sentence unit | A | Keep |
| Re-list κ/soft-F1 | C | Cross-ref Human § |
| Classification metrics + AUPRC vs t=0.5 | A | Keep once |
| “No ECE/Brier/AUROC” defensive line | A/B | One short clause (reviewer-facing) |
| Repeat sensitivity metric list | C | Cross-ref |

**Estimated savings if executed carefully:** ~1000–1300 words → landing near **1900–2200**.

---

## 5. Appendix relocation recommendations

Propose **one** new appendix subsection (or extend existing “Word-Level Attribution Aggregation in Detail”):

**Suggested title:** *Attribution aggregation, cache sampling, and alignment details*

| Move to appendix | Keep pointer in main text |
|-----------------|---------------------------|
| DeBERTa repair algorithm, `.bak`, whitespace exclusion, additive checks | “Repaired DeBERTa word lists (Appendix X)” |
| Full BASIL stratum names and cap table | “Multi-stratum union (Appendix X)” |
| Random-span placement / non-overlap retries | “Length-matched random spans (Appendix X)” |
| Soft-F1 / IoU formal definition | Optional |
| Hub SHA / fine-tune hyperparams (when supplied) | T09 |

**Do not** move: faithfulness conditions A–E; human study design; coverage-matched lex/inf caveat; population table; t=0.5 operating point; unpaired BABE warning.

---

## 6. Recommendations for T13 and T14

### T13 — Four-category linguistic taxonomy (Emotional/Evaluative, …)

| Option | Recommendation |
|--------|----------------|
| Keep as main Methods contribution | **No** |
| Redefine Em/Ev carefully and re-run as backbone | **No** — M1 shows catch-all; 90–96% invalid |
| Replace contribution with BASIL lex/inf (+ Other audit) | **Yes** |
| Where to put the correction | **Short Methods note or Analysis Framework replacement ¶** + full retraction numbers in Results/Appendix; Limitations mention coding artifact |

**Classification:** **Resolve during manuscript restructuring** (replace TODO with a 4–6 sentence *retraction + replacement* Methods paragraph; Results M4B-5 carries the Other/% table).  
**Do not** delete the `\revnote` until that replacement paragraph is approved.  
BASIL lexical/informational evidence analysis **adequately replaces** the earlier Em/Ev dominance contribution for the paper’s scientific story (claim ledger).

### T14 — Cross-model attribution similarity suite

| Already defensible (retain) | Not defensible / out of scope |
|-----------------------------|-------------------------------|
| Paired BD–DR top-$k$ Jaccard / cosine on **shared** BASIL errors (e.g. shared FP n≈112) | Unpaired pool “architecture” comparisons |
| Descriptive paired overlap on BABE all3 n=59 (disclose tiny same-cell) | New Jensen–Shannon / full vector suite unless already implemented |
| “Overlapping high-attribution tokens on paired data” | “Same linguistic mechanism” |

**Classification:** **Retain with specific evidence** for *paired* overlap already computed (M1); **defer/remove** the TODO’s request for a broad new metric suite.  
**Do not** propose new experiments to rescue same-mechanism.  
Replace T14 wording later with: “Paired token-overlap metrics (Jaccard@$k$, cosine of $|$SHAP$|$) on shared-ID subsets; no unpaired mechanism claim.”

---

## 7. Contradictions requiring correction (cross-section)

| Topic | Methods commitment | Downstream conflict | Where to fix |
|-------|--------------------|---------------------|--------------|
| Magnitude ≠ calibration | Explicit in Metrics | Results still use “calibration rather than mechanism” | M4B-4 / M4B-7 |
| Shared tokens ≠ shared reasoning | Faithfulness + Aggregation caveats | Intro/Results “same mechanism” language | M4D / M4B-6 |
| Lex vs inf after coverage match | Gold-span Methods | Old Results Em/Ev + lex≫inf narrative | M4B-2 / M4B-5 |
| DeBERTa coverage | Uneven; no M2B | Figures/tables implying 3-way parity | M4B + figures |
| Threshold-dependent cells | t=0.5 operating point | Any threshold-invariant attribution claim | M4B + Limitations |
| AnnB 26 yes∅spans | Methods policy | Must appear in Results denominators + Limitations | M4B-3 / M4C-1 |
| Human–SHAP ∩ small | BD34/DR42/Deb12 | Overgeneralizing to full 120 | M4B-3 / M4C-1 |
| 2-model vs 3-model | Primary BD/DR | “All three” AUPRC on BASIL | M4B-7 (flagged M4A-7) |

---

## 8. Estimated impact on manuscript length

| Action | Approx. Δ |
|--------|-----------|
| Main Methods compression to 1900–2200 words | **−1000 to −1300 words** (~1–1.5 pages) |
| Appendix relocation (net) | **+400–700 words** in appendix (acceptable) |
| T13 retraction ¶ (net vs removing long Em/Ev Results later) | Methods +80; Results **large cut** later |
| T14 no new suite | Saves future Methods inflation |

Net ARR PDF: Methods shorter; Results still need rewrite (will grow with faithfulness/human tables then shrink when Em/Ev removed). **Do Methods consolidation before M4B** so Results do not cite obsolete Methods structure.

---

## 9. Proposed sequence of small, independently reviewable edits

Approve **one** at a time; each should be a short PR-style module:

| ID | Edit | Risk | Depends on |
|----|------|------|------------|
| **M4A-8a** | Compress DeBERTa repair ¶ → 2 sentences + appendix pointer; make Aggregation the sole offset-alignment definition | Low | Author OK on appendix |
| **M4A-8b** | Slim Sampling prose to lean on Table~\ref{tab:eval_populations}; move stratum name list to appendix | Low | — |
| **M4A-8c** | Merge/shorten Analysis Framework + Stats/Metrics cross-ref cleanup; remove duplicated κ/metric lists | Low | 8a/8b optional |
| **M4A-8d** | Replace T13 `\revnote` with Em/Ev **retraction + BASIL lex/inf replacement** Methods paragraph (no Results numbers) | Med (scientific) | Claim ledger |
| **M4A-8e** | Replace T14 `\revnote` with paired-overlap metrics statement (Jaccard/cosine; no new suite; no same-mechanism) | Med | M1 pairing |
| **M4A-8f** | Trim Faithfulness/Gold/Human repeated alignment + AnnB revision-history tone | Low | 8a |

**First small consolidation edit for author approval:** **M4A-8a** (DeBERTa aggregation compression + single offset-alignment canonical paragraph).

**Do not start M4B** until at least 8a–8c (length) and ideally 8d (T13 conceptual clarity) are decided.

---

## Completeness checklist vs eight reader goals

1. Datasets/models — OK (trim).  
2. SHAP generation — OK (pin later).  
3. Word alignment — OK after 8a.  
4. Faithfulness — OK.  
5. Human-evidence alignment — OK.  
6. 120-study — OK after tone trim.  
7. Populations/pairing — OK (table essential).  
8. Stats/controls — OK after deduping.

**Scientifically critical problems:** (i) visible T13 TODO implying Em/Ev methods still planned; (ii) ACL over-length risk causing reviewers to miss TN n=3 / cache∩ / unpaired warnings; (iii) cross-section Results still contradict Methods on calibration and 3-model AUPRC — fix in Results, not by weakening Methods.

---

*End of M4A-8 audit. No manuscript edits performed.*
