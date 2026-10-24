#!/usr/bin/env python3
"""Trace the exact Recamán transition mechanisms behind early catalogue holes.

This is deliberately not a permanence proof.  For each catalogued missing value
up to ``target_cap`` it records every time that value was an addition or
subtraction candidate during an exact finite Recamán run.  Adjacent
non-catalogue integers provide magnitude-matched controls without a fitted
model.

An unvisited target can be missed in only two observed ways:

* it never becomes a candidate; or
* it is the addition candidate while a legal subtraction takes precedence.

If an unvisited positive value ever becomes a legal subtraction candidate, the
recurrence must choose it immediately.  Addition opportunities for a value m
are complete after step m, while future subtraction opportunities remain
right-censored at the finite run horizon.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "obstructions.txt"
OUTPUTS = ROOT / "outputs"
TRACE_PATH = OUTPUTS / "hole_mechanism_trace.csv"
PAIR_PATH = OUTPUTS / "hole_mechanism_pairs.csv"
SUMMARY_PATH = OUTPUTS / "hole_mechanism_summary.json"
REPORT_PATH = OUTPUTS / "hole_mechanism_report.md"
DEFAULT_STEPS = 10_000_000
DEFAULT_TARGET_CAP = 10_000_000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_catalogue_values(path: Path, cap: int) -> list[int]:
    values: list[int] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "-" in line:
            left, right = line.split("-", 1)
            start, end = int(left), int(right)
        else:
            start = end = int(line)
        if end < start:
            raise ValueError(f"reversed catalogue interval: {line}")
        if start > cap:
            continue
        values.extend(range(start, min(end, cap) + 1))
    return sorted(set(values))


def control_values(holes: list[int]) -> tuple[list[dict[str, int | str]], set[int]]:
    hole_set = set(holes)
    rows: list[dict[str, int | str]] = []
    tracked = set(holes)
    for hole in holes:
        for side, value in (("lower", hole - 1), ("upper", hole + 1)):
            if value <= 0 or value in hole_set:
                continue
            rows.append({"hole": hole, "side": side, "control": value})
            tracked.add(value)
    return rows, tracked


def empty_stats() -> dict[str, int | None]:
    return {
        "up_proposals": 0,
        "up_bypassed": 0,
        "up_chosen": 0,
        "down_proposals": 0,
        "down_chosen": 0,
        "down_collision": 0,
        "first_up_proposal_step": None,
        "first_bypass_step": None,
        "first_down_proposal_step": None,
        "first_visit_step": None,
    }


def increment(stats: dict[str, int | None], field: str, step: int) -> None:
    stats[field] = int(stats[field] or 0) + 1
    first_field = {
        "up_proposals": "first_up_proposal_step",
        "up_bypassed": "first_bypass_step",
        "down_proposals": "first_down_proposal_step",
    }.get(field)
    if first_field and stats[first_field] is None:
        stats[first_field] = step


def run_recurrence(
    steps: int, tracked: set[int]
) -> tuple[dict[int, dict[str, int | None]], dict[str, int]]:
    stats = {value: empty_stats() for value in tracked}
    visited = bytearray(1024)
    visited[0] = 1
    current = 0
    transition_counts: Counter[str] = Counter()
    maximum = 0

    for step in range(1, steps + 1):
        down = current - step
        up = current + step
        down_is_free = down > 0 and down < len(visited) and not visited[down]
        if down > 0 and down >= len(visited):
            down_is_free = True

        if down <= 0:
            reason = "boundary"
        elif not down_is_free:
            reason = "collision"
        else:
            reason = "free_down"

        if up in stats:
            item = stats[up]
            increment(item, "up_proposals", step)
            if down_is_free:
                increment(item, "up_bypassed", step)
            else:
                item["up_chosen"] = int(item["up_chosen"] or 0) + 1

        if down in stats:
            item = stats[down]
            increment(item, "down_proposals", step)
            if down_is_free:
                item["down_chosen"] = int(item["down_chosen"] or 0) + 1
            else:
                item["down_collision"] = int(item["down_collision"] or 0) + 1

        chosen = down if down_is_free else up
        transition_counts[reason] += 1
        if chosen >= len(visited):
            visited.extend(b"\x00" * (chosen + 1 - len(visited)))
        # The fallback addition is unconditional and may revisit a value (42 at
        # steps 20 and 24 is the first example).  Only the subtraction branch
        # requires an unseen destination.
        visited[chosen] = 1
        current = chosen
        maximum = max(maximum, chosen)
        if chosen in stats and stats[chosen]["first_visit_step"] is None:
            stats[chosen]["first_visit_step"] = step

    transition_counts["maximum_value"] = maximum
    transition_counts["final_value"] = current
    return stats, dict(transition_counts)


def mechanism_label(row: pd.Series) -> str:
    if bool(row["visited"]):
        return "visited_by_down" if row["down_chosen"] else "visited_by_addition"
    if row["up_bypassed"]:
        return "bypassed_addition_only"
    return "no_observed_proposal"


def build(steps: int, target_cap: int) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    holes = parse_catalogue_values(CATALOGUE, target_cap)
    if not holes:
        raise ValueError("no catalogue values fall within target cap")
    controls, tracked = control_values(holes)
    stats, transitions = run_recurrence(steps, tracked)

    control_set = {int(row["control"]) for row in controls}
    trace_rows: list[dict[str, object]] = []
    for value in sorted(tracked):
        item = stats[value]
        row: dict[str, object] = {
            "value": value,
            "group": "catalogue_hole" if value in set(holes) else "adjacent_control",
            **item,
            "visited": item["first_visit_step"] is not None,
            "addition_window_complete": steps >= value,
        }
        trace_rows.append(row)
    trace = pd.DataFrame(trace_rows)
    trace["mechanism"] = trace.apply(mechanism_label, axis=1)

    by_value = trace.set_index("value")
    pair_rows: list[dict[str, object]] = []
    for pair in controls:
        hole = int(pair["hole"])
        control = int(pair["control"])
        h = by_value.loc[hole]
        c = by_value.loc[control]
        pair_rows.append(
            {
                **pair,
                "hole_mechanism": h["mechanism"],
                "hole_up_proposals": int(h["up_proposals"]),
                "hole_up_bypassed": int(h["up_bypassed"]),
                "control_visited": bool(c["visited"]),
                "control_visit_step": c["first_visit_step"],
                "control_mechanism": c["mechanism"],
                "control_up_proposals": int(c["up_proposals"]),
                "control_up_bypassed": int(c["up_bypassed"]),
            }
        )
    pairs = pd.DataFrame(pair_rows)

    hole_trace = trace[trace["group"] == "catalogue_hole"]
    control_trace = trace[trace["group"] == "adjacent_control"]
    if bool(hole_trace["visited"].any()):
        visited_holes = hole_trace.loc[hole_trace["visited"], "value"].tolist()
        raise AssertionError(f"catalogued holes visited within run: {visited_holes[:10]}")
    if not bool(hole_trace["addition_window_complete"].all()):
        raise AssertionError("steps must cover the complete addition window for every target")

    hole_counts = hole_trace["mechanism"].value_counts().to_dict()
    summary: dict[str, object] = {
        "question": "How were the earliest catalogued holes missed by the exact recurrence?",
        "source": {
            "catalogue": "obstructions.txt",
            "catalogue_sha256": sha256(CATALOGUE),
        },
        "scope": {
            "steps": steps,
            "target_cap": target_cap,
            "catalogue_values": len(holes),
            "first_catalogue_value": holes[0],
            "last_catalogue_value": holes[-1],
            "unique_adjacent_controls": len(control_set),
        },
        "transition_causes": transitions,
        "hole_mechanisms": {key: int(value) for key, value in hole_counts.items()},
        "holes_with_bypassed_addition": int((hole_trace["up_bypassed"] > 0).sum()),
        "holes_with_no_observed_proposal": int((hole_trace["mechanism"] == "no_observed_proposal").sum()),
        "total_hole_bypasses": int(hole_trace["up_bypassed"].sum()),
        "adjacent_controls_visited": int(control_trace["visited"].sum()),
        "adjacent_controls_total": int(len(control_trace)),
        "adjacent_control_visit_rate": float(control_trace["visited"].mean()),
        "invariants": {
            "catalogue_holes_visited": int(hole_trace["visited"].sum()),
            "hole_down_proposals": int(hole_trace["down_proposals"].sum()),
            "hole_chosen_additions": int(hole_trace["up_chosen"].sum()),
            "addition_windows_complete": bool(hole_trace["addition_window_complete"].all()),
        },
        "interpretation_boundary": [
            "The transition trace identifies finite-run missed-opportunity mechanisms, not permanent non-visitation.",
            "Addition opportunities for target m are complete after step m; subtraction opportunities are right-censored at the run horizon.",
            "Adjacent controls validate local contrast but do not create a randomized causal design.",
            "No embedding is used as a substitute for recurrence state.",
        ],
    }
    return trace, pairs, summary


def render_report(summary: dict[str, object]) -> str:
    scope = summary["scope"]
    causes = summary["transition_causes"]
    return f"""# Mechanism-first trace of early Recamán holes

