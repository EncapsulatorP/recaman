"""Vector figures for the Recaman absolute-hole catalogue — Claude.ai version.

Everything here emits SVG text. There is no raster asset and no plotting
dependency: this Space ships plain standard-library Python, the output stays
crisp at any zoom, and it re-colours itself for light and dark viewers.

Colour follows the kugguk2022 house style — the neon-on-deep-space palette of
the Repo Galaxy artwork — without letting decoration touch the data channel.
Exactly two hues encode anything: brand cyan and brand amber separate the two
move directions in the arc diagram and the leakage-reduced from the easier
tasks in the score chart. Every label still wears an ink token and sits beside
a coloured mark, so identity is never carried by colour alone.

Both data slots clear the data-viz palette checks (chroma, CVD separation,
normal-vision separation, contrast) in both modes. One documented deviation:
in dark mode the two slots keep the brand's own brightness, which sits above
the checker's dark lightness band. That band is tuned to a lighter reference
surface than this palette's `#07101a`, and every reader-safety check still
passes, so the brand values are kept rather than dulled.

The module name and the watermark keep this variant distinct from the
next-move Space in `apps/space/`, which reports a different quantity entirely.
"""

from __future__ import annotations

import math
from html import escape

from holes import HoleCatalogue


VARIANT = "Claude.ai version"

FONT = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'

# Palette taken from the kugguk2022 "Repo Galaxy" artwork: neon on deep space.
# Data marks use only two slots — brand cyan and brand amber — because the
# figures only ever separate two things. The remaining brand hues are chrome:
# panel kickers and rules, never an encoding, so nothing rides on telling them
# apart. The two data slots were validated with the data-viz palette checker
# (see the module docstring for the one documented deviation).
BRAND = {
    "cyan": "#22e0ff",
    "amber": "#ffb457",
    "magenta": "#ff3df0",
    "blue": "#4d8dff",
    "rose": "#ff6b8f",
    "green": "#43ff9e",
}

TOKENS_LIGHT = {
    "surface": "#f8f7f2",
    "plane": "#ffffff",
    "ink": "#171510",
    "ink2": "#3f4a55",
    "muted": "#5d6b7a",
    "grid": "#e4e6e2",
    "axis": "#c7ccc9",
    "primary": "#008eab",
    "accent": "#ae6800",
    "chrome-1": "#008eab",
    "chrome-2": "#b14da7",
    "chrome-3": "#ae6800",
    "chrome-4": "#00964b",
    "ring": "rgba(23,21,16,0.12)",
    "glow": "rgba(0,142,171,0.00)",
}
TOKENS_DARK = {
    "surface": "#07101a",
    "plane": "#10263d",
    "ink": "#e6f4ff",
    "ink2": "#dceeff",
    "muted": "#8da6bf",
    "grid": "#173654",
    "axis": "#2a4a6b",
    "primary": "#22e0ff",
    "accent": "#ffb457",
    "chrome-1": "#22e0ff",
    "chrome-2": "#ff3df0",
    "chrome-3": "#ffb457",
    "chrome-4": "#43ff9e",
    "ring": "rgba(34,224,255,0.22)",
    "glow": "rgba(34,224,255,0.55)",
}

def _vars(tokens: dict[str, str]) -> str:
    return "".join(f"--rc-{name}:{value};" for name, value in tokens.items())


