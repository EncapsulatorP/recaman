"""Recamán Obstruction & Tower Lab — a source-backed Gradio Space."""

from __future__ import annotations

from functools import lru_cache

import gradio as gr
from arena_figures import arena_scoreboard
from figures import arc_diagram, bit_ribbon, svg_document
from model_arena import evaluate_arena, evidence_registry
from predictor import (
    N_EMPIRICAL,
    PHASE_SLIP_RATE,
    TRANSITION,
    load_measurements,
    predict_next_obstruction,
)
from recaman import MAX_INTERACTIVE_STEPS, MOVE_CHOICES, generate
from tower_figures import (
    auc_ladder_svg,
    evolution_race_svg,
    power_probe_svg,
    rank_tower_svg,
    signed_tower_svg,
)
from tower_lab import (
    CATALOGUE,
    evolution_rollout,
    hole_status,
    modular_power_probe,
    rank_tower,
    signed_snapshot,
    signed_window,
)
from tower_lab import (
    MEASUREMENTS as TOWER_MEASUREMENTS,
)

MEASUREMENTS = load_measurements()
DEFAULT_CHOICE = next(iter(MOVE_CHOICES))
REPO_URL = "https://github.com/EncapsulatorP/recaman"
SPACE_URL = "https://huggingface.co/spaces/kugguk/recaman-next-move"
MAX_RAW_STEPS = 5_000


@lru_cache(maxsize=16)
def _run(steps: int):
    return generate(steps)


def predict(previous_move: str) -> tuple[str, dict]:
    """Preserve the measured previous-bit baseline and its public API."""
    prediction = predict_next_obstruction(MOVE_CHOICES[previous_move])
    card = (
        f"### Next move: **{prediction.predicted_move}** · b = {prediction.predicted_bit}\n\n"
        f"# {prediction.confidence:.4%}\n"
        f"empirical confidence over N = {prediction.empirical_horizon:,} steps\n\n"
        f"The complementary same-bit phase slip was measured at "
        f"**{prediction.slip_probability:.4%}** after this move.\n\n"
        "> This is the narrow process-side baseline. It does not identify long-lasting "
        "missing values and it does not locate the rare phase slips."
    )
    return card, prediction.to_dict()


def simulate(steps: int, arcs: int) -> tuple[str, str, str]:
    """Generate a real prefix and expose the process-side measurements."""
    steps = max(24, min(int(steps), MAX_INTERACTIVE_STEPS))
    arcs = max(6, min(int(arcs), min(steps, 120)))
    run = _run(steps)
    arc_svg = svg_document(
        arc_diagram(run, 1000, 300, arcs=arcs),
        1000,
        300,
        f"First {arcs} steps of the Recamán sequence",
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
        f"| measured on | N | P(next = 1 given prev = 0) | same-bit slip rate |\n"
        f"| --- | ---: | ---: | ---: |\n"
        f"| your prefix | {run.steps:,} | {live['p01']:.4%} | {run.slip_rate():.4%} |\n"
        f"| saved run | {N_EMPIRICAL:,} | {TRANSITION['p01']:.4%} | {PHASE_SLIP_RATE:.4%} |\n\n"
        f"Your prefix contains **{len(run.slip_steps()):,} phase slips**. Every value is "
        "generated live from the exact visited-set rule."
    )
    return arc_svg, ribbon_svg, report


def simulate_bits(steps: int) -> dict:
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


def lookup_hole(value: int) -> tuple[str, dict]:
    payload = hole_status(value)
    number = payload["value"]
    if payload["status"] == "catalogued":
        report = (
            f"### Catalogued long-lasting obstruction\n\n"
            f"**{number:,}** lies in the catalogue event "
            f"{payload['event_start']:,}–{payload['event_end']:,}, a run of "
            f"**{payload['event_length']:,}** consecutive values.\n\n"
            "> This is exact membership in the repository’s supplied catalogue—not a new "
            "proof about the infinite sequence."
        )
    elif payload["status"] == "not_catalogued":
        report = (
            f"### Not listed in the covered catalogue\n\n"
            f"**{number:,}** is inside the catalogue span but is not one of its listed "
            f"obstructions. The nearest event is "
            f"{payload['nearest_event_start']:,}–{payload['nearest_event_end']:,}, "
            f"**{payload['distance_to_nearest']:,}** away."
        )
    else:
        report = (
            f"### Outside the catalogue’s scope\n\n"
            f"**{number:,}** is outside **{CATALOGUE.span_start:,}–{CATALOGUE.span_end:,}**. "
            "The Space makes no membership claim there."
        )
    return report, payload


