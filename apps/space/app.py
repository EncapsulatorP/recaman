"""Gradio Space for the Recaman next-obstruction-bit baseline.

Two things are on offer here. The first tab is the one-step predictor and the
measurement behind it. The second lets you generate the real sequence yourself
and watch the same statistic move with the horizon, which is the honest way to
see why the headline number is a snapshot and not a theorem.
"""

from __future__ import annotations

from functools import lru_cache

import gradio as gr

from figures import (
    arc_diagram,
    bit_ribbon,
    poster,
    slip_decay_chart,
    svg_document,
)
from predictor import (
    MEAN_RUN_LENGTH,
    N_EMPIRICAL,
    PHASE_SLIP_RATE,
    TRANSITION,
    horizon_points,
    load_measurements,
    predict_next_obstruction,
)
from recaman import MAX_INTERACTIVE_STEPS, MOVE_CHOICES, generate


MEASUREMENTS = load_measurements()
DEFAULT_CHOICE = next(iter(MOVE_CHOICES))
REPO_URL = "https://github.com/kugguk2022/recaman_obstructions"

# The raw-bit endpoint serialises every term, so it gets a much tighter cap
# than the plotting path, which only ever returns summary statistics.
MAX_RAW_STEPS = 5_000


@lru_cache(maxsize=16)
def _run(steps: int):
    """Cache prefixes so dragging a slider does not regenerate from scratch."""
    return generate(steps)


# The poster is deterministic, so build it once at import rather than per view.
POSTER_SVG = poster(MEASUREMENTS, _run(60_000))


def predict(previous_move: str) -> tuple[str, dict]:
    """Render one prediction for the UI and return the same payload for the API."""
    prediction = predict_next_obstruction(MOVE_CHOICES[previous_move])
    card = (
        f"### Next move: **{prediction.predicted_move}**  ·  `b = {prediction.predicted_bit}`\n\n"
        f"# {prediction.confidence:.4%}\n"
        f"empirical confidence, measured over N = {prediction.empirical_horizon:,} steps\n\n"
        f"The complementary outcome is a *phase slip* — the bit repeating itself — "
        f"seen at a rate of **{prediction.slip_probability:.4%}** after this move, "
        f"about once every **{prediction.expected_steps_to_next_slip:,.0f}** steps.\n\n"
        "> This predicts the next obstruction bit only. It says nothing about *where* "
        "the rare slips land, and nothing about which integers stay permanently missing "
        "from the sequence."
    )
    return card, prediction.to_dict()


def simulate(steps: int, arcs: int) -> tuple[str, str, str]:
    """Generate a real prefix and report what it says at that horizon."""
    steps = max(24, min(int(steps), MAX_INTERACTIVE_STEPS))
    arcs = max(6, min(int(arcs), min(steps, 120)))
    run = _run(steps)

    arc_svg = svg_document(
        arc_diagram(run, 1000, 300, arcs=arcs),
        1000,
        300,
        f"First {arcs} steps of the Recaman sequence",
    )

    first_step, window = run.window_around_slip(25)
    ribbon_svg = svg_document(
        bit_ribbon(window, 1000, 150, first_step),
        1000,
        150,
        "Obstruction bits around a phase slip",
    )

    live = run.transition_matrix()
    report = (
        f"| measured on | N | P(next = 1 \\| prev = 0) | same-bit slip rate |\n"
        f"| --- | ---: | ---: | ---: |\n"
        f"| your prefix | {run.steps:,} | {live['p01']:.4%} | {run.slip_rate():.4%} |\n"
        f"| saved run | {N_EMPIRICAL:,} | {TRANSITION['p01']:.4%} | {PHASE_SLIP_RATE:.4%} |\n\n"
        f"Your prefix contains **{len(run.slip_steps()):,} phase slips**. "
        f"The slip rate at N = {run.steps:,} is "
        f"**{run.slip_rate() / PHASE_SLIP_RATE:.1f}×** the rate at N = {N_EMPIRICAL:,} — "
        "the defects thin out as the horizon grows, which is exactly why the headline "
        "number is reported as a measurement at a stated N and not as a limit."
    )
    return arc_svg, ribbon_svg, report


def simulate_bits(steps: int) -> dict:
    """Return the raw terms, bits and slip positions for a short prefix."""
    steps = max(1, min(int(steps), MAX_RAW_STEPS))
    run = _run(steps)
    return {
        "steps": run.steps,
        "terms": list(run.terms),
        "bits": list(run.bits),
        "slip_steps": list(run.slip_steps()),
        "slip_rate": run.slip_rate(),
        "blocked_fraction": run.blocked_fraction,
        "transition_matrix": run.transition_matrix(),
    }


DECAY_SVG = svg_document(
    slip_decay_chart(horizon_points(), 900, 320),
    900,
    320,
    "Measured phase-slip rate against the measurement horizon",
)

