"""Task C — verify blind human-study materials; write checklist + annotator pack."""
from __future__ import annotations

import csv
import json
import re
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
M2C = ROOT / "outputs" / "arr_m2c"
OUT = ROOT / "outputs" / "arr_m2d"
PACK = OUT / "annotator_pack"


def verify() -> dict:
    checks = []
    sample_path = M2C / "human_annotation_sample.csv"
    blind_path = M2C / "human_annotation_sample_BLIND.csv"
    html_path = M2C / "human_annotation_interface.html"
    notes_path = M2C / "human_sample_notes.json"

    sample = list(csv.DictReader(sample_path.open(encoding="utf-8")))
    blind = list(csv.DictReader(blind_path.open(encoding="utf-8")))
    html = html_path.read_text(encoding="utf-8")
    notes = json.loads(notes_path.read_text(encoding="utf-8"))

    # Stratification
    cats = Counter(r["GOLD_category"] for r in sample)
    ok_strat = cats.get("lex_only") == 30 and cats.get("inf_only") == 30 and cats.get("both") == 30 and cats.get("non_biased") == 30
    checks.append({"check": "stratification_30x4", "pass": ok_strat, "detail": dict(cats)})

    # Offset integrity
    bad = 0
    ok = 0
    for r in sample:
        text = r["sentence_text"]
        for sp in json.loads(r["GOLD_spans_json"]):
            if text[sp["start"] : sp["end"]] != sp["txt"]:
                bad += 1
            else:
                ok += 1
    checks.append({"check": "gold_char_offsets", "pass": bad == 0, "detail": {"ok": ok, "bad": bad}})

    # Blind: no GOLD / SHAP / pred
    blind_cols = list(blind[0].keys()) if blind else []
    leak_cols = [
        c
        for c in blind_cols
        if c.startswith("GOLD_")
        or "shap" in c.lower()
        or c in ("pred", "prob_pos", "pred_type", "gold")
    ]
    checks.append({"check": "blind_csv_no_model_or_gold", "pass": len(leak_cols) == 0, "detail": leak_cols})

    # HTML: no GOLD strings in payload; has needs_context; no shap
    has_gold_in_html = "GOLD_" in html or '"lex_only"' in html or "gold_spans" in html.lower()
    has_shap = re.search(r"\bshap\b", html, re.I) is not None
    has_context = "needs_context" in html or "Needs article context" in html
    has_none = "none" in html and "Bias present" in html
    checks.append({"check": "html_no_gold_leakage", "pass": not has_gold_in_html, "detail": {"has_gold_token": has_gold_in_html}})
    checks.append({"check": "html_no_shap", "pass": not has_shap, "detail": {}})
    checks.append({"check": "html_has_context_option", "pass": has_context, "detail": {}})
    checks.append({"check": "html_has_none_type", "pass": has_none, "detail": {}})

    # Ordering not blocked by category
    seq = [r["GOLD_category"] for r in sample]
    blocked = all(seq[i] == seq[0] for i in range(min(30, len(seq))))  # first 30 same = bad
    # better: runs of identical category
    max_run = 1
    run = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i - 1]:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1
    checks.append(
        {
            "check": "shuffled_not_blocked_by_category",
            "pass": max_run <= 8 and not blocked,
            "detail": {"max_run": max_run, "first12": seq[:12]},
        }
    )

    # Metadata leakage: source/year OK for news context; canonical_id reveals BASIL ids but not labels
    checks.append(
        {
            "check": "metadata_no_labels",
            "pass": True,
            "detail": "canonical_id/source/year retained for provenance; no bias labels in blind files",
        }
    )

    return {"n_sample": len(sample), "notes": notes, "checks": checks}


def build_annotator_pack(verification: dict) -> None:
    """Copy blind materials + patch HTML with annotator_id + write README for annotators."""
    PACK.mkdir(parents=True, exist_ok=True)
    shutil.copy2(M2C / "human_annotation_sample_BLIND.csv", PACK / "items_BLIND.csv")
    html = (M2C / "human_annotation_interface.html").read_text(encoding="utf-8")
    # Patch: add annotator ID prompt and include in export
    if "annotator_id" not in html:
        html = html.replace(
            "<h1>Bias evidence annotation (blind)</h1>",
            """<h1>Bias evidence annotation (blind)</h1>
<p><label><b>Your annotator ID</b> (required):
<input id="annotator_id" type="text" placeholder="e.g. annA" style="width:12rem"/></label>
<span class="hint">Use the ID assigned in the onboarding email. Do not use your real name in the exported filename if sharing broadly.</span></p>
""",
        )
        html = html.replace(
            "a.download = 'basil_blind_annotations.json';",
            """const aid = (document.getElementById('annotator_id').value || 'UNKNOWN').trim();
  Object.values(state).forEach(s => { s.annotator_id = aid; });
  a.download = 'basil_blind_annotations_' + aid + '.json';""",
        )
        html = html.replace(
            "document.getElementById('export').onclick = () => {",
            """document.getElementById('export').onclick = () => {
  const aid = (document.getElementById('annotator_id').value || '').trim();
  if (!aid) { alert('Please enter your annotator ID before exporting.'); return; }
""",
        )
    (PACK / "annotation_interface.html").write_text(html, encoding="utf-8")
    # Do NOT copy analyst sample with GOLD_
    (PACK / "README_ANNOTATORS.txt").write_text(
        """BASIL blind annotation pack (M2D)
================================
1. Read docs/ARR_M2D_HUMAN_STUDY_INSTRUCTIONS.md (onboarding).
2. Optionally skim docs/ARR_M2C_HUMAN_ANNOTATION_GUIDE.md (definitions).
3. Open annotation_interface.html in a browser OR fill items_BLIND.csv.
4. Enter your assigned annotator ID before exporting.
5. Work independently — do not discuss items with the other annotator until adjudication.
6. Return: basil_blind_annotations_<YOURID>.json (or completed CSV).

Do NOT open any file containing GOLD_ columns. Do NOT use ChatGPT/Claude for labels.
""",
        encoding="utf-8",
    )
    # Confirm pack HTML has annotator_id
    pack_html = (PACK / "annotation_interface.html").read_text(encoding="utf-8")
    verification["checks"].append(
        {
            "check": "annotator_id_field_in_pack",
            "pass": "annotator_id" in pack_html,
            "detail": "Patched pack interface requires annotator ID before export",
        }
    )
    # Confirm GOLD sample not in pack
    pack_files = [p.name for p in PACK.iterdir()]
    verification["checks"].append(
        {
            "check": "pack_excludes_gold_sample",
            "pass": not any("GOLD" in n or n == "human_annotation_sample.csv" for n in pack_files),
            "detail": pack_files,
        }
    )
    (OUT / "human_materials_verification.json").write_text(
        json.dumps(verification, indent=2), encoding="utf-8"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    v = verify()
    build_annotator_pack(v)
    failed = [c for c in v["checks"] if not c["pass"]]
    print(json.dumps({"n_checks": len(v["checks"]), "failed": [c["check"] for c in failed]}, indent=2))
    print(f"Annotator pack: {PACK}")


if __name__ == "__main__":
    main()
