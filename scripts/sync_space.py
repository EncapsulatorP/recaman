#!/usr/bin/env python3
"""Derive the Space's measurement file from the saved validator run.

The Gradio Space is deployed on its own from `apps/space/`, so it cannot read
`outputs/`. This script projects the numbers it needs out of
`outputs/recaman_wheel_results.json` into `apps/space/measurements.json`, which
keeps the Space self-contained without hard-coding constants by hand.

Run it whenever the validator run is refreshed:

    python scripts/build_space_measurements.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "outputs" / "recaman_wheel_results.json"
DEFAULT_TARGET = REPO_ROOT / "apps" / "space" / "measurements.json"


def slip_rate_from_conditionals(q_prev0: float, q_prev1: float, p_b0: float) -> float:
    """P(b_n == b_{n-1}) given the two conditionals and the b=0 share.

    `q_prev0` is P(b_n = 1 | b_{n-1} = 0) and `q_prev1` is P(b_n = 1 | b_{n-1} = 1),
    so a repeat happens either after a 0 that stays 0, or after a 1 that stays 1.
    """
    return p_b0 * (1.0 - q_prev0) + (1.0 - p_b0) * q_prev1


def build(source: Path) -> dict[str, object]:
    results = json.loads(source.read_text(encoding="utf-8"))

    bit_history = results["step2b_bit_history_wheel"]
    slip = results["step3_phase_slip"]
    theta3 = results["step2a_theta3_wheel"]
    closure = results["step5_closure"]

    q_prev0 = bit_history["q_prev0"]
    q_prev1 = bit_history["q_prev1"]

    horizon = []
    for row in results["step6_stationarity"]:
        horizon.append(
            {
                "n": row["n"],
                "q_prev0": row["q_prev0"],
                "q_prev1": row["q_prev1"],
                "slip_rate": round(
                    slip_rate_from_conditionals(
                        row["q_prev0"], row["q_prev1"], row["emp_p_b0"]
                    ),
                    9,
                ),
            }
        )

    return {
        "source": "outputs/recaman_wheel_results.json",
        "generator": "scripts/build_space_measurements.py",
        "empirical_horizon": results["N_main"],
        "transition": {
            "p00": round(1.0 - q_prev0, 9),
            "p01": q_prev0,
            "p10": round(1.0 - q_prev1, 9),
            "p11": q_prev1,
        },
        "stationary": {
            "p_b0": bit_history["emp_b0"],
            "p_b1": bit_history["emp_b1"],
        },
        "phase_slip": {
            "rate": slip["slip_rate"],
            "count": slip["n_slips"],
            "pairs": slip["n_pairs"],
            "mean_run_length": slip["mean_run_length"],
        },
        "horizon_scan": horizon,
        "theta3_wheel": {
            "verdict": theta3["verdict"],
            "abs_delta_q": theta3["abs_delta_q"],
        },
        "accuracy": {
            "majority_baseline": closure["accuracy_majority_baseline"],
            "previous_bit_only": closure["accuracy_bit_history_only"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing if the target is out of date",
    )
    args = parser.parse_args()

    payload = json.dumps(build(args.source), indent=2) + "\n"

    if args.check:
        current = args.target.read_text(encoding="utf-8") if args.target.exists() else ""
        if current != payload:
            print(f"{args.target} is out of date; re-run without --check")
            return 1
        print(f"{args.target} is up to date")
        return 0

    args.target.write_text(payload, encoding="utf-8")
    print(f"wrote {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
