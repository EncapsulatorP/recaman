"""Contract and calculation checks for the comparison Space."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


pd = pytest.importorskip("pandas")
pytest.importorskip("plotly")
pytest.importorskip("gradio")
pytest.importorskip("huggingface_hub")


APP_PATH = Path(__file__).resolve().parents[1] / "apps" / "comparison" / "app.py"
SPEC = importlib.util.spec_from_file_location("recaman_comparison_app", APP_PATH)
assert SPEC is not None and SPEC.loader is not None
comparison = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = comparison
SPEC.loader.exec_module(comparison)


def _valid_store() -> object:
    sequence = pd.DataFrame(
        {
            "n": [0, 1, 2],
            "a_n_real": [0, 1, 3],
            "a_n_inferred": [0, 1, 2],
            "fit_score": [1.0, 0.9, 0.75],
            "run_id": ["check"] * 3,
        }
    )
    holes = pd.DataFrame(
        {
            "value": [930_058, 930_557, 964_420],
            "is_real_chaffin_hole": [True, True, True],
            "is_inferred_hole": [True, False, True],
            "fit_score": [0.99, 0.20, 0.80],
            "run_id": ["check"] * 3,
        }
    )
    fits = pd.DataFrame(
        {
            "run_id": ["check"],
            "threshold": [0.75],
            "precision": [1.0],
            "recall": [2 / 3],
        }
    )
    files = [
        "viewer/sequence/check.parquet",
        "viewer/holes/check.parquet",
        "viewer/fits/check.parquet",
        "viewer/summary/check.parquet",
    ]
    return comparison.Store(
        sequence=comparison._ensure_sequence_columns(sequence),
        holes=comparison._ensure_holes_columns(holes),
        fits=comparison._ensure_fits_columns(fits),
        summary=pd.DataFrame({"status": ["verified"]}),
        files=files,
        status="loaded",
        loaded_ok=True,
    )


def test_comparison_space_imports_without_loading_remote_data() -> None:
    assert comparison.demo is not None
    assert comparison.DATASET_ID == "kugguk/recaman-independent-check-bundle"


def test_validation_panel_reports_a_complete_valid_contract(monkeypatch) -> None:
    monkeypatch.setattr(comparison, "STORE", _valid_store())
    report = comparison.validation_report()
    assert "Dataset validation — **PASS**" in report
    assert "4/4 groups published" in report
    assert "3 scores in [0, 1]" in report


def test_validation_panel_rejects_out_of_range_scores(monkeypatch) -> None:
    store = _valid_store()
    store.holes.loc[0, "fit_score"] = 1.01
    monkeypatch.setattr(comparison, "STORE", store)
    report = comparison.validation_report()
    assert "Dataset validation — **FAIL**" in report
    assert "Values outside [0, 1]" in report


def test_hole_metrics_are_computed_from_boolean_evidence(monkeypatch) -> None:
    monkeypatch.setattr(comparison, "STORE", _valid_store())
    rows = comparison._hole_comparison_rows("check", 1_000_000, "≥ 0.75 fit")
    report = comparison.metrics_markdown(rows, "≥ 0.75 fit")
    assert "| Overlap / TP | **2** |" in report
    assert "| False positives | **0** |" in report
    assert "| Missed real holes | **1** |" in report
