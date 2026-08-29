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
from compression_lab import catalogue_benchmark, process_benchmark
from hole_figures import (
    VARIANT,
    arc_diagram,
    auc_chart,
    auc_rows,
    decade_chart,
    span_strip,
    svg_document,
)
from holes import load_catalogue
from interactive_figures import (
    CODEC_COLOURS,
    EVENT_COLOURS,
    benchmark_frame,
    catalogue_map_frame,
    phase_scope,
)
from sequence import walk
from theme import CSS, brand_theme

HERE = Path(__file__).resolve().parent
RESULTS = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
CATALOGUE = load_catalogue()
CATALOGUE_COMPRESSION = catalogue_benchmark(CATALOGUE, (HERE / "holes.txt").read_bytes())
REPO_URL = "https://github.com/EncapsulatorP/recaman"

WINDOW_WIDTHS = {
    "full span": None,
    "1,000,000,000": 1_000_000_000,
    "100,000,000": 100_000_000,
    "10,000,000": 10_000_000,
    "1,000,000": 1_000_000,
    "100,000": 100_000,
}

# Built once at import: the catalogue never changes at run time.
CATALOGUE_MAP = catalogue_map_frame(CATALOGUE)
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


def hero() -> str:
    """A compact control-room opening using only measured values."""
    best = CATALOGUE_COMPRESSION["best"]
    baseline = CATALOGUE_COMPRESSION["baseline_bytes"]
    return f'''<section class="kg-hero">
  <div class="kg-hero-copy">
    <div class="kg-kicker">LOSSLESS · REPRODUCIBLE · INTERACTIVE</div>
    <h1>Recamán Obstruction<br/>Compression Lab</h1>
    <p>Can structural regularity turn a 1.27-million-value obstruction catalogue
    into a tiny exact code—and can the same idea predict the next move?</p>
    <div class="kg-hero-actions"><a href="#compression-lab">Run the codec race ↓</a><span>Every winner must decode exactly.</span></div>
  </div>
  <div class="kg-hero-meter" aria-label="Catalogue compression summary">
    <div class="kg-meter-label"><span>expanded uint32</span><strong>{baseline / 1_000_000:.2f} MB</strong></div>
    <div class="kg-meter-track"><i style="width:100%"></i></div>
    <div class="kg-meter-label kg-meter-winner"><span>{best['name']}</span><strong>{best['bytes'] / 1_000:.2f} KB</strong></div>
    <div class="kg-meter-track kg-meter-small"><i style="width:{max(1.2, 100 / best['ratio']):.2f}%"></i></div>
    <div class="kg-meter-verdict"><strong>{best['ratio']:.0f}×</strong><span>smaller, byte-for-byte reversible</span></div>
  </div>
</section>
<div class="kg-statline">
  <div><strong>{CATALOGUE.integer_count:,}</strong><span>missing integers</span></div>
  <div><strong>{CATALOGUE.event_count:,}</strong><span>range events</span></div>
  <div><strong>{CATALOGUE_COMPRESSION['event_codec_bytes']:,} B</strong><span>auditable event code</span></div>
</div>'''


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
            f'<div class="kg-empty">No catalogued holes between <b>{low:,}</b> and '
            f'<b>{high:,}</b>. Every integer in this window is reached.</div>'
        )
    else:
        # Tiny shares round away to 0.0000%, so density is reported as "1 in N".
        rarity = round(1 / summary["coverage"]) if summary["coverage"] else 0
        relative = summary["coverage"] / CATALOGUE.coverage
        report = f'''<div class="kg-result-grid" aria-live="polite">
<div class="kg-result"><span>events in view</span><strong>{summary['events']:,}</strong><small>{summary['missing']:,} missing integers</small></div>
<div class="kg-result"><span>local rarity</span><strong>1 in {rarity:,}</strong><small>{relative:.2f}× catalogue density</small></div>
<div class="kg-result"><span>longest run</span><strong>{summary['longest_run']:,}</strong><small>consecutive missing values</small></div>
</div>'''
    return strip, report


