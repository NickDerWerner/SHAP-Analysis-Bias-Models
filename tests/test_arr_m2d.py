"""Unit tests for M2D robustness helpers and human-agreement metrics."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2d"))

from stats_utils import (  # noqa: E402
    bootstrap_mean_ci,
    cluster_bootstrap_mean_ci,
    coverage_matched_pairs,
    paired_bootstrap_mean_ci,
)
from human_agreement import (  # noqa: E402
    char_mask_from_spans,
    cohen_kappa,
    span_soft_f1,
)


def test_bootstrap_mean_ci_known():
    mean, lo, hi = bootstrap_mean_ci([1.0, 2.0, 3.0, 4.0, 5.0], n_boot=500, seed=7)
    assert abs(mean - 3.0) < 1e-9
    assert lo <= mean <= hi


def test_paired_bootstrap_excludes_zero_when_clear():
    diffs = [0.1] * 40
    mean, lo, hi = paired_bootstrap_mean_ci(diffs, n_boot=500, seed=7)
    assert mean == pytest.approx(0.1)
    assert lo > 0


def test_cluster_bootstrap_runs():
    vals = [0.1, 0.2, 0.15, 0.05, 0.12, 0.08]
    clusters = ["a", "a", "b", "b", "c", "c"]
    mean, lo, hi = cluster_bootstrap_mean_ci(vals, clusters, n_boot=200, seed=7)
    assert lo <= mean <= hi
    assert mean == pytest.approx(float(np.mean(vals)))


def test_coverage_matched_pairs_respects_tol():
    lex = [{"gold_char_coverage": 0.10, "id": "l1"}, {"gold_char_coverage": 0.50, "id": "l2"}]
    inf = [{"gold_char_coverage": 0.12, "id": "i1"}, {"gold_char_coverage": 0.90, "id": "i2"}]
    pairs = coverage_matched_pairs(lex, inf, tol=0.05, seed=7)
    assert len(pairs) == 1
    assert pairs[0][0]["id"] == "l1"
    assert pairs[0][1]["id"] == "i1"


def test_cohen_kappa_perfect():
    y = ["yes", "no", "yes", "no"]
    assert cohen_kappa(y, y) == pytest.approx(1.0)


def test_cohen_kappa_chance():
    # all same label → undefined/NaN pe edge
    k = cohen_kappa(["yes", "yes"], ["yes", "yes"])
    assert k != k or k == 1.0  # either nan or 1 depending on pe


def test_span_soft_f1_identical():
    m = np.array([0, 1, 1, 0, 1], dtype=bool)
    s = span_soft_f1(m, m.copy())
    assert s["f1"] == pytest.approx(1.0)
    assert s["iou"] == pytest.approx(1.0)


def test_span_soft_f1_disjoint():
    a = np.array([1, 1, 0, 0], dtype=bool)
    b = np.array([0, 0, 1, 1], dtype=bool)
    s = span_soft_f1(a, b)
    assert s["f1"] == pytest.approx(0.0)
    assert s["iou"] == pytest.approx(0.0)


def test_char_mask_from_spans():
    m = char_mask_from_spans(10, [{"start": 2, "end": 5}, {"start": 7, "end": 9}])
    assert m.tolist() == [0, 0, 1, 1, 1, 0, 0, 1, 1, 0]


def test_human_agreement_refuses_missing_files(tmp_path):
    from human_agreement import main

    missing = tmp_path / "nope.json"
    rc = main(["--annotator-a", str(missing), "--annotator-b", str(missing)])
    assert rc == 2


def test_verify_stratification_structure():
    from verify_human_materials import verify

    v = verify()
    assert v["n_sample"] == 120
    by_name = {c["check"]: c for c in v["checks"]}
    assert by_name["stratification_30x4"]["pass"]
    assert by_name["gold_char_offsets"]["pass"]
    assert by_name["blind_csv_no_model_or_gold"]["pass"]
    assert by_name["html_no_gold_leakage"]["pass"]
    assert by_name["html_has_context_option"]["pass"]