## Question

How were the earliest catalogue holes missed by the exact recurrence, rather
than merely how the catalogue is distributed?

## Finite-run evidence

- Exact recurrence horizon: **{scope['steps']:,} steps**.
- Catalogue targets: **{scope['catalogue_values']:,} values** from
  **{scope['first_catalogue_value']:,}** through **{scope['last_catalogue_value']:,}**.
- Adjacent non-catalogue controls: **{scope['unique_adjacent_controls']:,}**.
- Holes bypassed as an addition candidate at least once:
  **{summary['holes_with_bypassed_addition']:,}**.
- Holes with no observed proposal: **{summary['holes_with_no_observed_proposal']:,}**.
- Total bypass events involving catalogue holes: **{summary['total_hole_bypasses']:,}**.
- Adjacent controls visited: **{summary['adjacent_controls_visited']:,} /
  {summary['adjacent_controls_total']:,}**
  ({summary['adjacent_control_visit_rate']:.1%}).

The recurrence itself decomposed all {scope['steps']:,} transitions into
**{causes.get('free_down', 0):,} legal subtractions**,
**{causes.get('collision', 0):,} collision-forced additions**, and
**{causes.get('boundary', 0):,} boundary-forced additions**.

## What this means

For these targets, the observed explanation is now inspectable per value:
either the target never became a candidate, or it appeared as the addition
candidate but was bypassed because the subtraction candidate was legal.  A
positive, unvisited subtraction candidate cannot be ignored by Recamán's rule;
it would be chosen immediately.

