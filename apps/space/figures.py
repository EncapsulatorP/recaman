"""Vector figures for the Recaman obstruction Space and the repo infographic.

Everything here emits SVG text. There is no raster asset and no plotting
dependency: the Space ships plain standard-library Python, the output stays
crisp at any zoom, and it re-colours itself for light and dark viewers.

Colour roles follow a validated two-slot categorical pair - blue for the free
backward move, orange for the blocked forward move - over recessive ink, grid
and axis tokens. Labels always wear an ink token and sit beside a coloured
mark, so identity is never carried by colour alone.
"""

from __future__ import annotations

import math
from html import escape

from recaman import RecamanRun


FONT = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'

TOKENS_LIGHT = {
    "surface": "#fcfcfb",
    "plane": "#f9f9f7",
    "ink": "#0b0b0b",
    "ink2": "#52514e",
    "muted": "#898781",
    "grid": "#e1e0d9",
    "axis": "#c3c2b7",
    "free": "#2a78d6",
    "blocked": "#eb6834",
    "ring": "rgba(11,11,11,0.10)",
}
TOKENS_DARK = {
    "surface": "#1a1a19",
    "plane": "#0d0d0d",
    "ink": "#ffffff",
    "ink2": "#c3c2b7",
    "muted": "#898781",
    "grid": "#2c2c2a",
    "axis": "#383835",
    "free": "#3987e5",
    "blocked": "#d95926",
    "ring": "rgba(255,255,255,0.10)",
}

FREE_LABEL = "DOWN / FREE"
BLOCKED_LABEL = "UP / BLOCKED"


def _vars(tokens: dict[str, str]) -> str:
    return "".join(f"--rc-{name}:{value};" for name, value in tokens.items())


STYLE = (
    ".rc{" + _vars(TOKENS_LIGHT) + "font-family:" + FONT + ";}"
    "@media (prefers-color-scheme: dark){.rc{" + _vars(TOKENS_DARK) + "}}"
    ".rc .plane{fill:var(--rc-surface);}"
    ".rc .card{fill:var(--rc-plane);stroke:var(--rc-ring);stroke-width:1;}"
    ".rc text{fill:var(--rc-ink2);}"
    ".rc .h1{fill:var(--rc-ink);font-size:38px;font-weight:700;letter-spacing:-0.5px;}"
    ".rc .h2{fill:var(--rc-ink2);font-size:16px;}"
    ".rc .kicker{fill:var(--rc-muted);font-size:11px;font-weight:700;letter-spacing:1.5px;}"
    ".rc .title{fill:var(--rc-ink);font-size:16px;font-weight:600;}"
    ".rc .body{fill:var(--rc-ink2);font-size:13.5px;}"
    ".rc .small{fill:var(--rc-muted);font-size:12px;}"
    ".rc .tick{fill:var(--rc-muted);font-size:11px;font-variant-numeric:tabular-nums;}"
    ".rc .hero{fill:var(--rc-ink);font-size:44px;font-weight:700;letter-spacing:-1.2px;}"
    ".rc .num{fill:var(--rc-ink);font-size:14px;font-variant-numeric:tabular-nums;}"
    ".rc .mono{font-family:" + MONO + ";font-size:13px;fill:var(--rc-ink);}"
    ".rc .grid{stroke:var(--rc-grid);stroke-width:1;fill:none;}"
    ".rc .axis{stroke:var(--rc-axis);stroke-width:1;fill:none;}"
)


