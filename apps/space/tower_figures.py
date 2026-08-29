"""Dependency-free SVG views for the Obstruction & Tower Lab."""

from __future__ import annotations

from html import escape

from hole_catalogue import HoleCatalogue

PALETTE = {
    "ink": "#172033",
    "muted": "#667085",
    "grid": "#d8deea",
    "paper": "#ffffff",
    "violet": "#6d5dfc",
    "cyan": "#00a6b2",
    "amber": "#f59e0b",
    "rose": "#e54865",
    "green": "#15996b",
}


def _svg(body: str, width: int, height: int, title: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
 role="img" aria-label="{escape(title)}" style="width:100%;height:auto;display:block">
<title>{escape(title)}</title>
<rect width="{width}" height="{height}" rx="18" fill="{PALETTE['paper']}"/>
<style>
text{{font-family:Inter,ui-sans-serif,system-ui,sans-serif;fill:{PALETTE['ink']}}}
.small{{font-size:12px;fill:{PALETTE['muted']}}}.label{{font-size:13px;font-weight:650}}
.value{{font-size:16px;font-weight:750}}.grid{{stroke:{PALETTE['grid']};stroke-width:1}}
</style>{body}</svg>'''


def hole_density_svg(catalogue: HoleCatalogue, width: int = 1000, height: int = 250) -> str:
    bins = catalogue.density_bins(96)
    maximum = max(missing for _, _, missing in bins) or 1
    plot_x, plot_y, plot_w, plot_h = 56, 38, width - 88, height - 92
    bar_w = plot_w / len(bins)
    parts = [
        f'<text x="{plot_x}" y="24" class="label">Catalogue density across the covered span</text>',
        f'<line x1="{plot_x}" y1="{plot_y + plot_h}" x2="{plot_x + plot_w}" y2="{plot_y + plot_h}" class="grid"/>',
    ]
    for index, (_, _, missing) in enumerate(bins):
        bar_h = max(1.5, plot_h * missing / maximum) if missing else 0
        x = plot_x + index * bar_w
        y = plot_y + plot_h - bar_h
        opacity = 0.38 + 0.62 * missing / maximum
        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(bar_w - 1, 0.6):.2f}" '
            f'height="{bar_h:.2f}" rx="1" fill="{PALETTE["violet"]}" opacity="{opacity:.3f}"/>'
        )
    parts.extend(
        [
            f'<text x="{plot_x}" y="{height - 28}" class="small">{catalogue.span_start:,}</text>',
            f'<text x="{plot_x + plot_w}" y="{height - 28}" text-anchor="end" class="small">{catalogue.span_end:,}</text>',
            (
                f'<text x="{plot_x + plot_w / 2}" y="{height - 8}" text-anchor="middle" class="small">'
                'Height = catalogued integers per equal-width value bin (linear scale)</text>'
            ),
        ]
    )
    return _svg("".join(parts), width, height, "Density of catalogued Recamán obstructions")


def signed_tower_svg(rows: list[dict], width: int = 1000, height: int = 300) -> str:
    plot_x, plot_w, mid = 54, width - 86, 148
    bar_w = plot_w / max(len(rows), 1)
    maximum = max(abs(int(row["contribution"])) for row in rows) or 1
    parts = [
        f'<text x="{plot_x}" y="25" class="label">Signed triangular tower: each step contributes −n or +n</text>',
        f'<line x1="{plot_x}" y1="{mid}" x2="{plot_x + plot_w}" y2="{mid}" class="grid"/>',
        f'<text x="18" y="{mid - 64}" class="small">+n</text>',
        f'<text x="18" y="{mid + 72}" class="small">−n</text>',
    ]
    for index, row in enumerate(rows):
        contribution = int(row["contribution"])
        magnitude = 88 * abs(contribution) / maximum
        x = plot_x + index * bar_w
        y = mid - magnitude if contribution > 0 else mid
        colour = PALETTE["cyan"] if contribution > 0 else PALETTE["violet"]
        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(bar_w - 1.1, 1):.2f}" '
            f'height="{magnitude:.2f}" rx="1.5" fill="{colour}" opacity="0.82"/>'
        )
        if row["phase_slip"]:
            parts.append(
                f'<circle cx="{x + bar_w / 2:.2f}" cy="{mid:.2f}" r="4" '
                f'fill="{PALETTE["rose"]}" stroke="white" stroke-width="1.5"/>'
            )
    parts.extend(
        [
            f'<circle cx="{plot_x}" cy="{height - 36}" r="5" fill="{PALETTE["rose"]}"/>',
            f'<text x="{plot_x + 11}" y="{height - 31}" class="small">same-sign phase slip</text>',
            (
                f'<text x="{plot_x + plot_w}" y="{height - 31}" text-anchor="end" class="small">'
                f'steps {rows[0]["step"]:,}–{rows[-1]["step"]:,}</text>'
            ),
        ]
    )
    return _svg("".join(parts), width, height, "Signed Recamán step tower")


def rank_tower_svg(measurements: dict, selected: int, width: int = 1000, height: int = 320) -> str:
    tower = measurements["power_of_two_tower"]
    series = [
        ("Recamán", "real", PALETTE["violet"]),
        ("random null", "null_random", PALETTE["rose"]),
        ("pure alternation", "pure_alternation", PALETTE["cyan"]),
    ]
    max_level = len(tower["real"]) - 1
    max_rank = tower["vec_dim"]
    x0, y0, plot_w, plot_h = 62, 42, width - 100, height - 104
    parts = [
        f'<text x="{x0}" y="25" class="label">Power-of-two subsequence tower over GF(2)</text>',
    ]
    for tick in (0, 64, 128, 192, 256):
        y = y0 + plot_h * (1 - tick / max_rank)
        parts.append(f'<line x1="{x0}" y1="{y:.2f}" x2="{x0 + plot_w}" y2="{y:.2f}" class="grid"/>')
        parts.append(f'<text x="{x0 - 10}" y="{y + 4:.2f}" text-anchor="end" class="small">{tick}</text>')
    safe_x = x0 + plot_w * tower["artifact_free_max_level"] / max_level
    parts.append(
        f'<rect x="{x0}" y="{y0}" width="{safe_x - x0:.2f}" height="{plot_h}" '
        f'fill="{PALETTE["green"]}" opacity="0.055"/>'
    )
    for label, key, colour in series:
        points = []
        for row in tower[key]:
            x = x0 + plot_w * row["level"] / max_level
            y = y0 + plot_h * (1 - row["rank"] / max_rank)
            points.append(f"{x:.2f},{y:.2f}")
        parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{colour}" stroke-width="3"/>')
    selected_x = x0 + plot_w * selected / max_level
    parts.append(f'<line x1="{selected_x:.2f}" y1="{y0}" x2="{selected_x:.2f}" y2="{y0 + plot_h}" stroke="{PALETTE["amber"]}" stroke-width="2" stroke-dasharray="5 5"/>')
    legend_x = x0
    for label, _, colour in series:
        parts.append(f'<circle cx="{legend_x}" cy="{height - 38}" r="5" fill="{colour}"/>')
        parts.append(f'<text x="{legend_x + 10}" y="{height - 33}" class="small">{label}</text>')
        legend_x += 170
    parts.append(f'<text x="{x0 + plot_w}" y="{height - 33}" text-anchor="end" class="small">green = artifact-free through j = 7</text>')
    return _svg("".join(parts), width, height, "Power-of-two rank tower")


def power_probe_svg(payload: dict, width: int = 1000, height: int = 270) -> str:
    layers = payload["layers"]
    count = min(layers, 160)
    x0, plot_w = 62, width - 94
    cell_w = plot_w / count
    parts = [
        f'<text x="{x0}" y="25" class="label">Binary shadows: Recamán vs sign-flipping modular power iterator</text>',
    ]
    rows = [
        ("Recamán bₙ", payload["recaman_bits"][-count:], 64),
        ("flip tower", payload["flipped_shadow"][-count:], 124),
        ("fixed control", payload["fixed_shadow"][-count:], 184),
    ]
    for label, bits, y in rows:
        parts.append(f'<text x="{x0}" y="{y - 10}" class="small">{label}</text>')
        for index, bit in enumerate(bits):
            colour = PALETTE["violet"] if bit else PALETTE["cyan"]
            parts.append(
                f'<rect x="{x0 + index * cell_w:.2f}" y="{y}" width="{max(cell_w - 0.7, 1):.2f}" '
                f'height="22" rx="2" fill="{colour}" opacity="{0.9 if bit else 0.55}"/>'
            )
    parts.append(
        f'<text x="{x0}" y="{height - 18}" class="small">Last {count} layers · violet = 1 / upper-half residue · cyan = 0 / lower-half residue</text>'
    )
    return _svg("".join(parts), width, height, "Power iterator and Recamán bit shadows")


def evolution_race_svg(payload: dict, width: int = 1000, height: int = 360) -> str:
    """Draw free-running exact, alternation, and modular-power trajectories."""
    rows = payload["rows"]
    x0, y0, plot_w, plot_h = 70, 48, width - 108, height - 116
    series = [
        ("deterministic", "exact_value", PALETTE["ink"]),
        ("alternation model", "alternating_value", PALETTE["violet"]),
        ("power model", "power_value", PALETTE["amber"]),
    ]
    values = [int(row[key]) for _, key, _ in series for row in rows]
    low, high = min(values), max(values)
    span = max(high - low, 1)

    def point(index: int, value: int) -> tuple[float, float]:
        x = x0 + plot_w * index / max(len(rows) - 1, 1)
        y = y0 + plot_h * (high - value) / span
        return x, y

    parts = [
        f'<text x="{x0}" y="25" class="label">Free-running evolution from one exact checkpoint</text>',
    ]
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        value = high - span * fraction
        y = y0 + plot_h * fraction
        parts.append(f'<line x1="{x0}" y1="{y:.2f}" x2="{x0 + plot_w}" y2="{y:.2f}" class="grid"/>')
        parts.append(f'<text x="{x0 - 10}" y="{y + 4:.2f}" text-anchor="end" class="small">{value:,.0f}</text>')

    for _, key, colour in series:
        points = [point(index, int(row[key])) for index, row in enumerate(rows)]
        encoded = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        parts.append(
            f'<polyline points="{encoded}" fill="none" stroke="{colour}" '
            f'stroke-width="{3 if key == "exact_value" else 2.4}" stroke-linejoin="round"/>'
        )

    first_step, last_step = int(rows[0]["step"]), int(rows[-1]["step"])
    parts.extend(
        [
            f'<text x="{x0}" y="{y0 + plot_h + 24}" class="small">n = {first_step:,}</text>',
            f'<text x="{x0 + plot_w}" y="{y0 + plot_h + 24}" text-anchor="end" class="small">n = {last_step:,}</text>',
        ]
    )
    legend_x = x0
    for label, _, colour in series:
        parts.append(f'<line x1="{legend_x}" y1="{height - 24}" x2="{legend_x + 22}" y2="{height - 24}" stroke="{colour}" stroke-width="4"/>')
        parts.append(f'<text x="{legend_x + 30}" y="{height - 19}" class="small">{label}</text>')
        legend_x += 220
    return _svg("".join(parts), width, height, "Deterministic and model Recaman evolution")


def auc_ladder_svg(measurements: dict, width: int = 1000, height: int = 270) -> str:
    benchmark = measurements["signed_tower"]["benchmark"]
    values = [
        ("coin baseline", 0.5, PALETTE["muted"]),
        ("arithmetic only", benchmark["auc_without_prev_is_down"], PALETTE["cyan"]),
        ("hole gap dynamics D", measurements["value_side"]["dataset_d"]["mean_auc"], PALETTE["amber"]),
        ("+ previous sign", benchmark["auc_full_predecision"], PALETTE["violet"]),
        ("visited-set oracle", benchmark["auc_oracle_visited_set"], PALETTE["rose"]),
    ]
    x0, y0, plot_w = 220, 46, width - 270
    parts = ['<text x="32" y="25" class="label">What the repo can infer, under different information budgets</text>']
    for index, (label, value, colour) in enumerate(values):
        y = y0 + index * 41
        parts.append(f'<text x="{x0 - 14}" y="{y + 15}" text-anchor="end" class="small">{label}</text>')
        parts.append(f'<rect x="{x0}" y="{y}" width="{plot_w}" height="20" rx="10" fill="{PALETTE["grid"]}" opacity="0.55"/>')
        parts.append(f'<rect x="{x0}" y="{y}" width="{plot_w * value:.2f}" height="20" rx="10" fill="{colour}"/>')
        parts.append(f'<text x="{x0 + plot_w + 10}" y="{y + 15}" class="value">{value:.4f}</text>')
    return _svg("".join(parts), width, height, "Inference benchmark AUC ladder")
