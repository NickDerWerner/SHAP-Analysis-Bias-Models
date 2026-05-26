"""Re-aggregate DeBERTa SHAP word_attribs from cached tokens + shap_pos.

The original aggregate_subword_shap_to_words() in analysis.py assumes
RoBERTa-style Ġ or SentencePiece-style ▁ word-start markers. DeBERTa-v1's
tokenizer uses **leading spaces** as the word-boundary marker, which the
original aggregator does not recognize. As a result the cached word_attribs
for DeBERTa collapse entire phrases between commas into single "words" like
'Democrats really dont want to spend ...'.

This script re-computes word_attribs from the per-token tokens+shap_pos
arrays that ARE correctly cached in each JSONL record, using a
tokenizer-agnostic char-span approach. The fixed caches replace the
originals (in place); a `.bak` is left behind.

Usage:
    .venv/bin/python scripts/fix_deberta_word_aggregation.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    ROOT / "outputs" / "shap_samples_deberta.jsonl",
    ROOT / "outputs" / "basil_shap" / "samples_deberta.jsonl",
]


def reaggregate(tokens, shap_values):
    """Tokenizer-agnostic word aggregation.

    Concatenates all tokens (with Ġ/▁ markers replaced by spaces) to get the
    full text plus a parallel per-character SHAP array, then splits on
    whitespace. Each word's SHAP = sum of per-char SHAP over its span.
    """
    text_chars = []
    char_shap = []
    for tok, s in zip(tokens, shap_values):
        if tok in ("[CLS]", "[SEP]", "<s>", "</s>"):
            continue
        # Treat Ġ and ▁ as if they were whitespace.
        clean = tok.replace("Ġ", " ").replace("▁", " ")
        if not clean:
            continue
        per_char = float(s) / len(clean)
        for c in clean:
            text_chars.append(c)
            char_shap.append(per_char)

    word_attribs = []
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


def fix_jsonl(path: Path):
    if not path.exists():
        print(f"  [SKIP] {path} missing")
        return
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"  [backup] {bak.name}")

    in_count = 0
    out_count = 0
    word_total = 0
    new_word_total = 0
    with open(path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f]
    for r in records:
        in_count += 1
        word_total += len(r["word_attribs"])
        new_wa = reaggregate(r["tokens"], r["shap_pos"])
        r["word_attribs"] = new_wa
        out_count += 1
        new_word_total += len(new_wa)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  [rewrote] {path.name}: {in_count} records, "
          f"avg words/sentence: {word_total/in_count:.1f} → {new_word_total/in_count:.1f}")


def main():
    for p in TARGETS:
        print(f"Processing {p.relative_to(ROOT)} ...")
        fix_jsonl(p)


if __name__ == "__main__":
    main()
