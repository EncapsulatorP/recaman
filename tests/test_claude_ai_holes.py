"""Tests for the Claude.ai holes Space: the absolute-hole catalogue.

These cover a different object from `test_next_move_predictor.py` and
`test_space_sequence_and_figures.py`, which test the process-side obstruction
bit. Nothing here touches those.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from compression_figures import compression_bars
from compression_lab import (
    catalogue_benchmark,
    decode_events,
    decode_phase_slips,
    encode_events,
    encode_phase_slips,
    pack_bits,
    process_benchmark,
    unpack_bits,
)
from hole_figures import (
    POSTER_HEIGHT,
    POSTER_WIDTH,
    VARIANT,
    arc_diagram,
    auc_chart,
    auc_rows,
    decade_chart,
    poster,
    span_strip,
    svg_document,
)
from holes import HoleEvent, load_catalogue, parse
from sequence import walk

REPO_ROOT = Path(__file__).resolve().parents[1]
SPACE_DIR = REPO_ROOT / "apps" / "claude_ai_holes"
RESULTS = json.loads((SPACE_DIR / "results.json").read_text(encoding="utf-8"))

# A005132, which the research scripts check against too.
A005132_PREFIX = [
    0, 1, 3, 6, 2, 7, 13, 20, 12, 21, 11,
    22, 10, 23, 9, 24, 8, 25, 43, 62, 42,
]


@pytest.fixture(scope="module")
def catalogue():
    return load_catalogue()


# --- the catalogue ---------------------------------------------------------


def test_catalogue_matches_the_saved_version_c_summary(catalogue) -> None:
    """Every structural number must agree with the run that produced it."""
    saved = json.loads(
        (REPO_ROOT / "outputs" / "version_c_obstructions_results.json").read_text(
            encoding="utf-8"
        )
    )["summary"]
    gaps = catalogue.gaps()

    assert catalogue.event_count == saved["events"]
    assert catalogue.singleton_count == saved["singletons"]
    assert catalogue.range_count == saved["ranges"]
    assert max(catalogue.lengths()) == saved["range_length_max"]
    assert min(catalogue.lengths()) == saved["range_length_min"]
    assert catalogue.span_start == saved["start_min"]
    assert catalogue.events[-1].start == saved["start_max"]
    assert min(gaps) == saved["gap_min"]
    assert max(gaps) == saved["gap_max"]


def test_space_catalogue_is_verbatim_copy_of_the_repository_one() -> None:
    assert (SPACE_DIR / "holes.txt").read_bytes() == (
        REPO_ROOT / "obstructions.txt"
    ).read_bytes()


def test_counts_are_internally_consistent(catalogue) -> None:
    assert catalogue.singleton_count + catalogue.range_count == catalogue.event_count
    assert catalogue.integer_count == sum(catalogue.lengths())
    assert 0.0 < catalogue.coverage < 1.0
    # Every integer lands in exactly one decade band, so the bands must total.
    assert sum(integers for _, _, integers in catalogue.decade_profile()) == (
        catalogue.integer_count
    )
    assert sum(integers for _, _, integers in catalogue.length_buckets()) == (
        catalogue.integer_count
    )
    assert sum(events for _, events, _ in catalogue.length_buckets()) == (
        catalogue.event_count
    )


def test_parse_rejects_overlapping_and_inverted_events() -> None:
    with pytest.raises(ValueError, match="overlapping"):
        parse("10 - 20\n15\n")
    with pytest.raises(ValueError, match="ends before"):
        parse("30 - 20\n")
    with pytest.raises(ValueError, match="empty"):
        parse("# only a comment\n")


def test_parse_handles_comments_blank_lines_and_ordering() -> None:
    catalogue = parse("# header\n\n  50 - 60 \n10\n\n20 - 25\n")
    assert catalogue.events == (
        HoleEvent(10, 10),
        HoleEvent(20, 25),
        HoleEvent(50, 60),
    )
    assert catalogue.integer_count == 1 + 6 + 11


# --- windows ---------------------------------------------------------------


def test_window_summary_over_the_whole_span_reproduces_the_totals(catalogue) -> None:
    summary = catalogue.window_summary(catalogue.span_start, catalogue.span_end)
    assert summary["events"] == catalogue.event_count
    assert summary["missing"] == catalogue.integer_count
    assert summary["coverage"] == pytest.approx(catalogue.coverage)
    assert summary["longest_run"] == max(catalogue.lengths())


def test_window_summary_clamps_to_the_covered_span(catalogue) -> None:
    """The catalogue must never speak about values it does not cover."""
    summary = catalogue.window_summary(0, catalogue.span_end * 2)
    assert summary["low"] == catalogue.span_start
    assert summary["high"] == catalogue.span_end


def test_disjoint_windows_partition_the_missing_integers(catalogue) -> None:
    midpoint = catalogue.span_start + catalogue.span_width // 2
    lower = catalogue.window_summary(catalogue.span_start, midpoint)
    upper = catalogue.window_summary(midpoint + 1, catalogue.span_end)
    assert lower["missing"] + upper["missing"] == catalogue.integer_count


def test_events_in_window_finds_a_run_that_starts_before_the_window(catalogue) -> None:
    longest = max(catalogue.events, key=lambda event: event.length)
    inside = longest.start + longest.length // 2
    found = catalogue.events_in_window(inside, inside + 1)
    assert longest in found


# --- the sequence used only for the arc picture ----------------------------


def test_walk_matches_oeis_a005132(catalogue) -> None:
    terms, forward = walk(20)
    assert list(terms) == A005132_PREFIX
    assert len(forward) == 20
    for n in range(1, 21):
        previous, current = terms[n - 1], terms[n]
        assert current == (previous + n if forward[n - 1] else previous - n)


def test_walk_stays_below_the_smallest_catalogued_hole(catalogue) -> None:
    """The arc picture must not imply any drawn value is a hole."""
    terms, _ = walk(40)
    assert max(terms) < catalogue.span_start


def test_walk_rejects_empty_runs() -> None:
    with pytest.raises(ValueError):
        walk(0)


# --- compression experiment ----------------------------------------------


def test_catalogue_event_codec_round_trips_and_compresses(catalogue) -> None:
    encoded = encode_events(catalogue.events)
    assert decode_events(encoded) == catalogue.events
    benchmark = catalogue_benchmark(catalogue, (SPACE_DIR / "holes.txt").read_bytes())
    assert benchmark["event_round_trip"] is True
    assert benchmark["integer_count"] == 1_277_399
    assert benchmark["best"]["bytes"] < benchmark["event_codec_bytes"]
    assert benchmark["best"]["ratio"] > 100


def test_process_codecs_round_trip_and_reconstruct_the_trajectory() -> None:
    terms, bits = walk(20_000)
    packed = pack_bits(bits)
    slips = encode_phase_slips(bits)
    assert unpack_bits(packed, len(bits)) == bits
    assert decode_phase_slips(slips) == bits

    benchmark = process_benchmark(20_000)
    assert benchmark["final_term"] == terms[-1]
    assert all(benchmark["round_trips"].values())
    assert benchmark["best"]["bytes"] < len(bits) // 8
    assert benchmark["held_out_model"]["bits_per_step"] < 0.2


def test_compression_figure_is_well_formed(catalogue) -> None:
    payload = catalogue_benchmark(catalogue, (SPACE_DIR / "holes.txt").read_bytes())
    root = _parse(compression_bars(payload, "Compression test"))
    assert root.get("role") == "img"


# --- figures ---------------------------------------------------------------


def _parse(svg: str) -> ET.Element:
    """Parse and return the SVG root, proving it is well-formed XML."""
    return ET.fromstring(svg)


def test_figures_emit_well_formed_svg(catalogue) -> None:
    fragments = [
        (arc_diagram(*walk(24), 500, 200), 500, 200),
        (decade_chart(catalogue.decade_profile(), 600, 260), 600, 260),
        (auc_chart(auc_rows(RESULTS), 700, 260), 700, 260),
        (span_strip(catalogue, catalogue.span_start, catalogue.span_end, 800, 180), 800, 180),
    ]
    for fragment, width, height in fragments:
        root = _parse(svg_document(fragment, width, height, "figure"))
        assert root.get("viewBox") == f"0 0 {width} {height}"
        assert root.get("role") == "img"


def test_auc_rows_cover_every_measured_task() -> None:
    rows = auc_rows(RESULTS)
    assert len(rows) == 2 + len(RESULTS["version_c"]["datasets"])
    assert all(0.5 <= auc <= 1.0 for _, auc, _ in rows)
    # Only dataset D and the random-matrix runs count as leakage-reduced.
    assert [label for label, _, reduced in rows if reduced] == [
        "random-matrix · RF cross-validation",
        "random-matrix · best linear code",
        "Version C D · gap dynamics",
    ]


def test_poster_is_well_formed_and_carries_the_measured_numbers(catalogue) -> None:
    svg = poster(catalogue, RESULTS, walk(24))
    root = _parse(svg)
    assert root.get("viewBox") == f"0 0 {POSTER_WIDTH:g} {POSTER_HEIGHT:g}"

    text = " ".join(node.text or "" for node in root.iter())
    assert f"{catalogue.integer_count:,}" in text
    assert f"{catalogue.span_start:,}" in text
    assert f"{catalogue.span_end:,}" in text
    assert f"{RESULTS['version_c']['datasets']['D']['mean_auc']:.4f}" in text
    # The poster must state what it does not claim.
    assert "does not claim" in text.lower()


def test_poster_is_watermarked_as_the_claude_ai_version(catalogue) -> None:
    svg = poster(catalogue, RESULTS, walk(24))
    assert VARIANT.upper() in svg
    root = _parse(svg)
    assert VARIANT in (root.get("aria-label") or "")


def test_poster_declares_both_colour_schemes(catalogue) -> None:
    svg = poster(catalogue, RESULTS, walk(24))
    assert "prefers-color-scheme: dark" in svg
    # Every colour is a token, so no raw hex may appear outside the token block.
    body = svg.split("</style>", 1)[1]
    assert not re.search(r"#[0-9a-fA-F]{6}", body)


def test_rendered_infographic_is_current(catalogue) -> None:
    """The committed SVG must match what the generator produces today."""
    target = REPO_ROOT / "outputs" / "recaman_holes_infographic_claude-ai.svg"
    expected = poster(catalogue, RESULTS, walk(24)).encode("utf-8")
    assert target.read_bytes() == expected
