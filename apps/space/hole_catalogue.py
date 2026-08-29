"""Curated Recamán long-lasting-obstruction catalogue used by the Space."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from functools import lru_cache
from itertools import pairwise
from pathlib import Path

CATALOGUE_PATH = Path(__file__).resolve().parent / "holes.txt"


@dataclass(frozen=True)
class HoleEvent:
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start + 1


@dataclass(frozen=True)
class HoleCatalogue:
    events: tuple[HoleEvent, ...]

    @property
    def starts(self) -> tuple[int, ...]:
        return tuple(event.start for event in self.events)

    @property
    def span_start(self) -> int:
        return self.events[0].start

    @property
    def span_end(self) -> int:
        return self.events[-1].end

    @property
    def span_width(self) -> int:
        return self.span_end - self.span_start + 1

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def integer_count(self) -> int:
        return sum(event.length for event in self.events)

    @property
    def singleton_count(self) -> int:
        return sum(event.length == 1 for event in self.events)

    @property
    def range_count(self) -> int:
        return self.event_count - self.singleton_count

    @property
    def longest_run(self) -> int:
        return max(event.length for event in self.events)

    def locate(self, value: int) -> tuple[str, HoleEvent | None, HoleEvent | None]:
        """Return catalogue status, containing event, and nearest event."""
        if value < self.span_start or value > self.span_end:
            return "outside", None, None

        index = bisect_right(self.starts, value) - 1
        previous = self.events[max(index, 0)]
        if previous.start <= value <= previous.end:
            return "catalogued", previous, previous

        following = self.events[min(index + 1, self.event_count - 1)]
        nearest = min(
            (previous, following),
            key=lambda event: min(abs(value - event.start), abs(value - event.end)),
        )
        return "not_catalogued", None, nearest

    def density_bins(self, count: int = 96) -> list[tuple[int, int, int]]:
        """Return (low, high, missing integers) for equal-width span bins."""
        width = max(self.span_width // count, 1)
        bins: list[tuple[int, int, int]] = []
        event_index = 0
        for bin_index in range(count):
            low = self.span_start + bin_index * width
            high = self.span_end if bin_index == count - 1 else min(low + width - 1, self.span_end)
            while event_index < self.event_count and self.events[event_index].end < low:
                event_index += 1
            missing = 0
            cursor = event_index
            while cursor < self.event_count and self.events[cursor].start <= high:
                event = self.events[cursor]
                missing += max(0, min(event.end, high) - max(event.start, low) + 1)
                cursor += 1
            bins.append((low, high, missing))
        return bins


def parse(text: str) -> HoleCatalogue:
    events: list[HoleEvent] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "-" in line:
            start_text, end_text = line.split("-", 1)
            start, end = int(start_text), int(end_text)
        else:
            start = end = int(line)
        if end < start:
            raise ValueError(f"range ends before it starts: {line!r}")
        events.append(HoleEvent(start, end))

    if not events:
        raise ValueError("catalogue is empty")
    events.sort(key=lambda event: event.start)
    for previous, following in pairwise(events):
        if following.start <= previous.end:
            raise ValueError("catalogue contains overlapping events")
    return HoleCatalogue(tuple(events))


@lru_cache(maxsize=1)
def load_catalogue() -> HoleCatalogue:
    return parse(CATALOGUE_PATH.read_text(encoding="utf-8"))
