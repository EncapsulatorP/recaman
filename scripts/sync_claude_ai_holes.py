#!/usr/bin/env python3
"""Sync the files that make `apps/space/` self-contained.

The Space is deployed from `apps/space/` with that directory as its own root,
so it cannot read `obstructions.txt`, `outputs/` or `assets/` at run time.
Rather than hand-copying — or hotlinking another repository — every file the
Space needs is projected out of this repository here, and CI fails if any of
them drifts.

Three things are synced:

* `holes.txt` — a verbatim copy of the hole catalogue `obstructions.txt`. The
  Space recomputes the whole structural summary from it, so there is no derived
  copy of those numbers to fall out of date.
* `results.json` — the measured value-side model scores, which cannot be
  recomputed cheaply, read from the saved runs in `outputs/`.
* `assets/online-presence.svg` — the project mark, copied from `assets/`.

    python scripts/sync_space.py
    python scripts/sync_space.py --check     # CI: fail if anything is stale
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPACE_DIR = REPO_ROOT / "apps" / "space"

CATALOGUE = REPO_ROOT / "obstructions.txt"
VERSION_C = REPO_ROOT / "outputs" / "version_c_obstructions_results.json"
RANDOM_MATRIX = REPO_ROOT / "outputs" / "best_obstructions_random_20260512_172100.json"
BRAND_MARK = REPO_ROOT / "assets" / "online-presence.svg"

SPACE_CATALOGUE = SPACE_DIR / "holes.txt"
SPACE_RESULTS = SPACE_DIR / "results.json"
SPACE_BRAND_MARK = SPACE_DIR / "assets" / "online-presence.svg"

# What each Version C dataset actually asks, as documented in the repo README.
DATASET_LABELS = {
    "A": "singleton hole starts",
    "B": "hole-range starts",
    "C": "hole-range ends",
    "D": "gap dynamics between successive holes",
}


def build_results() -> dict[str, object]:
    """Collect the measured value-side scores the Space reports."""
    version_c = json.loads(VERSION_C.read_text(encoding="utf-8"))
    random_matrix = json.loads(RANDOM_MATRIX.read_text(encoding="utf-8"))

    candidate = random_matrix["candidate"]
    dataset = random_matrix["dataset"]
    search = random_matrix["search"]

    return {
        "generator": "scripts/sync_space.py",
        "sources": {
            "catalogue": "obstructions.txt",
            "version_c": "outputs/version_c_obstructions_results.json",
            "random_matrix": "outputs/best_obstructions_random_20260512_172100.json",
        },
        "random_matrix": {
            "script": "scripts/321_210_randmat.py",
            "positives": dataset["positives"],
            "controls": dataset["controls"],
            "feature_dim": dataset["feature_dim"],
            "positive_digit_lengths": dataset["positive_digit_lengths"],
            "controls_per_positive": search["controls_per_positive"],
            "cv_folds": search["cv_folds"],
            "trials": search["trials"],
            "code_auc": candidate["code_auc"],
            "rf_cv_auc_mean": candidate["rf_cv_auc_mean"],
        },
        "version_c": {
            "script": "scripts/321_210_version_c.py",
            "cv_scheme": version_c["cv_scheme"],
            "purge_contexts": version_c["purge_contexts"],
            "datasets": {
                name: {
                    "label": DATASET_LABELS[name],
                    "contexts": payload["contexts"],
                    "examples": payload["examples"],
                    "feature_dim": payload["feature_dim"],
                    "mean_auc": payload["mean_auc"],
                    "fold_auc": payload["auc"],
                }
                for name, payload in sorted(version_c["datasets"].items())
            },
        },
    }


def derived_files() -> dict[Path, bytes]:
    """Map each file the Space needs to the exact bytes it should hold.

    Copies are read, compared and written as bytes so a synced file matches its
    source down to the line endings, whichever platform runs the sync.
    """
    return {
        SPACE_CATALOGUE: CATALOGUE.read_bytes(),
        SPACE_RESULTS: (json.dumps(build_results(), indent=2) + "\n").encode("utf-8"),
        SPACE_BRAND_MARK: BRAND_MARK.read_bytes(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report and fail instead of writing if anything is out of date",
    )
    args = parser.parse_args()

    stale: list[Path] = []
    for target, content in derived_files().items():
        relative = target.relative_to(REPO_ROOT)
        current = target.read_bytes() if target.exists() else None

        if current == content:
            if args.check:
                print(f"up to date: {relative}")
            continue

        if args.check:
            stale.append(relative)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        print(f"wrote {relative}")

    if stale:
        for relative in stale:
            print(f"OUT OF DATE: {relative}")
        print("run `python scripts/sync_space.py` and commit the result")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
