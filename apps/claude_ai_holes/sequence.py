"""A short Recaman walk, used only to illustrate the rule in the arc diagram.

    a(0) = 0
    a(n) = a(n-1) - n   if that value is positive and not yet visited
    a(n) = a(n-1) + n   otherwise

This matches `scripts/recaman_wheel_validator.py` in the research repository.
It exists here for the picture alone: the hole catalogue is the data this Space
reports on, and no hole is anywhere near the range a drawable walk covers.
"""

from __future__ import annotations


def walk(steps: int) -> tuple[tuple[int, ...], tuple[bool, ...]]:
    """Return `(terms, forward)` for a(0) .. a(steps).

    `forward[i]` is True when step i + 1 had to move forward because the
    backward move was unavailable.
    """
    if steps < 1:
        raise ValueError("steps must be at least 1")

    terms = [0]
    forward: list[bool] = []
    seen = {0}
    current = 0

    for n in range(1, steps + 1):
        candidate = current - n
        went_forward = not (candidate > 0 and candidate not in seen)
        current = current + n if went_forward else candidate
        forward.append(went_forward)
        seen.add(current)
        terms.append(current)

    return tuple(terms), tuple(forward)
