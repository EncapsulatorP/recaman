"""Interactive data views for the obstruction compression lab."""

from __future__ import annotations

import math
from html import escape

import pandas as pd
from holes import HoleCatalogue
from sequence import walk

CODEC_COLOURS = {
    "baseline": "#788da3",
    "structural": "#22e0ff",
    "general": "#ffb457",
}
EVENT_COLOURS = {
    "singleton": "#788da3",
    "range": "#22e0ff",
    "long range": "#ffb457",
}


def benchmark_frame(payload: dict) -> pd.DataFrame:
    """Return a hover-friendly, log-scaled codec scoreboard."""
    records = []
    for row in payload["rows"]:
        records.append(
            {
                "codec": row["name"],
                "log10(bytes)": math.log10(max(row["bytes"], 1)),
                "bytes": row["bytes"],
                "compression ×": round(row["ratio"], 2),
                "space saved": f"{row['saving']:.2%}",
                "family": row["kind"],
                "round trip": "exact" if row["exact_round_trip"] else "failed",
            }
        )
    return pd.DataFrame.from_records(records)


def catalogue_map_frame(catalogue: HoleCatalogue) -> pd.DataFrame:
    """Put every catalogue event into a hoverable log/log phase map."""
    records = []
    for index, event in enumerate(catalogue.events, start=1):
        event_class = (
            "singleton"
            if event.length == 1
            else "long range"
            if event.length >= 1_000
            else "range"
        )
        records.append(
            {
                "event": index,
                "log10(start)": math.log10(event.start),
                "log10(run length)": math.log10(event.length),
                "start": event.start,
                "end": event.end,
                "run length": event.length,
                "kind": event_class,
            }
        )
    return pd.DataFrame.from_records(records)


def phase_scope(center: int, width: int) -> tuple[str, str]:
    """Render a scrub-able scope around obstruction-bit phase slips."""
    center = max(1, min(int(center), 200_000))
    width = max(32, min(int(width), 256))
    low = max(1, center - width // 2)
    high = min(200_000, low + width - 1)
    low = max(1, high - width + 1)
    terms, bits = walk(high)
    visible = bits[low - 1 : high]
    visible_terms = terms[low : high + 1]
    slips = [
        step
        for step in range(low, high + 1)
        if step > 1 and bits[step - 1] == bits[step - 2]
    ]

    svg_width, svg_height = 1_000, 300
    left, right = 54, 970
    usable = right - left

    def x(step: int) -> float:
        return left + usable * (step - low) / max(high - low, 1)

    bit_points = " ".join(
        f"{x(step):.2f},{74 if bit else 142}"
        for step, bit in zip(range(low, high + 1), visible)
    )
    term_min, term_max = min(visible_terms), max(visible_terms)
    term_span = max(term_max - term_min, 1)
    term_points = " ".join(
        f"{x(step):.2f},{258 - 66 * (term - term_min) / term_span:.2f}"
        for step, term in zip(range(low, high + 1), visible_terms)
    )
    slip_marks = "".join(
        f'<line x1="{x(step):.2f}" y1="48" x2="{x(step):.2f}" y2="164" class="slip"/>'
        f'<circle cx="{x(step):.2f}" cy="{74 if bits[step - 1] else 142}" r="5" class="slip-dot"/>'
        for step in slips
    )
    tick_steps = sorted({low, center, high})
    ticks = "".join(
        f'<text x="{x(step):.2f}" y="181" text-anchor="middle" class="tick">n={step:,}</text>'
        for step in tick_steps
    )
    title = f"Obstruction-bit scope, n={low:,}…{high:,}"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" role="img" aria-label="{escape(title)}" class="kg-scope">
<title>{escape(title)}</title><defs><linearGradient id="scope-line" x1="0" x2="1"><stop stop-color="#22e0ff"/><stop offset="1" stop-color="#ff3df0"/></linearGradient></defs>
<style>.kg-scope{{width:100%;height:auto;display:block;background:#091827;border-radius:20px}}.guide{{stroke:#29435a;stroke-width:1}}.signal{{fill:none;stroke:url(#scope-line);stroke-width:2.3;stroke-linejoin:round;stroke-linecap:round}}.term{{fill:none;stroke:#ffb457;stroke-width:2;opacity:.9}}.slip{{stroke:#ffb457;stroke-width:1.5;opacity:.55}}.slip-dot{{fill:#ffb457;stroke:#07101a;stroke-width:2}}.label{{font:600 12px system-ui;fill:#9db3c8;letter-spacing:1.4px}}.tick{{font:11px ui-monospace;fill:#9db3c8}}.value{{font:600 12px ui-monospace;fill:#e8f6ff}}</style>
<text x="54" y="28" class="label">BLOCKED / FREE SIGNAL</text><text x="946" y="28" text-anchor="end" class="value">{len(slips)} phase slips</text>
<line x1="54" y1="74" x2="970" y2="74" class="guide"/><line x1="54" y1="142" x2="970" y2="142" class="guide"/>
<text x="42" y="78" text-anchor="end" class="value">1</text><text x="42" y="146" text-anchor="end" class="value">0</text>
{slip_marks}<polyline points="{bit_points}" class="signal"/>{ticks}
<text x="54" y="210" class="label">EXACT TRAJECTORY IN THIS WINDOW</text><polyline points="{term_points}" class="term"/>
</svg>'''

    slip_rate = len(slips) / max(len(visible) - 1, 1)
    report = f'''<div class="kg-result-grid" aria-live="polite">
<div class="kg-result"><span>window</span><strong>{low:,}–{high:,}</strong><small>{len(visible):,} exact steps</small></div>
<div class="kg-result"><span>phase slips</span><strong>{len(slips):,}</strong><small>{slip_rate:.2%} of transitions</small></div>
<div class="kg-result"><span>a({high:,})</span><strong>{visible_terms[-1]:,}</strong><small>reconstructed from the sign stream</small></div>
</div>'''
    return svg, report
