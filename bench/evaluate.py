"""Score every (vehicle, timestep) sample, label it, and evaluate metrics.

Usage:
    python -m bench.evaluate --raw results/raw --out results

Outputs:
    results/samples.csv   one row per scored sample
    results/summary.json  AUROC + lead-time stats per metric

Evaluation:
  * AUROC - probability a random positive sample outranks a random negative
    one (Mann-Whitney with average ranks for ties).
  * Median warning lead time - alarm threshold fixed per metric at the 95th
    percentile of negative-sample scores (5% false-alarm rate); for each
    collision vehicle, lead = collision time minus first alarm time.
"""

import argparse
import csv
import glob
import json
import math
import os
import re
from typing import Dict, List

from .label import collision_times_by_vehicle, label_sample
from .metrics import METRICS
from .xmlio import iter_fcd, read_collisions

CONFLICT_RADIUS = 60.0  # score only vehicles within this range of the junction
FOE_RADIUS = 60.0
HORIZON = 5.0


def collect_samples(raw_dir, stride=1) -> List[Dict]:
    """stride=N scores every Nth FCD timestep (FCD period is 0.5 s)."""
    rows: List[Dict] = []
    for fcd_path in sorted(glob.glob(os.path.join(raw_dir, "fcd_*.xml"))):
        seed = int(re.search(r"fcd_(\d+)\.xml", fcd_path).group(1))
        col_path = os.path.join(raw_dir, "collisions_%05d.xml" % seed)
        first_collision = collision_times_by_vehicle(read_collisions(col_path))
        for step_idx, (t, actors) in enumerate(iter_fcd(fcd_path)):
            if step_idx % stride:
                continue
            near = [
                a for a in actors if math.hypot(a.x, a.y) <= CONFLICT_RADIUS
            ]
            for ego in near:
                label = label_sample(ego.veh_id, t, first_collision, HORIZON)
                if label is None:
                    continue
                foes = [
                    f
                    for f in actors
                    if f.veh_id != ego.veh_id
                    and math.hypot(f.x - ego.x, f.y - ego.y) <= FOE_RADIUS
                ]
                row = {"seed": seed, "veh": ego.veh_id, "t": t, "label": label}
                for name, fn in METRICS.items():
                    row[name] = fn(ego, foes)
                rows.append(row)
    return rows


def auroc(labels: List[int], scores: List[float]) -> float:
    """Mann-Whitney AUROC with average ranks for ties."""
    pairs = sorted(zip(scores, labels), key=lambda p: p[0])
    n = len(pairs)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    npos = sum(l for _, l in pairs)
    nneg = n - npos
    if npos == 0 or nneg == 0:
        return float("nan")
    rank_sum_pos = sum(r for r, (_, l) in zip(ranks, pairs) if l == 1)
    return (rank_sum_pos - npos * (npos + 1) / 2.0) / (npos * nneg)


def percentile(values: List[float], q: float) -> float:
    """Nearest-rank percentile, q in [0, 100]."""
    if not values:
        return float("nan")
    s = sorted(values)
    idx = min(len(s) - 1, max(0, int(math.ceil(q / 100.0 * len(s))) - 1))
    return s[idx]


def lead_times(rows: List[Dict], metric: str, threshold: float) -> List[float]:
    """Warning lead time per collision vehicle at the given threshold."""
    by_veh: Dict[str, List[Dict]] = {}
    for r in rows:
        by_veh.setdefault("%s/%s" % (r["seed"], r["veh"]), []).append(r)

    leads = []
    for _, series in by_veh.items():
        series.sort(key=lambda r: r["t"])
        if not any(r["label"] == 1 for r in series):
            continue
        # Last sample is the closest pre-collision observation retained.
        t_collision_bound = max(r["t"] for r in series if r["label"] == 1)
        alarm_t = None
        for r in series:
            if r[metric] >= threshold:
                alarm_t = r["t"]
                break
        if alarm_t is not None and alarm_t <= t_collision_bound:
            leads.append(t_collision_bound - alarm_t)
    return leads


def median(values: List[float]) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2.0


def evaluate(rows: List[Dict]) -> Dict:
    labels = [r["label"] for r in rows]
    out = {
        "n_samples": len(rows),
        "n_positive": sum(labels),
        "metrics": {},
    }
    for name in METRICS:
        scores = [r[name] for r in rows]
        neg_scores = [r[name] for r in rows if r["label"] == 0]
        thr = percentile(neg_scores, 95.0)
        leads = lead_times(rows, name, thr)
        out["metrics"][name] = {
            "auroc": auroc(labels, scores),
            "alarm_threshold_fpr05": thr,
            "n_warned_collision_vehicles": len(leads),
            "median_lead_time_s": median(leads),
        }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stride", type=int, default=1)
    args = ap.parse_args(argv)

    rows = collect_samples(args.raw, stride=args.stride)
    os.makedirs(args.out, exist_ok=True)

    fields = ["seed", "veh", "t", "label"] + list(METRICS)
    with open(os.path.join(args.out, "samples.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    summary = evaluate(rows)
    with open(os.path.join(args.out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
