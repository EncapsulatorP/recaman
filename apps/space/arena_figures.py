"""Dependency-free SVG for the forward-held-out model arena."""

from __future__ import annotations

from html import escape


def arena_scoreboard(payload: dict, width: int = 1000, height: int = 430) -> str:
    agents = [agent for agent in payload["agents"] if "oracle" not in agent["status"]]
    x0, y0, plot_w = 285, 58, width - 350
    row_h = min(45, (height - 100) / len(agents))
    colours = {
        "forward-held-out": "#6d5dfc",
        "negative control": "#8da6bf",
    }
    parts = [
        '<text x="32" y="28" class="title">Held-out predictive code length — lower is better</text>',
    ]
    for index, agent in enumerate(sorted(agents, key=lambda row: row["bits_per_step"])):
        y = y0 + index * row_h
        value = agent["bits_per_step"]
        bar_w = plot_w * min(value, 1.0)
        colour = colours.get(agent["status"], "#f59e0b")
        parts.extend(
            [
                f'<text x="{x0 - 14}" y="{y + 15:.2f}" text-anchor="end" class="label">{escape(agent["name"])}</text>',
                f'<rect x="{x0}" y="{y}" width="{plot_w}" height="20" rx="10" class="track"/>',
                f'<rect x="{x0}" y="{y}" width="{bar_w:.2f}" height="20" rx="10" fill="{colour}"/>',
                f'<text x="{x0 + plot_w + 10}" y="{y + 15:.2f}" class="value">{value:.4f}</text>',
            ]
        )
    parts.append(f'<text x="{x0}" y="{height - 18}" class="small">1.0 bit/step = prevalence control · final 20% was untouched during fitting</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Held-out model arena" style="width:100%;height:auto;display:block">
<title>Held-out model arena</title><rect width="{width}" height="{height}" rx="18" fill="#fff"/>
<style>.title{{font:700 16px system-ui;fill:#172033}}.label{{font:12px system-ui;fill:#344054}}.value{{font:700 12px ui-monospace;fill:#172033}}.small{{font:11px system-ui;fill:#667085}}.track{{fill:#e4e7ec}}</style>{''.join(parts)}</svg>'''
