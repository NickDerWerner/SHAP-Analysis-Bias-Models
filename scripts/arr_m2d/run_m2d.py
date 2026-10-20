#!/usr/bin/env python3
"""ARR M2D — robustness, qualitative analysis, human-materials verification.

Does not generate SHAP, does not simulate human labels, does not rewrite the paper.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from robustness import run_robustness, write_csv  # noqa: E402
from qualitative import run_qualitative  # noqa: E402
from verify_human_materials import main as verify_main  # noqa: E402

OUT = ROOT / "outputs" / "arr_m2d"


def make_summary_figures(summary_rows: list) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig_dir = OUT / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Coverage-matched lex−inf
    rows = [r for r in summary_rows if r["section"] == "coverage_matched" and r["metric"] == "abs_minus_rand"]
    if rows:
        fig, ax = plt.subplots(figsize=(6.5, 3.5))
        xs = np.arange(len(rows))
        means = [float(r["mean"]) if r["mean"] == r["mean"] else 0 for r in rows]
        los = [float(r["mean"]) - float(r["ci95_lo"]) if r["ci95_lo"] == r["ci95_lo"] else 0 for r in rows]
        his = [float(r["ci95_hi"]) - float(r["mean"]) if r["ci95_hi"] == r["ci95_hi"] else 0 for r in rows]
        ax.bar(xs, means, yerr=[los, his], capsize=4, color="#2c3e50")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(xs)
        ax.set_xticklabels([r["model"][:10] for r in rows], rotation=15)
        ax.set_ylabel("Mean (lex − inf) excess |SHAP| mass")
        ax.set_title("Coverage-matched lexical vs informational gap")
        fig.tight_layout()
        fig.savefig(fig_dir / "coverage_matched_lex_minus_inf.png", dpi=150)
        fig.savefig(fig_dir / "coverage_matched_lex_minus_inf.pdf")
        plt.close(fig)

    # Prob bands for BD lex vs inf
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), sharey=True)
    for ax, model in zip(axes, ("biasdetector", "daroberta")):
        for cat, color in (("lex_only", "#c0392b"), ("inf_only", "#2980b9")):
            band_rows = [
                r
                for r in summary_rows
                if r["section"] == "prob_band"
                and r["model"] == model
                and r["metric"] == "abs_minus_rand"
                and r["stratum"].startswith(cat + "|")
            ]
            # sort by band name
            order = ["p00_25", "p25_50", "p50_75", "p75_100"]
            band_rows = sorted(
                band_rows,
                key=lambda r: order.index(r["stratum"].split("|")[1])
                if r["stratum"].split("|")[1] in order
                else 99,
            )
            if not band_rows:
                continue
            x = np.arange(len(band_rows))
            m = [float(r["mean"]) for r in band_rows]
            lo = [float(r["mean"]) - float(r["ci95_lo"]) for r in band_rows]
            hi = [float(r["ci95_hi"]) - float(r["mean"]) for r in band_rows]
            ax.errorbar(x, m, yerr=[lo, hi], marker="o", label=cat, color=color, capsize=3)
            ax.set_xticks(x)
            ax.set_xticklabels([r["stratum"].split("|")[1] for r in band_rows], fontsize=8)
        ax.axhline(0, color="black", lw=0.7)
        ax.set_title(model)
        ax.set_xlabel("P(biased) band")
    axes[0].set_ylabel("Excess |SHAP| mass over random")
    axes[0].legend(fontsize=8)
    fig.suptitle("Alignment excess by predicted-probability band")
    fig.tight_layout()
    fig.savefig(fig_dir / "alignment_by_prob_band.png", dpi=150)
    fig.savefig(fig_dir / "alignment_by_prob_band.pdf")
    plt.close(fig)

    # Paired BD−DR
    paired = [
        r
        for r in summary_rows
        if r["section"] == "paired_model"
        and r["model"] == "biasdetector_minus_daroberta"
        and r["metric"] == "abs_minus_rand"
    ]
    if paired:
        fig, ax = plt.subplots(figsize=(5.5, 3.2))
        xs = np.arange(len(paired))
        means = [float(r["mean"]) for r in paired]
        los = [float(r["mean"]) - float(r["ci95_lo"]) for r in paired]
        his = [float(r["ci95_hi"]) - float(r["mean"]) for r in paired]
        ax.bar(xs, means, yerr=[los, his], capsize=4, color="#8e44ad")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(xs)
        ax.set_xticklabels([r["stratum"] for r in paired], rotation=20, ha="right")
        ax.set_ylabel("Mean (BD − DR) excess mass")
        ax.set_title("Paired model difference (negative ⇒ DR better)")
        fig.tight_layout()
        fig.savefig(fig_dir / "paired_bd_minus_dr.png", dpi=150)
        fig.savefig(fig_dir / "paired_bd_minus_dr.pdf")
        plt.close(fig)


def print_key_findings(summary: list) -> None:
    print("\n=== KEY ROBUSTNESS FINDINGS ===")
    for r in summary:
        if r["section"] == "coverage_matched" and r["metric"] == "abs_minus_rand":
            print(
                f"coverage_matched {r['model']}: n={r['n']} "
                f"lex−inf={float(r['mean']):+.3f} "
                f"CI=[{float(r['ci95_lo']):+.3f},{float(r['ci95_hi']):+.3f}] "
                f"tol={r.get('tol')} covL={r.get('mean_cov_lex')} covI={r.get('mean_cov_inf')}"
            )
        if r["section"] == "regression" and r["metric"] == "coef_is_lex":
            print(
                f"regression is_lex {r['model']} {r['stratum']}: "
                f"{float(r['mean']):+.3f} [{float(r['ci95_lo']):+.3f},{float(r['ci95_hi']):+.3f}]"
            )
        if (
            r["section"] == "paired_model"
            and r["model"] == "biasdetector_minus_daroberta"
            and r["metric"] == "abs_minus_rand"
        ):
            print(
                f"paired BD−DR {r['stratum']}: n={r['n']} "
                f"{float(r['mean']):+.3f} [{float(r['ci95_lo']):+.3f},{float(r['ci95_hi']):+.3f}]"
            )
        if r["section"] == "faith_join" and r["metric"] == "spearman_faith_abs_vs_align":
            print(f"faith↔align spearman {r['model']}: n={r['n']} r={float(r['mean']):+.3f}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Running robustness…")
    summary = run_robustness()
    write_csv(OUT / "robustness_summary.csv", summary)
    make_summary_figures(summary)
    print_key_findings(summary)

    print("\nRunning qualitative…")
    flat = run_qualitative()
    print(f"qualitative examples: {len(flat)} → {OUT / 'qualitative_examples.csv'}")

    print("\nVerifying human materials…")
    verify_main()

    meta = {
        "seed": 7,
        "inputs": {
            "m2c_alignment": "outputs/arr_m2c/gold_span_alignment.csv",
            "m2b_faithfulness": "outputs/arr_m2b/medium_results.csv",
        },
        "n_robustness_rows": len(summary),
        "n_qualitative": len(flat),
        "note": "Human agreement not computed — awaiting real annotator files.",
    }
    (OUT / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\nDone. Outputs in {OUT}")


if __name__ == "__main__":
    main()
