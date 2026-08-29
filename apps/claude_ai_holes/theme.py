"""The kugguk2022 house look for this Space — Claude.ai version.

The palette is lifted from the "Repo Galaxy" artwork on the kugguk2022 GitHub
profile: neon cyan and amber over deep-space navy, with magenta and green as
supporting accents. `hole_figures.py` uses the same tokens, so the SVG figures
and the surrounding Gradio chrome are one design rather than two.

The theme object only sets hue ramps through the constructor, which is the
stable part of the Gradio theming API. Everything expressive lives in `CSS`,
where a wrong guess degrades to plain styling instead of failing the build.
"""

from __future__ import annotations

import gradio as gr


# Brand anchors, straight from the Repo Galaxy artwork.
SPACE = "#07101a"
SPACE_CARD = "#10263d"
CYAN = "#22e0ff"
AMBER = "#ffb457"
MAGENTA = "#ff3df0"
GREEN = "#43ff9e"
PAPER = "#f8f7f2"
INK = "#171510"

# Ramps stepped from the anchors in OKLCH, so hue and chroma stay on brand.
CYAN_RAMP = {
    "c50": "#6cffff", "c100": "#5fffff", "c200": "#43efff", "c300": "#00d4f3",
    "c400": "#00b9d5", "c500": "#009eb8", "c600": "#00859b", "c700": "#00697d",
    "c800": "#004e5f", "c900": "#003443", "c950": "#001d29",
}
AMBER_RAMP = {
    "c50": "#ffe488", "c100": "#ffda7e", "c200": "#ffc66a", "c300": "#f7ac4f",
    "c400": "#d8943d", "c500": "#bb7d2c", "c600": "#9e671a", "c700": "#7f4f01",
    "c800": "#613700", "c900": "#442200", "c950": "#290d00",
}
NAVY_RAMP = {
    "c50": "#e0f8ff", "c100": "#d6eeff", "c200": "#c2daf5", "c300": "#a9c0da",
    "c400": "#92a7bf", "c500": "#7b8ea4", "c600": "#65768a", "c700": "#4d5c6d",
    "c800": "#374452", "c900": "#222c38", "c950": "#0e1720",
}


def brand_theme() -> gr.themes.Base:
    return gr.themes.Soft(
        primary_hue=gr.themes.Color(name="kugguk-cyan", **CYAN_RAMP),
        secondary_hue=gr.themes.Color(name="kugguk-amber", **AMBER_RAMP),
        neutral_hue=gr.themes.Color(name="kugguk-navy", **NAVY_RAMP),
        font=("system-ui", "-apple-system", "Segoe UI", "sans-serif"),
        font_mono=("ui-monospace", "SFMono-Regular", "Menlo", "monospace"),
    )


CSS = f"""
.gradio-container {{
  --kg-space: {SPACE};
  --kg-card: {SPACE_CARD};
  --kg-cyan: {CYAN};
  --kg-amber: {AMBER};
  --kg-magenta: {MAGENTA};
  --kg-green: {GREEN};
  --kg-paper: {PAPER};
  --kg-ink: {INK};
  --kg-surface: var(--kg-paper);
  --kg-text: var(--kg-ink);
  --kg-edge: rgba(23, 21, 16, 0.12);
  background: var(--kg-surface);
  color: var(--kg-text);
  max-width: 1280px !important;
}}

@media (prefers-color-scheme: dark) {{
  .gradio-container {{
    --kg-surface: var(--kg-space);
    --kg-text: #e6f4ff;
    --kg-edge: rgba(34, 224, 255, 0.22);
    background:
      radial-gradient(1200px 520px at 12% -8%, rgba(34, 224, 255, 0.13), transparent 62%),
      radial-gradient(900px 460px at 88% 4%, rgba(255, 61, 240, 0.10), transparent 60%),
      var(--kg-space);
  }}
}}

/* The poster sits flush, like the galaxy banner on the profile. */
#kg-poster {{ margin: 0 0 12px; }}
#kg-poster svg {{ display: block; width: 100%; height: auto; }}

/* Headings pick up the brand, biggest first. */
.gradio-container h1,
.gradio-container h2 {{
  background: linear-gradient(92deg, var(--kg-cyan), var(--kg-magenta) 52%, var(--kg-amber));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  font-weight: 750;
  letter-spacing: -0.4px;
}}
.gradio-container h3 {{ color: var(--kg-text); font-weight: 650; }}
.gradio-container h4 {{
  color: var(--kg-cyan);
  text-transform: uppercase;
  letter-spacing: 1.4px;
  font-size: 0.78rem;
}}

/* Tabs read as a row of lit buttons rather than a filing cabinet. */
.gradio-container .tab-nav button {{
  border: none;
  border-bottom: 2px solid transparent;
  font-weight: 600;
}}
.gradio-container .tab-nav button.selected {{
  border-bottom-color: var(--kg-cyan);
  color: var(--kg-cyan);
}}

/* Tables: brand rules, tabular figures, no heavy chrome. */
.gradio-container table {{ border-collapse: collapse; font-variant-numeric: tabular-nums; }}
.gradio-container table th {{
  border-bottom: 2px solid var(--kg-cyan);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: 0.72rem;
  opacity: 0.85;
}}
.gradio-container table td {{ border-bottom: 1px solid var(--kg-edge); }}
.gradio-container table tr:last-child td {{ font-weight: 700; }}

/* One accent rule, reused wherever a section breaks. */
.gradio-container hr {{
  height: 2px;
  border: 0;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--kg-cyan), var(--kg-magenta) 50%, var(--kg-amber));
  opacity: 0.9;
}}

.gradio-container blockquote {{
  border-left: 3px solid var(--kg-amber);
  padding-left: 12px;
  opacity: 0.92;
}}

#kg-mark svg {{ display: block; width: 180px; height: auto; }}
#kg-footer {{ opacity: 0.75; font-size: 0.85rem; }}
"""