def svg_document(body: str, width: float, height: float, title: str) -> str:
    """Wrap a fragment in a responsive, theme-aware standalone SVG."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {_n(width)} {_n(height)}" width="100%" '
        f'role="img" aria-label="{escape(title)}" '
        'preserveAspectRatio="xMidYMid meet" class="rc">'
        f"<style>{STYLE}</style>"
        f"<title>{escape(title)}</title>"
        f'<rect class="plane" x="0" y="0" width="{_n(width)}" height="{_n(height)}"/>'
        f"{body}</svg>"
    )


def _n(value: float) -> str:
    """Format a coordinate compactly so the SVG stays small."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _text(
    x: float,
    y: float,
    content: str,
    cls: str = "body",
    anchor: str = "start",
    extra: str = "",
    preserve: bool = False,
) -> str:
    # SVG collapses runs of whitespace unless asked not to, which silently
    # destroys column alignment in the monospaced formula lines.
    space = ' xml:space="preserve"' if preserve else ""
    return (
        f'<text x="{_n(x)}" y="{_n(y)}" class="{cls}" text-anchor="{anchor}"'
        f"{space}{extra}>{escape(content)}</text>"
    )


def _card(x: float, y: float, w: float, h: float) -> str:
    return (
        f'<rect class="card" x="{_n(x)}" y="{_n(y)}" '
        f'width="{_n(w)}" height="{_n(h)}" rx="10"/>'
    )


def _swatch(x: float, y: float, role: str, label: str) -> str:
    return (
        f'<rect x="{_n(x)}" y="{_n(y - 7)}" width="14" height="4" rx="2" '
        f'fill="var(--rc-{role})"/>' + _text(x + 22, y, label, "small")
    )


def _panel_head(x: float, y: float, kicker: str, title: str) -> str:
    return _text(x, y, kicker, "kicker") + _text(x, y + 22, title, "title")


# ---------------------------------------------------------------------------
# Panel: Recaman arc diagram, drawn from the real sequence
# ---------------------------------------------------------------------------


def arc_diagram(
    run: RecamanRun,
    width: float,
    height: float,
    arcs: int | None = None,
    show_legend: bool = True,
) -> str:
    """The classic Recaman arc picture: side and colour both encode the move."""
    n_arcs = min(arcs or run.steps, run.steps)
    terms = run.terms[: n_arcs + 1]
    bits = run.bits[:n_arcs]

    pad_x = 14.0
    label_band = 40.0 if show_legend else 22.0
    plot_w = width - 2 * pad_x
    span = max(max(terms), 1)
    scale = plot_w / span

    def px(value: int) -> float:
        return pad_x + value * scale

    radii = [abs(terms[i + 1] - terms[i]) * scale / 2 for i in range(n_arcs)]
    max_r = max(radii) if radii else 1.0
    room = (height - label_band) / 2 - 8
    # One uniform vertical squash keeps every arc in proportion to every other.
    squash = min(1.0, room / max_r) if max_r else 1.0
    baseline = (height - label_band) / 2

    parts = [
        f'<line class="axis" x1="{_n(pad_x)}" y1="{_n(baseline)}" '
        f'x2="{_n(width - pad_x)}" y2="{_n(baseline)}"/>'
    ]

    for i in range(n_arcs):
        start, end = terms[i], terms[i + 1]
        role = "blocked" if bits[i] else "free"
        rx = radii[i]
        ry = rx * squash
        left, right = (start, end) if start < end else (end, start)
        # sweep=1 bulges above the baseline, sweep=0 below it.
        sweep = 1 if bits[i] else 0
        parts.append(
            f'<path d="M {_n(px(left))} {_n(baseline)} A {_n(rx)} {_n(ry)} 0 0 '
            f'{sweep} {_n(px(right))} {_n(baseline)}" fill="none" '
            f'stroke="var(--rc-{role})" stroke-width="1.7" opacity="0.92"/>'
        )

    for value in sorted(set(terms)):
        parts.append(
            f'<circle cx="{_n(px(value))}" cy="{_n(baseline)}" r="2.2" '
            'fill="var(--rc-axis)"/>'
        )

    # The arcs sweep straight through where number-line ticks would sit, so the
    # value range is stated in the caption row instead.
    if show_legend:
        legend_y = height - 8
        parts.append(_swatch(pad_x, legend_y, "free", f"{FREE_LABEL} · b = 0 · backward"))
        parts.append(
            _swatch(pad_x + width * 0.46, legend_y, "blocked", f"{BLOCKED_LABEL} · b = 1 · forward")
        )
    return "".join(parts)


