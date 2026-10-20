"""Tokenizer-aware and tokenizer-agnostic word aggregation utilities (ARR M1).

Provides:
- reaggregate_charspan: DeBERTa fix path (may drop whitespace SHAP mass)
- reaggregate_additive: preserves full token SHAP mass by assigning each
  token's SHAP entirely to its non-space surface (or to a synthetic
  <space> bucket when the token is whitespace-only)
- diagnostics for additivity and source-text alignment
"""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple


SPECIAL = {"[CLS]", "[SEP]", "<s>", "</s>"}


def reaggregate_charspan(
    tokens: Sequence[str], shap_values: Sequence[float]
) -> List[Dict[str, float]]:
    """Original fix script: per-char split; whitespace SHAP excluded from words."""
    text_chars: List[str] = []
    char_shap: List[float] = []
    for tok, s in zip(tokens, shap_values):
        if tok in SPECIAL:
            continue
        clean = tok.replace("Ġ", " ").replace("▁", " ")
        if not clean:
            continue
        per_char = float(s) / len(clean)
        for c in clean:
            text_chars.append(c)
            char_shap.append(per_char)

    word_attribs: List[Dict[str, float]] = []
    i = 0
    n = len(text_chars)
    while i < n:
        while i < n and text_chars[i].isspace():
            i += 1
        start = i
        while i < n and not text_chars[i].isspace():
            i += 1
        if start < i:
            word = "".join(text_chars[start:i])
            total = float(sum(char_shap[start:i]))
            word_attribs.append({"word": word, "shap": total})
    return word_attribs


def reaggregate_additive(
    tokens: Sequence[str], shap_values: Sequence[float]
) -> Tuple[List[Dict[str, float]], Dict[str, float]]:
    """Word aggregation that preserves Σ token SHAP (excl. special tokens).

    For each token:
      - strip Ġ/▁ → space, then strip leading/trailing whitespace for the
        surface word contribution;
      - if the cleaned token has non-space content, assign the *entire*
        token SHAP to that surface word (continuations glue);
      - pure-whitespace tokens accumulate into meta['whitespace_shap'].

    Returns (word_attribs, meta) where meta includes:
      token_sum, word_sum, whitespace_shap, special_shap, residual
    """
    word_attribs: List[Dict[str, float]] = []
    cur_word = ""
    cur_sum = 0.0
    whitespace_shap = 0.0
    special_shap = 0.0
    token_sum = 0.0

    def flush():
        nonlocal cur_word, cur_sum
        if cur_word:
            word_attribs.append({"word": cur_word, "shap": float(cur_sum)})
        cur_word = ""
        cur_sum = 0.0

    for tok, s in zip(tokens, shap_values):
        s = float(s)
        if tok in SPECIAL:
            special_shap += s
            continue
        token_sum += s
        raw = tok.replace("Ġ", " ").replace("▁", " ")
        if raw == "" or raw.isspace():
            whitespace_shap += s
            flush()
            continue

        starts_new = len(raw) > 0 and raw[0].isspace()
        ends_word = len(raw) > 0 and raw[-1].isspace()
        surface = raw.strip()
        if not surface:
            whitespace_shap += s
            flush()
            continue

        if starts_new:
            flush()

        # Glue continuations (no leading space) onto current word.
        cur_word += surface
        cur_sum += s

        if ends_word:
            flush()

    flush()
    word_sum = sum(w["shap"] for w in word_attribs)
    meta = {
        "token_sum": token_sum,
        "word_sum": word_sum,
        "whitespace_shap": whitespace_shap,
        "special_shap": special_shap,
        "residual": token_sum - word_sum - whitespace_shap,
    }
    return word_attribs, meta


def reconstructed_text_from_tokens(tokens: Sequence[str]) -> str:
    parts = []
    for tok in tokens:
        if tok in SPECIAL:
            continue
        parts.append(tok.replace("Ġ", " ").replace("▁", " "))
    return "".join(parts)


def alnum_key(s: str) -> str:
    return "".join(c.lower() for c in s if c.isalnum())


def alignment_ok(source_text: str, word_attribs: List[Dict[str, float]]) -> bool:
    joined = " ".join(w["word"] for w in word_attribs)
    return alnum_key(source_text) == alnum_key(joined)


def mass_diagnostics(
    tokens: Sequence[str], shap_values: Sequence[float]
) -> Dict[str, float]:
    """Compare charspan vs additive aggregation mass accounting."""
    charspan = reaggregate_charspan(tokens, shap_values)
    additive, meta = reaggregate_additive(tokens, shap_values)

    tok_sum = sum(
        float(s) for t, s in zip(tokens, shap_values) if t not in SPECIAL
    )
    charspan_sum = sum(w["shap"] for w in charspan)

    # Space mass under charspan method
    text_chars: List[str] = []
    char_shap: List[float] = []
    for tok, s in zip(tokens, shap_values):
        if tok in SPECIAL:
            continue
        clean = tok.replace("Ġ", " ").replace("▁", " ")
        if not clean:
            continue
        per = float(s) / len(clean)
        for c in clean:
            text_chars.append(c)
            char_shap.append(per)
    space_mass = sum(cs for c, cs in zip(text_chars, char_shap) if c.isspace())

    return {
        "token_sum": tok_sum,
        "charspan_word_sum": charspan_sum,
        "charspan_space_mass": space_mass,
        "charspan_drop_frac": (
            abs(space_mass) / abs(tok_sum) if abs(tok_sum) > 1e-12 else 0.0
        ),
        "additive_word_sum": meta["word_sum"],
        "additive_whitespace_shap": meta["whitespace_shap"],
        "additive_residual": meta["residual"],
        "n_words_charspan": float(len(charspan)),
        "n_words_additive": float(len(additive)),
    }
