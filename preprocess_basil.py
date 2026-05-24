"""Convert BASIL into a sentence-level CSV for cross-dataset evaluation."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

BASIL_ROOT = Path(__file__).resolve().parent.parent / "BASIL"
OUT_PATH = Path(__file__).resolve().parent / "basil_sentences.csv"

COLUMNS = [
    "triplet_uuid",
    "article_uuid",
    "outlet_idx",
    "source",
    "year",
    "paragraph_idx",
    "sentence_idx",
    "text",
    "biased",
    "has_lex",
    "has_inf",
    "has_both_types",
    "quote_status",
    "n_spans",
    "n_spans_in_quote",
    "n_spans_not_in_quote",
]


def iter_article_pairs():
    for art_path in sorted((BASIL_ROOT / "articles").glob("*/*.json")):
        ann_path = (
            BASIL_ROOT / "annotations" / art_path.parent.name / f"{art_path.stem}_ann.json"
        )
        yield art_path, ann_path


def flatten_sentences(body_paragraphs):
    sentence_idx = 0
    for paragraph_idx, paragraph in enumerate(body_paragraphs):
        for text in paragraph:
            yield sentence_idx, paragraph_idx, text
            sentence_idx += 1


def group_spans_by_sentence(annotations):
    # `id` looks paragraph-like ('p0', 'p2') but is the flattened sentence index.
    # 3 corpus-wide id == 'title' annotations don't fit the sentence scheme — drop.
    by_sentence = defaultdict(list)
    for span in annotations.get("phrase-level-annotations", []):
        sid = span["id"]
        if sid == "title":
            continue
        by_sentence[int(sid[1:])].append(span)
    return by_sentence


def sentence_features(spans):
    n_spans = len(spans)
    types = {s["bias"] for s in spans}
    has_lex = int("lex" in types)
    has_inf = int("inf" in types)
    n_in_quote = sum(1 for s in spans if s.get("quote") == "yes")
    n_out_quote = n_spans - n_in_quote

    if n_spans == 0:
        quote_status = "none"
    elif n_in_quote == n_spans:
        quote_status = "all_in_quote"
    elif n_in_quote == 0:
        quote_status = "no_quote"
    else:
        quote_status = "mixed"

    return {
        "biased": int(n_spans > 0),
        "has_lex": has_lex,
        "has_inf": has_inf,
        "has_both_types": int(has_lex and has_inf),
        "quote_status": quote_status,
        "n_spans": n_spans,
        "n_spans_in_quote": n_in_quote,
        "n_spans_not_in_quote": n_out_quote,
    }


def build_rows():
    rows = []
    for art_path, ann_path in iter_article_pairs():
        article = json.loads(art_path.read_text(encoding="utf-8"))
        annotations = json.loads(ann_path.read_text(encoding="utf-8"))

        outlet_idx = int(art_path.stem.rsplit("_", 1)[1])
        year = art_path.parent.name
        spans_by_sentence = group_spans_by_sentence(annotations)

        for sid, pid, text in flatten_sentences(article["body-paragraphs"]):
            spans = spans_by_sentence.get(sid, [])
            rows.append(
                {
                    "triplet_uuid": article["triplet-uuid"],
                    "article_uuid": article["uuid"],
                    "outlet_idx": outlet_idx,
                    "source": article["source"].lower(),
                    "year": year,
                    "paragraph_idx": pid,
                    "sentence_idx": sid,
                    "text": text,
                    **sentence_features(spans),
                }
            )
    return rows


def print_summary(rows):
    n = len(rows)
    positives = [r for r in rows if r["biased"]]
    pos = len(positives)
    lex_only = sum(1 for r in positives if r["has_lex"] and not r["has_inf"])
    inf_only = sum(1 for r in positives if r["has_inf"] and not r["has_lex"])
    both = sum(1 for r in positives if r["has_both_types"])
    quote_counts = Counter(r["quote_status"] for r in rows)

    articles_per_source = Counter()
    seen = set()
    for r in rows:
        # An article is one file: (triplet_uuid, outlet_idx). `article_uuid` is
        # not unique — 3 hpo files share a uuid with another file in the corpus.
        key = (r["triplet_uuid"], r["outlet_idx"])
        if key in seen:
            continue
        seen.add(key)
        articles_per_source[r["source"]] += 1

    print(f"Wrote {n} sentences to {OUT_PATH}")
    print(f"  positives: {pos} ({pos / n:.1%})")
    print(f"  bias-type split of positives: lex-only {lex_only}, inf-only {inf_only}, both {both}")
    print(
        f"  quote_status: all_in_quote {quote_counts['all_in_quote']}, "
        f"no_quote {quote_counts['no_quote']}, mixed {quote_counts['mixed']}, "
        f"none {quote_counts['none']}"
    )
    print(f"  articles per source: {dict(articles_per_source)}")


def main():
    rows = build_rows()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print_summary(rows)


if __name__ == "__main__":
    main()