def inspect_signed_tower(step: int) -> tuple[str, str, dict]:
    snapshot, run = signed_snapshot(step)
    figure = signed_tower_svg(signed_window(run, snapshot.step))
    slip = " **This step is a same-sign phase slip.**" if snapshot.phase_slip else ""
    report = f"""
### Step {snapshot.step:,}: {snapshot.move}{snapshot.step:,} → a({snapshot.step:,}) = {snapshot.value:,}

The down candidate was **{snapshot.candidate:,}**; the rule chose {snapshot.move} because
{snapshot.reason}.{slip}

| exact layer | value |
| --- | ---: |
| triangular envelope Tₙ | {snapshot.triangular_envelope:,} |
| down-step index sum ΣDₙ | {snapshot.down_sum:,} |
| reconstruction Tₙ − 2ΣDₙ | {snapshot.identity_value:,} |
| generated aₙ | {snapshot.value:,} |

**Identity verified:** {snapshot.identity_verified}. This is the rigorous sign-flipping
tower: each step contributes −n when the backward move is free and +n when it is blocked.
"""
    return figure, report, snapshot.to_dict()


def inspect_rank_tower(level: int) -> tuple[str, str, dict]:
    payload = rank_tower(level)
    figure = rank_tower_svg(TOWER_MEASUREMENTS, payload["level"])
    validity = (
        "This level is inside the artifact-free range."
        if payload["artifact_free"]
        else "This level is context only: short subsequences are zero-padded here."
    )
    report = f"""
### Level j = {payload['level']} · stride 2^{payload['level']} = {payload['stride']:,}

| stream | GF(2) rank |
| --- | ---: |
| Recamán obstruction bits | {payload['real_rank']} |
| matched random null | {payload['random_rank']} |
| pure alternation | {payload['alternating_rank']} |

The Recamán stream is **{payload['rank_deficit_from_random']} dimensions below the random
null** at this level. {validity} Low rank measures dependency in this representation; it
does not prove a separate invariant.
"""
    return figure, report, payload


def inspect_power_probe(base: int, modulus: int, layers: int) -> tuple[str, str, dict]:
    payload = modular_power_probe(base, modulus, layers)
    figure = power_probe_svg(payload)
    report = f"""
### Sign-flipping modular power probe

{payload['definition']}

| shadow compared with real obstruction bits | agreement |
| --- | ---: |
| alternating signed base | {payload['flipped_agreement']:.3%} |
| fixed positive-base control | {payload['fixed_agreement']:.3%} |
| majority baseline | {payload['majority_baseline']:.3%} |

This is an exact bounded modular experiment, **not** a fitted model and not a literal claim
about gigantic tetration values. {payload['selection_warning']}
"""
    compact = {key: value for key, value in payload.items() if not isinstance(value, list)}
    compact["last_flipped_residues"] = payload["flipped_residues"][-16:]
    compact["last_fixed_residues"] = payload["fixed_residues"][-16:]
    return figure, report, compact


def inspect_evolution(seed_step: int, horizon: int, base: int, modulus: int) -> tuple[str, str, dict]:
    payload = evolution_rollout(seed_step, horizon, base, modulus)
    figure = evolution_race_svg(payload)
    frontier = payload["chaffin_frontier"]

    def divergence(value: int | None) -> str:
        return f"n = {value:,}" if value is not None else "none in window"

    report = f"""
### Deterministic truth vs autonomous model evolution

Every lane starts at the exact local checkpoint **a({payload['seed_step']:,}) =
{payload['seed_value']:,}**. After that, no model sees the true preceding bit.

| free-running lane | bit agreement | first wrong sign | final value | final error |
| --- | ---: | ---: | ---: | ---: |
| previous-sign alternation | {payload['alternating_bit_agreement']:.2%} | {divergence(payload['alternating_first_divergence'])} | {payload['alternating_final_value']:,} | {payload['alternating_final_error']:+,} |
| sign-flipping power shadow | {payload['power_bit_agreement']:.2%} | {divergence(payload['power_first_divergence'])} | {payload['power_final_value']:,} | {payload['power_final_error']:+,} |
| exact visited-set recurrence | 100.00% | - | {payload['exact_final_value']:,} | 0 |

The alternation lane attempted **{payload['alternating_illegal_downs']}** backward moves
that its inherited/own history would forbid; the power lane attempted
**{payload['power_illegal_downs']}**. Those violations show exactly where a sign model
stops being a valid Recaman generator.

#### Chaffin frontier

The supplied catalogue's last hole is **{frontier['last_catalogued_hole']:,}**, from
Chaffin's complete hole list below 2^32 after a computation of {frontier['computed_horizon']}.
It is a value-side result, **not a sequence checkpoint**, so the deterministic lane cannot
honestly start there without Chaffin's full visited-range state. The frontier is the place
to launch unverified model hypotheses, while the replay above is where those models can be
scored against deterministic truth. [Chaffin source]({frontier['source_url']}).
"""
    compact = {key: value for key, value in payload.items() if key != "rows"}
    compact["last_24_layers"] = payload["rows"][-24:]
    return figure, report, compact


