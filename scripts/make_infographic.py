#!/usr/bin/env python3
"""Render the Recaman next-move infographic as a vector asset.

The output is SVG on purpose: it is a few tens of kilobytes instead of a
multi-megabyte screenshot, it stays sharp on any display, it re-colours itself
for dark-mode readers, and every number in it is read from the saved validator
run rather than typed into an image editor.

    python scripts/make_infographic.py
    python scripts/make_infographic.py --check     # CI: fail if stale
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPACE_DIR = REPO_ROOT / "apps" / "space"
sys.path.insert(0, str(SPACE_DIR))

from figures import poster  # noqa: E402
from predictor import load_measurements  # noqa: E402
from recaman import generate  # noqa: E402


DEFAULT_TARGET = REPO_ROOT / "outputs" / "recaman_next_move_infographic.svg"

# Enough steps to contain a well-isolated phase slip for panel 3, while the arc
# panel only ever draws the first two dozen.
POSTER_STEPS = 60_000


def render(steps: int = POSTER_STEPS) -> str:
    return poster(load_measurements(), generate(steps))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--steps", type=int, default=POSTER_STEPS)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing if the target is out of date",
    )
    args = parser.parse_args()

    svg = render(args.steps)

    if args.check:
        current = args.target.read_text(encoding="utf-8") if args.target.exists() else ""
        if current != svg:
            print(f"{args.target} is out of date; re-run without --check")
            return 1
        print(f"{args.target} is up to date")
        return 0

    args.target.parent.mkdir(parents=True, exist_ok=True)
    args.target.write_text(svg, encoding="utf-8")
    print(f"wrote {args.target} ({len(svg.encode('utf-8')) / 1024:.1f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
