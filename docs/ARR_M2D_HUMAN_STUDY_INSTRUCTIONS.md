# M2D Human Study — Annotator Onboarding (short)

**Audience:** Two independent human annotators  
**Time:** ~2–3 hours for 120 sentences (varies)  
**Blind rule:** Sentence text only. No model outputs, no SHAP, no gold BASIL labels, no LLMs for labeling.

---

## What you receive

From `outputs/arr_m2d/annotator_pack/`:

1. `annotation_interface.html` — preferred (select text → exact character offsets)  
2. `items_BLIND.csv` — spreadsheet alternative  
3. This document + optional longer guide: `docs/ARR_M2C_HUMAN_ANNOTATION_GUIDE.md`

You will **not** receive any file with `GOLD_` columns.

---

## Your ID

You will be assigned an ID (e.g. `annA`, `annB`).

- Enter it in the HTML form **before** exporting.  
- Export filename: `basil_blind_annotations_<YOURID>.json`.  
- Do not share working notes with the other annotator until adjudication.

---

## Per sentence (5 questions)

1. **Bias present?** yes / no  
2. **Type:** lexical / informational / both / none  
3. **Spans:** minimal evidence spans (character-exact). Empty if none.  
4. **Needs article context?** yes / no / unsure  
5. **Uncertainty:** low / med / high (+ optional comment)

### Lexical vs informational (one sentence each)

- **Lexical:** loaded wording (*bombastic*, *despicable*, *knuckle-rapping*). Mark the words.  
- **Informational:** slant from facts/framing/omission without needing a loaded adjective. Mark the informational unit; set **Needs article context = yes** if you cannot judge fairly from the sentence alone.  
- **None:** ordinary reporting. Prefer none over inventing weak informational bias.  
- **Both:** only if both types are clearly present; use separate spans when possible.

Full examples: M2C annotation guide.

---

## How to annotate (HTML)

1. Open `annotation_interface.html` in Chrome/Firefox/Safari.  
2. Enter your annotator ID.  
3. For each item: select evidence in the gray box → **Add span**.  
4. Fill dropdowns.  
5. **Export annotations JSON** when finished (or periodically — state is in-memory only; export often).  
6. Return the JSON file to the study coordinator.

### Spreadsheet alternative

Fill `ann_*` columns in `items_BLIND.csv`. Verify `sentence_text[start:end] == span_text`. Add `annotator_id` column with your ID.

---

## Independence and adjudication

| Phase | Who | What |
|-------|-----|------|
| Primary | Each annotator alone | Full 120 items |
| Agreement | Analysts | Run `scripts/arr_m2d/human_agreement.py` on both exports |
| Adjudication | Annotators + optional third | Discuss disagreements **only after** both files are locked; record final consensus separately; **keep raw labels** |

Disagreement resolution order:

1. Presence (yes/no)  
2. Type  
3. Span boundaries (prefer minimal overlapping consensus span)  
4. Needs-context  

If unresolved: keep dual labels; flag `unresolved` in comments. Do not force agreement.

---

## What not to do

- Do not discuss specific items with the other annotator before both exports are submitted.  
- Do not open analyst CSVs or SHAP/HTML visualizations.  
- Do not paste sentences into ChatGPT/Claude/etc. for labels.  
- Do not “fix” spelling or quotes — match the displayed string exactly.

---

## Contact / deliverable

Return: `basil_blind_annotations_<YOURID>.json` (or completed CSV with `annotator_id`).  
Study status: **materials ready; annotation not started.**
