#!/usr/bin/env python3
"""Measure Recamán obstruction structure beyond event frequency.

The analysis is descriptive of Benjamin Chaffin's catalogue after 10^612
computed terms.  It measures severity concentration, local isolation,
clustering against a magnitude-matched null, scale stability, and a small
predeclared arithmetic screen.  It does not infer permanence or causation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, spearmanr


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "obstructions.txt"
OUTPUTS = ROOT / "outputs"
EVENTS_PATH = OUTPUTS / "obstruction_anatomy_events.parquet"
SCALES_PATH = OUTPUTS / "obstruction_anatomy_scales.csv"
ARITHMETIC_PATH = OUTPUTS / "obstruction_anatomy_arithmetic.csv"
SUMMARY_PATH = OUTPUTS / "obstruction_anatomy_summary.json"
REPORT_PATH = OUTPUTS / "obstruction_anatomy_report.md"
FIRST_HOLE = 852_655
LIMIT_EXCLUSIVE = 2**32
NULL_BINS = 24
NULL_REPLICATES = 1_000
SEED = 852_655
PRIMES = (2, 3, 5, 7, 11, 13)


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
    if len(events) != 3_103 or int(events.iloc[0]["start"]) != FIRST_HOLE:
        raise ValueError("unexpected Chaffin catalogue shape or first event")
    if events["start"].duplicated().any():
        raise ValueError("duplicate catalogue event starts")
    if (events["start"].iloc[1:].to_numpy() <= events["end"].iloc[:-1].to_numpy()).any():
        raise ValueError("overlapping or unordered catalogue intervals")
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


def gini(values: np.ndarray) -> float:
    ordered = np.sort(values.astype(float))
    count = len(ordered)
    weighted = np.sum((np.arange(1, count + 1) * ordered))
    return float((2.0 * weighted) / (count * ordered.sum()) - (count + 1) / count)


def nearest_log_distance(values: np.ndarray) -> np.ndarray:
    ordered = np.sort(np.log10(values.astype(float)))
    gaps = np.diff(ordered)
    return np.concatenate(
        ([gaps[0]], np.minimum(gaps[:-1], gaps[1:]), [gaps[-1]])
    )


def sample_matched_starts(
    rng: np.random.Generator,
    counts: np.ndarray,
    edges: np.ndarray,
) -> np.ndarray:
    samples: list[np.ndarray] = []
    for index, count in enumerate(counts):
        low = int(np.ceil(10 ** edges[index]))
        high = min(LIMIT_EXCLUSIVE - 1, int(np.ceil(10 ** edges[index + 1])) - 1)
        samples.append(rng.integers(low, high + 1, size=int(count), dtype=np.int64))
    return np.concatenate(samples)


def analyse(
    events: pd.DataFrame,
    null_replicates: int = NULL_REPLICATES,
    seed: int = SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    if null_replicates < 99:
        raise ValueError("null_replicates must be at least 99")

    enriched = events.copy()
    enriched.insert(0, "event_id", np.arange(1, len(events) + 1))
    enriched["previous_gap"] = (
        enriched["start"] - enriched["end"].shift(1) - 1
    ).astype("Int64")
    enriched["next_gap"] = (
        enriched["start"].shift(-1) - enriched["end"] - 1
    ).astype("Int64")
    enriched["isolation_gap"] = pd.concat(
        [enriched["previous_gap"], enriched["next_gap"]], axis=1
    ).min(axis=1)
    enriched["log10_start"] = np.log10(enriched["start"])
    enriched["log10_length"] = np.log10(enriched["length"])
    enriched["log10_isolation_plus_one"] = np.log10(
        enriched["isolation_gap"].astype(float) + 1.0
    )
    enriched["is_range"] = enriched["length"] > 1
    enriched["severity_class"] = pd.cut(
        enriched["length"],
        bins=[0, 1, 9, 99, 999, np.inf],
        labels=["singleton", "2–9", "10–99", "100–999", "≥1,000"],
    ).astype(str)

    usable = enriched.dropna(subset=["isolation_gap"])
    isolation_rho, isolation_p = spearmanr(
        usable["log10_length"], usable["log10_isolation_plus_one"]
    )

    ordered_lengths = np.sort(enriched["length"].to_numpy(dtype=np.int64))
    cumulative_missing = np.cumsum(ordered_lengths)
    enriched_sorted = enriched.sort_values("length", ignore_index=True).copy()
    enriched_sorted["cumulative_event_share"] = (
        np.arange(1, len(enriched_sorted) + 1) / len(enriched_sorted)
    )
    enriched_sorted["cumulative_missing_share"] = (
        cumulative_missing / cumulative_missing[-1]
    )

    top_count = max(1, int(np.ceil(len(enriched) * 0.01)))
    top_one_share = float(
        enriched.nlargest(top_count, "length")["length"].sum()
        / enriched["length"].sum()
    )

    log_edges = np.linspace(
        np.log10(FIRST_HOLE), np.log10(LIMIT_EXCLUSIVE), NULL_BINS + 1
    )
    bin_ids = np.searchsorted(
        log_edges, enriched["log10_start"].to_numpy(), side="right"
    ) - 1
    bin_ids = np.clip(bin_ids, 0, NULL_BINS - 1)
    bin_counts = np.bincount(bin_ids, minlength=NULL_BINS)
    observed_median_nn = float(np.median(nearest_log_distance(enriched["start"].to_numpy())))
    rng = np.random.default_rng(seed)
    null_medians = np.empty(null_replicates, dtype=float)
    for replicate in range(null_replicates):
        null_starts = sample_matched_starts(rng, bin_counts, log_edges)
        null_medians[replicate] = np.median(nearest_log_distance(null_starts))
    clustering_p = float(
        (np.count_nonzero(null_medians <= observed_median_nn) + 1)
        / (null_replicates + 1)
    )
    null_median = float(np.median(null_medians))

    scale_edges = np.linspace(
        np.log10(FIRST_HOLE), np.log10(LIMIT_EXCLUSIVE), 4
    )
    scale_ids = np.searchsorted(
        scale_edges, enriched["log10_start"].to_numpy(), side="right"
    ) - 1
    scale_ids = np.clip(scale_ids, 0, 2)
    scale_rows: list[dict[str, object]] = []
    for scale_id, label in enumerate(("early", "middle", "late")):
        subset = enriched.loc[scale_ids == scale_id]
        scale_rows.append(
            {
                "scale": label,
                "value_low": int(np.ceil(10 ** scale_edges[scale_id])),
                "value_high": min(
                    LIMIT_EXCLUSIVE - 1,
                    int(np.ceil(10 ** scale_edges[scale_id + 1])) - 1,
                ),
                "event_count": len(subset),
                "range_event_count": int(subset["is_range"].sum()),
                "range_event_share": float(subset["is_range"].mean()),
                "missing_values": int(subset["length"].sum()),
                "median_run_length": float(subset["length"].median()),
                "mean_run_length": float(subset["length"].mean()),
                "max_run_length": int(subset["length"].max()),
                "median_isolation_gap": float(subset["isolation_gap"].median()),
            }
        )
    scales = pd.DataFrame(scale_rows)

    arithmetic_rows: list[dict[str, object]] = []
    for prime in PRIMES:
        divisible = int(enriched["start"].mod(prime).eq(0).sum())
        test = binomtest(divisible, len(enriched), 1.0 / prime)
        arithmetic_rows.append(
            {
                "prime": prime,
                "divisible_events": divisible,
                "event_count": len(enriched),
                "observed_share": divisible / len(enriched),
                "uniform_expected_share": 1.0 / prime,
                "observed_to_expected": (divisible / len(enriched)) * prime,
                "raw_two_sided_p": float(test.pvalue),
            }
        )
    arithmetic = pd.DataFrame(arithmetic_rows)
    arithmetic["holm_adjusted_p"] = holm_adjust(
        arithmetic["raw_two_sided_p"].tolist()
    )
    arithmetic["survives_holm_005"] = arithmetic["holm_adjusted_p"] < 0.05

    summary: dict[str, object] = {
        "schema_version": 1,
        "status": "READY_WITH_CAVEATS",
        "source": {
            "path": "obstructions.txt",
            "sha256": sha256(CATALOGUE),
            "upstream": "https://benchaffin.com/recaman/rec-holes-2_32.txt",
            "events": len(enriched),
            "missing_values": int(enriched["length"].sum()),
        },
        "severity": {
            "gini_run_length": gini(enriched["length"].to_numpy()),
            "top_one_percent_event_count": top_count,
            "top_one_percent_missing_share": top_one_share,
            "median_run_length": float(enriched["length"].median()),
            "p95_run_length": float(enriched["length"].quantile(0.95)),
            "p99_run_length": float(enriched["length"].quantile(0.99)),
            "maximum_run_length": int(enriched["length"].max()),
        },
        "isolation": {
            "metric": "Spearman(log10 run length, log10 nearest event gap + 1)",
            "rho": float(isolation_rho),
            "two_sided_p": float(isolation_p),
            "event_count": len(usable),
        },
        "clustering": {
            "metric": "median nearest-neighbour distance in log10(value)",
            "observed": observed_median_nn,
            "matched_null_median": null_median,
            "observed_to_null": observed_median_nn / null_median,
            "empirical_one_sided_p": clustering_p,
            "null_replicates": null_replicates,
            "matching": f"same event count in each of {NULL_BINS} log10(value) bins",
            "seed": seed,
        },
        "arithmetic": {
            "primes_tested": list(PRIMES),
            "multiple_testing": "Holm family-wise correction",
            "significant_after_correction": int(
                arithmetic["survives_holm_005"].sum()
            ),
        },
        "limitations": [
            "Catalogue membership is conditioned on the 10^612-term computation horizon.",
            "Run length is severity on the value axis, not survivor time.",
            "The clustering null matches magnitude but not unknown Recaman landing opportunities.",
            "Arithmetic tests are a small predeclared screen, not a search over formulas.",
            "Associations do not establish the visited-set-saturation mechanism.",
        ],
    }
    return enriched_sorted, scales, arithmetic, summary


def render_report(
    scales: pd.DataFrame, arithmetic: pd.DataFrame, summary: dict[str, object]
) -> str:
    severity = summary["severity"]
    isolation = summary["isolation"]
    clustering = summary["clustering"]
    arithmetic_summary = summary["arithmetic"]
    assert isinstance(severity, dict)
    assert isinstance(isolation, dict)
    assert isinstance(clustering, dict)
    assert isinstance(arithmetic_summary, dict)
    scale_rows = "\n".join(
        f"| {row.scale} | {row.event_count:,} | {row.range_event_share:.1%} | "
        f"{row.mean_run_length:,.1f} | {row.max_run_length:,} | "
        f"{row.median_isolation_gap:,.0f} |"
        for row in scales.itertuples()
    )
    arithmetic_rows = "\n".join(
        f"| {int(row.prime)} | {row.observed_share:.2%} | "
        f"{row.uniform_expected_share:.2%} | {row.observed_to_expected:.3f} | "
        f"{row.holm_adjusted_p:.4g} | "
        f"{'yes' if row.survives_holm_005 else 'no'} |"
        for row in arithmetic.itertuples()
    )
    return f"""# Recamán obstruction anatomy