## What this does not mean

This is not a proof that any target is permanently absent.  Addition
opportunities for a value `m` are complete after step `m`, but a future
subtraction opportunity can still occur beyond the {scope['steps']:,}-step
horizon.  The trace therefore establishes finite causal transition history,
not infinite-horizon causation or permanence.

## Reproduce

```bash
python scripts/analyze_hole_mechanisms.py
python scripts/analyze_hole_mechanisms.py --check
```
"""


def serialize(trace: pd.DataFrame, pairs: pd.DataFrame, summary: dict[str, object]) -> dict[Path, bytes]:
    return {
        TRACE_PATH: trace.to_csv(index=False).encode("utf-8"),
        PAIR_PATH: pairs.to_csv(index=False).encode("utf-8"),
        SUMMARY_PATH: (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        REPORT_PATH: render_report(summary).encode("utf-8"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--target-cap", type=int, default=DEFAULT_TARGET_CAP)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.steps < args.target_cap:
        parser.error("--steps must be at least --target-cap to complete addition windows")

    trace, pairs, summary = build(args.steps, args.target_cap)
    payloads = serialize(trace, pairs, summary)
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, data in payloads.items() if not path.exists() or path.read_bytes() != data]
        if stale:
            raise SystemExit(f"stale mechanism outputs: {', '.join(stale)}")
        print("hole-mechanism results are current")
        return 0

    OUTPUTS.mkdir(exist_ok=True)
    for path, data in payloads.items():
        path.write_bytes(data)
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
