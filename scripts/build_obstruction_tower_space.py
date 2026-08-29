"""Build the compact data bundle for the Obstruction & Tower Hugging Face Space."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPACE = ROOT / "apps" / "space"
MEASUREMENTS_PATH = SPACE / "tower_measurements.json"
HOLES_PATH = SPACE / "holes.txt"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> dict:
    logistic = _read_json(ROOT / "outputs" / "recaman_logistic_towers.json")
    grass = _read_json(ROOT / "outputs" / "recaman_grassmannian_tower.json")
    value_side = _read_json(ROOT / "outputs" / "version_c_obstructions_results.json")
    process_side = _read_json(SPACE / "measurements.json")

    return {
        "sources": {
            "logistic": "outputs/recaman_logistic_towers.json",
            "grassmannian": "outputs/recaman_grassmannian_tower.json",
            "value_side": "outputs/version_c_obstructions_results.json",
            "process_side": "outputs/recaman_wheel_results.json",
            "catalogue": "obstructions.txt",
        },
        "signed_tower": {
            "summary": logistic["summary"],
            "benchmark": logistic["logistic_benchmark"],
            "pair_constraints": logistic["pair_constraints"],
        },
        "power_of_two_tower": {
            "vec_dim": grass["two_kernel"]["vec_dim"],
            "stream_length": grass["two_kernel"]["stream_length"],
            "artifact_free_max_level": 7,
            "real": grass["two_kernel"]["real"],
            "null_random": grass["two_kernel"]["null_random"],
            "pure_alternation": grass["two_kernel"]["pure_alternation"],
            "interpretation": grass["two_kernel"]["interpretation"],
        },
        "branch_geometry": grass["branch_grassmannian"],
        "shadow_rank": grass["shadow_rank"],
        "value_side": {
            "summary": value_side["summary"],
            "cv_scheme": value_side["cv_scheme"],
            "purge_contexts": value_side["purge_contexts"],
            "dataset_d": {
                key: value_side["datasets"]["D"][key]
                for key in ("feature_dim", "contexts", "examples", "auc", "mean_auc")
            },
        },
        "process_side": {
            "empirical_horizon": process_side["empirical_horizon"],
            "phase_slip": process_side["phase_slip"],
            "accuracy": process_side["accuracy"],
            "theta3_wheel": process_side["theta3_wheel"],
        },
    }


def _encoded(payload: dict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    expected_json = _encoded(build())
    expected_holes = (ROOT / "obstructions.txt").read_text(encoding="utf-8")

    if args.check:
        mismatches = []
        if not MEASUREMENTS_PATH.exists() or MEASUREMENTS_PATH.read_text(encoding="utf-8") != expected_json:
            mismatches.append(str(MEASUREMENTS_PATH.relative_to(ROOT)))
        if not HOLES_PATH.exists() or HOLES_PATH.read_text(encoding="utf-8") != expected_holes:
            mismatches.append(str(HOLES_PATH.relative_to(ROOT)))
        if mismatches:
            print("out of date: " + ", ".join(mismatches))
            return 1
        print("Obstruction & Tower Space data is current")
        return 0

    MEASUREMENTS_PATH.write_text(expected_json, encoding="utf-8")
    HOLES_PATH.write_text(expected_holes, encoding="utf-8")
    print(f"wrote {MEASUREMENTS_PATH.relative_to(ROOT)}")
    print(f"wrote {HOLES_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
