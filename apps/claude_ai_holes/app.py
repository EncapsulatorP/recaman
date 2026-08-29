"""Recaman absolute holes — Claude.ai version.

A structure explorer for the hole catalogue: the integers the Recaman sequence
never reaches. It reports the shape of that set — how many, where they sit, how
they clump, how far apart they are — and the measured scores of the models that
try to separate holes from matched controls.

It deliberately makes no claim about any individual integer. The honest
separation measured in this repository tops out at AUC 0.7586, which is real
signal and nowhere near a test, so no per-number verdict is offered here.

This is a different quantity from the Space in `apps/space/`, which predicts the
process-side obstruction bit b(n). The two must not be confused.
"""

from __future__ import annotations

import json
from pathlib import Path

import gradio as gr

from hole_figures import (
    VARIANT,
    arc_diagram,
    auc_chart,
    auc_rows,
    decade_chart,
    poster,
    span_strip,
    svg_document,
)
from holes import load_catalogue
from sequence import walk
from theme import CSS, brand_theme


HERE = Path(__file__).resolve().parent
RESULTS = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
MARK = (HERE / "assets" / "online-presence.svg").read_text(encoding="utf-8")
CATALOGUE = load_catalogue()
REPO_URL = "https://github.com/kugguk2022/recaman_obstructions"
PROFILE_URL = "https://github.com/kugguk2022"

WINDOW_WIDTHS = {
    "full span": None,
    "1,000,000,000": 1_000_000_000,
    "100,000,000": 100_000_000,
    "10,000,000": 10_000_000,
    "1,000,000": 1_000_000,
    "100,000": 100_000,
}

# Built once at import: the catalogue never changes at run time.
POSTER_SVG = poster(CATALOGUE, RESULTS, walk(24))
DECADE_SVG = svg_document(
    decade_chart(CATALOGUE.decade_profile(), 900, 300), 900, 300,
    "Missing integers per power-of-ten band",
)
AUC_SVG = svg_document(
    auc_chart(auc_rows(RESULTS), 900, 280, show_legend=True), 900, 280,
    "Measured separation of holes from matched controls",
)
ARC_SVG = svg_document(
    arc_diagram(*walk(40), 900, 260), 900, 260,
    "The first 40 steps of the Recaman sequence",
)


def _percentiles(values: list[int]) -> dict[str, int]:
    ordered = sorted(values)
    def at(fraction: float) -> int:
        return ordered[min(int(fraction * len(ordered)), len(ordered) - 1)]
    return {"min": ordered[0], "p25": at(0.25), "median": at(0.5), "p75": at(0.75), "max": ordered[-1]}


def overview() -> str:
    """The headline structure of the catalogue, all recomputed from holes.txt."""
    buckets = CATALOGUE.length_buckets()
    long_runs = buckets[-1]
    gaps = _percentiles(CATALOGUE.gaps())
    rows = "\n".join(
        f"| {label} | {events:,} | {integers:,} | {integers / CATALOGUE.integer_count:.1%} |"
        for label, events, integers in buckets
    )
    return f"""
## {CATALOGUE.integer_count:,} integers that Recamán never reaches

They are catalogued as **{CATALOGUE.event_count:,} events** —
{CATALOGUE.singleton_count:,} lone integers and {CATALOGUE.range_count:,} runs of
consecutive ones — spanning **{CATALOGUE.span_start:,} to {CATALOGUE.span_end:,}**.
That is **{CATALOGUE.coverage:.4%}** of the covered span, about one integer in
{round(1 / CATALOGUE.coverage):,}.

### They arrive in runs

| run length | events | missing integers | share |
| --- | ---: | ---: | ---: |
{rows}

**{long_runs[2] / CATALOGUE.integer_count:.1%}** of all missing integers sit inside just
**{long_runs[1]:,}** long runs. The longest is **{max(CATALOGUE.lengths()):,}** consecutive
integers, none of which the sequence ever visits.

### How far apart the events are

Measured start-to-start, the same way `scripts/321_210_version_c.py` measures it:

| min | 25th pct | median | 75th pct | max |
| ---: | ---: | ---: | ---: | ---: |
| {gaps['min']:,} | {gaps['p25']:,} | {gaps['median']:,} | {gaps['p75']:,} | {gaps['max']:,} |
"""


def explore(window_label: str, position: float) -> tuple[str, str]:
    """Show the missing integers inside one window of the covered span."""
    width = WINDOW_WIDTHS.get(window_label)
    if width is None or width >= CATALOGUE.span_width:
        low, high = CATALOGUE.span_start, CATALOGUE.span_end
    else:
        slack = CATALOGUE.span_width - width
        low = CATALOGUE.span_start + int(slack * max(0.0, min(position, 100.0)) / 100.0)
        high = low + width - 1

    summary = CATALOGUE.window_summary(low, high)
    strip = svg_document(
        span_strip(CATALOGUE, low, high, 1000, 190),
        1000,
        190,
        f"Missing integers between {low:,} and {high:,}",
    )

    if summary["events"] == 0:
        report = (
            f"No catalogued holes between **{low:,}** and **{high:,}**. "
            "Every integer in this window is reached by the sequence."
        )
    else:
        # Tiny shares round away to 0.0000%, so density is reported as "1 in N".
        rarity = round(1 / summary["coverage"]) if summary["coverage"] else 0
        report = (
            f"| window | integers | hole events | missing | density | longest run |\n"
            f"| --- | ---: | ---: | ---: | ---: | ---: |\n"
            f"| {low:,} – {high:,} | {summary['width']:,} | {summary['events']:,} "
            f"| {summary['missing']:,} | 1 in {rarity:,} "
            f"| {summary['longest_run']:,} |\n\n"
            f"The catalogue as a whole misses 1 integer in "
            f"{round(1 / CATALOGUE.coverage):,}, so this window is "
            f"**{summary['coverage'] / CATALOGUE.coverage:.2f}×** as dense."
        )
    return strip, report


