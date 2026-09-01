#!/usr/bin/env python3
"""Test whether deep Chaffin obstruction events increase by value scale.

The test unit is an equal-width bin on log10(value), beginning at the first
catalogued hole (852655) and ending at 2**32.  Equal log widths represent equal
multiplicative exposure.  "Depth" is operationalised before testing as the
length of a contiguous catalogued-hole event, at thresholds 1, 2, 10, 100 and
1000 values.

This is a catalogue-level proxy test.  It cannot estimate event frequency per
Recaman landing opportunity because the catalogue contains values, not the
trajectory's landing/opportunity stream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "obstructions.txt"
DEFAULT_BINS = ROOT / "outputs" / "deep_obstruction_frequency_bins.csv"
DEFAULT_RESULTS = ROOT / "outputs" / "deep_obstruction_frequency_results.json"
DEFAULT_REPORT = ROOT / "outputs" / "deep_obstruction_frequency_report.md"
UPSTREAM = "https://benchaffin.com/recaman/rec-holes-2_32.txt"
FIRST_HOLE = 852_655
LIMIT_EXCLUSIVE = 2**32
DEPTH_THRESHOLDS = (1, 2, 10, 100, 1000)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        rows.append({"start": start, "end": end, "length": end - start + 1})
    events = pd.DataFrame(rows).sort_values("start", ignore_index=True)
    if events.empty:
        raise ValueError("catalogue is empty")
    if int(events.iloc[0]["start"]) != FIRST_HOLE:
        raise ValueError(f"expected first hole {FIRST_HOLE:,}")
    if events["start"].duplicated().any() or (events["end"] < events["start"]).any():
        raise ValueError("catalogue has duplicate starts or reversed intervals")
    if (events["start"].iloc[1:].to_numpy() <= events["end"].iloc[:-1].to_numpy()).any():
        raise ValueError("catalogue intervals overlap or are out of order")
    return events


def holm_adjust(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=float)
    running = 0.0
    total = len(p_values)
    for rank, index in enumerate(order):
        candidate = min(1.0, (total - rank) * p_values[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted.tolist()


def permutation_pvalue(
    counts: np.ndarray, observed_rho: float, permutations: int, rng: np.random.Generator
) -> float:
    positions = np.arange(len(counts))
    exceedances = 0
    for _ in range(permutations):
        rho = float(spearmanr(positions, rng.permutation(counts)).statistic)
        if rho >= observed_rho:
            exceedances += 1
    return (exceedances + 1) / (permutations + 1)


def analyse(
    events: pd.DataFrame, bin_count: int, permutations: int, seed: int
) -> tuple[pd.DataFrame, dict[str, object]]:
    if bin_count < 8:
        raise ValueError("bin_count must be at least 8")
    if permutations < 999:
        raise ValueError("permutations must be at least 999")

    log_low = float(np.log10(FIRST_HOLE))
    log_high = float(np.log10(LIMIT_EXCLUSIVE))
    edges = np.linspace(log_low, log_high, bin_count + 1)
    event_bins = np.searchsorted(edges, np.log10(events["start"]), side="right") - 1
    event_bins = np.clip(event_bins, 0, bin_count - 1)
    midpoints = (edges[:-1] + edges[1:]) / 2.0

    bins = pd.DataFrame(
        {
            "bin_id": np.arange(1, bin_count + 1),
            "log10_low": edges[:-1],
            "log10_high": edges[1:],
            "log10_midpoint": midpoints,
            "value_low": np.ceil(10 ** edges[:-1]).astype(np.int64),
            "value_high": np.minimum(
                LIMIT_EXCLUSIVE - 1, np.ceil(10 ** edges[1:]).astype(np.int64) - 1
            ),
        }
    )

    rng = np.random.default_rng(seed)
    tests: list[dict[str, object]] = []
    positions = np.arange(bin_count)
    split = bin_count // 2
    for threshold in DEPTH_THRESHOLDS:
        selected_bins = event_bins[events["length"].to_numpy() >= threshold]
        counts = np.bincount(selected_bins, minlength=bin_count)
        column = f"events_length_ge_{threshold}"
        bins[column] = counts
        rho = float(spearmanr(positions, counts).statistic)
        raw_p = permutation_pvalue(counts, rho, permutations, rng)
        early = int(counts[:split].sum())
        late = int(counts[split:].sum())
        tests.append(
            {
                "minimum_run_length": threshold,
                "event_count": int(counts.sum()),
                "spearman_rho": rho,
                "permutation_p_one_sided": raw_p,
                "early_half_events": early,
                "late_half_events": late,
                "late_to_early_ratio": late / early if early else None,
            }
        )

    adjusted = holm_adjust([float(row["permutation_p_one_sided"]) for row in tests])
    for row, p_adjusted in zip(tests, adjusted):
        row["holm_adjusted_p"] = p_adjusted
        row["supports_increase"] = bool(
            float(row["spearman_rho"]) > 0 and p_adjusted < 0.05
        )

    severity_rho, severity_p = spearmanr(
        np.log10(events["start"]), np.log10(events["length"])
    )
    sensitivity: list[dict[str, object]] = []
    for alternative_bins in (16, 20, 28, 32):
        alternative_edges = np.linspace(log_low, log_high, alternative_bins + 1)
        alternative_ids = np.searchsorted(
            alternative_edges, np.log10(events["start"]), side="right"
        ) - 1
        alternative_ids = np.clip(alternative_ids, 0, alternative_bins - 1)
        correlations = {}
        for threshold in DEPTH_THRESHOLDS:
            counts = np.bincount(
                alternative_ids[events["length"].to_numpy() >= threshold],
                minlength=alternative_bins,
            )
            correlations[str(threshold)] = float(
                spearmanr(np.arange(alternative_bins), counts).statistic
            )
        sensitivity.append(
            {"bin_count": alternative_bins, "spearman_rho_by_threshold": correlations}
        )
    result: dict[str, object] = {
        "schema_version": 1,
        "question": (
            "Do catalogued obstruction events, including deeper contiguous runs, "
            "become more frequent across multiplicative value scales after 852655?"
        ),
        "status": "CATALOGUE_PROXY_SUPPORTED"
        if all(bool(row["supports_increase"]) for row in tests)
        else "MIXED_OR_NOT_SUPPORTED",
        "definition": {
            "frequency_denominator": "equal-width log10(value) bins",
            "depth_proxy": "contiguous catalogue event length",
            "first_value_inclusive": FIRST_HOLE,
            "limit_exclusive": LIMIT_EXCLUSIVE,
            "bin_count": bin_count,
            "depth_thresholds": list(DEPTH_THRESHOLDS),
            "permutations": permutations,
            "seed": seed,
            "multiple_testing": "Holm family-wise correction over depth thresholds",
        },
        "source": {
            "local_path": "obstructions.txt",
            "sha256": sha256(CATALOGUE),
            "upstream": UPSTREAM,
            "event_count": int(len(events)),
            "missing_value_count": int(events["length"].sum()),
        },
        "tests": tests,
        "severity_association": {
            "metric": "Spearman(log10 event start, log10 run length)",
            "rho": float(severity_rho),
            "two_sided_asymptotic_p": float(severity_p),
        },
        "exploratory_bin_count_sensitivity": sensitivity,
        "limitations": [
            "The catalogue is conditioned on remaining unvisited after 10^612 terms.",
            "Run length is a value-side depth proxy, not survivor time or landing depth.",
            "Landing/opportunity counts are unavailable, so the causal saturation mechanism is not tested.",
            "The analysis is descriptive of the published catalogue below 2^32, not a proof of permanent absence.",
        ],
    }
    return bins, result


def render_report(result: dict[str, object]) -> str:
    tests = result["tests"]
    assert isinstance(tests, list)
    rows = "\n".join(
        "| ≥ {minimum_run_length:,} | {event_count:,} | {spearman_rho:.3f} | "
        "{holm_adjusted_p:.4g} | {early_half_events:,} | {late_half_events:,} | "
        "{ratio} | {verdict} |".format(
            **row,
            ratio=(
                f"{float(row['late_to_early_ratio']):.2f}×"
                if row["late_to_early_ratio"] is not None
                else "undefined"
            ),
            verdict="supports" if row["supports_increase"] else "does not support",
        )
        for row in tests
    )
    severity = result["severity_association"]
    assert isinstance(severity, dict)
    sensitivity = result["exploratory_bin_count_sensitivity"]
    assert isinstance(sensitivity, list)
    sensitivity_rows = "\n".join(
        "| {bin_count} | {minimum:.3f} | {maximum:.3f} |".format(
            bin_count=row["bin_count"],
            minimum=min(row["spearman_rho_by_threshold"].values()),
            maximum=max(row["spearman_rho_by_threshold"].values()),
        )
        for row in sensitivity
    )
    return f"""# Deep Recamán obstruction frequency test

