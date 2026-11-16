# ARR M4E-2a — Abstract Precision and Figure-Path Repair

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Status:** Complete (author review).  
**Scope:** Abstract wording (two scientific corrections) + two `\includegraphics` paths only.

---

## 1. Abstract — before / after

### Before

```text
Masking the highest-positive SHAP words ($k{=}2$) lowers
$P(\mathrm{biased})$ by about ${-}0.33$ (BD) and ${-}0.29$ (DR) on
paired BASIL sentences---more than random or low-$|$SHAP$|$ controls.
SHAP mass in BASIL lexical spans exceeds length-matched random
baselines; the apparent lexical--informational gap disappears for BD/DR
after coverage matching.
```

### After

```text
On paired BASIL sentences, masking the highest-positive SHAP words
($k{=}2$) changes $P(\mathrm{biased})$ by about ${-}0.33$ (BD) and
${-}0.29$ (DR); absolute probability changes exceed random and
low-$|$SHAP$|$ controls.
SHAP mass in BASIL lexical spans exceeds length-matched random
baselines; the apparent lexical--informational difference was not
sustained for BD/DR after matching annotation coverage.
```

### Evidence mapping

| Abstract assertion | Verified source | Meaning |
|--------------------|-----------------|---------|
| ≈ −0.33 (BD), −0.29 (DR) | M2B / M4B-1: A_pos $k{=}2$ ΔP **−0.327** / **−0.293** | Signed change in $P(\mathrm{biased})$ under high-positive masking — **not** a paired contrast vs random |
| Absolute changes exceed random / low-\|SHAP\| | M2B / M4B-1: high-\|SHAP\| vs random / low controls | Separate qualitative superiority statement; **no** numerical control Δ reported in Abstract |
| Lexical mass > length-matched random | M2C / M4B-2 | Excess absolute SHAP mass |
| Lex–inf difference not sustained after coverage matching | M2D / M4B-2 | Coverage-matched gap removed for BD/DR — **not** proof of lex≡inf equivalence |

---

## 2. Figure paths — before / after

| Location | Before | After | Asset check |
|----------|--------|-------|-------------|
| Intro `fig:figure1` (~L223) | `latex/figure1_redesign.pdf` | `figure1_redesign.pdf` | **Exists** at Overleaf root (30025 bytes) |
| Results `fig:smd_babe` (~L1133) | `latex/babe_fig3_with_fn.pdf` | `babe_fig3_with_fn.pdf` | **Exists** at Overleaf root (28261 bytes) |

### Directory inspection

- No `\graphicspath` in the project.  
- No `latex/` subdirectory.  
- Sibling BASIL figure already used root path `basil_fig3_with_fn.pdf` (unchanged).  
- No other `\includegraphics` paths modified.  
- Filenames/case/extensions verified exactly.

---

## 3. Diff scope

| Edited | Not edited |
|--------|------------|
| Abstract sentences (masking + coverage) | Title, captions, other Abstract findings |
| Two `\includegraphics` paths | Appendix, Related Work, Ethics, Results prose |
| `% RESOLVED M4E-2a` comment under Abstract | Figure file contents / designs |

---

## 4. Compilation

**UNVERIFIED** — no local LaTeX engine.  
Remaining compile risks (out of M4E-2a): appendix/content issues, open `\revnote`s, Overleaf full build.

---

## 5. Remaining blockers (not fixed here)

Per M4E-1: Appendix outdated calibration/pathway claims; Related Work T05/T06; title; Ethics T29; optional Significance condensation.

**Next proposed module:** M4E-2b Appendix reconciliation.