def inspect_model_arena(steps: int, base: int, modulus: int) -> tuple[str, str, dict]:
    payload = evaluate_arena(steps, base, modulus)
    figure = arena_scoreboard(payload)
    ranked = sorted(
        (agent for agent in payload["agents"] if agent["status"] == "forward-held-out"),
        key=lambda agent: agent["bits_per_step"],
    )
    rows = "\n".join(
        f"| {agent['name']} | {agent['auc']:.4f} | {agent['accuracy']:.2%} | "
        f"{agent['bits_per_step']:.4f} | {agent['brier']:.4f} |"
        for agent in ranked
    )
    tower = next(agent for agent in ranked if agent["name"] == "Tower scout")
    report = f"""
## Forward-held-out Agent Arena

Fit: **{payload['train_steps']:,}** chronological steps. Untouched test:
**{payload['test_steps']:,}** later steps. Target: `{payload['target']}`.

| inferred agent | AUC | accuracy | bits/step ↓ | Brier ↓ |
| --- | ---: | ---: | ---: | ---: |
{rows}

**Champion by held-out compression:** {payload['champion']} at
**{payload['champion_bits_per_step']:.4f} bits/step**. Tower Scout receives
**{payload['tower_added_to_ensemble']:.2%}** of the train-derived ensemble weight and
scores **{tower['auc']:.4f} AUC** on the future block. It earns more influence only if
those measurements improve.

The Skeptic/prevalence control remains the 1-bit reference. {payload['leakage_boundary']}
No AUC from the separate value-side hole task is mixed with this next-bit target.
"""
    return figure, report, payload


BENCHMARK = TOWER_MEASUREMENTS["signed_tower"]["benchmark"]
VALUE_SIDE = TOWER_MEASUREMENTS["value_side"]
BRANCH = TOWER_MEASUREMENTS["branch_geometry"]
REGISTRY = evidence_registry(TOWER_MEASUREMENTS)
REGISTRY_ROWS = "\n".join(
    f"| {row['model']} | {row['target']} | {row['auc']:.4f} | {row['role']} |"
    for row in REGISTRY
)

HERO = f"""
<section class="lab-hero">
  <div class="lab-kicker">RECAMÁN · FORWARD VALIDATION · MODEL EVOLUTION</div>
  <h1>Next-Move Model Lab</h1>
  <p>Fit inferred agents on the past, freeze them, and score them on the future.
  Tower and modular features earn ensemble influence only by improving held-out
  AUC, code length, or calibration.</p>
  <div class="lab-metrics">
    <div><b>80 / 20</b><span>chronological split</span></div>
    <div><b>{BENCHMARK['auc_full_predecision']:.4f}</b><span>full process AUC</span></div>
    <div><b>{BENCHMARK['auc_without_prev_is_down']:.4f}</b><span>arithmetic-only AUC</span></div>
    <div><b>1.0000</b><span>oracle ceiling</span></div>
  </div>
</section>
"""

CSS = """
.gradio-container{max-width:1220px!important;margin:auto!important}
.lab-hero{padding:34px;border-radius:24px;background:linear-gradient(135deg,#17142f 0%,#2b225d 58%,#075968 100%);color:#fff;box-shadow:0 18px 48px rgba(23,20,47,.22);margin-bottom:18px}
.lab-kicker{font-size:.78rem;font-weight:800;letter-spacing:.14em;color:#b9f5ef}
.lab-hero h1{font-size:clamp(2.1rem,5vw,4.6rem);line-height:.96;margin:.35rem 0 .8rem;color:#fff}
.lab-hero p{max-width:800px;color:#e4e0ff;font-size:1.05rem;line-height:1.55}
.lab-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:24px}
.lab-metrics div{padding:14px 16px;border-radius:15px;background:rgba(255,255,255,.105);border:1px solid rgba(255,255,255,.13)}
.lab-metrics b{display:block;font-size:1.35rem;color:#fff}.lab-metrics span{font-size:.78rem;color:#c8c3ef}
@media(max-width:760px){.lab-metrics{grid-template-columns:repeat(2,1fr)}.lab-hero{padding:24px 20px}}
"""

