# ARR M4E-5a — Anonymous Submission Packaging

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Macros:** `/Users/go52nom/Downloads/overleaf_latex/revision_macros.tex`  
**Scope:** Anonymity packaging only — no scientific claim/result edits.  
**Status:** Complete (author review). Compiled PDF anonymity **UNVERIFIED**.

---

## 1. Anonymity inventory

| Item | Location | Treatment |
|------|----------|-----------|
| `\author` names, TUM affiliation, email | Preamble `\author{…}` | **Kept in source** for camera-ready; ACL `[review]` replaces display with “Anonymous ACL submission” via `acl.sty` `\outauthor` |
| `\usepackage[review]{acl}` | Preamble L6 | **Already set** (official review mode) |
| GitHub `NickDerWerner/…` | Intro (was active `\url`) | **Omitted** from review text; URL preserved in `%` comment for restore |
| Code pointer | Intro | Neutral: “Code and artifacts will be released with the camera-ready version.” |
| PDF metadata | After `\begin{document}` | `\hypersetup{pdfauthor={}, pdftitle={}, …}` when `\ifacl@anonymize` |
| `\revnote` yellow TODOs | 8 call sites | **Suppressed** under `\ifacl@anonymize` in `revision_macros.tex`; source notes retained |
| ORCID helper macro | Preamble | Unused in body; no ORCID IDs present |
| Acknowledgments / funding | — | None present |
| Third-party HF / Anthology URLs | Methods footnotes, cites | **Retained** (not author-identifying) |
| Self-work cite `ghosh2025` | Intro/Methods | **Retained** (third-person model name + cite; not “we previously showed”) |
| Co-author venue cites (e.g. Dhaini/Kasneci) | Related Work | **Retained** as scholarly citations |

---

## 2. Exact source changes

### `acl_latex.tex`
1. **Title** updated to recommended string; old title kept in `%` comment.  
2. Comment documenting ACL review-mode author hiding.  
3. `\hypersetup{pdfauthor={}, …}` gated on `\ifacl@anonymize`.  
4. Identifying GitHub `\url` commented; neutral release sentence for review.  
5. `% RESOLVED M4E-5a` note.

### `revision_macros.tex`
- `\revnote` is a no-op when `\ifacl@anonymize` is true; otherwise unchanged yellow `\todo`.

**Not edited:** Abstract/Methods/Results/Discussion/Limitations/Ethics/Appendix scientific prose; bibliography entries; numerical results.

---

## 3. Repository-link handling

| Link | Action |
|------|--------|
| `https://github.com/NickDerWerner/SHAP-Analysis-Bias-Models` | Removed from rendered review text; stored in comment for camera-ready restore |
| Invented Anonymous GitHub URL | **Not used** (authors did not provide one) |

---

## 4. Title decision

| | Text |
|--|------|
| **Before** | Explaining News Bias Detection: A Comparative SHAP Analysis of Transformer Model Decision Mechanisms |
| **After (applied)** | Evaluating SHAP Explanations for News Bias Detection: Prediction Sensitivity and Human Evidence Alignment |

Applied under M4E-5a approval (recommended title in approved module scope).

---

## 5. Review annotation handling

| Check | Status |
|-------|--------|
| `\revnote` call sites remaining in source | **8** (T08, T09, optional×4, T24, T29) |
| Visible in review PDF | **Intended suppressed** via `\ifacl@anonymize` |
| TODO audit still open | **Yes** — T08/T09/T24/T29 not marked resolved |
| Scientific prose removed with notes? | **No** — only macro expansion gated |

---

## 6. Remaining anonymity risks

1. **Compiled PDF not inspected** — visual anonymity UNVERIFIED.  
2. Author names remain in **TeX source** (intentional ACL pattern); ensure the uploaded PDF is built with `[review]`, not `[final]`/`[preprint]`.  
3. Overleaf project name / supplementary zip filenames may identify authors — check outside this file.  
4. Figure file metadata (PDF/PNG author fields) not inspected.  
5. Public non-anonymous preprint (prior ARR form listed arXiv) is a separate policy choice; not edited here.  
6. Citing `ghosh2025` / Kasneci-linked works can allow educated guesses; allowed under ACL citation rules if not phrased as revealing self-reference.

**Do not claim complete anonymity without Overleaf PDF inspection.**

---

## 7. Compilation status

**UNVERIFIED** — no local `pdflatex`/`xelatex`/`latexmk`.

Authors should compile on Overleaf and confirm: “Anonymous ACL submission”; no GitHub username; no yellow TODOs; new title on page 1.

---

## 8. Restore-to-camera-ready instructions

1. Change `\usepackage[review]{acl}` → `\usepackage[final]{acl}` (or `[preprint]`).  
2. Restore code URL block (uncomment the `% Code and artifacts:` / `\url{…}` lines; remove the temporary “will be released…” sentence if desired).  
3. Keep or drop `\input{revision_macros}` — under `[final]`, `\revnote` would show again; **delete remaining `\revnote`s** or remove the input before camera-ready.  
4. Title: keep the M4E-5a title unless authors choose otherwise.  
5. `\author{…}` already contains camera-ready names/affiliation/email.  
6. Re-enable PDF metadata if desired (or leave empty).  
7. Complete T29 Ethics answers and Responsible NLP checklist before final upload.

---

## 9. Scientific integrity

Unresolved T08/T09/T24/T29 remain open in the TODO audit. Limitations/Ethics scientific text untouched. No experiments run.