PREDICTABLE = f"""
### What the models actually score

Two pipelines in the repository try to separate catalogued holes from matched
controls. Both are measured, and neither is a test for holeness.

* **Random-matrix search** (`{RESULTS['random_matrix']['script']}`) encodes each
  integer as {RESULTS['random_matrix']['feature_dim']} arithmetic and digit features and searches
  random linear projections. On {RESULTS['random_matrix']['positives']:,} positives against
  {RESULTS['random_matrix']['controls']:,} digit-length-matched controls it reaches
  **{RESULTS['random_matrix']['rf_cv_auc_mean']:.4f}** mean AUC under
  {RESULTS['random_matrix']['cv_folds']}-fold cross-validation; the best single linear code
  reaches **{RESULTS['random_matrix']['code_auc']:.4f}**.
* **Version C** (`{RESULTS['version_c']['script']}`) compresses the catalogue into events and
  models four tasks with {RESULTS['version_c']['cv_scheme']} cross-validation and a purge window of
  {RESULTS['version_c']['purge_contexts']}.

The honest headline is dataset **D**, gap dynamics between successive holes, at
**{RESULTS['version_c']['datasets']['D']['mean_auc']:.4f}**. Datasets A, B and C score above 0.99, but
they ask an easier question — separating a known event's anchor from a broad
control — and are kept as a ceiling, not as a result.

### What none of this claims

* No model here decides whether a given integer is a hole, and this Space
  deliberately offers no per-number verdict.
* The catalogue is silent outside {CATALOGUE.span_start:,}–{CATALOGUE.span_end:,}, and so is
  everything shown here.
* The structural facts above are exact counts over the catalogue. The AUCs are
  measurements from saved runs, not proofs about the sequence.
"""

METHOD = f"""
### The rule

    a(0) = 0
    a(n) = a(n-1) - n    if that value is positive and not yet visited
    a(n) = a(n-1) + n    otherwise

The sequence hops backward when it can and forward when it cannot. An integer
it never lands on — at any step, ever — is an **absolute hole**. This is OEIS
A005132; the arc picture below shows the first 40 steps, and nothing in that
range is a hole. The smallest hole in this catalogue is {CATALOGUE.span_start:,}.

### The catalogue

`holes.txt` is a verbatim copy of `obstructions.txt` in the research
repository: Benjamin Chaffin's certified list of values the sequence never
reaches. It is complete over the span it covers, so within
{CATALOGUE.span_start:,}–{CATALOGUE.span_end:,} an integer that is not listed *is*
reached by the sequence. Below and above that span the catalogue says nothing.

Every structural number in this Space is recomputed from that file at load
time — the event, singleton, range, span and gap totals all match the saved
`outputs/version_c_obstructions_results.json` run exactly. The model scores in
`results.json` are projected from the saved runs by
`scripts/sync_claude_ai_holes.py`; nothing here is a hand-typed constant.

### Not the same thing as the obstruction bit

The research repository also studies the *process-side* obstruction bit `b(n)`
— whether the backward move was blocked at step `n` — and has a separate Space
for it. That is a different label on a different object. A blocked step is not
a hole, and predicting `b(n)` says nothing about which integers go missing.

### Source

[{REPO_URL}]({REPO_URL})
"""


with gr.Blocks(
    title=f"Recaman Absolute Holes — {VARIANT}",
    theme=brand_theme(),
    css=CSS,
    analytics_enabled=False,
) as demo:
    gr.HTML(POSTER_SVG, elem_id="kg-poster")

    with gr.Tabs():
        with gr.Tab("The hole set"):
            gr.Markdown(overview())
            gr.Markdown("#### Missing integers per power-of-ten band")
            gr.HTML(DECADE_SVG)

        with gr.Tab("Explore the span"):
            gr.Markdown(
                "Pick a window and slide it across the covered span. Each column of "
                "the strip is one slice of the window; its height is the share of that "
                "slice the catalogue marks missing."
            )
            with gr.Row():
                window_label = gr.Dropdown(
                    choices=list(WINDOW_WIDTHS),
                    value="full span",
                    label="Window width",
                )
                position = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=0,
                    step=0.5,
                    label="Position across the span (%)",
                )
            strip_view = gr.HTML()
            window_report = gr.Markdown()

            explore_inputs = [window_label, position]
            explore_outputs = [strip_view, window_report]
            window_label.change(fn=explore, inputs=explore_inputs, outputs=explore_outputs)
            position.release(fn=explore, inputs=explore_inputs, outputs=explore_outputs)

        with gr.Tab("What is predictable"):
            gr.Markdown(PREDICTABLE)
            gr.HTML(AUC_SVG)

        with gr.Tab("Method and sources"):
            gr.Markdown(METHOD)
            gr.HTML(ARC_SVG)

    gr.Markdown(f"---\n\n**{VARIANT}** of the Recamán obstruction research.")
    gr.HTML(f'<div style="max-width:180px">{MARK}</div>')

    demo.load(fn=explore, inputs=explore_inputs, outputs=explore_outputs)


if __name__ == "__main__":
    demo.queue().launch()