STYLE = (
    ".rch{" + _vars(TOKENS_LIGHT) + "font-family:" + FONT + ";}"
    "@media (prefers-color-scheme: dark){.rch{" + _vars(TOKENS_DARK) + "}}"
    ".rch .plane{fill:var(--rc-surface);}"
    ".rch .rule{fill:url(#brandRule);}"
    ".rch .card{fill:var(--rc-plane);stroke:var(--rc-ring);stroke-width:1;}"
    ".rch text{fill:var(--rc-ink2);}"
    ".rch .h1{fill:var(--rc-ink);font-size:38px;font-weight:700;letter-spacing:-0.5px;}"
    ".rch .h2{fill:var(--rc-ink2);font-size:16px;}"
    ".rch .kicker{font-size:11px;font-weight:700;letter-spacing:1.5px;}"
    ".rch .k1{fill:var(--rc-chrome-1);} .rch .k2{fill:var(--rc-chrome-2);}"
    ".rch .k3{fill:var(--rc-chrome-3);} .rch .k4{fill:var(--rc-chrome-4);}"
    ".rch .k0{fill:var(--rc-muted);}"
    ".rch .title{fill:var(--rc-ink);font-size:16px;font-weight:600;}"
    ".rch .body{fill:var(--rc-ink2);font-size:13.5px;}"
    ".rch .small{fill:var(--rc-muted);font-size:12px;}"
    ".rch .tick{fill:var(--rc-muted);font-size:11px;font-variant-numeric:tabular-nums;}"
    ".rch .hero{fill:var(--rc-ink);font-size:42px;font-weight:700;letter-spacing:-1.2px;}"
    ".rch .num{fill:var(--rc-ink);font-size:14px;font-variant-numeric:tabular-nums;}"
    ".rch .mono{font-family:" + MONO + ";font-size:13px;fill:var(--rc-ink);}"
    ".rch .grid{stroke:var(--rc-grid);stroke-width:1;fill:none;}"
    ".rch .axis{stroke:var(--rc-axis);stroke-width:1;fill:none;}"
    ".rch .stamp{fill:var(--rc-chrome-1);font-size:10px;font-weight:700;letter-spacing:1.4px;}"
    ".rch .stamp-box{fill:none;stroke:var(--rc-chrome-1);stroke-width:1;opacity:0.55;}"
    ".rch .glow{filter:drop-shadow(0 0 6px var(--rc-glow));}"
)


def svg_document(body: str, width: float, height: float, title: str) -> str:
    """Wrap a fragment in a responsive, theme-aware standalone SVG."""
    labelled = f"{title} ({VARIANT})"
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {_n(width)} {_n(height)}" width="100%" '
        f'role="img" aria-label="{escape(labelled)}" '
        'preserveAspectRatio="xMidYMid meet" class="rch">'
        f"<style>{STYLE}</style>"
        "<defs><linearGradient id=\"brandRule\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"0\">"
        '<stop offset="0" stop-color="var(--rc-chrome-1)"/>'
        '<stop offset="0.5" stop-color="var(--rc-chrome-2)"/>'
        '<stop offset="1" stop-color="var(--rc-chrome-3)"/>'
        "</linearGradient></defs>"
        f"<title>{escape(labelled)}</title>"
        f'<rect class="plane" x="0" y="0" width="{_n(width)}" height="{_n(height)}"/>'
        f"{body}</svg>"
    )


