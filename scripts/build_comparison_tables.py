#!/usr/bin/env python3
"""Build source-backed comparison tables for the independent-check Space."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "comparison"
EMBEDDING_DIR = APP_DIR / "source" / "embeddings"
VIEWER_DIR = APP_DIR / "viewer"
CATALOGUE = ROOT / "obstructions.txt"

EXPECTED_SHA256 = {
    "arc_lift.npz": "bc59999d42c2eec3f33b9030aae12add3f9a230552fcb9b1b55a65f9f94ea713",
    "delay_tau2.npz": "ca7a8e6b32646b2810214c7db608760d12999529c8be887354fb16a00e92d96b",
    "metadata.json": "c15d6d303fe37d6c37a309f436f69228263423b73e17be021927f6168b4a4423",
    "recaman_sequence.npz": "e0f880bb425580e6bb50d7d2b6068d54403a17ff1aeca887c8ef942ee9a72e8d",
    "spatiotemporal.npz": "425283939cd9ade61e5252bc8c757fa4b4121908f732adced7ab4057406f4abc",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources() -> dict[str, str]:
    actual = {name: sha256(EMBEDDING_DIR / name) for name in EXPECTED_SHA256}
    mismatches = {
        name: {"expected": EXPECTED_SHA256[name], "actual": digest}
        for name, digest in actual.items()
        if digest != EXPECTED_SHA256[name]
    }
    if mismatches:
        raise ValueError(f"embedding checksum mismatch: {mismatches}")
    return actual


def generate_recaman(steps: int) -> tuple[np.ndarray, np.ndarray]:
    values = np.zeros(steps + 1, dtype=np.int64)
    blocked = np.zeros(steps + 1, dtype=np.int8)
    visited = {0}
    for n in range(1, steps + 1):
        candidate = int(values[n - 1]) - n
        if candidate > 0 and candidate not in visited:
            values[n] = candidate
        else:
            values[n] = int(values[n - 1]) + n
            blocked[n] = 1
        visited.add(int(values[n]))
    return values, blocked


def parse_catalogue(path: Path) -> pd.DataFrame:
    rows: list[dict[str, int]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "-" in line:
            start_text, end_text = line.split("-", 1)
            start, end = int(start_text), int(end_text)
        else:
            start = end = int(line)
        if end < start:
            raise ValueError(f"reversed catalogue interval: {line}")
        rows.append(
            {
                "event_id": len(rows) + 1,
                "start": start,
                "end": end,
                "length": end - start + 1,
            }
        )
    return pd.DataFrame(rows)


def delay_points(values: np.ndarray, tau: int) -> np.ndarray:
    return np.column_stack(
        [values[: -2 * tau], values[tau:-tau], values[2 * tau :]]
    ).astype(float)


def spatiotemporal_points(values: np.ndarray, blocked: np.ndarray) -> np.ndarray:
    indices = np.arange(1, len(values), dtype=float)
    delta = np.diff(values).astype(float)
    signed_step = np.where(blocked[1:] == 1, delta, -delta)
    return np.column_stack([indices, values[1:].astype(float), signed_step])


def arc_lift_points(
    values: np.ndarray,
    blocked: np.ndarray,
    samples_per_arc: int,
    twist: float,
    elevation_scale: float,
) -> tuple[np.ndarray, np.ndarray]:
    point_rows: list[np.ndarray] = []
    blocked_rows: list[np.ndarray] = []
    total_steps = len(values) - 1
    max_gap = max(1.0, float(np.max(np.abs(np.diff(values)))))
    height_scale = elevation_scale / max_gap
    for n in range(1, len(values)):
        start, end = float(values[n - 1]), float(values[n])
        radius = abs(end - start) / 2.0
        center = (start + end) / 2.0
        theta = (
            np.linspace(np.pi, 0.0, samples_per_arc)
            if end >= start
            else np.linspace(0.0, np.pi, samples_per_arc)
        )
        x = center + radius * np.cos(theta)
        y = radius * np.sin(theta)
        z = np.full_like(theta, (n - 1) * elevation_scale)
        z += np.linspace(0.0, radius * height_scale, samples_per_arc)
        angle = twist * (n / total_steps) * 2.0 * np.pi
        cos_angle, sin_angle = np.cos(angle), np.sin(angle)
        x, y = x * cos_angle - y * sin_angle, x * sin_angle + y * cos_angle
        point_rows.append(np.column_stack([x, y, z]))
        blocked_rows.append(np.full(samples_per_arc, blocked[n], dtype=np.int8))
    return np.vstack(point_rows), np.concatenate(blocked_rows)


def check_row(
    name: str,
    source_file: str,
    actual: np.ndarray,
    expected: np.ndarray,
    source_hashes: dict[str, str],
) -> dict[str, object]:
    if actual.shape != expected.shape:
        return {
            "check": name,
            "rows": len(actual),
            "exact_rows": 0,
            "max_abs_error": float("inf"),
            "status": "FAIL",
            "source_file": source_file,
            "sha256": source_hashes[source_file],
        }
    difference = np.abs(actual.astype(float) - expected.astype(float))
    row_match = np.all(np.isclose(actual, expected, rtol=0.0, atol=1e-12), axis=-1)
    return {
        "check": name,
        "rows": len(actual),
        "exact_rows": int(row_match.sum()),
        "max_abs_error": float(difference.max(initial=0.0)),
        "status": "PASS" if bool(row_match.all()) else "FAIL",
        "source_file": source_file,
        "sha256": source_hashes[source_file],
    }


def build() -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    hashes = verify_sources()
    metadata = json.loads((EMBEDDING_DIR / "metadata.json").read_text(encoding="utf-8"))
    embedded = np.load(EMBEDDING_DIR / "recaman_sequence.npz")
    steps = int(metadata["steps"])
    reference_values, reference_blocked = generate_recaman(steps)

    embedded_steps = embedded["step"]
    embedded_values = embedded["value"]
    embedded_blocked = embedded["blocked"]
    sequence = pd.DataFrame(
        {
            "n": embedded_steps,
            "a_n_reference": reference_values,
            "a_n_embedding": embedded_values,
            "delta": embedded_values - reference_values,
            "value_exact": embedded_values == reference_values,
            "blocked_reference": reference_blocked,
            "blocked_embedding": embedded_blocked,
            "blocked_exact": embedded_blocked == reference_blocked,
        }
    )

    delay = np.load(EMBEDDING_DIR / "delay_tau2.npz")
    spatiotemporal = np.load(EMBEDDING_DIR / "spatiotemporal.npz")
    arc = np.load(EMBEDDING_DIR / "arc_lift.npz")
    expected_arc_points, expected_arc_blocked = arc_lift_points(
        reference_values,
        reference_blocked,
        int(metadata["arc_lift"]["samples_per_arc"]),
        float(metadata["arc_lift"]["twist"]),
        float(metadata["arc_lift"]["elevation_scale"]),
    )
    checks = [
        check_row(
            "Recamán values",
            "recaman_sequence.npz",
            embedded_values.reshape(-1, 1),
            reference_values.reshape(-1, 1),
            hashes,
        ),
        check_row(
            "Blocked-step bits",
            "recaman_sequence.npz",
            embedded_blocked.reshape(-1, 1),
            reference_blocked.reshape(-1, 1),
            hashes,
        ),
        check_row(
            "Delay embedding τ=2",
            "delay_tau2.npz",
            delay["points"],
            delay_points(reference_values, int(metadata["delay"]["tau"])),
            hashes,
        ),
        check_row(
            "Spatiotemporal embedding",
            "spatiotemporal.npz",
            spatiotemporal["points"],
            spatiotemporal_points(reference_values, reference_blocked),
            hashes,
        ),
        check_row(
            "Arc-lift embedding",
            "arc_lift.npz",
            arc["points"],
            expected_arc_points,
            hashes,
        ),
        check_row(
            "Arc-lift blocked labels",
            "arc_lift.npz",
            arc["blocked"].reshape(-1, 1),
            expected_arc_blocked.reshape(-1, 1),
            hashes,
        ),
    ]
    fits = pd.DataFrame(checks)

    holes = parse_catalogue(CATALOGUE)
    holes = holes.sort_values("start", ignore_index=True)
    holes["event_id"] = np.arange(1, len(holes) + 1)
    previous_end = holes["end"].shift(1)
    holes["gap_from_previous"] = (holes["start"] - previous_end - 1).astype(
        "Int64"
    )
    holes["log10_start"] = np.log10(holes["start"])
    holes["log10_gap_plus_one"] = np.log10(
        holes["gap_from_previous"].fillna(0).astype(float) + 1.0
    )
    holes["log10_length"] = np.log10(holes["length"])
    holes["cumulative_missing_values"] = holes["length"].cumsum()
    observed_values = set(map(int, embedded_values))
    embedded_min, embedded_max = int(embedded_values.min()), int(embedded_values.max())
    holes["within_embedding_value_span"] = (
        holes["start"].le(embedded_max) & holes["end"].ge(embedded_min)
    )
    holes["observed_event_start"] = holes["start"].isin(observed_values)
    holes["coverage_status"] = np.where(
        holes["within_embedding_value_span"],
        "WITHIN_VALUE_SPAN",
        "OUTSIDE_EMBEDDING_SPAN",
    )

    # An interpretable feature embedding of every Chaffin event.  These are
    # catalogue coordinates, not Recaman trajectory coordinates and not model
    # predictions: x=value scale, y=preceding empty gap, z=run length.
    obstruction_features = holes[
        [
            "event_id",
            "start",
            "end",
            "length",
            "gap_from_previous",
            "log10_start",
            "log10_gap_plus_one",
            "log10_length",
            "cumulative_missing_values",
        ]
    ].copy()

    band_rows: list[dict[str, object]] = []
    first_hole = int(holes["start"].min())
    last_hole = int(holes["end"].max())
    catalogue_limit_exclusive = 2**32
    first_power = int(np.floor(np.log10(first_hole)))
    last_power = int(np.floor(np.log10(last_hole)))
    for power in range(first_power, last_power + 1):
        low = 10**power
        high = min(catalogue_limit_exclusive - 1, 10 ** (power + 1) - 1)
        starts = holes.loc[holes["start"].between(low, high)].copy()
        overlapping = holes.loc[holes["start"].le(high) & holes["end"].ge(low)]
        missing = int(
            sum(
                max(0, min(int(row.end), high) - max(int(row.start), low) + 1)
                for row in overlapping.itertuples()
            )
        )
        width = high - low + 1
        event_count = len(starts)
        range_events = int(starts["length"].gt(1).sum())
        band_rows.append(
            {
                "band": f"{low:,}–{high:,}",
                "low": low,
                "high": high,
                "width": width,
                "event_starts": event_count,
                "range_events": range_events,
                "missing_values": missing,
                "run_extension_values": max(0, missing - event_count),
                "events_per_million": event_count / width * 1_000_000,
                "missing_values_per_million": missing / width * 1_000_000,
                "range_share_of_events": range_events / event_count if event_count else 0.0,
                "extension_share_of_missing": (
                    max(0, missing - event_count) / missing if missing else 0.0
                ),
                "median_event_length": float(starts["length"].median()) if event_count else 0.0,
                "max_event_length": int(starts["length"].max()) if event_count else 0,
            }
        )
    frequency_bands = pd.DataFrame(band_rows)

    summary = pd.DataFrame(
        [
            {
                "embedding_steps": steps,
                "embedding_rows": len(sequence),
                "embedding_value_min": embedded_min,
                "embedding_value_max": embedded_max,
                "sequence_value_matches": int(sequence["value_exact"].sum()),
                "sequence_blocked_matches": int(sequence["blocked_exact"].sum()),
                "embedding_checks_passed": int(fits["status"].eq("PASS").sum()),
                "embedding_checks_total": len(fits),
                "chaffin_event_count": len(holes),
                "chaffin_value_count": int(holes["length"].sum()),
                "chaffin_min": int(holes["start"].min()),
                "chaffin_max": int(holes["end"].max()),
                "chaffin_events_within_embedding_span": int(
                    holes["within_embedding_value_span"].sum()
                ),
                "catalogue_feature_events_covered": len(obstruction_features),
                "catalogue_feature_event_coverage": 1.0,
                "overall_status": (
                    "PASS" if fits["status"].eq("PASS").all() else "FAIL"
                ),
            }
        ]
    )
    manifest = {
        "generator": "scripts/build_comparison_tables.py",
        "embedding_source": "https://huggingface.co/datasets/kugguk/recaman-independent-check-bundle/tree/main/embeddings",
        "catalogue_source": "obstructions.txt",
        "catalogue_upstream": "https://benchaffin.com/recaman/rec-holes-2_32.txt",
        "catalogue_limit_exclusive": catalogue_limit_exclusive,
        "catalogue_sha256": sha256(CATALOGUE),
        "embedding_sha256": hashes,
        "tables": {
            "sequence": "viewer/sequence/sequence.parquet",
            "holes": "viewer/holes/chaffin_events.parquet",
            "fits": "viewer/fits/embedding_checks.parquet",
            "summary": "viewer/summary/summary.parquet",
            "obstruction_features": "viewer/obstructions/features.parquet",
            "frequency_bands": "viewer/obstructions/frequency_bands.parquet",
        },
    }
    return {
        "sequence": sequence,
        "holes": holes,
        "fits": fits,
        "summary": summary,
        "obstruction_features": obstruction_features,
        "frequency_bands": frequency_bands,
    }, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    tables, manifest = build()
    targets = {
        "sequence": VIEWER_DIR / "sequence" / "sequence.parquet",
        "holes": VIEWER_DIR / "holes" / "chaffin_events.parquet",
        "fits": VIEWER_DIR / "fits" / "embedding_checks.parquet",
        "summary": VIEWER_DIR / "summary" / "summary.parquet",
        "obstruction_features": VIEWER_DIR / "obstructions" / "features.parquet",
        "frequency_bands": VIEWER_DIR / "obstructions" / "frequency_bands.parquet",
    }
    manifest_path = VIEWER_DIR / "manifest.json"
    if args.check:
        for name, expected in tables.items():
            target = targets[name]
            if not target.exists() or not pd.read_parquet(target).equals(expected):
                print(f"{target} is out of date")
                return 1
        expected_manifest = json.dumps(manifest, indent=2) + "\n"
        if not manifest_path.exists() or manifest_path.read_text(encoding="utf-8") != expected_manifest:
            print(f"{manifest_path} is out of date")
            return 1
        print("comparison tables are current")
        return 0
    for name, table in tables.items():
        target = targets[name]
        target.parent.mkdir(parents=True, exist_ok=True)
        table.to_parquet(target, index=False)
        print(f"wrote {target.relative_to(ROOT)} ({len(table):,} rows)")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