## Result

The catalogue is not merely becoming more frequent by multiplicative scale.
Its missing values are extremely concentrated in a small number of long runs,
and those long runs occur inside denser event neighbourhoods rather than as
isolated outliers.

- Run-length Gini: **{float(severity['gini_run_length']):.4f}**.
- Largest 1% of events contain **{float(severity['top_one_percent_missing_share']):.1%}** of all catalogued missing values.
- Run length versus nearest-event isolation: **rho = {float(isolation['rho']):.3f}**, `p = {float(isolation['two_sided_p']):.3g}`.
- Median log-neighbour distance is **{float(clustering['observed_to_null']):.1%}** of the magnitude-matched null (`p = {float(clustering['empirical_one_sided_p']):.4g}`, {int(clustering['null_replicates']):,} replicates).

## Scale stability

| Equal-log scale third | Events | Range-event share | Mean run | Maximum run | Median isolation gap |
|---|---:|---:|---:|---:|---:|
{scale_rows}

## Arithmetic screen

| Divisor | Observed | Uniform expectation | Observed/expected | Holm p | Survives 0.05? |
|---:|---:|---:|---:|---:|---|
{arithmetic_rows}

**{int(arithmetic_summary['significant_after_correction'])} of {len(PRIMES)}**
predeclared divisibility tests survive family-wise correction. This is useful
negative evidence against a simple small-prime explanation of event starts.