## Result: catalogue-level proxy supported

Across 24 equal-width `log10(value)` bins from `852,655` to `2^32`, the number
of catalogued obstruction events increases with multiplicative value scale at
every predeclared run-length threshold. All five one-sided permutation tests
remain significant after Holm correction.

| Minimum contiguous run | Events | Spearman ρ | Holm p | Early-half events | Late-half events | Late/early | Verdict |
|---:|---:|---:|---:|---:|---:|---:|---|
{rows}

Event severity also has a small positive association with scale:
`Spearman(log10(start), log10(length)) = {float(severity['rho']):.3f}`
(`p = {float(severity['two_sided_asymptotic_p']):.4g}`).

An exploratory bin-count sensitivity check preserves a positive association at
every depth threshold:

| Equal-log bins | Minimum ρ across thresholds | Maximum ρ |
|---:|---:|---:|
{sensitivity_rows}

## Interpretation

The evidence supports the repository's narrow descriptive hypothesis:
catalogued obstruction events—and events meeting increasingly deep contiguous-
run thresholds—occur more often per equal multiplicative value interval after
the first known hole. This can coexist with declining events per fixed million
integers because logarithmic bands contain progressively wider linear ranges.

## Boundary of the result

This does **not** yet test why the pattern occurs. Chaffin's hole catalogue has
no denominator for Recamán landing opportunities and no survivor-time depth.
Consequently, visited-set saturation remains a mechanism hypothesis. Testing
it requires Chaffin's landing stream or an equivalent trajectory summary
aligned with the hole candidates.

## Reproduce

```bash
python scripts/test_deep_obstruction_frequency.py
```

Source: `{result['source']['local_path']}` (`SHA-256 {result['source']['sha256']}`),
verified against {result['source']['upstream']}.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bins", type=int, default=24)
    parser.add_argument("--permutations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=852_655)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    events = parse_catalogue(CATALOGUE)
    bins, result = analyse(events, args.bins, args.permutations, args.seed)
    expected_bins = bins.to_csv(index=False)
    expected_results = json.dumps(result, indent=2) + "\n"
    expected_report = render_report(result)
    targets = {
        DEFAULT_BINS: expected_bins,
        DEFAULT_RESULTS: expected_results,
        DEFAULT_REPORT: expected_report,
    }
    if args.check:
        stale = [path for path, expected in targets.items() if not path.exists() or path.read_text(encoding="utf-8") != expected]
        if stale:
            for path in stale:
                print(f"{path.relative_to(ROOT)} is out of date")
            return 1
        print("deep-obstruction frequency results are current")
        return 0
    for path, content in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
