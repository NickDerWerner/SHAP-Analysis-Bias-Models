"""ARR M1 revised linguistic taxonomy with explicit Other/Unassigned.

Preserves the original four-way decision order and lexicons from
babe_fig6_confound.categorize_word, but replaces the residual catch-all
return of Emotional/Evaluative with Other/Unassigned.

Legacy categorize_word_legacy() remains available for side-by-side audit.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

CATEGORIES_V2: List[str] = [
    "Explicit Bias Terms",
    "Framing/Reporting Verbs",
    "Function/Temporal Words",
    "Emotional/Evaluative",
    "Other/Unassigned",
]

CATEGORIES_LEGACY: List[str] = [
    "Emotional/Evaluative",
    "Explicit Bias Terms",
    "Framing/Reporting Verbs",
    "Function/Temporal Words",
]

EXPLICIT_BIAS_TERMS = {
    "racist",
    "antisemitic",
    "xenophobic",
    "sexist",
    "bigoted",
    "prejudice",
    "discriminatory",
    "stereotype",
    "stereotyping",
    "discrimination",
}

FRAMING_VERBS = {
    "claim",
    "claims",
    "claimed",
    "claiming",
    "allege",
    "alleges",
    "alleged",
    "alleging",
    "report",
    "reports",
    "reported",
    "reporting",
    "state",
    "states",
    "stated",
    "stating",
    "say",
    "says",
    "said",
    "saying",
    "suggest",
    "suggests",
    "suggested",
    "suggesting",
    "assert",
    "asserts",
    "asserted",
    "asserting",
    "maintain",
    "maintains",
    "maintained",
    "insist",
    "insists",
    "insisted",
    "insisting",
    "argue",
    "argues",
    "argued",
    "arguing",
    "call",
    "calls",
    "called",
    "calling",
    "describe",
    "describes",
    "described",
    "describing",
    "characterize",
    "characterizes",
    "characterized",
    "portray",
    "portrays",
    "portrayed",
}

FUNCTION_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "if",
    "of",
    "to",
    "in",
    "on",
    "at",
    "for",
    "from",
    "with",
    "by",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "having",
    "do",
    "does",
    "did",
    "doing",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "can",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "they",
    "them",
    "their",
    "there",
    "then",
    "than",
    "more",
    "most",
    "some",
    "any",
    "all",
    "each",
    "every",
    "other",
    "another",
    "much",
    "many",
    "very",
}

TEMPORAL_WORDS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "today",
    "yesterday",
    "tomorrow",
    "now",
    "then",
    "when",
    "before",
    "after",
    "during",
    "while",
    "since",
    "until",
    "ago",
    "recently",
    "previously",
    "earlier",
    "later",
    "next",
    "last",
    "year",
    "years",
    "month",
    "months",
    "week",
    "weeks",
    "day",
    "days",
    "hour",
    "hours",
    "time",
    "times",
}

EMOTIONAL_EVALUATIVE_TERMS = {
    "boasted",
    "bloated",
    "dubious",
    "relentlessly",
    "flagrantly",
    "misleading",
    "frantically",
    "sided",
    "mess",
    "quixotic",
    "lashed",
    "denigrate",
    "bizarre",
    "uglier",
    "blown",
    "nasty",
    "ranted",
    "heartlessness",
    "flippantly",
    "flippancy",
    "blasted",
    "junkies",
    "sandbag",
    "guzzling",
    "gruesome",
    "predominantly",
    "relentless",
    "fierce",
    "heated",
    "intense",
    "extreme",
    "drastic",
    "radical",
    "mockery",
    "ridicule",
    "scorn",
    "contempt",
    "disgust",
    "anger",
    "hate",
    "despise",
    "amazing",
    "terrible",
    "awful",
    "horrible",
    "wonderful",
    "fantastic",
    "incredible",
}

# Precedence order (first match wins).
PRECEDENCE: List[str] = [
    "Explicit Bias Terms",
    "Framing/Reporting Verbs",
    "Function/Temporal Words",
    "Emotional/Evaluative",
    "Other/Unassigned",
]


def normalize_word(word: str) -> str:
    return word.lower().strip('.,!?;:"()[]{}')


def categorize_word_v2(word: str) -> str:
    """Revised taxonomy: residual tokens → Other/Unassigned."""
    w = normalize_word(word)
    if not w:
        return "Other/Unassigned"

    if any(term in w for term in EXPLICIT_BIAS_TERMS):
        return "Explicit Bias Terms"
    if w in FRAMING_VERBS:
        return "Framing/Reporting Verbs"
    if w in FUNCTION_WORDS or w in TEMPORAL_WORDS:
        return "Function/Temporal Words"
    if any(term in w for term in EMOTIONAL_EVALUATIVE_TERMS):
        return "Emotional/Evaluative"
    if (w.endswith("less") or w.endswith("ful")) and len(w) > 4:
        return "Emotional/Evaluative"
    return "Other/Unassigned"


def categorize_word_legacy(word: str) -> str:
    """Original catch-all Emotional/Evaluative (verbatim logic)."""
    w = normalize_word(word)
    if any(term in w for term in EXPLICIT_BIAS_TERMS):
        return "Explicit Bias Terms"
    if w in FRAMING_VERBS:
        return "Framing/Reporting Verbs"
    if w in FUNCTION_WORDS or w in TEMPORAL_WORDS:
        return "Function/Temporal Words"
    if any(term in w for term in EMOTIONAL_EVALUATIVE_TERMS):
        return "Emotional/Evaluative"
    if (w.endswith("less") or w.endswith("ful")) and len(w) > 4:
        return "Emotional/Evaluative"
    return "Emotional/Evaluative"


def categorize_with_rule(word: str) -> Tuple[str, str]:
    """Return (v2_category, matched_rule_id) for documentation / QA."""
    w = normalize_word(word)
    if not w:
        return "Other/Unassigned", "empty"
    if any(term in w for term in EXPLICIT_BIAS_TERMS):
        return "Explicit Bias Terms", "explicit_substring"
    if w in FRAMING_VERBS:
        return "Framing/Reporting Verbs", "framing_exact"
    if w in FUNCTION_WORDS or w in TEMPORAL_WORDS:
        return "Function/Temporal Words", "function_or_temporal_exact"
    if any(term in w for term in EMOTIONAL_EVALUATIVE_TERMS):
        return "Emotional/Evaluative", "emotional_substring"
    if (w.endswith("less") or w.endswith("ful")) and len(w) > 4:
        return "Emotional/Evaluative", "emotional_suffix"
    return "Other/Unassigned", "residual_other"


EXAMPLES: Dict[str, List[str]] = {
    "Explicit Bias Terms": ["racist", "xenophobic", "stereotype"],
    "Framing/Reporting Verbs": ["claimed", "alleged", "said"],
    "Function/Temporal Words": ["the", "and", "yesterday", "years"],
    "Emotional/Evaluative": ["fierce", "misleading", "heartless", "wonderful"],
    "Other/Unassigned": ["Obama", "policy", "Cuba", "economy", "Democrats"],
}
