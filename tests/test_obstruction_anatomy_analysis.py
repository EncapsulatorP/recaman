"""Tests for source-backed obstruction anatomy metrics."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_obstruction_anatomy.py"
SPEC = importlib.util.spec_from_file_location("obstruction_anatomy_analysis", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
anatomy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(anatomy)


def test_anatomy_metrics_are_source_backed_and_internally_consistent() -> None:
    events = anatomy.parse_catalogue(ROOT / "obstructions.txt")
    event_table, scales, arithmetic, summary = anatomy.analyse(
        events, null_replicates=99, seed=852_655
    )

    assert len(event_table) == 3_103
    assert event_table["length"].sum() == 1_277_400
    assert scales["event_count"].sum() == 3_103
    assert scales["missing_values"].sum() == 1_277_400
    assert len(arithmetic) == 6
    assert not arithmetic["survives_holm_005"].any()
    assert summary["severity"]["gini_run_length"] > 0.98
    assert summary["severity"]["top_one_percent_missing_share"] > 0.77
    assert summary["isolation"]["rho"] < 0
    assert summary["clustering"]["observed_to_null"] < 0.10


def test_checked_in_anatomy_outputs_are_current() -> None:
    assert anatomy.main(["--check"]) == 0
