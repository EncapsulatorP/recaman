"""One-step obstruction-bit predictor, read from the measured 10^7-step run.

The numbers are not written by hand here. `measurements.json` is generated from
`outputs/recaman_wheel_results.json` by `scripts/build_space_measurements.py`,
so the Space and the research repo can never drift apart silently.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

from recaman import DOWN_FREE, MOVE_NAMES, UP_BLOCKED


MEASUREMENTS_PATH = Path(__file__).resolve().parent / "measurements.json"


@lru_cache(maxsize=1)
def load_measurements() -> dict:
    """Load the saved empirical measurements that back every number shown."""
    return json.loads(MEASUREMENTS_PATH.read_text(encoding="utf-8"))


_M = load_measurements()

N_EMPIRICAL: int = _M["empirical_horizon"]
TRANSITION: dict[str, float] = _M["transition"]
P_UP_GIVEN_PREVIOUS_DOWN: float = TRANSITION["p01"]
P_UP_GIVEN_PREVIOUS_UP: float = TRANSITION["p11"]
PHASE_SLIP_RATE: float = _M["phase_slip"]["rate"]
MEAN_RUN_LENGTH: float = _M["phase_slip"]["mean_run_length"]
HORIZON_SCAN: list[dict] = _M["horizon_scan"]


@dataclass(frozen=True)
class NextMovePrediction:
    """One transparent prediction plus the evidence it rests on."""

    previous_bit: int
    previous_move: str
    predicted_bit: int
    predicted_move: str
    confidence: float
    slip_probability: float
    expected_steps_to_next_slip: float
    empirical_horizon: int = N_EMPIRICAL
    phase_slip_rate: float = PHASE_SLIP_RATE

    def to_dict(self) -> dict[str, int | str | float]:
        """Return a JSON-serializable representation."""
        return asdict(self)


def predict_next_obstruction(previous_bit: int) -> NextMovePrediction:
    """Predict the next obstruction bit from the preceding bit.

    This is a finite-horizon empirical baseline. It predicts the usual
    alternating move, not the locations of the rare phase slips and not which
    values stay permanently missing from the Recaman sequence.
    """
    if isinstance(previous_bit, bool) or previous_bit not in (DOWN_FREE, UP_BLOCKED):
        raise ValueError("previous_bit must be either 0 (DOWN/FREE) or 1 (UP/BLOCKED)")

    predicted_bit = UP_BLOCKED if previous_bit == DOWN_FREE else DOWN_FREE
    slip_probability = TRANSITION[f"p{previous_bit}{previous_bit}"]

    return NextMovePrediction(
        previous_bit=previous_bit,
        previous_move=MOVE_NAMES[previous_bit],
        predicted_bit=predicted_bit,
        predicted_move=MOVE_NAMES[predicted_bit],
        confidence=TRANSITION[f"p{previous_bit}{predicted_bit}"],
        slip_probability=slip_probability,
        expected_steps_to_next_slip=(1.0 / slip_probability if slip_probability else float("inf")),
    )


def horizon_points() -> list[tuple[int, float]]:
    """Measured (N, same-bit slip rate) pairs, ordered by horizon."""
    return [(row["n"], row["slip_rate"]) for row in HORIZON_SCAN]
