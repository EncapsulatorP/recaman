"""The Recaman absolute-hole catalogue: parsing and structure.

An *absolute hole* is an integer the Recaman sequence never reaches. This
module reads the catalogue shipped with the Space (`holes.txt`, a verbatim copy
of `obstructions.txt` from the research repository) and reports its structure.

The catalogue is Benjamin Chaffin's certified list of missing values, and it is
complete over the span it covers, so within that span "not listed" means the
sequence does reach the value. Outside the span the catalogue says nothing at
all, and neither does this module.

Event gaps use the same start-to-start definition as
`scripts/321_210_version_c.py`, so the numbers here match the saved run.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


CATALOGUE_PATH = Path(__file__).resolve().parent / "holes.txt"


@dataclass(frozen=True)
class HoleEvent:
    """One catalogue entry: a single missing integer, or a run of them."""

    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start + 1

    @property
    def is_range(self) -> bool:
        return self.end > self.start


@dataclass(frozen=True)
class HoleCatalogue:
    """A parsed catalogue plus the structural summaries the Space displays."""

    events: tuple[HoleEvent, ...]

    # -- extent ------------------------------------------------------------
    @property
    def span_start(self) -> int:
        return self.events[0].start

    @property
    def span_end(self) -> int:
        return self.events[-1].end

    @property
    def span_width(self) -> int:
        return self.span_end - self.span_start + 1

    # -- counts ------------------------------------------------------------
    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def singleton_count(self) -> int:
        return sum(1 for event in self.events if not event.is_range)

    @property
    def range_count(self) -> int:
        return sum(1 for event in self.events if event.is_range)

    @property
    def integer_count(self) -> int:
        """How many individual integers the catalogue marks as missing."""
        return sum(event.length for event in self.events)

    @property
    def coverage(self) -> float:
        """Share of the covered span that is missing from the sequence."""
        return self.integer_count / self.span_width

    # -- distributions -----------------------------------------------------
    def lengths(self) -> list[int]:
        return [event.length for event in self.events]

    def gaps(self) -> list[int]:
        """Start-to-start distance between successive events."""
        return [
            following.start - preceding.start
            for preceding, following in zip(self.events, self.events[1:])
        ]

    def length_buckets(self) -> list[tuple[str, int, int]]:
        """Event counts and missing integers, bucketed by run length."""
        edges = [(1, 1), (2, 2), (3, 10), (11, 100), (101, 1_000), (1_001, None)]
        buckets = []
        for low, high in edges:
            chosen = [
                event
                for event in self.events
                if event.length >= low and (high is None or event.length <= high)
            ]
            label = f"{low:,}" if low == high else (
                f"{low:,}+" if high is None else f"{low:,}–{high:,}"
            )
            buckets.append((label, len(chosen), sum(event.length for event in chosen)))
        return buckets

    def decade_profile(self) -> list[tuple[int, int, int]]:
        """Per power-of-ten band: (exponent, events, missing integers).

        A band covers [10^e, 10^(e+1)). Runs that straddle a boundary have
        their integers counted in the band each part falls in, so the integer
        totals stay exact.
        """
        low_exponent = len(str(self.span_start)) - 1
        high_exponent = len(str(self.span_end)) - 1
        profile = []
        for exponent in range(low_exponent, high_exponent + 1):
            low, high = 10**exponent, 10 ** (exponent + 1) - 1
            events = 0
            integers = 0
            for event in self.events:
                overlap = min(event.end, high) - max(event.start, low) + 1
                if overlap > 0:
                    integers += overlap
                    if low <= event.start <= high:
                        events += 1
            profile.append((exponent, events, integers))
        return profile

    # -- windows -----------------------------------------------------------
    def events_in_window(self, low: int, high: int) -> tuple[HoleEvent, ...]:
        """Every event overlapping [low, high], in order."""
        starts = [event.start for event in self.events]
        first = max(bisect_right(starts, low) - 1, 0)
        return tuple(
            event
            for event in self.events[first:]
            if event.start <= high and event.end >= low
        )

    def window_summary(self, low: int, high: int) -> dict[str, int | float]:
        """Counts and coverage for the part of [low, high] the catalogue covers."""
        low, high = max(low, self.span_start), min(high, self.span_end)
        width = max(high - low + 1, 0)
        events = self.events_in_window(low, high)
        missing = sum(
            min(event.end, high) - max(event.start, low) + 1 for event in events
        )
        return {
            "low": low,
            "high": high,
            "width": width,
            "events": len(events),
            "missing": missing,
            "coverage": missing / width if width else 0.0,
            "longest_run": max((event.length for event in events), default=0),
        }


def parse(text: str) -> HoleCatalogue:
    """Parse the catalogue format: one integer, or `start - end`, per line."""
    events: list[HoleEvent] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "-" in line:
            start_text, end_text = line.split("-", 1)
            start, end = int(start_text), int(end_text)
            if end < start:
                raise ValueError(f"range ends before it starts: {line!r}")
        else:
            start = end = int(line)
        events.append(HoleEvent(start=start, end=end))

    if not events:
        raise ValueError("catalogue is empty")

    events.sort(key=lambda event: event.start)
    for preceding, following in zip(events, events[1:]):
        if following.start <= preceding.end:
            raise ValueError(
                f"overlapping events: {preceding.start}-{preceding.end} "
                f"and {following.start}-{following.end}"
            )
    return HoleCatalogue(events=tuple(events))


@lru_cache(maxsize=1)
def load_catalogue(path: Path = CATALOGUE_PATH) -> HoleCatalogue:
    return parse(path.read_text(encoding="utf-8"))
