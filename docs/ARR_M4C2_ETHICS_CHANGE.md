# ARR M4C-2 — Ethics and Human Annotation Transparency

**Date:** 2026-11-16  
**Manuscript:** `/Users/go52nom/Downloads/overleaf_latex/acl_latex.tex`  
**Scope:** `\section{Ethical Considerations}` only.  
**Status:** Partial (verified protocol + responsible use in TeX; procedural consent/IRB/etc. unresolved).

---

## Word count

| | Approx. words (comments stripped) |
|--|--:|
| Before | 196 |
| After | ~310 |

---

## Evidence map (procedural claims in Ethics)

| Claim in Ethics | Verified? | Source |
|-----------------|-----------|--------|
| Two independent annotators | **Yes** | M3R; `annA`/`annB` JSON; Methods |
| 120 BASIL sentences; seed-7 30×4 strata | **Yes** | `human_materials_verification.json`; Methods |
| Blind: no model/SHAP/gold in annotator view | **Yes** | Guide; pack README; verification checks |
| Fields: presence, type, spans, needs_context, uncertainty | **Yes** | Guide; JSON schema |
| Shared written instructions + interface/CSV pack | **Yes** | `README_ANNOTATORS.txt`; M2D instructions |
| Instructed to work independently pre-adjudication | **Yes** | M2D instructions |
| Anonymous study IDs only in JSON (`annA`/`annB`) | **Yes** | Annotation files (no name/email fields) |
| Not a fused consensus gold standard | **Yes** | Methods + M3R reporting |
| Yes without localizable spans excluded from span/SHAP metrics | **Yes** | M3R; Results |
| Responsible-use: not objective journalism verdicts; FP risk; HITL; SHAP ≠ verified reasoning | **Yes** (interpretive, scoped) | Discussion/Limitations/Results framing |

---

## Unverified — author confirmation checklist

Do **not** invent answers. Confirm for camera-ready / checklist:

1. **Recruitment / roles:** Who were the annotators (e.g., authors, students, hired raters)? Expertise?  
2. **Voluntary participation:** Were they free to decline?  
3. **Compensation:** Paid / unpaid / course credit / none?  
4. **Informed consent:** Was written or oral consent obtained? What were they told about use of labels?  
5. **Ethics review:** IRB/ethics committee required / obtained / waived / not sought? Institution?  
6. **Withdrawal:** Could annotators withdraw data after submission?  
7. **PII beyond study IDs:** Any side channels (email threads, spreadsheets with names)?  
8. **Release plan:** Will raw annotations be public, restricted, or private? Access control?  
9. **Licenses:** BABE/BASIL/model Hub licenses; code license; redistributability of annotations.  
10. **Reproducibility extras (T29 residual):** pinned Hub revisions / hyperparameters (may belong in checklist, not Ethics prose).

Manuscript placeholder: `\revnote{TODO P1 | Human-study procedural disclosures}{...}`.

---

## T29 status

| Component | Status |
|-----------|--------|
| Human-in-loop / misuse warnings | **Done** |
| Human-study transparency (verified protocol) | **Done** |
| Consent / IRB / compensation / recruitment | **Unresolved** (TODO kept) |
| Artifact licenses / repro checklist | **Unresolved** (same TODO + future checklist pass) |

**T29 = partially resolved.** Do not mark fully complete until author checklist is answered.

---

## Proposed later (not edited this module)

- Methods: one sentence on consent/IRB once authors confirm.  
- Limitations: already covers yes∅spans / cache∩ (M4C-1).  
- Appendix: annotation guide excerpt.  
- ARR Responsible NLP checklist update for human subjects.

---

## Diff scope

Ethics section only. No Methodology/Results/Discussion/Limitations/Abstract/Intro/Conclusion/Appendix edits.

---

## Compilation

**UNVERIFIED** (no TeX engine on PATH).