METHOD = f"""
### What is being predicted

The Recaman sequence starts at `a(0) = 0` and, at each step `n`, tries the
backward move `a(n-1) - n`. It takes it when the result is positive and has not
been visited before; otherwise it is *obstructed* and moves forward to
`a(n-1) + n`. The **obstruction bit** records which happened:

* `b(n) = 0` — the backward move was free (DOWN / FREE)
* `b(n) = 1` — the backward move was blocked (UP / BLOCKED)

### What was measured

Over N = {N_EMPIRICAL:,} steps the stream is near-perfect alternation with rare
same-bit defects. Conditioning on the previous bit alone reaches
{MEASUREMENTS['accuracy']['previous_bit_only']:.3%} accuracy against a
{MEASUREMENTS['accuracy']['majority_baseline']:.0%} baseline. Slips occur at a rate of
{PHASE_SLIP_RATE:.4%}, giving a mean run of {MEAN_RUN_LENGTH:,.0f} clean
alternations between defects.

The classic `Θ₃` wheel is **{MEASUREMENTS['theta3_wheel']['verdict'].lower()}** on the same
run: its two states differ by only {MEASUREMENTS['theta3_wheel']['abs_delta_q']:.1e}, so it
carries no usable signal about the real obstruction bit.

### What this is not

* Not a proof. Every number here is an empirical measurement at a stated
  horizon, and the slip rate is still falling as that horizon grows.
* Not a predictor of *where* slips occur. Locating the defects is the open part
  of the problem.
* Not a statement about which integers are permanently missing from the
  sequence. That is a different (value-side) question in the repository.

### Provenance

Every number displayed is read from `measurements.json`, which
`scripts/build_space_measurements.py` derives from
`outputs/recaman_wheel_results.json` in the research repository — nothing here
is typed in by hand. Source, methods and the full result set:
[{REPO_URL}]({REPO_URL}).
"""


with gr.Blocks(
    title="Recaman Next-Move Predictor",
    theme=gr.themes.Soft(),
    analytics_enabled=False,
) as demo:
    gr.HTML(POSTER_SVG)

    with gr.Tabs():
        with gr.Tab("Predict"):
            with gr.Row():
                with gr.Column(scale=2):
                    previous_move = gr.Radio(
                        choices=list(MOVE_CHOICES),
                        value=DEFAULT_CHOICE,
                        label="Previous move  b(n−1)",
                        info="The state the predictor conditions on.",
                    )
                    predict_button = gr.Button("Predict next move", variant="primary")
                    payload = gr.JSON(label="API payload")
                with gr.Column(scale=3):
                    card = gr.Markdown()

            predict_button.click(
                fn=predict,
                inputs=previous_move,
                outputs=[card, payload],
                api_name="predict_next_obstruction",
            )
            previous_move.change(fn=predict, inputs=previous_move, outputs=[card, payload])

        with gr.Tab("Explore the real sequence"):
            gr.Markdown(
                "Generate the sequence for yourself. The statistic that matters — how "
                "often a bit repeats the one before it — is recomputed from your own "
                "prefix, so you can watch it approach the saved figure."
            )
            with gr.Row():
                steps = gr.Slider(
                    minimum=100,
                    maximum=MAX_INTERACTIVE_STEPS,
                    value=20_000,
                    step=100,
                    label="Steps to generate  (N)",
                )
                arcs = gr.Slider(
                    minimum=6,
                    maximum=120,
                    value=32,
                    step=1,
                    label="Arcs to draw",
                    info="Only affects the picture, not the statistics.",
                )
            arc_view = gr.HTML(label="Arc diagram")
            ribbon_view = gr.HTML(label="Bit stream around the most isolated slip")
            report = gr.Markdown()

            simulate_inputs = [steps, arcs]
            simulate_outputs = [arc_view, ribbon_view, report]
            steps.release(fn=simulate, inputs=simulate_inputs, outputs=simulate_outputs)
            arcs.release(fn=simulate, inputs=simulate_inputs, outputs=simulate_outputs)

            with gr.Accordion("Raw terms and bits", open=False):
                gr.Markdown(
                    "The same generator as a plain endpoint: terms, obstruction bits "
                    f"and slip positions, up to {MAX_RAW_STEPS:,} steps."
                )
                with gr.Row():
                    raw_steps = gr.Number(
                        value=64,
                        minimum=1,
                        maximum=MAX_RAW_STEPS,
                        precision=0,
                        label="Steps",
                    )
                    raw_button = gr.Button("Generate")
                raw_output = gr.JSON(label="Terms, bits and statistics")
                raw_button.click(
                    fn=simulate_bits,
                    inputs=raw_steps,
                    outputs=raw_output,
                    api_name="simulate_obstruction_bits",
                )

        with gr.Tab("Method and limits"):
            gr.Markdown(METHOD)
            gr.Markdown("#### Measured phase-slip rate against the horizon")
            gr.HTML(DECAY_SVG)

    demo.load(fn=predict, inputs=previous_move, outputs=[card, payload])
    demo.load(fn=simulate, inputs=simulate_inputs, outputs=simulate_outputs)


if __name__ == "__main__":
    demo.queue().launch()
