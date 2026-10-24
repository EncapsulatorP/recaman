"""Tests for the deep-obstruction multiplicative-scale hypothesis."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "test_deep_obstruction_frequency.py"
SPEC = importlib.util.spec_from_file_location("deep_obstruction_frequency", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
frequency = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(frequency)


def test_catalogue_profile_and_primary_result() -> None:
    events = frequency.parse_catalogue(ROOT / "obstructions.txt")
    assert len(events) == 3_103
    assert events["length"].sum() == 1_277_400
    assert events.iloc[0]["start"] == 852_655

    bins, result = frequency.analyse(events, 24, 999, 852_655)
    assert len(bins) == 24
    assert result["status"] == "CATALOGUE_PROXY_SUPPORTED"
    assert all(row["spearman_rho"] > 0 for row in result["tests"])
    assert all(
        row["late_half_events"] > row["early_half_events"]
        for row in result["tests"]
    )


def test_checked_in_frequency_outputs_are_current() -> None:
    assert frequency.main(["--check"]) == 0
