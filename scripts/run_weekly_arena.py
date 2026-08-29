"""Advance or verify the Recamán champion–challenger season ledger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPACE = ROOT / "apps" / "space"
OUTPUT = SPACE / "weekly_arena.json"
sys.path.insert(0, str(SPACE))

from model_arena import evaluate_weekly_league


def _render(season: int, steps: int) -> str:
    payload = {
        "season": season,
        "evaluation": evaluate_weekly_league(steps),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--steps", type=int, default=200_000)
    parser.add_argument("--advance", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    previous = None
    if args.output.exists():
        previous = json.loads(args.output.read_text(encoding="utf-8"))

    if args.check:
        if previous is None:
            raise SystemExit(f"missing weekly ledger: {args.output}")
        season = int(previous["season"])
        steps = int(previous["evaluation"]["steps"])
    elif args.advance and previous is not None:
        if int(previous["evaluation"]["steps"]) >= 500_000:
            print("weekly horizon is at the current 500,000-step safety ceiling")
            return 0
        season = int(previous["season"]) + 1
        steps = int(previous["evaluation"]["steps"]) + 50_000
    else:
        season = 1
        steps = args.steps

    rendered = _render(season, steps)
    if args.check:
        if args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit("weekly arena ledger is stale; rerun without --check")
        print(f"weekly arena ledger is current (season {season}, n={steps:,})")
        return 0

    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote season {season} through n={steps:,} to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
