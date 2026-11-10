# Bias Evidence Annotation Guide

**Purpose:** Judge whether a news sentence contains linguistic bias evidence, what type, and which exact character spans justify that judgment.

**Blind rule:** You see **sentence text only**. Do not use model predictions, SHAP highlights, gold labels, or LLM assistants for labeling.

**Sample:** 120 sentences, shuffled, balanced across lexical, informational, both-type, and non-biased controls.

---

## Task (per item)

1. **Bias present?** `yes` / `no`
2. **Bias type:** `lexical` / `informational` / `both` / `none`
3. **Evidence spans:** one or more exact character spans that justify the judgment (empty if none)
4. **Needs article context?** `yes` / `no` / `unsure` — would you need surrounding article text to decide confidently?
5. **Uncertainty:** `low` / `med` / `high`
6. **Comments:** optional free text

---

## Definitions (adapted from BASIL)

### Lexical bias

Bias signaled by **wording choice** inside the sentence: loaded, subjective, or evaluative language that colors the reader’s view beyond bare reporting.

Mark as lexical when:

- Adjectives/adverbs or nouns carry clear evaluative load (*bombastic*, *despicable*, *bigoted*, *fake news* as speaker framing, *wimp*)
- Metaphorical or figurative attacks that encode judgment
- Quotes that themselves contain loaded language **and** you judge that language to be the bias evidence (still lexical if the cue is lexical)

**Example (lexical):**

> Trump issued a **bombastic** call for President Obama to resign…

Span: `bombastic` (and similar loaded terms). The factual claim that he called for resignation is not itself lexical bias.

### Informational bias

Bias from **what is stated, omitted, emphasized, or framed** as information—not primarily from a single loaded word. Includes selective facts, one-sided framing, implied causality, or juxtaposition that steers interpretation.

Mark as informational when:

- The sentence presents facts or claims in a way that favors one side without needing a clearly loaded lexical item
- Framing verbs + content together create slant (*claimed*, *insisted* can be informational when they cast doubt, even if mild)
- You suspect bias mainly because of **missing counter-context** → still mark informational **and** set **Needs article context = yes**

**Example (informational):**

> Democrats have been pounding LePage, saying that he needs to step down and **questioning his mental abilities**.

The framing of Democrats’ attack and the highlighted content can be informational even without a single pejorative adjective from the journalist’s voice.

### Both

The sentence has **distinct** lexical *and* informational evidence. Mark separate spans when possible. Prefer `both` only if both types are clearly present—not as a default hedge.

### None / non-biased

Straight reporting, attributed quotes without added slant, or procedural/factual content without persuasive framing. If unsure between weak informational and none, prefer **Needs article context = unsure/yes** and raise **Uncertainty**.

---

## Span rules (critical for offsets)

1. Select the **minimal continuous** substring that justifies the judgment. Prefer the biased cue, not the whole sentence, unless the whole sentence is the informational unit.
2. Spans are **half-open character offsets** `[start, end)` into the exact displayed sentence string.
3. Do **not** “correct” typos or normalize quotes; match the displayed text.
4. Multiple spans allowed; order does not matter.
5. If bias present = no, leave spans empty and type = `none`.
6. Quoted speech: annotate the biased language if it constitutes the bias evidence; do not mark the entire quote by default.

---

## Decision tips

| Situation | Guidance |
|-----------|----------|
| Strong loaded adjective, rest neutral | Lexical; short span on the word |
| Neutral wording, one-sided fact selection | Informational; may need context = yes |
| Loaded word **and** selective framing | Both; two spans if separable |
| Cannot decide without the article | Needs context = yes; still give best sentence-local type |
| Pure attribution of someone else’s insult | Often lexical on the insult words |
| Borderline | Uncertainty = med/high; do not invent bias |

---

## What not to do

- Do not consult model outputs or SHAP visualizations
- Do not paste sentences into ChatGPT/Claude/etc. for labels
- Do not expand spans to “look nicer” for metrics
- Do not mark bias solely because the topic is political
