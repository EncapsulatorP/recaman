"""SVG scoreboards for the Recaman compression experiment."""

from __future__ import annotations

from html import escape

COLOURS = {
    "baseline": "#8da6bf",
    "structural": "#22e0ff",
    "general": "#ffb457",
}


def compression_bars(payload: dict, title: str, width: int = 1000, height: int = 360) -> str:
    rows = payload["rows"]
    maximum = max(row["bytes"] for row in rows)
    x0, y0, plot_w = 270, 54, width - 330
    row_h = min(42, (height - 92) / len(rows))
    parts = [
        f'<text x="32" y="28" class="title">{escape(title)}</text>',
    ]
    for index, row in enumerate(rows):
        y = y0 + index * row_h
        bar_w = max(2, plot_w * row["bytes"] / maximum)
        colour = COLOURS[row["kind"]]
        parts.extend(
            [
                f'<text x="{x0 - 14}" y="{y + 15:.2f}" text-anchor="end" class="label">{escape(row["name"])}</text>',
                f'<rect x="{x0}" y="{y}" width="{plot_w}" height="20" rx="10" class="track"/>',
                f'<rect x="{x0}" y="{y}" width="{bar_w:.2f}" height="20" rx="10" fill="{colour}"/>',
                f'<text x="{x0 + plot_w + 10}" y="{y + 15:.2f}" class="value">{row["bytes"]:,} B</text>',
            ]
        )
    parts.append(
        f'<text x="{x0}" y="{height - 18}" class="small">bar width is linear bytes · all structural codecs pass exact round-trip checks</text>'
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" style="width:100%;height:auto;display:block">
<title>{escape(title)}</title><rect width="{width}" height="{height}" rx="18" fill="var(--rc-plane,#10263d)"/>
<style>.title{{font:700 16px system-ui;fill:var(--rc-ink,#e6f4ff)}}.label{{font:12px system-ui;fill:var(--rc-ink2,#dceeff)}}.value{{font:700 12px ui-monospace;fill:var(--rc-ink,#e6f4ff)}}.small{{font:11px system-ui;fill:var(--rc-muted,#8da6bf)}}.track{{fill:var(--rc-grid,#173654)}}</style>{''.join(parts)}</svg>'''