def watermark(x: float, y: float, anchor: str = "end") -> str:
    """The variant stamp: a hairline pill naming which version this is."""
    box_w, box_h = 132.0, 20.0
    box_x = x - box_w if anchor == "end" else x
    return (
        '<g class="glow">'
        f'<rect class="stamp-box" x="{_n(box_x)}" y="{_n(y - box_h / 2)}" '
        f'width="{_n(box_w)}" height="{_n(box_h)}" rx="10"/>'
        + _text(box_x + box_w / 2, y + 4, VARIANT.upper(), "stamp", "middle")
        + "</g>"
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
    # destroys column alignment in the monospaced lines.
    space = ' xml:space="preserve"' if preserve else ""
    return (
        f'<text x="{_n(x)}" y="{_n(y)}" class="{cls}" text-anchor="{anchor}"'
        f"{space}{extra}>{escape(content)}</text>"
    )


def _rule(x: float, y: float, width: float, height: float = 2.5) -> str:
    """A brand-gradient rule.

    Drawn as a rect, not a line: a horizontal line has a zero-height bounding
    box, and an objectBoundingBox gradient collapses to nothing on it.
    """
    return (
        f'<rect class="rule" x="{_n(x)}" y="{_n(y - height / 2)}" '
        f'width="{_n(width)}" height="{_n(height)}" rx="{_n(height / 2)}"/>'
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


def _panel_head(x: float, y: float, kicker: str, title: str, slot: int = 0) -> str:
    """A panel heading. `slot` picks a brand hue for the kicker — decoration
    only: the kicker text never encodes anything, so nothing depends on
    telling the hues apart."""
    return _text(x, y, kicker, f"kicker k{slot}") + _text(x, y + 22, title, "title")


def _paragraph(
    x: float,
    y: float,
    lines: list[str],
    leading: float = 18.0,
    cls: str = "small",
) -> str:
    return "".join(_text(x, y + i * leading, line, cls) for i, line in enumerate(lines))


def _superscript(value: int) -> str:
    digits = "⁰¹²³⁴⁵⁶⁷⁸⁹"
    sign = "⁻" if value < 0 else ""
    return sign + "".join(digits[int(d)] for d in str(abs(value)))


def _compact(value: int) -> str:
    """Short axis-friendly form: 1,200,000 -> 1.2M."""
    for limit, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "k")):
        if value >= limit:
            scaled = value / limit
            text = f"{scaled:.1f}".rstrip("0").rstrip(".")
            return f"{text}{suffix}"
    return f"{value:,}"


# ---------------------------------------------------------------------------
# The sequence itself: what it means for an integer to be missed
# ---------------------------------------------------------------------------


def arc_diagram(
    terms: tuple[int, ...],
    forward: tuple[bool, ...],
    width: float,
    height: float,
    show_legend: bool = True,
) -> str:
    """The classic Recaman arc picture, one arc per step.

    Side and colour both carry the move direction. This illustrates how the
    sequence covers the number line; it does not, and cannot, show an absolute
    hole, because the smallest catalogued hole is far beyond this range.
    """
    n_arcs = len(forward)
    pad_x = 14.0
    label_band = 40.0 if show_legend else 20.0
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
        role = "accent" if forward[i] else "primary"
        rx = radii[i]
        left, right = (start, end) if start < end else (end, start)
        # sweep=1 bulges above the baseline, sweep=0 below it.
        sweep = 1 if forward[i] else 0
        parts.append(
            f'<path d="M {_n(px(left))} {_n(baseline)} A {_n(rx)} {_n(rx * squash)} '
            f'0 0 {sweep} {_n(px(right))} {_n(baseline)}" fill="none" '
            f'stroke="var(--rc-{role})" stroke-width="1.7" opacity="0.92"/>'
        )

    for value in sorted(set(terms)):
        parts.append(
            f'<circle cx="{_n(px(value))}" cy="{_n(baseline)}" r="2.2" '
            'fill="var(--rc-axis)"/>'
        )

    if show_legend:
        legend_y = height - 8
        parts.append(_swatch(pad_x, legend_y, "primary", "backward move  a(n−1) − n"))
        parts.append(
            _swatch(pad_x + width * 0.46, legend_y, "accent", "forward move  a(n−1) + n")
        )
    return "".join(parts)


# ---------------------------------------------------------------------------
# Where the missing integers sit
# ---------------------------------------------------------------------------


