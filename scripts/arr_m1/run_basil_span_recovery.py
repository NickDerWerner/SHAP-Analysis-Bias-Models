#!/usr/bin/env python3
"""ARR M1 Task D — recover BASIL gold spans and align to basil_sentences.csv."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "arr_m1" / "basil_spans"
CSV_PATH = ROOT / "basil_sentences.csv"

LAUNCHNLP = Path("/Users/rick/DoksOhneidrive/BASIL_launchnlp")
EMNLP19 = Path("/Users/rick/DoksOhneidrive/BASIL_emnlp19")


def git_meta(repo: Path) -> Dict[str, str]:
    import subprocess

    def run(args):
        try:
            return subprocess.check_output(args, cwd=repo, text=True).strip()
        except Exception as e:
            return f"ERR:{e}"

    return {
        "path": str(repo),
        "commit": run(["git", "rev-parse", "HEAD"]),
        "commit_short": run(["git", "rev-parse", "--short", "HEAD"]),
        "describe": run(["git", "log", "-1", "--oneline"]),
        "remote": run(["git", "remote", "get-url", "origin"]),
        "license_file_present": str(
            any(repo.glob("LICENSE*")) or any(repo.glob("license*"))
        ),
    }


def flatten_sentences(body_paragraphs):
    sentence_idx = 0
    for paragraph_idx, paragraph in enumerate(body_paragraphs):
        for text in paragraph:
            yield sentence_idx, paragraph_idx, text
            sentence_idx += 1


def load_csv_rows() -> List[dict]:
    with CSV_PATH.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rebuild_from(repo_articles: Path, repo_anns: Path) -> Tuple[List[dict], List[dict]]:
    """Rebuild sentence rows + span rows from a BASIL release."""
    sent_rows = []
    span_rows = []
    for art_path in sorted(repo_articles.glob("*/*.json")):
        ann_path = repo_anns / art_path.parent.name / f"{art_path.stem}_ann.json"
        if not ann_path.exists():
            continue
        article = json.loads(art_path.read_text(encoding="utf-8"))
        annotations = json.loads(ann_path.read_text(encoding="utf-8"))
        outlet_idx = int(art_path.stem.rsplit("_", 1)[1])
        year = art_path.parent.name

        spans_by_sent = defaultdict(list)
        for span in annotations.get("phrase-level-annotations", []):
            sid = span["id"]
            if sid == "title":
                continue
            spans_by_sent[int(sid[1:])].append(span)

        for sid, pid, text in flatten_sentences(article["body-paragraphs"]):
            spans = spans_by_sent.get(sid, [])
            types = {s["bias"] for s in spans}
            n_in_quote = sum(1 for s in spans if s.get("quote") == "yes")
            n_spans = len(spans)
            if n_spans == 0:
                quote_status = "none"
            elif n_in_quote == n_spans:
                quote_status = "all_in_quote"
            elif n_in_quote == 0:
                quote_status = "no_quote"
            else:
                quote_status = "mixed"

            sent_rows.append(
                {
                    "triplet_uuid": article["triplet-uuid"],
                    "article_uuid": article["uuid"],
                    "outlet_idx": outlet_idx,
                    "source": article["source"].lower(),
                    "year": year,
                    "paragraph_idx": pid,
                    "sentence_idx": sid,
                    "text": text,
                    "biased": int(n_spans > 0),
                    "has_lex": int("lex" in types),
                    "has_inf": int("inf" in types),
                    "has_both_types": int("lex" in types and "inf" in types),
                    "quote_status": quote_status,
                    "n_spans": n_spans,
                    "n_spans_in_quote": n_in_quote,
                    "n_spans_not_in_quote": n_spans - n_in_quote,
                }
            )
            for sp in spans:
                start, end = int(sp["start"]), int(sp["end"])
                frag = text[start:end]
                span_rows.append(
                    {
                        "triplet_uuid": article["triplet-uuid"],
                        "article_uuid": article["uuid"],
                        "outlet_idx": outlet_idx,
                        "sentence_idx": sid,
                        "paragraph_idx": pid,
                        "year": year,
                        "bias": sp.get("bias"),
                        "quote": sp.get("quote"),
                        "polarity": sp.get("polarity"),
                        "aim": sp.get("aim"),
                        "target": sp.get("target"),
                        "start": start,
                        "end": end,
                        "span_txt": sp.get("txt", ""),
                        "offset_slice": frag,
                        "offset_matches_txt": int(frag == sp.get("txt", "")),
                        "find_pos": text.find(sp.get("txt", "")),
                        "sentence_text": text,
                    }
                )
    return sent_rows, span_rows


def key(r: dict) -> Tuple:
    return (
        r["triplet_uuid"],
        int(r["outlet_idx"]),
        int(r["sentence_idx"]),
    )


def compare_to_csv(rebuilt: List[dict], csv_rows: List[dict]) -> Dict[str, Any]:
    rb = {key(r): r for r in rebuilt}
    cv = {key(r): r for r in csv_rows}

    rb_keys, cv_keys = set(rb), set(cv)
    only_rb = rb_keys - cv_keys
    only_cv = cv_keys - rb_keys
    common = rb_keys & cv_keys

    exact = 0
    text_mismatch = 0
    label_mismatch = 0
    recoverable = 0  # text differs only by whitespace?
    examples = {"text_mismatch": [], "label_mismatch": [], "only_csv": [], "only_repo": []}

    label_fields = [
        "biased",
        "has_lex",
        "has_inf",
        "has_both_types",
        "quote_status",
        "n_spans",
    ]

    for k in common:
        a, b = rb[k], cv[k]
        text_ok = a["text"] == b["text"]
        labels_ok = all(str(a[f]) == str(b[f]) for f in label_fields)
        if text_ok and labels_ok:
            exact += 1
        else:
            if not text_ok:
                text_mismatch += 1
                # recoverable if alnum match
                alnum = lambda s: "".join(c.lower() for c in s if c.isalnum())
                if alnum(a["text"]) == alnum(b["text"]):
                    recoverable += 1
                if len(examples["text_mismatch"]) < 5:
                    examples["text_mismatch"].append(
                        {
                            "key": k,
                            "repo_text": a["text"][:160],
                            "csv_text": b["text"][:160],
                        }
                    )
            if not labels_ok:
                label_mismatch += 1
                if len(examples["label_mismatch"]) < 5:
                    examples["label_mismatch"].append(
                        {
                            "key": k,
                            "repo": {f: a[f] for f in label_fields},
                            "csv": {f: b[f] for f in label_fields},
                        }
                    )

    for k in list(only_cv)[:5]:
        examples["only_csv"].append({"key": k, "text": cv[k]["text"][:120]})
    for k in list(only_rb)[:5]:
        examples["only_repo"].append({"key": k, "text": rb[k]["text"][:120]})

    return {
        "n_repo_sentences": len(rb),
        "n_csv_sentences": len(cv),
        "n_common_keys": len(common),
        "n_only_repo": len(only_rb),
        "n_only_csv": len(only_cv),
        "exact_match": exact,
        "text_mismatch": text_mismatch,
        "label_mismatch_among_common": label_mismatch,
        "recoverable_alnum_text_mismatch": recoverable,
        "unrecoverable_key_mismatch": len(only_rb) + len(only_cv),
        "examples": examples,
    }


def write_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    csv_rows = load_csv_rows()

    meta = {
        "launchnlp": git_meta(LAUNCHNLP),
        "emnlp19": git_meta(EMNLP19),
        "license_note": (
            "Neither clone contains a LICENSE file at repo root. "
            "Do not redistribute BASIL contents from this project without "
            "confirming terms with the dataset authors / paper. "
            "For analysis, keep data outside git-tracked outputs or under "
            "documented non-redistribution policy."
        ),
        "selected_version": None,
        "selection_reason": None,
    }

    # Rebuild both
    ln_sents, ln_spans = rebuild_from(LAUNCHNLP / "articles", LAUNCHNLP / "annotations")
    em_articles = EMNLP19 / "data" / "articles"
    em_anns = EMNLP19 / "data" / "annotations" / "resolved"
    em_sents, em_spans = rebuild_from(em_articles, em_anns)

    cmp_ln = compare_to_csv(ln_sents, csv_rows)
    cmp_em = compare_to_csv(em_sents, csv_rows)

    # Choose matching version
    if cmp_ln["exact_match"] >= cmp_em["exact_match"]:
        meta["selected_version"] = "launchnlp/BASIL"
        meta["selection_reason"] = (
            f"Higher exact sentence+label match vs basil_sentences.csv "
            f"({cmp_ln['exact_match']} vs {cmp_em['exact_match']}). "
            "Also matches preprocess_basil.py path layout."
        )
        selected_sents, selected_spans = ln_sents, ln_spans
        selected_cmp = cmp_ln
    else:
        meta["selected_version"] = "marshallwhiteorg/emnlp19-media-bias"
        meta["selection_reason"] = "Higher exact match to CSV."
        selected_sents, selected_spans = em_sents, em_spans
        selected_cmp = cmp_em

    # Span offset quality on selected
    off_ok = sum(1 for s in selected_spans if s["offset_matches_txt"] == 1)
    off_fail = len(selected_spans) - off_ok
    bias_counts = Counter(s["bias"] for s in selected_spans)

    # Export spans (analysis artifact under outputs/arr_m1 — not a redistribution of full articles)
    # We export span records with identifiers + offsets + span text only.
    export_spans = []
    for s in selected_spans:
        export_spans.append(
            {
                "triplet_uuid": s["triplet_uuid"],
                "article_uuid": s["article_uuid"],
                "outlet_idx": s["outlet_idx"],
                "sentence_idx": s["sentence_idx"],
                "paragraph_idx": s["paragraph_idx"],
                "year": s["year"],
                "bias": s["bias"],
                "quote": s["quote"],
                "polarity": s["polarity"],
                "start": s["start"],
                "end": s["end"],
                "span_txt": s["span_txt"],
                "offset_matches_txt": s["offset_matches_txt"],
            }
        )
    write_csv(OUT / "gold_spans.csv", export_spans)

    # Alignment of cached SHAP sentences to gold spans
    basil_cache = ROOT / "outputs" / "basil_shap" / "samples_biasdetector.jsonl"
    cache_align = []
    if basil_cache.exists():
        with basil_cache.open(encoding="utf-8") as f:
            cache = [json.loads(l) for l in f]
        spans_index = defaultdict(list)
        for s in export_spans:
            spans_index[(s["triplet_uuid"], int(s["outlet_idx"]), int(s["sentence_idx"]))].append(s)
        for r in cache:
            k = (r["triplet_uuid"], int(r["outlet_idx"]), int(r["sentence_idx"]))
            sps = spans_index.get(k, [])
            cache_align.append(
                {
                    "triplet_uuid": r["triplet_uuid"],
                    "outlet_idx": r["outlet_idx"],
                    "sentence_idx": r["sentence_idx"],
                    "gold_biased_cache": r["gold"],
                    "n_gold_spans": len(sps),
                    "has_lex_span": int(any(s["bias"] == "lex" for s in sps)),
                    "has_inf_span": int(any(s["bias"] == "inf" for s in sps)),
                    "text_matches_csv": "",  # filled below
                }
            )
        # text match vs csv
        csv_idx = {key(r): r["text"] for r in csv_rows}
        for row in cache_align:
            k = (row["triplet_uuid"], int(row["outlet_idx"]), int(row["sentence_idx"]))
            # find cache text
            pass
        # richer: join cache text
        cache_by_k = {
            (r["triplet_uuid"], int(r["outlet_idx"]), int(r["sentence_idx"])): r["text"]
            for r in cache
        }
        for row in cache_align:
            k = (row["triplet_uuid"], int(row["outlet_idx"]), int(row["sentence_idx"]))
            ct = cache_by_k[k]
            csv_t = csv_idx.get(k)
            row["text_matches_csv"] = int(csv_t == ct) if csv_t is not None else -1
        write_csv(OUT / "shap_cache_span_coverage.csv", cache_align)

    report = {
        "meta": meta,
        "compare_launchnlp": {k: v for k, v in cmp_ln.items() if k != "examples"},
        "compare_emnlp19": {k: v for k, v in cmp_em.items() if k != "examples"},
        "selected_compare": {k: v for k, v in selected_cmp.items() if k != "examples"},
        "examples_selected": selected_cmp["examples"],
        "span_stats": {
            "n_spans": len(selected_spans),
            "offset_match_txt": off_ok,
            "offset_mismatch": off_fail,
            "bias_type_counts": dict(bias_counts),
        },
        "usable_for_human_alignment": bool(
            selected_cmp["exact_match"] > 0.99 * selected_cmp["n_csv_sentences"]
            and off_fail == 0
        ),
    }
    (OUT / "alignment_report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    (OUT / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("[basil_spans] selected:", meta["selected_version"])
    print("  exact_match", selected_cmp["exact_match"], "/", selected_cmp["n_csv_sentences"])
    print("  text_mismatch", selected_cmp["text_mismatch"], "label_mismatch", selected_cmp["label_mismatch_among_common"])
    print("  spans", len(selected_spans), "offset_ok", off_ok, "offset_fail", off_fail)
    print("  bias counts", dict(bias_counts))


if __name__ == "__main__":
    main()
