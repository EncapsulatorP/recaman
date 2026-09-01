"""Tests for the exact transition trace behind early catalogue holes."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_hole_mechanisms.py"
SPEC = importlib.util.spec_from_file_location("hole_mechanism_analysis", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mechanisms = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mechanisms)


def test_small_trace_respects_unconditional_addition_revisits() -> None:
    stats, causes = mechanisms.run_recurrence(24, {42})
    assert stats[42]["first_visit_step"] == 20
    assert stats[42]["down_chosen"] == 1
    assert stats[42]["up_chosen"] == 1
    assert causes["free_down"] + causes["collision"] + causes["boundary"] == 24


def test_saved_mechanism_result_has_exact_invariants() -> None:
    trace, pairs, summary = mechanisms.build(10_000_000, 10_000_000)
    holes = trace.loc[trace["group"] == "catalogue_hole"]

    assert len(holes) == 103
    assert len(pairs) == 198
    assert not holes["visited"].any()
    assert holes["addition_window_complete"].all()
    assert holes["down_proposals"].sum() == 0
    assert (holes["mechanism"] == "bypassed_addition_only").sum() == 23
    assert (holes["mechanism"] == "no_observed_proposal").sum() == 80
    assert summary["adjacent_controls_visited"] == 110
    assert summary["transition_causes"]["free_down"] == 4_999_986


def test_saved_outputs_are_current() -> None:
    assert mechanisms.main(["--check"]) == 0
