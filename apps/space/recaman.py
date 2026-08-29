"""Recaman sequence and obstruction-bit generation.

This is the single source of truth for the process-side definition used by the
Space. It matches `scripts/recaman_wheel_validator.py`:

    a(0) = 0
    a(n) = a(n-1) - n   if that value is positive and not yet visited  -> b(n) = 0
    a(n) = a(n-1) + n   otherwise                                      -> b(n) = 1

`b(n) = 1` means the backward (down) move was *blocked*, so the sequence was
forced up. `b(n) = 0` means the backward move was free.
"""

from __future__ import annotations

from dataclasses import dataclass


DOWN_FREE = 0
UP_BLOCKED = 1

MOVE_NAMES = {DOWN_FREE: "DOWN / FREE", UP_BLOCKED: "UP / BLOCKED"}


@dataclass(frozen=True)
class RecamanRun:
    """A finite prefix of the sequence together with its obstruction bits."""

    terms: tuple[int, ...]
    bits: tuple[int, ...]

    @property
    def steps(self) -> int:
        return len(self.bits)

    @property
    def blocked_fraction(self) -> float:
        return sum(self.bits) / len(self.bits) if self.bits else 0.0

    def slip_indices(self) -> tuple[int, ...]:
        """Return every n where b(n) == b(n-1) (a same-bit phase slip).

        Indices are into `bits`, so index i refers to step i + 1 of the
        sequence and means `b(i+1) == b(i)`.
        """
        return tuple(
            i for i in range(1, len(self.bits)) if self.bits[i] == self.bits[i - 1]
        )

    def slip_rate(self) -> float:
        pairs = max(len(self.bits) - 1, 0)
        return len(self.slip_indices()) / pairs if pairs else 0.0

    def transition_counts(self) -> dict[tuple[int, int], int]:
        """Count observed (previous bit, next bit) transitions."""
        counts = {(0, 0): 0, (0, 1): 0, (1, 0): 0, (1, 1): 0}
        for previous, following in zip(self.bits, self.bits[1:]):
            counts[(previous, following)] += 1
        return counts


def generate(steps: int) -> RecamanRun:
    """Generate `steps` obstruction bits, i.e. terms a(0) .. a(steps)."""
    if steps < 1:
        raise ValueError("steps must be at least 1")

    terms = [0]
    bits: list[int] = []
    seen = {0}
    current = 0

    for n in range(1, steps + 1):
        candidate = current - n
        if candidate > 0 and candidate not in seen:
            current = candidate
            bits.append(DOWN_FREE)
        else:
            current += n
            bits.append(UP_BLOCKED)
        seen.add(current)
        terms.append(current)

    return RecamanRun(terms=tuple(terms), bits=tuple(bits))
