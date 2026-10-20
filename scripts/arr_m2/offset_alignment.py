"""Offset-aware mapping from SHAP Text-masker tokens to source-text words.

Design
------
1. Authoritative word boundaries come from the **source sentence**
   (whitespace-delimited non-space spans), not from `word_attribs` strings.
2. Each SHAP token (from cached ``tokens`` / ``shap_pos``) is greedily
   located in the source via its non-space character content, advancing a
   cursor so repeated tokens bind left-to-right.
3. Token SHAP mass is aggregated onto overlapping source word spans.
4. Perturbations mask complete source-word spans by character offsets.

This avoids brittle lookup of corrupted word_attribs surfaces
(e.g. ``100FALSE!!!``, ``““He``, ``him&``).

Failure rule
------------
If a SHAP token's content cannot be located in the remaining source text,
it is recorded as ``unaligned_token``. Words that receive no aligned SHAP
remain selectable only if they somehow get mass; selection operates on
words with finite shap. Sentence-level ``alignment_ok`` requires that
every non-space SHAP token content was located (coverage ≥ threshold).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


SPECIAL = {"[CLS]", "[SEP]", "<s>", "</s>", "[PAD]", "<pad>"}
_WS_WORD = re.compile(r"\S+")


@dataclass
class SourceWord:
    index: int
    start: int
    end: int
    surface: str
    shap: float = 0.0
    n_shap_tokens: int = 0
    shap_token_indices: List[int] = field(default_factory=list)

    @property
    def abs_shap(self) -> float:
        return abs(self.shap)


@dataclass
class AlignmentResult:
    text: str
    words: List[SourceWord]
    n_shap_tokens_content: int
    n_shap_tokens_aligned: int
    unaligned_token_indices: List[int]
    unaligned_token_strs: List[str]
    reconstruction_notes: List[str]

    @property
    def token_align_rate(self) -> float:
        if self.n_shap_tokens_content == 0:
            return 1.0
        return self.n_shap_tokens_aligned / self.n_shap_tokens_content

    @property
    def alignment_ok(self) -> bool:
        """Eligible for perturbation: all content SHAP tokens located."""
        return (
            self.n_shap_tokens_content > 0
            and len(self.unaligned_token_indices) == 0
            and len(self.words) > 0
        )


def source_word_spans(text: str) -> List[SourceWord]:
    words = []
    for i, m in enumerate(_WS_WORD.finditer(text)):
        words.append(
            SourceWord(index=i, start=m.start(), end=m.end(), surface=m.group())
        )
    return words


def _normalize_quotes(s: str) -> str:
    """Map curly/smart quotes and dashes to ASCII for soft matching."""
    table = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u00ab": '"',
        "\u00bb": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\ufeff": "",
    }
    out = []
    for ch in s:
        out.append(table.get(ch, ch))
    return "".join(out)


def _token_search_content(tok: str) -> Tuple[str, bool, bool]:
    """Return (content, had_leading_space_marker, had_trailing_space)."""
    if tok is None:
        return "", False, False
    raw = tok.replace("Ġ", " ").replace("▁", " ")
    lead = len(raw) > 0 and raw[0].isspace()
    trail = len(raw) > 0 and raw[-1].isspace()
    content = raw.strip()
    return content, lead, trail


def _find_content_from(
    text: str, content: str, cursor: int, soft: bool = True
) -> Optional[Tuple[int, int]]:
    """Find exact content in text at/after cursor; optional soft quote fold."""
    if not content:
        return None
    # Exact search from cursor
    idx = text.find(content, cursor)
    if idx >= 0:
        return idx, idx + len(content)
    if not soft:
        return None
    # Soft: search in quote-normalized space, map back via equal length assumption
    # Build normalized text with index map
    norm_chars = []
    idx_map = []  # norm pos -> original pos
    for i, ch in enumerate(text):
        n = _normalize_quotes(ch)
        if n == "":
            continue
        for c in n:
            norm_chars.append(c)
            idx_map.append(i)
    norm_text = "".join(norm_chars)
    norm_content = _normalize_quotes(content)
    # Map cursor to norm
    norm_cursor = 0
    while norm_cursor < len(idx_map) and idx_map[norm_cursor] < cursor:
        norm_cursor += 1
    j = norm_text.find(norm_content, norm_cursor)
    if j < 0:
        return None
    start_orig = idx_map[j]
    end_orig = idx_map[j + len(norm_content) - 1] + 1
    return start_orig, end_orig


def align_record(
    text: str,
    tokens: Sequence[str],
    shap_pos: Sequence[float],
    *,
    min_align_rate: float = 1.0,
) -> AlignmentResult:
    """Align SHAP tokens to source words; aggregate SHAP onto words."""
    words = source_word_spans(text)
    notes: List[str] = []
    unaligned_idx: List[int] = []
    unaligned_str: List[str] = []
    n_content = 0
    n_aligned = 0
    cursor = 0

    # Precompute word membership by char index
    char_to_word = [-1] * len(text)
    for wi, w in enumerate(words):
        for c in range(w.start, w.end):
            char_to_word[c] = wi

    for ti, (tok, sval) in enumerate(zip(tokens, shap_pos)):
        if tok in SPECIAL:
            continue
        content, lead, trail = _token_search_content(tok)
        if content == "":
            # whitespace-only / empty SHAP token — advance cursor over spaces
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            continue
        n_content += 1
        if lead:
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1

        found = _find_content_from(text, content, cursor, soft=True)
        if found is None and cursor > 0:
            # rare: token already consumed / out of order — search from 0 but
            # only unused region is hard; try from 0 as last resort without
            # moving past already-passed exclusive zones: still allow global
            found = _find_content_from(text, content, 0, soft=True)
            if found is not None:
                notes.append(f"token[{ti}]={content!r} matched with cursor reset")

        if found is None:
            unaligned_idx.append(ti)
            unaligned_str.append(tok)
            continue

        start, end = found
        n_aligned += 1
        # Assign full token SHAP to overlapping words proportional to overlap length
        overlap_words: Dict[int, int] = {}
        for c in range(start, end):
            wi = char_to_word[c] if c < len(char_to_word) else -1
            if wi >= 0:
                overlap_words[wi] = overlap_words.get(wi, 0) + 1
        if not overlap_words:
            # matched punctuation-only between words? attach to nearest left word
            left = start - 1
            while left >= 0 and char_to_word[left] < 0:
                left -= 1
            if left >= 0:
                overlap_words[char_to_word[left]] = max(1, end - start)
            else:
                unaligned_idx.append(ti)
                unaligned_str.append(tok)
                n_aligned -= 1
                continue

        total_ov = sum(overlap_words.values())
        for wi, ov in overlap_words.items():
            frac = ov / total_ov
            words[wi].shap += float(sval) * frac
            words[wi].n_shap_tokens += 1
            words[wi].shap_token_indices.append(ti)

        cursor = max(cursor, end)
        if trail:
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1

    result = AlignmentResult(
        text=text,
        words=words,
        n_shap_tokens_content=n_content,
        n_shap_tokens_aligned=n_aligned,
        unaligned_token_indices=unaligned_idx,
        unaligned_token_strs=unaligned_str,
        reconstruction_notes=notes,
    )
    # Optional soft gate via min_align_rate (default strict 1.0)
    if min_align_rate < 1.0 and result.token_align_rate >= min_align_rate:
        # already computed; alignment_ok property stays strict — callers may
        # use token_align_rate directly for soft gates
        pass
    return result


def select_source_words(
    words: Sequence[SourceWord],
    condition: str,
    k: int,
    rng,
) -> List[SourceWord]:
    items = [w for w in words if w.surface.strip()]
    if not items or k <= 0:
        return []
    k = min(k, len(items))
    if condition == "A_pos":
        ranked = sorted(items, key=lambda w: w.shap, reverse=True)
        pos = [w for w in ranked if w.shap > 0]
        return (pos[:k] if len(pos) >= k else ranked[:k])
    if condition == "B_neg":
        ranked = sorted(items, key=lambda w: w.shap)
        neg = [w for w in ranked if w.shap < 0]
        return (neg[:k] if len(neg) >= k else ranked[:k])
    if condition == "C_abs":
        return sorted(items, key=lambda w: w.abs_shap, reverse=True)[:k]
    if condition == "D_random":
        pool = list(items)
        rng.shuffle(pool)
        return pool[:k]
    if condition == "E_lowabs":
        return sorted(items, key=lambda w: w.abs_shap)[:k]
    raise ValueError(condition)


def apply_mask_offsets(
    text: str,
    words: Sequence[SourceWord],
    mask_token: str,
) -> Tuple[str, Dict]:
    """Mask selected source words by exact character offsets.

    Never substitutes a different word on failure — if a span is invalid,
    it is counted as failed and skipped (caller should treat incomplete
    budgets as excluded under the predefined rule).
    """
    replacements = []
    failed = []
    used = set()
    for w in words:
        key = (w.start, w.end)
        if key in used:
            failed.append(w.surface)
            continue
        if not (0 <= w.start < w.end <= len(text)):
            failed.append(w.surface)
            continue
        if text[w.start : w.end] != w.surface:
            failed.append(w.surface)
            continue
        used.add(key)
        replacements.append((w.start, w.end, w.surface, w.shap))

    new_text = text
    for start, end, surface, _ in sorted(replacements, key=lambda x: -x[0]):
        new_text = new_text[:start] + mask_token + new_text[end:]

    meta = {
        "n_requested": len(words),
        "n_applied": len(replacements),
        "n_failed": len(failed),
        "failed_words": failed,
        "replaced": [
            {"word": s, "start": a, "end": b, "shap": sh}
            for a, b, s, sh in replacements
        ],
        "mask_token": mask_token,
        "complete_budget": len(replacements) == len(words) and len(failed) == 0,
    }
    return new_text, meta
