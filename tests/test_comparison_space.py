"""Evidence and rendering checks for the comparison Space."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


pytest.importorskip("pandas")
pytest.importorskip("plotly")
pytest.importorskip("gradio")
pytest.importorskip("pyarrow")

APP_PATH = Path(__file__).resolve().parents[1] / "apps" / "comparison" / "app.py"
SPEC = importlib.util.spec_from_file_location("recaman_comparison_app", APP_PATH)
assert SPEC is not None and SPEC.loader is not None
comparison = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = comparison
SPEC.loader.exec_module(comparison)


def test_real_comparison_tables_are_loaded() -> None:
    assert len(comparison.SEQUENCE) == 2_801
    assert len(comparison.HOLES) == 3_102
    assert len(comparison.CHECKS) == 6
    assert len(comparison.SUMMARY) == 1


def test_embedding_sequence_matches_independent_recurrence_exactly() -> None:
    assert comparison.SEQUENCE["value_exact"].all()
    assert comparison.SEQUENCE["blocked_exact"].all()
    assert comparison.SEQUENCE["delta"].eq(0).all()
    assert comparison.SEQUENCE["a_n_embedding"].max() == 10_163


def test_every_embedding_reconstruction_check_passes() -> None:
    assert comparison.CHECKS["status"].eq("PASS").all()
    assert comparison.CHECKS["max_abs_error"].eq(0.0).all()
    assert comparison.CHECKS["rows"].sum() == 235_199
    assert comparison.CHECKS["exact_rows"].sum() == 235_199


def test_chaffin_catalogue_is_exact_and_outside_embedding_span() -> None:
    summary = comparison.SUMMARY.iloc[0]
    assert summary["chaffin_event_count"] == 3_102
    assert summary["chaffin_value_count"] == 1_277_399
    assert summary["chaffin_min"] == 930_058
    assert summary["chaffin_max"] == 4_293_242_951
    assert summary["chaffin_events_within_embedding_span"] == 0
    assert comparison.HOLES["coverage_status"].eq("OUTSIDE_EMBEDDING_SPAN").all()


def test_views_expose_exact_matches_and_horizon_boundary() -> None:
    sequence_figure, mismatches = comparison.sequence_view(2_800)
    assert len(sequence_figure.data) == 2
    assert mismatches.empty

    check_figure, checks = comparison.embedding_checks_view()
    assert len(check_figure.data) == 1
    assert len(checks) == 6

    hole_figure, holes, boundary = comparison.chaffin_view(1)
    assert hole_figure.data
    assert len(holes) == 3_102
    assert "0 of 3,102" in boundary
    assert "not testable by this finite embedding" in boundary


def test_validation_report_contains_source_hashes() -> None:
    report = comparison.validation_report()
    assert "Validation status — **PASS**" in report
    assert "2,801/2,801 exact" in report
    for digest in comparison.MANIFEST["embedding_sha256"].values():
        assert digest in report
