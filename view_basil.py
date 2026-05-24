"""Read BASIL articles end-to-end with biased sentences highlighted inline.

Usage:
  python view_basil.py                          # 30 random articles, seeded
  python view_basil.py --limit 50
  python view_basil.py --seed 7
  python view_basil.py --source nyt             # one outlet
  python view_basil.py --triplet <UUID>         # all 3 outlets for one event
  python view_basil.py --triplet <UUID> --outlet 2

Reads basil_sentences.csv (produced by preprocess_basil.py) and pulls
article titles from the original BASIL article JSON files.
"""

import argparse
import json
import random
import signal
import sys
from pathlib import Path

import pandas as pd

# Make piping to head/less quiet instead of dumping a BrokenPipeError traceback.
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "basil_sentences.csv"
ARTICLES_DIR = ROOT.parent / "BASIL" / "articles"


def load_title(year, triplet_uuid, outlet_idx):
    path = ARTICLES_DIR / str(year) / f"{triplet_uuid}_{outlet_idx}.json"
    return json.loads(path.read_text(encoding="utf-8"))["title"]


def format_tags(row):
    tags = []
    if row.has_lex:
        tags.append("lex")
    if row.has_inf:
        tags.append("inf")
    if row.quote_status == "all_in_quote":
        tags.append("all-in-quote")
    elif row.quote_status == "mixed":
        in_q, total = int(row.n_spans_in_quote), int(row.n_spans)
        tags.append(f"quote {in_q}/{total}")
    return ", ".join(tags)


def render_sentence(row):
    sid = f"[{int(row.sentence_idx):>2}]"
    if row.biased:
        return f"{sid} >>> {row.text} <<<   [{format_tags(row)}]"
    return f"{sid}     {row.text}"


def list_sentences(df):
    """Flat dump of every matching sentence, sorted for stable reading."""
    df = df.sort_values(["source", "year", "triplet_uuid", "outlet_idx", "sentence_idx"])
    for _, row in df.iterrows():
        ref = f"{row.source} {row.year} {row.triplet_uuid[:8]}/{int(row.outlet_idx)}:{int(row.sentence_idx):>2}"
        tags = format_tags(row)
        print(f"[{ref}]  [{tags}]  {row.text}")
    print(f"\n{len(df)} sentences.")


def show_article(group, idx, total):
    group = group.sort_values("sentence_idx")
    first = group.iloc[0]
    title = load_title(first.year, first.triplet_uuid, int(first.outlet_idx))
    n_pos = int(group.biased.sum())
    n = len(group)

    print()
    print("=" * 78)
    print(f"Article {idx}/{total}  ·  {first.source} {first.year}  ·  {n_pos}/{n} sentences biased")
    print(f"Title:   {title}")
    print(f"Triplet: {first.triplet_uuid}   Outlet: {int(first.outlet_idx)}")
    print("=" * 78)

    last_pid = -1
    for _, row in group.iterrows():
        if row.paragraph_idx != last_pid:
            print()
            last_pid = row.paragraph_idx
        print(render_sentence(row))
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--source", choices=["nyt", "fox", "hpo"])
    parser.add_argument("--triplet", help="Show only this triplet UUID")
    parser.add_argument("--outlet", type=int, choices=[1, 2, 3])
    parser.add_argument(
        "--list",
        choices=["lex", "inf", "both", "any"],
        help="Flat list of sentences matching this bias type. Skips article browsing.",
    )
    args = parser.parse_args()

    df = pd.read_csv(CSV_PATH)
    if args.source:
        df = df[df.source == args.source]
    if args.triplet:
        df = df[df.triplet_uuid == args.triplet]
    if args.outlet:
        df = df[df.outlet_idx == args.outlet]

    if args.list:
        if args.list == "lex":
            df = df[df.has_lex == 1]
        elif args.list == "inf":
            df = df[df.has_inf == 1]
        elif args.list == "both":
            df = df[df.has_both_types == 1]
        elif args.list == "any":
            df = df[df.biased == 1]
        if df.empty:
            print("No sentences match those filters.", file=sys.stderr)
            sys.exit(1)
        list_sentences(df)
        return

    if df.empty:
        print("No articles match those filters.", file=sys.stderr)
        sys.exit(1)

    groups = [g for _, g in df.groupby(["triplet_uuid", "outlet_idx"], sort=False)]
    # Random walk through articles unless the user pinned a specific triplet.
    if not args.triplet:
        random.Random(args.seed).shuffle(groups)
    groups = groups[: args.limit]

    print(f"Showing {len(groups)} article(s). [Enter] next  ·  [q] quit")
    for i, group in enumerate(groups, 1):
        show_article(group, i, len(groups))
        if i < len(groups):
            try:
                resp = input("[Enter] next  ·  [q] quit > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
            if resp == "q":
                break


if __name__ == "__main__":
    main()
