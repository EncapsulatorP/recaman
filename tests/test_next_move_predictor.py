from __future__ import annotations

import pytest

from apps.space.predictor import (
    N_EMPIRICAL,
    PHASE_SLIP_RATE,
    predict_next_obstruction,
)


def test_down_predicts_up() -> None:
    result = predict_next_obstruction(0)
    assert result.previous_move == "DOWN / FREE"
    assert result.predicted_bit == 1
    assert result.predicted_move == "UP / BLOCKED"
    assert result.confidence == pytest.approx(0.998919)


def test_up_predicts_down() -> None:
    result = predict_next_obstruction(1)
    assert result.previous_move == "UP / BLOCKED"
    assert result.predicted_bit == 0
    assert result.predicted_move == "DOWN / FREE"
    assert result.confidence == pytest.approx(0.998913)


def test_prediction_metadata_and_serialization() -> None:
    payload = predict_next_obstruction(0).to_dict()
    assert payload["empirical_horizon"] == N_EMPIRICAL
    assert payload["phase_slip_rate"] == PHASE_SLIP_RATE


@pytest.mark.parametrize("invalid", [-1, 2, True, None, "0"])
def test_invalid_previous_bit_is_rejected(invalid: object) -> None:
    with pytest.raises(ValueError):
        predict_next_obstruction(invalid)  # type: ignore[arg-type]
