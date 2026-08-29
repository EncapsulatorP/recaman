"""Transparent one-step predictor derived from the 10-million-step run."""

from __future__ import annotations

from dataclasses import asdict, dataclass


N_EMPIRICAL = 10_000_000
P_UP_GIVEN_PREVIOUS_DOWN = 0.998919
P_UP_GIVEN_PREVIOUS_UP = 0.001087
PHASE_SLIP_RATE = 0.001084


@dataclass(frozen=True)
class NextMovePrediction:
    previous_bit: int
    previous_move: str
    predicted_bit: int
    predicted_move: str
    confidence: float
    empirical_horizon: int = N_EMPIRICAL
    phase_slip_rate: float = PHASE_SLIP_RATE

    def to_dict(self) -> dict[str, int | str | float]:
        """Return a JSON-serializable representation."""
        return asdict(self)


def predict_next_obstruction(previous_bit: int) -> NextMovePrediction:
    """Predict the next obstruction bit from the preceding bit.

    This is a finite-horizon empirical baseline. It predicts the usual
    alternating move, not the locations of rare phase slips and not permanent
    missing values in the Recaman sequence.
    """
    if isinstance(previous_bit, bool) or previous_bit not in (0, 1):
        raise ValueError("previous_bit must be either 0 (DOWN/FREE) or 1 (UP/BLOCKED)")

    if previous_bit == 0:
        return NextMovePrediction(
            previous_bit=0,
            previous_move="DOWN / FREE",
            predicted_bit=1,
            predicted_move="UP / BLOCKED",
            confidence=P_UP_GIVEN_PREVIOUS_DOWN,
        )

    return NextMovePrediction(
        previous_bit=1,
        previous_move="UP / BLOCKED",
        predicted_bit=0,
        predicted_move="DOWN / FREE",
        confidence=1.0 - P_UP_GIVEN_PREVIOUS_UP,
    )
