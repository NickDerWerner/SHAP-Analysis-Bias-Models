"""Word-level perturbation utilities for ARR M2 faithfulness pilot.

Masking protocol (documented for reproducibility):
- Words are selected from cached `word_attribs` entries (model-specific SHAP).
- Each selected surface string is located in the original sentence using
  left-to-right whole-token matching (whitespace/punct-aware), preferring
  an exact case-sensitive span, then case-insensitive.
- Default replacement uses the model tokenizer's `mask_token` when defined
  (RoBERTa: ``<mask>``); otherwise the word is deleted.
- Multi-word budgets replace the first unused occurrence of each distinct
  selected word; if a word string cannot be located, it is recorded as a
  failed alignment and skipped (budget may be under-filled — flagged).
- Special tokens and pure-whitespace are never selected.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


_WORD_SPLIT = re.compile(r"\S+")


@dataclass
class WordSpan:
    start: int
    end: int
    surface: str


def iter_whitespace_tokens(text: str) -> List[WordSpan]:
    return [WordSpan(m.start(), m.end(), m.group()) for m in _WORD_SPLIT.finditer(text)]


def normalize_for_match(s: str) -> str:
    return s.strip()


def locate_word_span(
    text: str, word: str, used: Optional[set] = None
) -> Optional[WordSpan]:
    """Find a whitespace token in `text` matching `word` (from word_attribs).

    Matching rules (in order):
    1. Exact equality with a whitespace token surface.
    2. Case-insensitive equality.
    3. Equality after stripping shared leading/trailing punctuation from both.
    """
    used = used or set()
    target = normalize_for_match(word)
    if not target:
        return None
    tokens = iter_whitespace_tokens(text)

    def strip_punct(s: str) -> str:
        return s.strip('.,!?;:"()[]{}\'""''')

    for mode in ("exact", "ci", "strip"):
        for tok in tokens:
            key = (tok.start, tok.end)
            if key in used:
                continue
            surf = tok.surface
            if mode == "exact" and surf == target:
                return tok
            if mode == "ci" and surf.lower() == target.lower():
                return tok
            if mode == "strip" and strip_punct(surf).lower() == strip_punct(target).lower():
                if strip_punct(surf):
                    return tok
    return None


def select_words(
    word_attribs: Sequence[dict],
    condition: str,
    k: int,
    rng,
) -> List[dict]:
    """Return up to k word_attrib dicts for a selection condition.

    Conditions:
      A_pos     — highest signed SHAP (biased-class positive evidence)
      B_neg     — most negative signed SHAP
      C_abs     — highest |SHAP|
      D_random  — random sample of size k from all word_attribs
      E_lowabs  — lowest |SHAP|
    """
    items = [wa for wa in word_attribs if str(wa.get("word", "")).strip()]
    if not items or k <= 0:
        return []
    k = min(k, len(items))

    if condition == "A_pos":
        ranked = sorted(items, key=lambda w: float(w["shap"]), reverse=True)
        # Prefer strictly positive; if fewer than k, fill with least-negative
        pos = [w for w in ranked if float(w["shap"]) > 0]
        if len(pos) >= k:
            return pos[:k]
        return ranked[:k]
    if condition == "B_neg":
        ranked = sorted(items, key=lambda w: float(w["shap"]))  # ascending
        neg = [w for w in ranked if float(w["shap"]) < 0]
        if len(neg) >= k:
            return neg[:k]
        return ranked[:k]
    if condition == "C_abs":
        ranked = sorted(items, key=lambda w: abs(float(w["shap"])), reverse=True)
        return ranked[:k]
    if condition == "D_random":
        pool = list(items)
        rng.shuffle(pool)
        return pool[:k]
    if condition == "E_lowabs":
        ranked = sorted(items, key=lambda w: abs(float(w["shap"])))
        return ranked[:k]
    raise ValueError(f"Unknown condition: {condition}")


def apply_mask(
    text: str,
    words: Sequence[dict],
    mask_token: str,
) -> Tuple[str, Dict]:
    """Replace selected words with mask_token; return (new_text, meta)."""
    used = set()
    replacements = []
    failed = []
    for wa in words:
        span = locate_word_span(text, wa["word"], used=used)
        if span is None:
            failed.append(wa["word"])
            continue
        used.add((span.start, span.end))
        replacements.append((span.start, span.end, wa["word"], span.surface))

    # Apply from right to left to preserve offsets
    new_text = text
    for start, end, want, surface in sorted(replacements, key=lambda x: -x[0]):
        new_text = new_text[:start] + mask_token + new_text[end:]

    # Collapse accidental double spaces from edge cases (mask token keeps place)
    meta = {
        "n_requested": len(words),
        "n_applied": len(replacements),
        "n_failed": len(failed),
        "failed_words": failed,
        "replaced": [
            {"word": w, "surface": s, "start": a, "end": b}
            for a, b, w, s in replacements
        ],
        "mask_token": mask_token,
    }
    return new_text, meta


def count_changed_whitespace_tokens(original: str, perturbed: str, mask_token: str) -> int:
    """Count how many whitespace tokens differ (approx. words changed)."""
    o = [t.surface for t in iter_whitespace_tokens(original)]
    p = [t.surface for t in iter_whitespace_tokens(perturbed)]
    # If lengths match, count positions that became mask or differ
    if len(o) == len(p):
        return sum(1 for a, b in zip(o, p) if a != b)
    # Fallback: count mask tokens in perturbed minus original
    return abs(len(o) - len(p)) + perturbed.count(mask_token)
