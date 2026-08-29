"""Tests for the Space's sequence generator and its SVG figures."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from figures import POSTER_HEIGHT, POSTER_WIDTH, arc_diagram, bit_ribbon, poster, svg_document
from predictor import load_measurements
from recaman import DOWN_FREE, UP_BLOCKED, generate


# A005132, which the research scripts also check against.
A005132_PREFIX = [
    0, 1, 3, 6, 2, 7, 13, 20, 12, 21, 11,
    22, 10, 23, 9, 24, 8, 25, 43, 62, 42,
]


def test_generator_matches_oeis_a005132() -> None:
    run = generate(20)
    assert list(run.terms) == A005132_PREFIX
    assert run.steps == 20


def test_bits_agree_with_the_move_that_was_taken() -> None:
    run = generate(500)
    for n in range(1, run.steps + 1):
        previous, current = run.terms[n - 1], run.terms[n]
        if run.bit(n) == DOWN_FREE:
            assert current == previous - n
        else:
            assert run.bit(n) == UP_BLOCKED
            assert current == previous + n


def test_slip_steps_are_step_numbers_not_offsets() -> None:
    run = generate(200)
    for n in run.slip_steps():
        assert 2 <= n <= run.steps
        assert run.bit(n) == run.bit(n - 1)
    non_slips = set(range(2, run.steps + 1)) - set(run.slip_steps())
    for n in non_slips:
        assert run.bit(n) != run.bit(n - 1)


def test_slip_rate_thins_out_with_the_horizon() -> None:
    """The headline caveat: the defects get rarer as N grows."""
    rates = [generate(n).slip_rate() for n in (1_000, 10_000, 100_000)]
    assert rates == sorted(rates, reverse=True)


def test_transition_matrix_rows_sum_to_one() -> None:
    matrix = generate(5_000).transition_matrix()
    for previous in (0, 1):
        row = matrix[f"p{previous}0"] + matrix[f"p{previous}1"]
        assert row == pytest.approx(1.0)


def test_window_around_slip_is_centred_and_clamped() -> None:
    run = generate(20_000)
    first_step, window = run.window_around_slip(25)
    assert len(window) == 25
    assert first_step >= 1
    assert first_step + len(window) - 1 <= run.steps
    assert any(window[i] == window[i - 1] for i in range(1, len(window)))


@pytest.mark.parametrize("steps", [1, 2, 3])
def test_short_runs_do_not_raise(steps: int) -> None:
    run = generate(steps)
    assert run.steps == steps
    run.window_around_slip(4)


def test_generate_rejects_empty_runs() -> None:
    with pytest.raises(ValueError):
        generate(0)


def _parse(svg: str) -> ET.Element:
    """Parse and return the SVG root, which also proves it is well-formed XML."""
    return ET.fromstring(svg)


def test_figures_emit_well_formed_svg() -> None:
    run = generate(2_000)
    for fragment, width, height in (
        (arc_diagram(run, 500, 200, arcs=24), 500, 200),
        (bit_ribbon(run.window_around_slip(21)[1], 800, 120, 1), 800, 120),
    ):
        root = _parse(svg_document(fragment, width, height, "figure"))
        assert root.get("viewBox") == f"0 0 {width} {height}"
        assert root.get("role") == "img"


def test_poster_is_well_formed_and_carries_the_measured_numbers() -> None:
    measurements = load_measurements()
    svg = poster(measurements, generate(60_000))
    root = _parse(svg)

    assert root.get("viewBox") == f"0 0 {POSTER_WIDTH:g} {POSTER_HEIGHT:g}"
    text = " ".join(node.text or "" for node in root.iter())

    assert f"{measurements['transition']['p01']:.4%}" in text
    assert f"{measurements['phase_slip']['count']:,}" in text
    assert str(measurements["empirical_horizon"]) not in text  # always thousands-separated
    assert f"{measurements['empirical_horizon']:,}" in text
    assert "not a proof" in text.lower() or "no limiting value" in text.lower()


def test_poster_declares_both_colour_schemes() -> None:
    svg = poster(load_measurements(), generate(2_000))
    assert "prefers-color-scheme: dark" in svg
    # Every colour is a token, so no raw hex may appear outside the token block.
    body = svg.split("</style>", 1)[1]
    assert not re.search(r"#[0-9a-fA-F]{6}", body)
