"""Recaman sequence generation and the process-side obstruction bit.

This is the single source of truth for the definition the Space uses, and it
matches `scripts/recaman_wheel_validator.py` in the research repo:

    a(0) = 0
    a(n) = a(n-1) - n   if that value is positive and not yet visited -> b(n) = 0
    a(n) = a(n-1) + n   otherwise                                     -> b(n) = 1

`b(n) = 1` means the backward (down) move was *blocked*, so the sequence was
forced up. `b(n) = 0` means the backward move was free. Bits are stored
zero-indexed, so `bits[i]` is `b(i + 1)`; every public method that talks about
positions speaks in step numbers `n`, never in list offsets.
"""

from __future__ import annotations

from dataclasses import dataclass


DOWN_FREE = 0
UP_BLOCKED = 1

MOVE_NAMES = {DOWN_FREE: "DOWN / FREE", UP_BLOCKED: "UP / BLOCKED"}
MOVE_CHOICES = {f"{MOVE_NAMES[bit]}  (b = {bit})": bit for bit in (DOWN_FREE, UP_BLOCKED)}

# Generating a prefix is linear, but the Space is a shared CPU box: keep the
# interactive explorer inside a size a request can serve comfortably.
MAX_INTERACTIVE_STEPS = 200_000


@dataclass(frozen=True)
class RecamanRun:
    """A finite prefix of the sequence together with its obstruction bits."""

    terms: tuple[int, ...]
    bits: tuple[int, ...]

    @property
    def steps(self) -> int:
        return len(self.bits)

    def bit(self, n: int) -> int:
        """Return b(n) for a one-based step number."""
        return self.bits[n - 1]

    @property
    def blocked_fraction(self) -> float:
        return sum(self.bits) / len(self.bits) if self.bits else 0.0

    def slip_steps(self) -> tuple[int, ...]:
        """Step numbers n >= 2 where b(n) == b(n-1), i.e. the phase slips."""
        return tuple(
            n
            for n in range(2, self.steps + 1)
            if self.bits[n - 1] == self.bits[n - 2]
        )

    def slip_rate(self) -> float:
        pairs = max(self.steps - 1, 0)
        return len(self.slip_steps()) / pairs if pairs else 0.0

    def transition_counts(self) -> dict[str, int]:
        """Observed (previous bit, next bit) counts, keyed like ``"p01"``."""
        counts = {"p00": 0, "p01": 0, "p10": 0, "p11": 0}
        for previous, following in zip(self.bits, self.bits[1:]):
            counts[f"p{previous}{following}"] += 1
        return counts

    def transition_matrix(self) -> dict[str, float]:
        """Row-normalised transition probabilities for this prefix."""
        counts = self.transition_counts()
        matrix = {}
        for previous in (0, 1):
            row = counts[f"p{previous}0"] + counts[f"p{previous}1"]
            for following in (0, 1):
                key = f"p{previous}{following}"
                matrix[key] = counts[key] / row if row else 0.0
        return matrix

    def window(self, first_step: int, length: int) -> tuple[int, tuple[int, ...]]:
        """Return ``(first_step, bits)`` for a clamped window of the bit stream."""
        first_step = max(1, min(first_step, max(self.steps - length + 1, 1)))
        return first_step, self.bits[first_step - 1 : first_step - 1 + length]

    def window_around_slip(self, length: int = 23) -> tuple[int, tuple[int, ...]]:
        """Centre a window on the most isolated slip, or on the run's middle.

        The most isolated slip is the honest illustration: it shows one defect
        inside otherwise clean alternation, which is what the stream looks like
        once the early transient is behind you.
        """
        slips = self.slip_steps()
        if not slips:
            return self.window(max(self.steps // 2 - length // 2, 1), length)

        def isolation(index: int) -> int:
            step = slips[index]
            before = step - slips[index - 1] if index else step
            after = slips[index + 1] - step if index + 1 < len(slips) else self.steps - step
            return min(before, after)

        best = max(range(len(slips)), key=isolation)
        return self.window(slips[best] - length // 2, length)


def generate(steps: int) -> RecamanRun:
    """Generate b(1) .. b(steps), i.e. the terms a(0) .. a(steps)."""
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
