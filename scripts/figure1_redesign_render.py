"""Render the Figure 1 redesign as a column-friendly stacked-text figure.

Two rows, one per model, both showing the SAME shared-FP sentence with per-word
background shading proportional to |SHAP|. Color sign by SHAP sign (pink =
positive contribution toward BIASED, blue = toward NON-BIASED). Intensity is
normalized over BOTH rows combined, so visual comparison is fair: same word
shaded darker under bias-detector than under DA-RoBERTa means bias-detector
attributed more weight to that token.

Source of word-level SHAP: cached samples_*.jsonl from basil_shap_generate.py
(no model re-run required).

Outputs:
  outputs/examples/figure1_redesign.pdf   (paper figure)
  outputs/examples/figure1_redesign.png   (preview / Slack)
"""

import json
import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

TARGET = "A Cuba policy that is stuck in the Cold War."

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = {
    "bias-detector": os.path.join(ROOT, "outputs/basil_shap/samples_biasdetector.jsonl"),
    "DA-RoBERTa-BABE-FT": os.path.join(ROOT, "outputs/basil_shap/samples_daroberta.jsonl"),
}
OUT_DIR = os.path.join(ROOT, "outputs/examples")

# SHAP-native red/blue, kept for visual continuity with the existing HTML plots.
POS_RGB = (255 / 255, 0 / 255, 81 / 255)
NEG_RGB = (0 / 255, 138 / 255, 250 / 255)


def load_record(path, target_text):
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            if d["text"] == target_text:
                return d
    raise KeyError(f"{target_text!r} not found in {path}")


def shade(shap, vmax):
    """Return rgba background for a word given its SHAP and the global vmax."""
    intensity = min(1.0, abs(shap) / vmax) if vmax > 0 else 0.0
    base = POS_RGB if shap >= 0 else NEG_RGB
    # White-to-color mix so darkness scales with intensity (cleaner than alpha
    # over a white background, which can look washed out when rasterized).
    r, g, b = base
    return (1 - intensity * (1 - r),
            1 - intensity * (1 - g),
            1 - intensity * (1 - b),
            1.0)


def text_color_for(bg):
    """Always black; pink/blue backgrounds stay legible at full saturation
    and a uniform text color reads as a cleaner figure."""
    return "black"


def measure_text_px(ax, fig, text, fontsize, family):
    """Render text invisibly to measure its rendered width/height in pixels."""
    t = ax.text(0, -10, text, fontsize=fontsize, family=family,
                transform=ax.transAxes)
    fig.canvas.draw()
    bb = t.get_window_extent(fig.canvas.get_renderer())
    t.remove()
    return bb.width, bb.height


def render_row(ax, model_name, prob, word_attribs, vmax, fig):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    renderer = fig.canvas.get_renderer()
    ax_px = ax.get_window_extent(renderer)
    px_to_ax_x = lambda px: px / ax_px.width
    px_to_ax_y = lambda px: px / ax_px.height

    # ---- Header: model name only ----
    header_y = 0.72
    ax.text(0.0, header_y, model_name, fontsize=11, fontweight="bold",
            transform=ax.transAxes, va="center")

    # ---- Thin rule between header and text row ----
    rule_y = 0.62
    ax.add_line(Line2D([0.0, 1.0], [rule_y, rule_y],
                       color=(0.80, 0.80, 0.80), linewidth=0.6,
                       transform=ax.transAxes, clip_on=False))

    # ---- Highlighted-text line (and prediction pill on the same row) ----
    word_fontsize = 12
    word_family = "serif"
    pad_x_px = 5            # horizontal padding inside each colored box
    pad_y_px = 4            # vertical padding inside each colored box
    gap_px = 4              # gap between adjacent boxes
    text_y = 0.27           # vertical center of the text row

    # Prediction pill, vertically aligned with the text row.
    pill_text = f"p(BIASED) = {prob:.3f}  →  predicts BIASED"
    ax.text(1.0, text_y, pill_text, fontsize=10,
            transform=ax.transAxes, va="center", ha="right",
            color=(0.25, 0.05, 0.10),
            bbox=dict(facecolor=(0.98, 0.90, 0.93),
                      edgecolor=(0.85, 0.60, 0.70),
                      linewidth=0.6,
                      boxstyle="round,pad=0.45,rounding_size=0.5"))

    # Pre-measure all words so we know the box height and total width.
    word_widths_px = []
    word_heights_px = []
    for wa in word_attribs:
        w_px, h_px = measure_text_px(ax, fig, wa["word"], word_fontsize, word_family)
        word_widths_px.append(w_px)
        word_heights_px.append(h_px)
    box_h_px = max(word_heights_px) + 2 * pad_y_px
    box_h_ax = px_to_ax_y(box_h_px)

    cursor_ax = 0.0
    for wa, w_px in zip(word_attribs, word_widths_px):
        word, shap = wa["word"], wa["shap"]
        box_w_ax = px_to_ax_x(w_px + 2 * pad_x_px)
        bg = shade(shap, vmax)
        fg = text_color_for(bg)

        ax.add_patch(mpatches.FancyBboxPatch(
            (cursor_ax, text_y - box_h_ax / 2),
            box_w_ax, box_h_ax,
            boxstyle="round,pad=0,rounding_size=0.012",
            facecolor=bg, edgecolor="none",
            transform=ax.transAxes, clip_on=False))

        ax.text(cursor_ax + box_w_ax / 2, text_y, word,
                fontsize=word_fontsize, family=word_family, color=fg,
                transform=ax.transAxes, ha="center", va="center")

        cursor_ax += box_w_ax + px_to_ax_x(gap_px)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    records = {name: load_record(path, TARGET) for name, path in SAMPLES.items()}
    for name, r in records.items():
        assert r["gold"] == 0, f"{name}: expected gold=0 (non-biased), got {r['gold']}"
        assert r["pred"] == 1, f"{name}: expected pred=1 (FP), got {r['pred']}"

    # Global color normalization across both models for fair visual comparison.
    vmax = max(abs(wa["shap"])
               for r in records.values()
               for wa in r["word_attribs"])
    print(f"global |SHAP| max across both models: {vmax:.4f}")

    fig = plt.figure(figsize=(7.2, 2.6), dpi=200)
    gs = fig.add_gridspec(
        nrows=3, ncols=1,
        height_ratios=[0.35, 1.0, 1.0],
        hspace=0.05, left=0.02, right=0.98, top=0.94, bottom=0.04,
    )

    title_ax = fig.add_subplot(gs[0])
    title_ax.axis("off")
    title_ax.text(
        0.5, 0.5,
        "Shared false positive",
        ha="center", va="center", fontsize=12, fontweight="bold",
        transform=title_ax.transAxes,
    )

    # Need an initial draw so renderer is initialised before measuring text.
    fig.canvas.draw()

    for i, (name, key) in enumerate([
        ("bias-detector", "bias-detector"),
        ("DA-RoBERTa-BABE-FT", "DA-RoBERTa-BABE-FT"),
    ]):
        ax = fig.add_subplot(gs[i + 1])
        rec = records[key]
        render_row(ax, name, rec["prob_pos"], rec["word_attribs"], vmax, fig)

    pdf_path = os.path.join(OUT_DIR, "figure1_redesign.pdf")
    png_path = os.path.join(OUT_DIR, "figure1_redesign.png")
    fig.savefig(pdf_path)
    fig.savefig(png_path)
    print(f"wrote {pdf_path}")
    print(f"wrote {png_path}")


if __name__ == "__main__":
    main()