def decade_chart(
    profile: list[tuple[int, int, int]],
    width: float,
    height: float,
    partial_first: bool = True,
) -> str:
    """Missing integers per power-of-ten band, on a log scale.

    Counts, not densities: the lowest band is only covered from the catalogue's
    first entry upward, and a count stays exact under partial coverage where a
    density would not.
    """
    if len(profile) < 2:
        return ""

    left, right, top, bottom = 62.0, 34.0, 32.0, 52.0
    plot_w = width - left - right
    plot_h = height - top - bottom

    counts = [max(integers, 1) for _, _, integers in profile]
    y_lo = math.floor(math.log10(min(counts)))
    y_hi = math.ceil(math.log10(max(counts)))
    step = plot_w / max(len(profile) - 1, 1)

    def px(index: int) -> float:
        return left + index * step

    def py(count: int) -> float:
        return top + (y_hi - math.log10(count)) / (y_hi - y_lo) * plot_h

    parts: list[str] = []
    for decade in range(y_lo, y_hi + 1):
        y = top + (y_hi - decade) / (y_hi - y_lo) * plot_h
        parts.append(
            f'<line class="grid" x1="{_n(left)}" y1="{_n(y)}" '
            f'x2="{_n(left + plot_w)}" y2="{_n(y)}"/>'
        )
        parts.append(_text(left - 10, y + 4, _compact(10**decade), "tick", "end"))
    parts.append(
        f'<line class="axis" x1="{_n(left)}" y1="{_n(top + plot_h)}" '
        f'x2="{_n(left + plot_w)}" y2="{_n(top + plot_h)}"/>'
    )

    line = " ".join(f"{_n(px(i))},{_n(py(c))}" for i, c in enumerate(counts))
    parts.append(
        f'<polyline points="{line}" fill="none" stroke="var(--rc-primary)" stroke-width="2"/>'
    )
    for i, (exponent, _, integers) in enumerate(profile):
        parts.append(
            f'<circle cx="{_n(px(i))}" cy="{_n(py(counts[i]))}" r="4.5" '
            'fill="var(--rc-primary)" stroke="var(--rc-surface)" stroke-width="2"/>'
        )
        parts.append(
            _text(px(i), top + plot_h + 18, f"10{_superscript(exponent)}", "tick", "middle")
        )
        if i == 0:
            parts.append(_text(px(i) + 10, py(counts[i]) - 9, f"{integers:,}", "num"))
        elif i == len(profile) - 1:
            parts.append(_text(px(i), py(counts[i]) - 13, f"{integers:,}", "num", "end"))

    parts.append(_text(left, top + plot_h + 40, "band, by power of ten", "small"))
    if partial_first:
        parts.append(
            _text(left + plot_w, top + plot_h + 40, "lowest band partly covered", "small", "end")
        )
    return "".join(parts)


def span_strip(
    catalogue: HoleCatalogue,
    low: int,
    high: int,
    width: float,
    height: float,
    buckets: int = 220,
) -> str:
    """A density strip of the missing integers across [low, high].

    Each column is one slice of the window; its height is the share of that
    slice the catalogue marks missing, so a tall column is a dense stretch.
    """
    low, high = max(low, catalogue.span_start), min(high, catalogue.span_end)
    if high <= low:
        return ""

    left, right, top, bottom = 16.0, 16.0, 12.0, 34.0
    plot_w = width - left - right
    plot_h = height - top - bottom
    slice_width = (high - low + 1) / buckets

    shares = [0.0] * buckets
    for event in catalogue.events_in_window(low, high):
        first = max(int((max(event.start, low) - low) / slice_width), 0)
        last = min(int((min(event.end, high) - low) / slice_width), buckets - 1)
        for index in range(first, last + 1):
            slice_lo = low + index * slice_width
            slice_hi = slice_lo + slice_width
            overlap = min(event.end + 1, slice_hi) - max(event.start, slice_lo)
            if overlap > 0:
                shares[index] += overlap / slice_width

    peak = max(shares) if any(shares) else 1.0
    column = plot_w / buckets

    parts = [
        f'<line class="axis" x1="{_n(left)}" y1="{_n(top + plot_h)}" '
        f'x2="{_n(left + plot_w)}" y2="{_n(top + plot_h)}"/>'
    ]
    for index, share in enumerate(shares):
        if share <= 0:
            continue
        # A floor of 2px keeps a lone missing integer visible at this scale.
        bar = max(share / peak * plot_h, 2.0)
        parts.append(
            f'<rect x="{_n(left + index * column)}" y="{_n(top + plot_h - bar)}" '
            f'width="{_n(max(column - 0.6, 0.6))}" height="{_n(bar)}" '
            'fill="var(--rc-primary)"/>'
        )

    parts.append(_text(left, height - 12, f"{low:,}", "tick"))
    parts.append(_text(left + plot_w, height - 12, f"{high:,}", "tick", "end"))
    parts.append(
        _text(
            left + plot_w / 2,
            height - 12,
            f"tallest column {peak:.1%} missing",
            "small",
            "middle",
        )
    )
    return "".join(parts)


