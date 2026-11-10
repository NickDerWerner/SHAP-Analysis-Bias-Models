# Annotator Onboarding

**Audience:** Two independent human annotators  
**Time:** ~2–3 hours for 120 sentences (varies)  
**Blind rule:** Sentence text only. No model outputs, no SHAP, no gold labels, no LLMs for labeling.

---

## Your ID

You will be assigned an ID (e.g. `annA`, `annB`).

- Enter it in the annotation form **before** exporting
- Export filename: `basil_blind_annotations_<YOURID>.json`
- Do not share working notes with the other annotator until adjudication

---

## Per sentence

1. **Bias present?** yes / no  
2. **Type:** lexical / informational / both / none  
3. **Spans:** minimal evidence spans (character-exact). Empty if none  
4. **Needs article context?** yes / no / unsure  
5. **Uncertainty:** low / med / high (+ optional comment)

### Quick definitions

- **Lexical:** loaded wording (*bombastic*, *despicable*). Mark the words.
- **Informational:** slant from facts/framing/omission. Mark the unit; set needs-context = yes if the sentence alone is insufficient.
- **None:** ordinary reporting. Prefer none over inventing weak informational bias.
- **Both:** only if both types are clearly present; use separate spans when possible.

Full definitions and examples: [guide.md](guide.md).

---

## How to annotate

1. Open [annotate.html](annotate.html) in Chrome/Firefox/Safari (or use the website form built from these files).
2. Enter your annotator ID.
3. For each item: select evidence in the sentence → **Add span**.
4. Fill the dropdowns.
5. **Export annotations JSON** periodically (state may be in-memory only).
6. Return the JSON file to the study coordinator.

### Spreadsheet alternative

Fill `ann_*` columns in [items.csv](items.csv). Verify `sentence_text[start:end] == span_text`. Set `annotator_id`.

---

## Independence and adjudication

| Phase | Who | What |
|-------|-----|------|
| Primary | Each annotator alone | Full 120 items |
| Agreement | Analysts | Compare both exports |
| Adjudication | Annotators + optional third | Discuss disagreements **only after** both files are locked; keep raw labels |

Resolve in order: presence → type → span boundaries → needs-context.  
If unresolved: keep dual labels; flag `unresolved` in comments.

---

## What not to do

- Do not discuss specific items with the other annotator before both exports are submitted
- Do not use AI tools for labels
- Do not “fix” spelling or quotes — match the displayed string exactly

---

## Deliverable

Return: `basil_blind_annotations_<YOURID>.json` (or completed CSV with `annotator_id`).
