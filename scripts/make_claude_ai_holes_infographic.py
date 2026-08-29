#!/usr/bin/env python3
"""Render the hole-catalogue infographic — Claude.ai version.

This is a separate asset from `scripts/make_infographic.py`, which renders the
process-side next-move poster. That one is about the obstruction bit `b(n)`;
this one is about the absolute holes, the integers the sequence never reaches.
Both are kept; the rendered poster carries a watermark naming this variant.

The output is SVG on purpose: a few tens of kilobytes instead of a
multi-megabyte screenshot, sharp on any display, legible in dark mode, and
every number in it read from `obstructions.txt` and the saved runs in
`outputs/` rather than typed into an image editor.

    python scripts/make_claude_ai_holes_infographic.py
    python scripts/make_claude_ai_holes_infographic.py --check     # CI: fail if stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPACE_DIR = REPO_ROOT / "apps" / "claude_ai_holes"
sys.path.insert(0, str(SPACE_DIR))

from hole_figures import poster  # noqa: E402
from holes import load_catalogue  # noqa: E402
from sequence import walk  # noqa: E402


DEFAULT_TARGET = REPO_ROOT / "outputs" / "recaman_holes_infographic_claude-ai.svg"
RESULTS = SPACE_DIR / "results.json"

# Only the arc panel uses the walk, and it draws two dozen steps.
WALK_STEPS = 24


def render() -> str:
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    return poster(load_catalogue(), results, walk(WALK_STEPS))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing if the target is out of date",
    )
    args = parser.parse_args()

    # Written as bytes so the file is identical whichever platform renders it.
    payload = render().encode("utf-8")

    if args.check:
        current = args.target.read_bytes() if args.target.exists() else b""
        if current != payload:
            print(f"{args.target} is out of date; re-run without --check")
            return 1
        print(f"{args.target} is up to date")
        return 0

    args.target.parent.mkdir(parents=True, exist_ok=True)
    args.target.write_bytes(payload)
    print(f"wrote {args.target} ({len(payload) / 1024:.1f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
