from __future__ import annotations

import json
from pathlib import Path

import pytest

from predictor import (
    MEASUREMENTS_PATH,
    N_EMPIRICAL,
    PHASE_SLIP_RATE,
    TRANSITION,
    horizon_points,
    predict_next_obstruction,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_down_predicts_up() -> None:
    result = predict_next_obstruction(0)
    assert result.previous_move == "DOWN / FREE"
    assert result.predicted_bit == 1
    assert result.predicted_move == "UP / BLOCKED"
    assert result.confidence == pytest.approx(0.998919)
    assert result.slip_probability == pytest.approx(0.001081)


def test_up_predicts_down() -> None:
    result = predict_next_obstruction(1)
    assert result.previous_move == "UP / BLOCKED"
    assert result.predicted_bit == 0
    assert result.predicted_move == "DOWN / FREE"
    assert result.confidence == pytest.approx(0.998913)
    assert result.slip_probability == pytest.approx(0.001087)


def test_prediction_metadata_and_serialization() -> None:
    payload = predict_next_obstruction(0).to_dict()
    assert payload["empirical_horizon"] == N_EMPIRICAL
    assert payload["phase_slip_rate"] == PHASE_SLIP_RATE
    assert payload["expected_steps_to_next_slip"] == pytest.approx(1 / 0.001081)
    assert json.dumps(payload)


@pytest.mark.parametrize("invalid", [-1, 2, True, None, "0"])
def test_invalid_previous_bit_is_rejected(invalid: object) -> None:
    with pytest.raises(ValueError):
        predict_next_obstruction(invalid)  # type: ignore[arg-type]


def test_transition_rows_are_normalised() -> None:
    for previous in (0, 1):
        row = TRANSITION[f"p{previous}0"] + TRANSITION[f"p{previous}1"]
        assert row == pytest.approx(1.0)


def test_horizon_scan_is_monotonically_decreasing() -> None:
    points = horizon_points()
    assert len(points) >= 3
    horizons = [n for n, _ in points]
    rates = [rate for _, rate in points]
    assert horizons == sorted(horizons)
    assert rates == sorted(rates, reverse=True)
    # The headline slip rate is the last point of the same scan.
    assert rates[-1] == pytest.approx(PHASE_SLIP_RATE)


def test_measurements_file_matches_its_generator() -> None:
    """The Space's copy must stay in step with the saved validator run."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_space_measurements", REPO_ROOT / "scripts" / "build_space_measurements.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    rebuilt = module.build(REPO_ROOT / "outputs" / "recaman_wheel_results.json")
    assert rebuilt == json.loads(MEASUREMENTS_PATH.read_text(encoding="utf-8"))
