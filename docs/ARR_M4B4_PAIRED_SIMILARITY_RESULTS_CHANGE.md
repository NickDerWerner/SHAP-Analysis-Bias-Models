# ARR M4B-4 — Paired Cross-Model Attribution Similarity Results

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** Results — rewrite magnitude-section similarity claims; new paired-similarity subsection + table; soften error-overlap mechanism wording.  
**Status:** Complete (author review). No new experiments.

---

## Evidence sources

| Artifact | Path |
|----------|------|
| Code | `scripts/arr_m1/run_paired_alignment.py` |
| BASIL BD–DR summary | `outputs/arr_m1/paired/basil_pair_summary.csv` |
| BASIL sentence pairs | `outputs/arr_m1/paired/basil_paired_bd_dr.csv` (n=371) |
| BASIL all3 | `outputs/arr_m1/paired/basil_paired_all3.csv` (n=60) |
| BABE summary | `outputs/arr_m1/paired/babe_paired_similarity_summary.csv` |
| Coverage | `outputs/arr_m1/paired/{babe,basil}_coverage.csv` |
| Methods change | `docs/ARR_M4A8E_SIMILARITY_METHOD_CHANGE.md` |

**Not used:** pre-M1 paper n=100 stratum; unpaired pool comparisons as architecture effects.

---

## Metric definitions (verified in code)

| Metric | Definition |
|--------|------------|
| Jaccard@20 | Top-20 words by \|SHAP\|; lowercased + light punct strip; \|A∩B\|/\|A∪B\| per sentence; **median** over sentences |
| Cosine \|SHAP\| | Word-type bags of abs SHAP; L1-normalize; cosine on union keys; **median** |
| mean \|SHAP\| | Mean abs word SHAP over **all** words in the sentence (not intersection-only) |
| Pairing | BABE: `babe:`+SHA256(text)[:16]; BASIL: `basil:uuid\|outlet\|sent` |
| Uncertainty | **None** computed for similarity medians |

---

## Number → source map

### BASIL BD–DR (`basil_pair_summary.csv`)

| Subset | n | Med Jac@20 | Med cos\|SHAP\| | Med mean\|SHAP\| BD | DR | Ratio BD/DR |
|--------|--:|-----------:|---------------:|--------------------:|---:|------------:|
| shared FP | 112 | 0.818 | 0.855 | 0.0501 | 0.0388 | ≈1.29 |
| shared FN | 104 | 0.727 | 0.781 | 0.0344 | 0.0173 | ≈1.99 |
| all ∩ | 371 | 0.762 | 0.820 | 0.0410 | 0.0316 | — |

### BABE all3 intersection (`babe_paired_similarity_summary.csv`)

| Pair | n | Med Jac@20 | Med cos\|SHAP\| |
|------|--:|-----------:|---------------:|
| BD–DR | 59 | 0.625 | 0.783 |
| BD–Deb | 59 | 0.538 | 0.666 |
| DR–Deb | 59 | 0.500 | 0.627 |

### BASIL all3 (exploratory; prose only)

| Pair | n | Med Jac@20 | Med cos\|SHAP\| |
|------|--:|-----------:|---------------:|
| BD–DR | 60 | 0.799 | 0.848 |
| BD–Deb | 60 | 0.659 | 0.773 |
| DR–Deb | 60 | 0.604 | 0.729 |

---

## Manuscript edits

### A. `\subsection{SHAP Magnitude Patterns}` (trimmed)

**Removed / corrected:**
- “On 100 shared FP… share 81% of their top-20…” (wrong n; wrong Jaccard interpretation)
- “33% higher magnitude … to those shared words” (unsupported intersection-restricted mass; ratio ≈29% on whole-sentence mean \|SHAP\|)
- “same-mechanism detection with different calibration”
- “attend to the same lexical categories… calibration-vs-mechanism… across architecture families”
- T20 `\revnote`

**Retained (descriptive magnitude):** TN/FN three-model median ordering + MWU pointer; brief Figure~1 qualitative pointer to new section.

### B. New `\subsection{Paired Cross-Model Attribution Similarity}` `\label{sec:paired_similarity}`

+ `Table~\ref{tab:paired_sim}` (BASIL shared FP/FN/all ∩; BABE BD–DR all3).

### C. Error-overlap block (partial)

- Softened “All three models tend to err on the same content” → co-error ≠ mechanism; cross-ref paired similarity.
- **T25** `\revnote` **retained** (threshold/bin re-analysis not done).

---

## Unsupported claims removed from edited text

| Old claim | Disposition |
|-----------|-------------|
| Jaccard ≈ “81% of top-20 tokens shared” | Corrected to median Jac@20 = \|∩\|/\|∪\| |
| n=100 shared FP/FN | → 112 / 104 |
| 33% higher mag on shared words | → ≈1.29× whole-sentence mean \|SHAP\| |
| Same-mechanism / different calibration (from overlap) | Removed |
| Architecture-family mechanism extension | Removed |
| Forced all-3 same-cell redesign | Still out of scope (not claimed complete) |
| JS / signed / random baselines | Still out of scope |

---

## TODOs

| ID | Status |
|----|--------|
| **T20** Results | **Resolved** |
| T14 Methods | Already resolved (M4A-8e) |
| T25 Error overlap thresholds | **Open** |
| T22 Em/Ev | **Open** |
| T26 Two-pathway | **Open** |

---

## Diff scope

Intended: magnitude-section similarity paragraphs; new similarity subsection+table; one softener sentence in error-overlap block.  
Not edited: Abstract, Intro, Methods, gold-span/human/faithfulness Results, Em/Ev category tables, Conclusion, Limitations, Ethics, Appendix.

---

## Compilation

**UNVERIFIED** — no TeX engine on PATH.
