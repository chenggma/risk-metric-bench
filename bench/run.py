"""Batch runner: one SUMO process per seed, collisions + FCD logged.

Usage:
    python -m bench.run --outdir results/raw --seeds 60 [--end 300]

Each seed writes fcd_<seed>.xml and collisions_<seed>.xml. FCD is sampled
at 0.5 s (device.fcd.period) to keep files tractable.
"""

import argparse
import os
import subprocess
import sys

from .scenario import write_config, write_scenario


def sumo_binary():
    """Locate the sumo binary: PATH first, then the eclipse-sumo wheel."""
    for name in ("sumo",):
        try:
            subprocess.run([name, "--version"], capture_output=True, check=True)
            return name
        except (OSError, subprocess.CalledProcessError):
            pass
    try:
        import sumo  # type: ignore

        cand = os.path.join(os.path.dirname(sumo.__file__), "bin", "sumo")
        if os.path.exists(cand):
            return cand
    except ImportError:
        pass
    raise RuntimeError("no sumo binary found; pip install eclipse-sumo")


def netconvert_binary():
    b = sumo_binary()
    if b == "sumo":
        return "netconvert"
    return os.path.join(os.path.dirname(b), "netconvert")


def run_seed(outdir, seed, end_s, sumo_bin):
    cfg = write_config(outdir, seed, end_s)
    fcd = os.path.join(outdir, "fcd_%05d.xml" % seed)
    col = os.path.join(outdir, "collisions_%05d.xml" % seed)
    subprocess.run(
        [
            sumo_bin,
            "-c", cfg,
            "--fcd-output", fcd,
            "--device.fcd.period", "0.5",
            "--collision-output", col,
            "--no-step-log",
            "--no-warnings",
        ],
        check=True,
        capture_output=True,
    )
    return fcd, col


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--seeds", type=int, default=60)
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--end", type=int, default=300)
    args = ap.parse_args(argv)

    sumo_bin = sumo_binary()
    write_scenario(args.outdir, end_s=args.end, netconvert_bin=netconvert_binary())
    for i in range(args.first_seed, args.first_seed + args.seeds):
        run_seed(args.outdir, i, args.end, sumo_bin)
        if i % 10 == 0:
            print("seed %d done" % i, flush=True)
    print("all %d seeds done" % args.seeds)


if __name__ == "__main__":
    sys.exit(main())
