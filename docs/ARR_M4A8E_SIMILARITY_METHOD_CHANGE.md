# M4A-8e Change Record — Paired Attribution Similarity (T14 Methods)

**Date:** 2026-11-16  
**File:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** `\subsection{Analysis Framework}` — new `\paragraph{Paired attribution similarity.}`; T14 `\revnote` removed.  
**Not edited:** Results, Abstract, Intro, appendices, other Methods subsections.

---

## Metrics actually implemented (M1)

| Metric | Definition in code | Status |
|--------|-------------------|--------|
| Jaccard@20 | Top-20 words by \|SHAP\|; lowercased, light punct strip; \|A∩B\|/\|A∪B\| | **Done** |
| Cosine of \|SHAP\| | Bags of abs SHAP by word type; L1-normalize; cosine on union keys | **Done** |
| Pairing IDs | BABE: `babe:`+SHA256(text)[:16]; BASIL: `basil:uuid\|outlet\|sent` | **Done** |
| BASIL BD∩DR subsets | all intersection; shared FP; shared FN | **Done** |
| BABE/BASIL all3 overlaps | Pairwise Jaccard/cosine on n=59 / n=60 | **Done** (limited) |
| Jensen–Shannon | — | **Not run** → deferred / out of scope |
| Signed normalized vector suite | — | **Not run** → deferred |
| Random/baseline similarity for token overlap | — | **Not run** → deferred |
| Forced all-3 same-cell redesign | — | **Not run** → out of scope |

**Code:** `scripts/arr_m1/run_paired_alignment.py` (`top_k_words`, `jaccard`, `cosine_abs_aligned`).  
**Outputs:** `outputs/arr_m1/paired/*`.

Effective *n* (methods state design, not result values): see Table~\ref{tab:eval_populations} and M1 coverage (BABE all3 59; BASIL BD∩DR 371 / shared FP 112 / shared FN 104; all3 60).

---

## T14 status

| Request in old TODO | Disposition |
|---------------------|-------------|
| Top-k Jaccard | **Methods resolved** |
| Cosine of abs attributions | **Methods resolved** |
| Same sentences / pairing | **Methods resolved** |
| JS / signed vectors / random baselines | **Deferred / out of scope** (never implemented) |
| Results rewrite of similarity claims | **Pending** (T20 Results `\revnote`) |

---

## Scientific safeguards in TeX

- Paired IDs only; no unpaired-pool pairing.  
- Overlap ≠ mechanism / semantic equivalence (stated).  
- No numerical results in Methods.  
- No “surprising high overlap” rhetoric.

---

## Downstream

| Item | Action |
|------|--------|
| Results shared-FP Jaccard ~0.81 | Retain if framed as paired BD–DR; verify n |
| “Same mechanism” language | Remove in Results/Conclusion (still open) |
| T20 all-3 forced redesign | Out of scope; disclose limited all3 n |

---

## Word count

Paired-similarity paragraph ≈ **114** words. T14 TODO removed (−1 `\revnote`; open count **22**).

---

## Verification

- Cosine **was** computed (do not omit).  
- Compile: **UNVERIFIED**.  
- Diff: Analysis Framework only.
