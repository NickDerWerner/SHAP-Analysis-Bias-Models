# Human annotation website pack

Self-contained files for building an annotator-facing website. **No gold labels, model predictions, or SHAP data.**

## Contents

| File | Role |
|------|------|
| [onboarding.md](onboarding.md) | Short start-here instructions |
| [guide.md](guide.md) | Full annotation definitions and span rules |
| [annotate.html](annotate.html) | Working annotation UI (120 items embedded; exports JSON) |
| [items.json](items.json) | Same 120 items as structured data for a custom UI |
| [items.csv](items.csv) | Spreadsheet fallback + blank `ann_*` columns |

## Suggested site pages

1. **Onboarding** ← `onboarding.md`
2. **Guide** ← `guide.md`
3. **Annotate** ← `annotate.html`, or rebuild the form loading `items.json`

## Expected export schema (JSON)

Each item object should include:

- `annotator_id` (string)
- `item_id`, `canonical_id`
- `bias_present`: `yes` | `no`
- `bias_type`: `lexical` | `informational` | `both` | `none`
- `spans`: `[{start, end, text}, ...]` (character offsets into the exact sentence)
- `needs_context`: `yes` | `no` | `unsure`
- `uncertainty`: `low` | `med` | `high`
- `comments` (optional)

## Notes

- 120 items, seed 7, shuffled; balanced 30/30/30/30 across strata (labels not exposed here).
- Character offsets must match the exact `text` / `sentence_text` string.
- Keep annotators independent until both exports are submitted.
