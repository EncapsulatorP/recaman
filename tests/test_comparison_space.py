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
    assert len(comparison.HOLES) == 3_103
    assert len(comparison.OBSTRUCTION_FEATURES) == 3_103
    assert len(comparison.FREQUENCY_BANDS) == 5
    assert len(comparison.DEEP_FREQUENCY_TESTS) == 5
    assert len(comparison.ANATOMY_EVENTS) == 3_103
    assert len(comparison.ANATOMY_SCALES) == 3
    assert len(comparison.ANATOMY_ARITHMETIC) == 6
    assert len(comparison.ANATOMY_SUMMARY) == 1
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
    assert summary["chaffin_event_count"] == 3_103
    assert summary["chaffin_value_count"] == 1_277_400
    assert summary["chaffin_min"] == 852_655
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
    assert len(holes) == 3_103
    assert "0 of 3,103" in boundary
    assert "not testable by this finite embedding" in boundary


def test_obstruction_embedding_covers_catalogue_and_decomposes_frequency() -> None:
    feature_figure, features = comparison.obstruction_feature_view()
    assert feature_figure.data
    assert len(features) == 3_103
    assert features.iloc[0]["start"] == 852_655
    assert features["event_id"].is_unique

    frequency_figure, bands, tests, explanation = comparison.frequency_view()
    assert frequency_figure.data
    assert bands["missing_values"].sum() == 1_277_400
    assert (bands["missing_values"] >= bands["event_starts"]).all()
    assert tests["supports_increase"].all()
    assert "per equal multiplicative" in explanation


def test_validation_report_contains_source_hashes() -> None:
    report = comparison.validation_report()
    assert "Validation status — **PASS**" in report
    assert "2,801/2,801 exact" in report
    for digest in comparison.MANIFEST["embedding_sha256"].values():
        assert digest in report


def test_obstruction_anatomy_views_match_saved_evidence() -> None:
    overview = comparison.anatomy_overview()
    assert "77.6%" in overview
    assert "0 of 6" in overview

    severity_figure, severe = comparison.severity_concentration_view()
    assert len(severity_figure.data) == 2
    assert len(severe) == 20
    assert severe.iloc[0]["length"] == 368_058

    isolation_figure, isolated = comparison.isolation_view()
    assert isolation_figure.data
    assert len(isolated) == 100

    scale_figure, scales, arithmetic_figure, arithmetic = (
        comparison.scale_and_arithmetic_view()
    )
    assert scale_figure.data and arithmetic_figure.data
    assert scales["event_count"].sum() == 3_103
    assert not arithmetic["survives_holm_005"].any()