OVERVIEW = f"""
## Model registry — targets never silently mixed

| model | target | saved AUC | arena role |
| --- | --- | ---: | --- |
{REGISTRY_ROWS}

The live Agent Arena below refits lightweight process agents on a chronological 80/20
split. The saved 0.7586 value-side model remains first-class evidence, but it cannot be
blended into a next-bit ensemble until both models share an aligned target.
"""

METHOD = f"""
## Interpretation boundary

- Evolution races are free-running from a local exact checkpoint; models consume their own outputs.
- The signed tower is exact: it is just the Recamán recurrence unrolled.
- The power-of-two rank tower is measured against random and pure-alternation controls.
- The modular sign-flip probe is exploratory. Changing its base or modulus after seeing
  the score creates selection bias.
- The visited-set collision flag is the exact oracle, but requires the complete history;
  local arithmetic without previous-sign information reaches AUC {BENCHMARK['auc_without_prev_is_down']:.4f}.
- Adding the previous sign raises measured AUC to {BENCHMARK['auc_full_predecision']:.4f},
  mainly because the bit stream almost alternates. This still does not locate phase slips.

Source code and saved measurements: [{REPO_URL}]({REPO_URL}).
"""


with gr.Blocks(
    title="Recamán Next-Move Model Lab",
    theme=gr.themes.Soft(primary_hue="violet", secondary_hue="cyan"),
    css=CSS,
    analytics_enabled=False,
) as demo:
    gr.HTML(HERO)

    with gr.Tabs():
        with gr.Tab("Agent Arena"):
            gr.Markdown(
                "Every inferred agent fits only the first 80% of the exact stream. The final "
                "20% stays untouched until scoring. Code length is the primary ranking: a model "
                "that cannot compress future bits does not get to hide behind an attractive chart."
            )
            with gr.Row():
                arena_steps = gr.Slider(10_000, 200_000, value=100_000, step=10_000, label="Exact history horizon")
                arena_base = gr.Slider(2, 97, value=3, step=1, label="Tower feature base")
                arena_modulus = gr.Slider(3, 997, value=210, step=1, label="Tower feature modulus")
            arena_button = gr.Button("Fit, freeze, and score agents", variant="primary")
            arena_figure = gr.HTML()
            arena_report = gr.Markdown()
            arena_payload = gr.JSON(label="Forward-validation audit payload")
            arena_button.click(
                inspect_model_arena,
                [arena_steps, arena_base, arena_modulus],
                [arena_figure, arena_report, arena_payload],
                api_name="model_arena",
            )

        with gr.Tab("Evidence map"):
            gr.Markdown(OVERVIEW)
            gr.HTML(auc_ladder_svg(TOWER_MEASUREMENTS))
            gr.Markdown(
                f"The branch-geometry distance is **{BRANCH['taken_vs_blocked_candidates']['chordal_distance']:.4f}** "
                f"against a shuffled-label null of **{BRANCH['null_shuffled_labels']['chordal_distance']:.4f}**. "
                "Seven of eight principal directions nearly coincide; one direction carries most of the separation."
            )

        with gr.Tab("Evolution race"):
            gr.Markdown(
                "Start every lane from the same exact checkpoint. The deterministic recurrence keeps "
                "its full visited set; the alternation and power models evolve from their own outputs, "
                "so one wrong sign can compound into a visibly different path."
            )
            with gr.Row():
                evolution_seed = gr.Slider(24, 199_488, value=20_000, step=1, label="Shared exact checkpoint n")
                evolution_horizon = gr.Slider(16, 512, value=192, step=8, label="Free-running layers")
            with gr.Row():
                evolution_base = gr.Slider(2, 97, value=3, step=1, label="Power-model base")
                evolution_modulus = gr.Slider(3, 997, value=210, step=1, label="Power-model modulus")
            evolution_button = gr.Button("Run the evolution race", variant="primary")
            evolution_figure = gr.HTML()
            evolution_report = gr.Markdown()
            evolution_payload = gr.JSON(label="Evolution summary")
            evolution_button.click(
                inspect_evolution,
                [evolution_seed, evolution_horizon, evolution_base, evolution_modulus],
                [evolution_figure, evolution_report, evolution_payload],
                api_name="evolution_race",
            )

        with gr.Tab("Signed ±n tower"):
            gr.Markdown(
                "Choose a step. The chart shows the latest signed contributions: −n for a free "
                "backward move and +n for a blocked move. Red dots mark failures of alternation."
            )
            tower_step = gr.Slider(24, 200_000, value=20_000, step=1, label="Tower height / Recamán step n")
            signed_figure = gr.HTML()
            signed_report = gr.Markdown()
            signed_payload = gr.JSON(label="Exact tower layers")
            tower_step.release(inspect_signed_tower, tower_step, [signed_figure, signed_report, signed_payload], api_name="signed_tower_snapshot")

        with gr.Tab("Sign-flipping power probe"):
            gr.Markdown(
                "A bounded modular power iterator tests the intuition directly. It is shown beside a "
                "fixed-sign control and the real obstruction bits, so a decorative pattern cannot masquerade as evidence."
            )
            with gr.Row():
                power_base = gr.Slider(2, 97, value=3, step=1, label="Base")
                power_modulus = gr.Slider(3, 997, value=210, step=1, label="Modulus")
                power_layers = gr.Slider(16, 512, value=128, step=8, label="Layers")
            power_button = gr.Button("Run controlled power probe", variant="primary")
            power_figure = gr.HTML()
            power_report = gr.Markdown()
            power_payload = gr.JSON(label="Probe summary")
            power_button.click(
                inspect_power_probe,
                [power_base, power_modulus, power_layers],
                [power_figure, power_report, power_payload],
                api_name="sign_flipping_power_probe",
            )

        with gr.Tab("Power-of-two rank tower"):
            gr.Markdown(
                "The repository’s measured tower: arithmetic subsequences b[r::2ʲ] become "
                "vectors over GF(2), and cumulative rank is compared with two nulls."
            )
            rank_level = gr.Slider(0, 12, value=7, step=1, label="Tower level j")
            rank_figure = gr.HTML()
            rank_report = gr.Markdown()
            rank_payload = gr.JSON(label="Rank payload")
            rank_level.release(inspect_rank_tower, rank_level, [rank_figure, rank_report, rank_payload], api_name="power_of_two_rank")

        with gr.Tab("Sequence & API"):
            with gr.Accordion("Measured next-bit baseline", open=True):
                with gr.Row():
                    previous_move = gr.Radio(list(MOVE_CHOICES), value=DEFAULT_CHOICE, label="Previous move")
                    predict_button = gr.Button("Predict next move", variant="primary")
                prediction_card = gr.Markdown()
                prediction_payload = gr.JSON(label="Prediction payload")
                predict_button.click(predict, previous_move, [prediction_card, prediction_payload], api_name="predict_next_obstruction")
                previous_move.change(predict, previous_move, [prediction_card, prediction_payload])

            with gr.Accordion("Generate the real sequence", open=False):
                with gr.Row():
                    steps = gr.Slider(100, MAX_INTERACTIVE_STEPS, value=20_000, step=100, label="Steps")
                    arcs = gr.Slider(6, 120, value=32, step=1, label="Arcs to draw")
                sequence_button = gr.Button("Generate prefix")
                arc_view = gr.HTML()
                ribbon_view = gr.HTML()
                sequence_report = gr.Markdown()
                sequence_button.click(simulate, [steps, arcs], [arc_view, ribbon_view, sequence_report])

            with gr.Accordion("Raw endpoint", open=False):
                raw_steps = gr.Number(value=64, minimum=1, maximum=MAX_RAW_STEPS, precision=0, label="Steps")
                raw_button = gr.Button("Return raw terms and bits")
                raw_payload = gr.JSON()
                raw_button.click(simulate_bits, raw_steps, raw_payload, api_name="simulate_obstruction_bits")

        with gr.Tab("Method & limits"):
            gr.Markdown(METHOD)

    gr.Markdown(f"[Research repository]({REPO_URL}) · [Hugging Face Space]({SPACE_URL})")

    demo.load(
        inspect_model_arena,
        [arena_steps, arena_base, arena_modulus],
        [arena_figure, arena_report, arena_payload],
    )
    demo.load(
        inspect_evolution,
        [evolution_seed, evolution_horizon, evolution_base, evolution_modulus],
        [evolution_figure, evolution_report, evolution_payload],
    )
    demo.load(inspect_signed_tower, tower_step, [signed_figure, signed_report, signed_payload])
    demo.load(inspect_power_probe, [power_base, power_modulus, power_layers], [power_figure, power_report, power_payload])
    demo.load(inspect_rank_tower, rank_level, [rank_figure, rank_report, rank_payload])
    demo.load(predict, previous_move, [prediction_card, prediction_payload])


if __name__ == "__main__":
    demo.queue().launch()
