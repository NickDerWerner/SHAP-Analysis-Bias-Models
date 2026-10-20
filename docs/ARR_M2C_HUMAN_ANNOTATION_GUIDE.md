# BASIL Bias Evidence — Blind Annotation Guide (M2C)

**Purpose:** Collect independent human judgments of whether a news sentence contains linguistic bias evidence, what type, and which exact character spans justify that judgment.  
**Blind rule:** Annotators see **sentence text only**. Do not consult model predictions, SHAP highlights, gold BASIL labels, or LLM assistants for labeling.

**Materials**

| File | Use |
|------|-----|
| `outputs/arr_m2c/human_annotation_interface.html` | Preferred: select text → capture offsets → Export JSON |
| `outputs/arr_m2c/human_annotation_sample_BLIND.csv` | Spreadsheet alternative (fill `ann_*` columns) |
| `outputs/arr_m2c/human_annotation_sample.csv` | Analyst-only (contains `GOLD_*`; do **not** give to annotators) |

**Sample:** 120 sentences, seed 7, balanced 30/30/30/30 across lexical-only, informational-only, both-type (BASIL), and non-biased controls. Items are shuffled.

**IAA plan:** Ideally two annotators label all 120. If capacity is limited, double-annotate a fixed subset of ≥40 stratified items and single-annotate the rest. Compute agreement on bias presence, bias type, and span overlap (e.g. character F1 / IoU) after collection.

---

## Task (per item)

1. **Bias present?** `yes` / `no`  
2. **Bias type:** `lexical` / `informational` / `both` / `none`  
3. **Evidence spans:** one or more exact character spans that justify the judgment (empty if none).  
4. **Needs article context?** `yes` / `no` / `unsure` — would you need surrounding article text (other sentences, headline, omitted facts) to decide confidently?  
5. **Uncertainty:** `low` / `med` / `high`  
6. **Comments:** optional free text.

---

## Definitions (adapted from BASIL)

### Lexical bias

Bias signaled by **wording choice** inside the sentence: loaded, subjective, or evaluative language that colors the reader’s view beyond bare reporting.

**Mark as lexical when:**

- Adjectives/adverbs or nouns carry clear evaluative load (*bombastic*, *despicable*, *bigoted*, *fake news* as speaker framing, *wimp*).  
- Metaphorical or figurative attacks that encode judgment.  
- Quotes that themselves contain loaded language **and** you judge that language to be the bias evidence (still lexical if the cue is lexical).

**Example (lexical):**  
> Trump issued a **bombastic** call for President Obama to resign…

Span: `bombastic` (and similar loaded terms). The factual claim that he called for resignation is not itself lexical bias.

### Informational bias

Bias from **what is stated, omitted, emphasized, or framed** as information—not primarily from a single loaded word. Includes selective facts, one-sided framing, implied causality, or juxtaposition that steers interpretation.

**Mark as informational when:**

- The sentence presents facts or claims in a way that favors one side without needing a clearly loaded lexical item.  
- Framing verbs + content together create slant (*claimed*, *insisted* can be informational when they cast doubt, even if mild).  
- You suspect bias mainly because of **missing counter-context** you would expect in fair coverage → still mark informational **and** set **Needs article context = yes**.

**Example (informational):**  
> Democrats have been pounding LePage, saying that he needs to step down and **questioning his mental abilities**.

The framing of Democrats’ attack and the highlighted content can be informational even without a single pejorative adjective from the journalist’s voice.

### Both

The sentence has **distinct** lexical *and* informational evidence. Mark separate spans when possible (one lexical, one informational). Prefer `both` only if both types are clearly present—not as a default hedge.

### None / non-biased

Straight reporting, attributed quotes without added slant, or procedural/factual content without persuasive framing. If unsure between weak informational and none, prefer **Needs article context = unsure/yes** and raise **Uncertainty**.

---

## Span rules (critical for offsets)

1. Select the **minimal continuous** substring that justifies the judgment. Prefer the biased cue, not the whole sentence, unless the whole sentence is the informational unit.  
2. Spans are **half-open character offsets** `[start, end)` into the exact `sentence_text` string (same as HTML selection).  
3. Do **not** “correct” typos or normalize quotes; match the displayed text.  
4. Multiple spans allowed; order does not matter.  
5. If bias present = no, leave spans empty and type = `none`.  
6. Quoted speech: annotate the biased language if it constitutes the bias evidence; do not mark the entire quote by default.

### HTML form

1. Open `human_annotation_interface.html` in a browser (local file is fine).  
2. Drag-select text in the gray sentence box → **Add span from selection**.  
3. Fill dropdowns; optional comments.  
4. **Export annotations JSON** → save as `annotator_<name>_basil_blind.json`.  
5. Do not clear browser storage mid-session without exporting (state is in-memory only).

### CSV form

Fill columns: `ann_bias_present`, `ann_bias_type`, `ann_span1_start/end/text`, `ann_span2_*` (add rows/columns if >2 spans), `ann_needs_article_context`, `ann_uncertainty`, `ann_comments`.  
Verify `ann_span*_text == sentence_text[start:end]` exactly.

---

## Decision tips

| Situation | Guidance |
|-----------|----------|
| Strong loaded adjective, rest neutral | Lexical; short span on the word |
| Neutral wording, one-sided fact selection | Informational; may need context = yes |
| Loaded word **and** selective framing | Both; two spans if separable |
| Cannot decide without the article | Needs context = yes; still give best sentence-local type |
| Pure attribution of someone else’s insult | Often lexical on the insult words; comment if journalist framing is the issue |
| Borderline | Uncertainty = med/high; do not invent bias |

---

## What not to do

- Do not peek at `GOLD_*` columns or model/SHAP outputs.  
- Do not paste sentences into ChatGPT/Claude/etc. for labels.  
- Do not expand spans to “look nicer” for metrics.  
- Do not mark bias solely because the topic is political.

---

## After annotation (analysts)

1. Collect independent JSON/CSV files; keep annotator IDs separate.  
2. Compute agreement before adjudication.  
3. Optional adjudication pass for disagreements; keep raw labels.  
4. Score human spans vs BASIL gold and vs SHAP top-k **only after** blinding is lifted.  
5. Report human study as complete only when labels and IAA are in hand.

**Status:** Study materials prepared. Human annotation **not** completed as of this document.