## Interpretation boundary

The supported statement is structural: severity concentrates and clusters on
the value axis. The catalogue does not contain survivor times or landing
opportunities, so this analysis cannot identify the causal Recamán state that
creates those clusters.

## Reproduce

```bash
python scripts/analyze_obstruction_anatomy.py
python scripts/analyze_obstruction_anatomy.py --check
```
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--null-replicates", type=int, default=NULL_REPLICATES)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    events = parse_catalogue(CATALOGUE)
    event_table, scales, arithmetic, summary = analyse(
        events, null_replicates=args.null_replicates, seed=args.seed
    )
    expected = {
        EVENTS_PATH: event_table,
        SCALES_PATH: scales.to_csv(index=False),
        ARITHMETIC_PATH: arithmetic.to_csv(index=False),
        SUMMARY_PATH: json.dumps(summary, indent=2) + "\n",
        REPORT_PATH: render_report(scales, arithmetic, summary),
    }
    if args.check:
        stale: list[Path] = []
        for path, content in expected.items():
            if not path.exists():
                stale.append(path)
            elif isinstance(content, pd.DataFrame):
                if not pd.read_parquet(path).equals(content):
                    stale.append(path)
            elif path.read_text(encoding="utf-8") != content:
                stale.append(path)
        if stale:
            for path in stale:
                print(f"{path.relative_to(ROOT)} is out of date")
            return 1
        print("obstruction-anatomy results are current")
        return 0

    for path, content in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, pd.DataFrame):
            content.to_parquet(path, index=False)
        else:
            path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