# ---------------------------------------------------------------------------
# How the missing integers clump, and what the models score
# ---------------------------------------------------------------------------


def bucket_table(
    buckets: list[tuple[str, int, int]],
    total_integers: int,
    x: float,
    y: float,
    width: float,
) -> str:
    """Run-length breakdown as a table: counts belong in columns, not in bars."""
    col_events, col_integers, col_share = x + width * 0.46, x + width * 0.72, x + width * 0.98
    parts = [
        _text(x, y, "RUN LENGTH", "kicker"),
        _text(col_events, y, "EVENTS", "kicker", "end"),
        _text(col_integers, y, "MISSING", "kicker", "end"),
        _text(col_share, y, "SHARE", "kicker", "end"),
        f'<line class="axis" x1="{_n(x)}" y1="{_n(y + 10)}" '
        f'x2="{_n(x + width)}" y2="{_n(y + 10)}"/>',
    ]
    for index, (label, events, integers) in enumerate(buckets):
        row_y = y + 30 + index * 22
        share = integers / total_integers if total_integers else 0.0
        emphasis = ' font-weight="700"' if share > 0.5 else ""
        parts.append(_text(x, row_y, label, "body", extra=' font-size="13"'))
        parts.append(_text(col_events, row_y, f"{events:,}", "num", "end"))
        parts.append(_text(col_integers, row_y, f"{integers:,}", "num", "end", emphasis))
        parts.append(_text(col_share, row_y, f"{share:.1%}", "num", "end", emphasis))
    return "".join(parts)


def auc_chart(
    rows: list[tuple[str, float, bool]],
    width: float,
    height: float,
    show_legend: bool = False,
) -> str:
    """Measured AUCs on a chance-anchored axis.

    `rows` are (label, auc, leakage_reduced). The axis starts at 0.5 because
    that is where a coin lands; the chance line is drawn, not implied. On the
    poster the legend sits beside the panel title, so it is off by default;
    standalone renders ask for it.
    """
    if not rows:
        return ""

    left, right, top, bottom = 264.0, 64.0, (36.0 if show_legend else 16.0), 44.0
    plot_w = width - left - right
    plot_h = height - top - bottom
    row_step = plot_h / len(rows)

    def px(auc: float) -> float:
        return left + (auc - 0.5) / 0.5 * plot_w

    parts: list[str] = []
    for tick in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        x = px(tick)
        parts.append(
            f'<line class="grid" x1="{_n(x)}" y1="{_n(top)}" '
            f'x2="{_n(x)}" y2="{_n(top + plot_h)}"/>'
        )
        parts.append(_text(x, top + plot_h + 16, f"{tick:.1f}", "tick", "middle"))

    parts.append(
        f'<line class="axis" x1="{_n(px(0.5))}" y1="{_n(top)}" '
        f'x2="{_n(px(0.5))}" y2="{_n(top + plot_h)}" stroke-width="1.5"/>'
    )
    parts.append(_text(px(0.5), top + plot_h + 32, "chance", "small", "middle"))

    for index, (label, auc, leakage_reduced) in enumerate(rows):
        y = top + (index + 0.5) * row_step
        role = "primary" if leakage_reduced else "accent"
        parts.append(
            f'<line x1="{_n(px(0.5))}" y1="{_n(y)}" x2="{_n(px(auc))}" y2="{_n(y)}" '
            f'stroke="var(--rc-{role})" stroke-width="2" stroke-linecap="round"/>'
        )
        parts.append(
            f'<circle cx="{_n(px(auc))}" cy="{_n(y)}" r="4.5" fill="var(--rc-{role})" '
            'stroke="var(--rc-surface)" stroke-width="2"/>'
        )
        parts.append(_text(left - 14, y + 4, label, "body", "end", ' font-size="13"'))
        parts.append(_text(px(auc) + 12, y + 4, f"{auc:.4f}", "num"))

    parts.append(_text(left + plot_w / 2, top + plot_h + 32, "mean AUC", "small", "middle"))
    if show_legend:
        parts.append(_swatch(left - 250, 16, "primary", "leakage-reduced task"))
        parts.append(_swatch(left - 62, 16, "accent", "easier task"))
    return "".join(parts)