# ---------------------------------------------------------------------------
# Panel: obstruction-bit square wave; a defect reads as a double plateau
# ---------------------------------------------------------------------------


def bit_ribbon(
    bits: tuple[int, ...] | list[int],
    width: float,
    height: float,
    first_index: int = 1,
    annotate_slip: bool = True,
) -> str:
    """Draw b(n) as a square wave, so a phase slip is a shape, not just a hue."""
    if not bits:
        return ""

    left_gutter, pad_r, top, bottom = 128.0, 20.0, 34.0, 44.0
    plot_w = width - left_gutter - pad_r
    step = plot_w / len(bits)
    y_high, y_low = top, height - bottom

    def level(bit: int) -> float:
        return y_high if bit else y_low

    parts: list[str] = []
    for y, role, label, bit_text in (
        (y_high, "blocked", BLOCKED_LABEL, "b = 1"),
        (y_low, "free", FREE_LABEL, "b = 0"),
    ):
        parts.append(
            f'<line class="grid" x1="{_n(left_gutter)}" y1="{_n(y)}" '
            f'x2="{_n(width - pad_r)}" y2="{_n(y)}"/>'
        )
        parts.append(_text(left_gutter - 18, y - 3, label, "small", "end"))
        parts.append(_text(left_gutter - 18, y + 13, bit_text, "num", "end"))
        parts.append(
            f'<rect x="{_n(left_gutter - 9)}" y="{_n(y - 8)}" width="4" height="16" '
            f'rx="2" fill="var(--rc-{role})"/>'
        )

    for i, bit in enumerate(bits):
        x0 = left_gutter + i * step
        role = "blocked" if bit else "free"
        parts.append(
            f'<line x1="{_n(x0)}" y1="{_n(level(bit))}" x2="{_n(x0 + step)}" '
            f'y2="{_n(level(bit))}" stroke="var(--rc-{role})" stroke-width="2.6" '
            'stroke-linecap="round"/>'
        )
        if i and bits[i - 1] != bit:
            parts.append(
                f'<line class="axis" x1="{_n(x0)}" y1="{_n(level(bits[i - 1]))}" '
                f'x2="{_n(x0)}" y2="{_n(level(bit))}"/>'
            )

    slips = [i for i in range(1, len(bits)) if bits[i] == bits[i - 1]]
    if annotate_slip and slips:
        i = slips[len(slips) // 2]
        x0 = left_gutter + (i - 1) * step
        x1 = left_gutter + (i + 1) * step
        y = level(bits[i])
        direction = -1 if bits[i] else 1
        bracket = y + direction * 20
        parts.append(
            f'<path d="M {_n(x0)} {_n(bracket)} L {_n(x0)} {_n((bracket + y) / 2)} '
            f'L {_n(x1)} {_n((bracket + y) / 2)} L {_n(x1)} {_n(bracket)}" '
            'fill="none" stroke="var(--rc-ink)" stroke-width="1.3" opacity="0.6"/>'
        )
        parts.append(
            _text(
                (x0 + x1) / 2,
                bracket + (-7 if direction < 0 else 15),
                "phase slip · b(n) = b(n−1)",
                "small",
                "middle",
                ' font-weight="600"',
            )
        )

    parts.append(_text(left_gutter, height - 12, f"n = {first_index:,}", "tick"))
    parts.append(
        _text(width - pad_r, height - 12, f"n = {first_index + len(bits) - 1:,}", "tick", "end")
    )
    return "".join(parts)


# ---------------------------------------------------------------------------
# Panel: how the measured slip rate falls as the horizon grows
# ---------------------------------------------------------------------------


def slip_decay_chart(points: list[tuple[int, float]], width: float, height: float) -> str:
    """Log-log decay of the same-bit slip rate. One series, so no legend box."""
    if len(points) < 2:
        return ""

    left, right, top, bottom = 60.0, 136.0, 18.0, 54.0
    plot_w = width - left - right
    plot_h = height - top - bottom

    xs = [math.log10(n) for n, _ in points]
    ys = [math.log10(rate) for _, rate in points]
    x_lo, x_hi = math.floor(min(xs)), math.ceil(max(xs))
    y_lo, y_hi = math.floor(min(ys)), math.ceil(max(ys))

    def px(log_n: float) -> float:
        return left + (log_n - x_lo) / (x_hi - x_lo) * plot_w

    def py(log_rate: float) -> float:
        return top + (y_hi - log_rate) / (y_hi - y_lo) * plot_h

    parts: list[str] = []
    for decade in range(int(y_lo), int(y_hi) + 1):
        y = py(decade)
        parts.append(
            f'<line class="grid" x1="{_n(left)}" y1="{_n(y)}" '
            f'x2="{_n(left + plot_w)}" y2="{_n(y)}"/>'
        )
        parts.append(_text(left - 10, y + 4, _percent_tick(decade), "tick", "end"))
    for decade in range(int(x_lo), int(x_hi) + 1):
        x = px(decade)
        parts.append(
            f'<line class="grid" x1="{_n(x)}" y1="{_n(top)}" '
            f'x2="{_n(x)}" y2="{_n(top + plot_h)}"/>'
        )
        parts.append(_text(x, top + plot_h + 18, f"10{_superscript(decade)}", "tick", "middle"))
    parts.append(
        f'<line class="axis" x1="{_n(left)}" y1="{_n(top + plot_h)}" '
        f'x2="{_n(left + plot_w)}" y2="{_n(top + plot_h)}"/>'
    )

    slope, intercept = _fit_line(xs, ys)
    guide = " ".join(f"{_n(px(x))},{_n(py(intercept + slope * x))}" for x in (x_lo, x_hi))
    parts.append(
        f'<polyline points="{guide}" fill="none" stroke="var(--rc-muted)" '
        'stroke-width="1.1" opacity="0.85"/>'
    )
    # The guide hugs the data, so its label goes in the empty lower-left corner.
    parts.append(
        _text(
            left + 8,
            top + plot_h - 10,
            f"power-law guide · slope {slope:.2f}",
            "small",
        )
    )

    line = " ".join(f"{_n(px(x))},{_n(py(y))}" for x, y in zip(xs, ys))
    parts.append(
        f'<polyline points="{line}" fill="none" stroke="var(--rc-free)" stroke-width="2"/>'
    )
    for x, y in zip(xs, ys):
        parts.append(
            f'<circle cx="{_n(px(x))}" cy="{_n(py(y))}" r="4.5" fill="var(--rc-free)" '
            'stroke="var(--rc-surface)" stroke-width="2"/>'
        )

    last_n, last_rate = points[-1]
    parts.append(
        f'<line class="axis" x1="{_n(px(xs[-1]) + 8)}" y1="{_n(py(ys[-1]))}" '
        f'x2="{_n(px(xs[-1]) + 22)}" y2="{_n(py(ys[-1]))}"/>'
    )
    parts.append(_text(px(xs[-1]) + 28, py(ys[-1]) - 1, f"{last_rate:.4%}", "num"))
    parts.append(
        _text(px(xs[-1]) + 28, py(ys[-1]) + 15, f"at N = 10{_superscript(int(round(xs[-1])))}", "small")
    )
    parts.append(
        _text(left + plot_w / 2, top + plot_h + 40, "measurement horizon N", "small", "middle")
    )
    return "".join(parts)


def _percent_tick(decade: int) -> str:
    value = 10.0**decade * 100
    return f"{value:g}%" if value >= 0.01 else f"{value:.3g}%"


def _superscript(value: int) -> str:
    digits = "⁰¹²³⁴⁵⁶⁷⁸⁹"
    sign = "⁻" if value < 0 else ""
    return sign + "".join(digits[int(d)] for d in str(abs(value)))


def _fit_line(xs: list[float], ys: list[float]) -> tuple[float, float]:
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denominator = sum((x - mean_x) ** 2 for x in xs)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denominator
    return slope, mean_y - slope * mean_x


# ---------------------------------------------------------------------------
# Panel: the measured transition table
# ---------------------------------------------------------------------------


def transition_table(matrix: dict[str, float], x: float, y: float, width: float) -> str:
    """Four measured conditional probabilities as a table, not as a chart."""
    rows = (
        ("0", FREE_LABEL, "free", matrix["p00"], matrix["p01"]),
        ("1", BLOCKED_LABEL, "blocked", matrix["p10"], matrix["p11"]),
    )
    col_zero, col_one = x + width * 0.58, x + width * 0.87
    parts = [
        _text(x, y, "PREVIOUS BIT", "kicker"),
        _text(col_zero, y, "NEXT b = 0", "kicker", "middle"),
        _text(col_one, y, "NEXT b = 1", "kicker", "middle"),
        f'<line class="axis" x1="{_n(x)}" y1="{_n(y + 12)}" '
        f'x2="{_n(x + width)}" y2="{_n(y + 12)}"/>',
    ]
    for index, (bit, label, role, p_zero, p_one) in enumerate(rows):
        row_y = y + 38 + index * 32
        parts.append(
            f'<rect x="{_n(x)}" y="{_n(row_y - 9)}" width="4" height="12" rx="2" '
            f'fill="var(--rc-{role})"/>'
        )
        parts.append(_text(x + 14, row_y, f"b = {bit}   {label}", "body"))
        for column, value in ((col_zero, p_zero), (col_one, p_one)):
            emphasis = ' font-weight="700"' if value > 0.5 else ' opacity="0.5"'
            parts.append(_text(column, row_y, f"{value:.4%}", "num", "middle", emphasis))
    return "".join(parts)


# ---------------------------------------------------------------------------
# The composed poster, shared by the Space header and the repo infographic
# ---------------------------------------------------------------------------

POSTER_WIDTH = 1200.0
POSTER_HEIGHT = 1010.0


def _paragraph(
    x: float,
    y: float,
    lines: list[str],
    leading: float = 20.0,
    cls: str = "body",
) -> str:
    return "".join(_text(x, y + i * leading, line, cls) for i, line in enumerate(lines))


def poster(measurements: dict, run: RecamanRun) -> str:
    """Compose the full infographic from live sequence data and saved measurements.

    `run` supplies the pictures (arcs and the bit stream); `measurements`
    supplies every number, so the poster cannot drift from the validator run
    that produced it.
    """
    transition = measurements["transition"]
    slip = measurements["phase_slip"]
    horizon = measurements["empirical_horizon"]
    points = [(row["n"], row["slip_rate"]) for row in measurements["horizon_scan"]]

    parts: list[str] = []

    # --- title band --------------------------------------------------------
    parts.append(_text(40, 52, "RECAMÁN OBSTRUCTIONS · PROCESS-SIDE RESULT", "kicker"))
    parts.append(_text(40, 92, "Predicting Recamán's next move", "h1"))
    parts.append(
        _text(
            40,
            120,
            f"The previous obstruction bit calls the next one "
            f"{transition['p01']:.2%} of the time, measured over N = {horizon:,} steps.",
            "h2",
        )
    )
    parts.append(
        f'<line class="axis" x1="40" y1="140" x2="{_n(POSTER_WIDTH - 40)}" y2="140"/>'
    )

    # --- 1 · the rule ------------------------------------------------------
    parts.append(_card(36, 158, 552, 344))
    parts.append(_panel_head(60, 190, "1 · THE RULE", "Try backward first, else go forward"))
    for offset, line in enumerate(
        (
            "a(0) = 0",
            "a(n) = a(n−1) − n    if positive and unvisited    →  b(n) = 0",
            "a(n) = a(n−1) + n    otherwise                    →  b(n) = 1",
        )
    ):
        parts.append(_text(60, 248 + offset * 21, line, "mono", preserve=True))
    parts.append(
        _text(
            60,
            322,
            f"The first {min(run.steps, 24)} steps drawn as arcs, over values 0 – "
            f"{max(run.terms[:25]):,}:",
            "small",
        )
    )
    parts.append(
        f'<g transform="translate(56,330)">' + arc_diagram(run, 512, 164, arcs=24) + "</g>"
    )

    # --- 2 · the measured transition --------------------------------------
    parts.append(_card(612, 158, 552, 344))
    parts.append(
        _panel_head(636, 190, "2 · THE MEASURED TRANSITION", "The previous bit is the state")
    )
    parts.append(_text(636, 272, f"{transition['p01']:.2%}", "hero"))
    parts.append(
        _paragraph(
            636,
            300,
            [
                "of steps that follow a free backward move are blocked,",
                f"against a {measurements['accuracy']['majority_baseline']:.0%} coin-flip baseline.",
            ],
            leading=18,
            cls="small",
        )
    )
    parts.append(transition_table(transition, 636, 356, 504))
    parts.append(
        _paragraph(
            636,
            470,
            [
                f"The classic Θ₃ wheel is {measurements['theta3_wheel']['verdict'].lower()} on the "
                "same run: its two",
                f"states differ by only {measurements['theta3_wheel']['abs_delta_q']:.1e}.",
            ],
            leading=17,
            cls="small",
        )
    )

    # --- 3 · what the errors look like ------------------------------------
    first_step, window = run.window_around_slip(23)
    parts.append(_card(36, 522, 1128, 184))
    parts.append(
        _panel_head(
            60,
            554,
            "3 · WHAT THE ERRORS LOOK LIKE",
            f"One real phase slip in the bit stream near n = {first_step + 11:,}",
        )
    )
    parts.append(
        f'<g transform="translate(56,584)">' + bit_ribbon(window, 1088, 116, first_step) + "</g>"
    )

    # --- 4 · why this is a snapshot ---------------------------------------
    parts.append(_card(36, 726, 700, 232))
    parts.append(
        _panel_head(60, 758, "4 · WHY THIS IS A SNAPSHOT", "The slip rate is still falling")
    )
    parts.append(f'<g transform="translate(48,790)">' + slip_decay_chart(points, 676, 160) + "</g>")

    parts.append(_card(760, 726, 404, 232))
    parts.append(_panel_head(784, 758, "READ THIS BEFORE CITING IT", "What it does not claim"))
    first_rate = points[0][1]
    parts.append(
        _paragraph(
            784,
            812,
            [
                f"The rate fell by a factor of {first_rate / slip['rate']:.0f} between",
                "N = 10⁴ and N = 10⁷ and shows no sign of",
                "settling, so no limiting value is claimed.",
                "",
                f"Observed: {slip['count']:,} slips across",
                f"{slip['pairs']:,} consecutive pairs — a mean run",
                f"of {slip['mean_run_length']:.0f} clean alternations between defects.",
            ],
            leading=17,
            cls="small",
        )
    )

    # --- footer ------------------------------------------------------------
    parts.append(
        f'<line class="axis" x1="40" y1="{_n(POSTER_HEIGHT - 32)}" '
        f'x2="{_n(POSTER_WIDTH - 40)}" y2="{_n(POSTER_HEIGHT - 32)}"/>'
    )
    parts.append(
        _text(
            40,
            POSTER_HEIGHT - 12,
            "Predicts the next obstruction bit only — not where the rare slips land, "
            "and not which integers stay permanently missing.",
            "small",
        )
    )
    parts.append(
        _text(
            POSTER_WIDTH - 40,
            POSTER_HEIGHT - 12,
            f"source: {measurements['source']}",
            "small",
            "end",
        )
    )

    return svg_document(
        "".join(parts), POSTER_WIDTH, POSTER_HEIGHT, "Predicting Recaman's next move"
    )
