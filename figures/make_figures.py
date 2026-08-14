"""Regenerate the results figures from results/full/samples.csv.

Usage:  python figures/make_figures.py
The samples file is not committed (19 MB); regenerate it first with
`python -m bench.run ...` and `python -m bench.evaluate ...` as described in
the README. Given the same seeds and SUMO version, the CSV - and therefore
these figures - reproduce exactly.
"""

import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bench.evaluate import auroc, lead_times, percentile

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "..", "results", "full", "samples.csv")

METRICS = [
    ("pora", "PORA", "#0072B2"),
    ("inv_ttc", "inverse TTC", "#D55E00"),
    ("neg_tts_margin", "TTS margin", "#009E73"),
]
INK = "#333333"


def load_rows():
    rows = []
    with open(SAMPLES) as f:
        for r in csv.DictReader(f):
            rows.append({
                "seed": r["seed"], "veh": r["veh"], "t": float(r["t"]),
                "label": int(r["label"]),
                "pora": float(r["pora"]),
                "inv_ttc": float(r["inv_ttc"]),
                "neg_tts_margin": float(r["neg_tts_margin"]),
            })
    return rows


def roc_points(labels, scores):
    pairs = sorted(zip(scores, labels), key=lambda p: -p[0])
    npos = sum(labels)
    nneg = len(labels) - npos
    tps = fps = 0
    xs, ys = [0.0], [0.0]
    prev = None
    for s, l in pairs:
        if prev is not None and s != prev:
            xs.append(fps / nneg)
            ys.append(tps / npos)
        if l:
            tps += 1
        else:
            fps += 1
        prev = s
    xs.append(1.0)
    ys.append(1.0)
    return xs, ys


def fig_roc(rows):
    labels = [r["label"] for r in rows]
    fig, ax = plt.subplots(figsize=(5.6, 5.0))
    ax.plot([0, 1], [0, 1], color="#bbbbbb", linewidth=1, linestyle="--")
    for key, name, color in METRICS:
        scores = [r[key] for r in rows]
        xs, ys = roc_points(labels, scores)
        a = auroc(labels, scores)
        ax.plot(xs, ys, color=color, linewidth=2, label=f"{name} (AUROC {a:.3f})")
    ax.set_xlabel("false positive rate", fontsize=10, color=INK)
    ax.set_ylabel("true positive rate", fontsize=10, color=INK)
    ax.set_title(
        "Predicting a collision within 5 s\n"
        "(60 seeded runs; 258,770 samples; 10,321 positive)",
        fontsize=10.5, color=INK,
    )
    ax.legend(fontsize=9, loc="lower right", framealpha=0.9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(alpha=0.25, linewidth=0.5)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_roc.png"), dpi=160)
    plt.close(fig)


def fig_lead_time(rows):
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    bins = [i * 2.0 for i in range(16)]
    for key, name, color in METRICS:
        neg = [r[key] for r in rows if r["label"] == 0]
        thr = percentile(neg, 95.0)
        leads = lead_times(rows, key, thr)
        med = sorted(leads)[len(leads) // 2] if leads else float("nan")
        ax.hist(
            leads, bins=bins, histtype="step", linewidth=2, color=color,
            label=f"{name} - {len(leads)} vehicles, median {med:.0f} s",
        )
    ax.set_xlabel("warning lead time at 5% false-alarm rate (s)",
                  fontsize=10, color=INK)
    ax.set_ylabel("collision vehicles", fontsize=10, color=INK)
    ax.set_title(
        "The AUROC winner is not the earliest warner",
        fontsize=10.5, color=INK,
    )
    ax.legend(fontsize=8.5, framealpha=0.9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(alpha=0.25, linewidth=0.5)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_lead_time.png"), dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    rows = load_rows()
    fig_roc(rows)
    fig_lead_time(rows)
    print("wrote 2 figures to", HERE)