def compression_experiment(steps: int) -> tuple[object, object, str, dict]:
    """Run both exact compression scoreboards and expose their audit payload."""
    process = process_benchmark(steps)
    catalogue_figure = benchmark_frame(CATALOGUE_COMPRESSION)
    process_figure = benchmark_frame(process)
    catalogue_best = CATALOGUE_COMPRESSION["best"]
    process_best = process["best"]
    model = process["held_out_model"]
    report = f'''<div class="kg-result-grid" aria-live="polite">
<div class="kg-result kg-result-accent"><span>catalogue winner</span><strong>{catalogue_best['ratio']:.1f}×</strong><small>{catalogue_best['name']} · {catalogue_best['bytes']:,} bytes</small></div>
<div class="kg-result"><span>process winner</span><strong>{process_best['ratio']:.1f}×</strong><small>{process_best['name']} · {process_best['bytes']:,} bytes</small></div>
<div class="kg-result"><span>held-out prediction</span><strong>{model['bits_per_step']:.4f}</strong><small>bits/step · {model['theoretical_saving']:.2%} below the 1-bit baseline</small></div>
</div>
<div class="kg-verification"><b>✓ Exact round trips</b><span>events</span><span>packed bits</span><span>phase slips</span><span>trajectory a({process['steps']:,}) = {process['final_term']:,}</span></div>'''
    payload = {
        "catalogue": CATALOGUE_COMPRESSION,
        "process": process,
    }
    return catalogue_figure, process_figure, report, payload


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
    title="Recamán Obstruction Compression Lab",
    theme=brand_theme(),
    css=CSS,
    analytics_enabled=False,
) as demo:
    gr.HTML(hero(), elem_id="kg-hero")

    with gr.Tabs(selected="compression"):
        with gr.Tab("Codec race", id="compression"):
            gr.HTML(
                '<div class="kg-section-head" id="compression-lab"><span>01 / CODEC RACE</span>'
                '<h2>Make structure pay rent.</h2><p>Hover every bar. Change the exact prefix. '
                'The byte count—not visual drama—chooses the winner.</p></div>'
            )
            with gr.Row(elem_classes="kg-control-row"):
                compression_steps = gr.Slider(
                    minimum=1_000,
                    maximum=200_000,
                    value=100_000,
                    step=1_000,
                    label="Exact Recamán prefix",
                    info="The final 20% is always held out before scoring.",
                    scale=4,
                )
                compression_button = gr.Button(
                    "Race codecs",
                    variant="primary",
                    scale=1,
                )
            compression_report = gr.HTML(elem_id="kg-live-results")
            with gr.Row(equal_height=True):
                catalogue_compression_view = gr.BarPlot(
                    x="codec",
                    y="log10(bytes)",
                    color="family",
                    color_map=CODEC_COLOURS,
                    title="Catalogue — log₁₀ serialized bytes",
                    x_title="codec",
                    y_title="log₁₀(bytes)",
                    tooltip="all",
                    x_label_angle=-24,
                    y_lim=[0, None],
                    height=390,
                    show_fullscreen_button=True,
                    show_export_button=True,
                    container=False,
                )
                process_compression_view = gr.BarPlot(
                    x="codec",
                    y="log10(bytes)",
                    color="family",
                    color_map=CODEC_COLOURS,
                    title="Obstruction stream — log₁₀ serialized bytes",
                    x_title="codec",
                    y_title="log₁₀(bytes)",
                    tooltip="all",
                    x_label_angle=-24,
                    y_lim=[0, None],
                    height=390,
                    show_fullscreen_button=True,
                    show_export_button=True,
                    container=False,
                )
            with gr.Accordion("Open exact audit payload", open=False):
                compression_payload = gr.JSON(label="Every byte count and round-trip check")
            compression_button.click(
                fn=compression_experiment,
                inputs=compression_steps,
                outputs=[
                    catalogue_compression_view,
                    process_compression_view,
                    compression_report,
                    compression_payload,
                ],
                api_name="compression_experiment",
            )
            compression_steps.release(
                fn=compression_experiment,
                inputs=compression_steps,
                outputs=[
                    catalogue_compression_view,
                    process_compression_view,
                    compression_report,
                    compression_payload,
                ],
                show_progress="minimal",
            )

        with gr.Tab("Obstruction map"):
            gr.HTML(
                '<div class="kg-section-head"><span>02 / EVENT MAP</span>'
                '<h2>All 3,102 events. No aggregation.</h2><p>Hover an event to inspect its '
                'exact range. Long runs rise out of the singleton floor.</p></div>'
            )
            gr.ScatterPlot(
                value=CATALOGUE_MAP,
                x="log10(start)",
                y="log10(run length)",
                color="kind",
                color_map=EVENT_COLOURS,
                title="Absolute-hole events across the verified catalogue",
                x_title="log₁₀(event start)",
                y_title="log₁₀(run length)",
                tooltip="all",
                height=460,
                show_fullscreen_button=True,
                show_export_button=True,
                container=False,
            )
            gr.HTML('<div class="kg-subhead"><b>Scrub the verified span</b><span>Move the viewport; density is recomputed exactly.</span></div>')
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
            window_report = gr.HTML()

            explore_inputs = [window_label, position]
            explore_outputs = [strip_view, window_report]
            window_label.change(fn=explore, inputs=explore_inputs, outputs=explore_outputs)
            position.release(fn=explore, inputs=explore_inputs, outputs=explore_outputs)

        with gr.Tab("Phase-slip scope"):
            gr.HTML(
                '<div class="kg-section-head"><span>03 / SIGNAL SCOPE</span>'
                '<h2>Scrub the process, catch the slips.</h2><p>The bit stream nearly '
                'alternates. Amber needles mark the rare moments it refuses to flip.</p></div>'
            )
            with gr.Row(elem_classes="kg-control-row"):
                phase_center = gr.Slider(
                    minimum=128,
                    maximum=200_000,
                    value=50_000,
                    step=128,
                    label="Scope centre n",
                    scale=4,
                )
                phase_width = gr.Radio(
                    choices=[64, 128, 256],
                    value=128,
                    label="Window",
                    scale=1,
                )
            phase_view = gr.HTML()
            phase_report = gr.HTML()
            phase_inputs = [phase_center, phase_width]
            phase_outputs = [phase_view, phase_report]
            phase_center.release(
                fn=phase_scope,
                inputs=phase_inputs,
                outputs=phase_outputs,
                show_progress="hidden",
            )
            phase_width.change(
                fn=phase_scope,
                inputs=phase_inputs,
                outputs=phase_outputs,
                show_progress="hidden",
            )

        with gr.Tab("Evidence"):
            gr.HTML(
                '<div class="kg-section-head"><span>04 / EVIDENCE</span>'
                '<h2>Exact facts and measured claims stay separate.</h2></div>'
            )
            gr.Markdown(overview())
            gr.HTML(DECADE_SVG)
            gr.Markdown(PREDICTABLE)
            gr.HTML(AUC_SVG)
            with gr.Accordion("Method, provenance, and limitations", open=False):
                gr.Markdown(METHOD)
            gr.HTML(ARC_SVG)

    gr.HTML(
        f'<footer id="kg-footer"><span><b>{VARIANT}</b> · Recamán obstruction research</span>'
        f'<span><a href="{REPO_URL}">source and reproducibility ↗</a></span></footer>'
    )

    demo.load(fn=explore, inputs=explore_inputs, outputs=explore_outputs)
    demo.load(fn=phase_scope, inputs=phase_inputs, outputs=phase_outputs)
    demo.load(
        fn=compression_experiment,
        inputs=compression_steps,
        outputs=[
            catalogue_compression_view,
            process_compression_view,
            compression_report,
            compression_payload,
        ],
    )


if __name__ == "__main__":
    demo.queue().launch()