def auc_rows(results: dict) -> list[tuple[str, float, bool]]:
    """Order the measured scores hardest-task-first, as the repo reads them."""
    version_c = results["version_c"]["datasets"]
    random_matrix = results["random_matrix"]
    short = {
        "A": "singleton starts",
        "B": "range starts",
        "C": "range ends",
        "D": "gap dynamics",
    }
    rows = [
        ("random-matrix · RF cross-validation", random_matrix["rf_cv_auc_mean"], True),
        ("random-matrix · best linear code", random_matrix["code_auc"], True),
    ]
    for name in ("D", "A", "B", "C"):
        payload = version_c[name]
        rows.append((f"Version C {name} · {short[name]}", payload["mean_auc"], name == "D"))
    return rows


# ---------------------------------------------------------------------------
# The composed poster
# ---------------------------------------------------------------------------

POSTER_WIDTH = 1200.0
POSTER_HEIGHT = 1010.0


def poster(catalogue: HoleCatalogue, results: dict, walk: tuple) -> str:
    """Compose the infographic from the catalogue and the saved model scores.

    `walk` is `(terms, forward)` for a short prefix of the sequence, used only
    to illustrate the rule in panel 1.
    """
    terms, forward = walk
    buckets = catalogue.length_buckets()
    long_runs = buckets[-1]
    concentration = long_runs[2] / catalogue.integer_count

    parts: list[str] = []

    # --- title band --------------------------------------------------------
    parts.append(_text(40, 52, "RECAMÁN OBSTRUCTIONS · THE HOLE CATALOGUE", "kicker k1"))
    parts.append(
        '<g class="glow">'
        + _text(40, 92, "The integers Recamán never reaches", "h1")
        + "</g>"
    )
    parts.append(
        _text(
            40,
            120,
            f"{catalogue.integer_count:,} certified absolute holes between "
            f"{catalogue.span_start:,} and {catalogue.span_end:,}.",
            "h2",
        )
    )
    parts.append(watermark(POSTER_WIDTH - 40, 52))
    parts.append(
        _rule(40, 140, POSTER_WIDTH - 80)
    )

    # --- 1 · what a hole is ------------------------------------------------
    parts.append(_card(36, 158, 552, 344))
    parts.append(_panel_head(60, 190, "1 · WHAT A HOLE IS", "A value the sequence never lands on", 1))
    for offset, line in enumerate(
        (
            "a(0) = 0",
            "a(n) = a(n−1) − n    if positive and unvisited",
            "a(n) = a(n−1) + n    otherwise",
        )
    ):
        parts.append(_text(60, 244 + offset * 21, line, "mono", preserve=True))
    parts.append(
        _paragraph(
            60,
            326,
            [
                "The sequence hops backward when it can and forward when it",
                "cannot. An integer it never lands on — at any step, ever — is",
                "an absolute hole. Nothing in the range drawn below is one:",
                f"the smallest hole in this catalogue is {catalogue.span_start:,}.",
            ],
            leading=17,
        )
    )
    parts.append(
        f'<g transform="translate(56,388)">' + arc_diagram(terms, forward, 512, 110) + "</g>"
    )

    # --- 2 · how many, and where -------------------------------------------
    parts.append(_card(612, 158, 552, 344))
    parts.append(_panel_head(636, 190, "2 · WHERE THEY SIT", "Missing integers by magnitude", 2))
    parts.append(
        _text(636, 262, f"{catalogue.coverage:.4%}", "hero", extra=' fill="var(--rc-chrome-2)"')
    )
    parts.append(
        _paragraph(
            636,
            288,
            [
                f"of the {catalogue.span_width:,} integers in the covered span are",
                f"missing — about one in {round(1 / catalogue.coverage):,}. The catalogue is",
                "complete over that span, so every other value is reached.",
            ],
            leading=17,
        )
    )
    parts.append(
        f'<g transform="translate(624,344)">'
        + decade_chart(catalogue.decade_profile(), 528, 148)
        + "</g>"
    )

    # --- 3 · they arrive in runs -------------------------------------------
    parts.append(_card(36, 522, 1128, 214))
    parts.append(
        _panel_head(60, 554, "3 · THEY ARRIVE IN RUNS", "Almost all of the mass is in 104 events", 3)
    )
    parts.append(
        _text(60, 626, f"{concentration:.1%}", "hero", extra=' fill="var(--rc-chrome-3)"')
    )
    parts.append(
        _paragraph(
            60,
            652,
            [
                f"of all missing integers fall inside the {long_runs[1]:,} runs of",
                f"{long_runs[0].replace('+', ' or more')} consecutive values, out of "
                f"{catalogue.event_count:,} events in total.",
                f"The longest single run is {max(catalogue.lengths()):,} consecutive integers.",
            ],
            leading=17,
        )
    )
    parts.append(bucket_table(buckets, catalogue.integer_count, 560, 566, 580))

    # --- 4 · what is predictable -------------------------------------------
    parts.append(_card(36, 756, 744, 202))
    parts.append(
        _panel_head(60, 788, "4 · WHAT IS PREDICTABLE", "Measured separation from matched controls", 4)
    )
    parts.append(_swatch(408, 788, "primary", "leakage-reduced task"))
    parts.append(_swatch(596, 788, "accent", "easier task"))
    parts.append(
        f'<g transform="translate(48,800)">' + auc_chart(auc_rows(results), 720, 152) + "</g>"
    )

    parts.append(_card(804, 756, 360, 202))
    parts.append(_panel_head(828, 788, "READ THIS BEFORE CITING IT", "What it does not claim"))
    parts.append(
        _paragraph(
            828,
            824,
            [
                "No model here decides whether a given integer",
                "is a hole. The honest scores sit between 0.60",
                "and 0.76 — real separation, far from a test.",
                "",
                "The three tasks above 0.99 ask an easier",
                "question and are kept only as a ceiling.",
                "",
                "Outside the covered span the catalogue is",
                "silent, and so is everything shown here.",
            ],
            leading=17,
        )
    )

    # --- footer ------------------------------------------------------------
    parts.append(
        _rule(40, POSTER_HEIGHT - 32, POSTER_WIDTH - 80, 2.0)
    )
    parts.append(
        _text(
            40,
            POSTER_HEIGHT - 12,
            "Hole catalogue certified by Benjamin Chaffin; scores measured in this repository.",
            "small",
        )
    )
    parts.append(
        _text(
            POSTER_WIDTH - 40,
            POSTER_HEIGHT - 12,
            f"{VARIANT} · source: {results['sources']['catalogue']}",
            "small",
            "end",
        )
    )

    return svg_document(
        "".join(parts), POSTER_WIDTH, POSTER_HEIGHT, "The integers Recaman never reaches"
    )
