"""Gradio application for the Recaman next-obstruction-bit baseline."""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from predictor import predict_next_obstruction


HERE = Path(__file__).resolve().parent
INFOGRAPHIC = HERE / "assets" / "recaman_next_move_infographic.png"
MOVE_TO_BIT = {
    "DOWN / FREE (b = 0)": 0,
    "UP / BLOCKED (b = 1)": 1,
}


def render_prediction(last_move: str) -> str:
    """Render one transparent empirical prediction for the Space UI/API."""
    prediction = predict_next_obstruction(MOVE_TO_BIT[last_move])
    return (
        f"## Predict next: {prediction.predicted_move} "
        f"(`b = {prediction.predicted_bit}`)\n\n"
        f"**Empirical confidence:** {prediction.confidence:.4%}\n\n"
        f"Measured at **N = {prediction.empirical_horizon:,}**. "
        f"The observed same-bit phase-slip rate was "
        f"**{prediction.phase_slip_rate:.4%}**.\n\n"
        "> This predicts the next obstruction bit. It does not predict the "
        "location of rare phase slips or which values remain permanently missing."
    )


with gr.Blocks(title="Recaman Next-Move Predictor") as demo:
    gr.Markdown(
        "# Predicting Recamán's Next Move\n"
        "A transparent, one-step empirical baseline for the obstruction bit."
    )
    if INFOGRAPHIC.exists():
        gr.Image(value=str(INFOGRAPHIC), show_label=False, interactive=False)

    with gr.Row():
        last_move = gr.Radio(
            choices=list(MOVE_TO_BIT),
            value="DOWN / FREE (b = 0)",
            label="Previous move",
        )
        prediction = gr.Markdown()

    predict_button = gr.Button("Predict next move", variant="primary")
    predict_button.click(
        fn=render_prediction,
        inputs=last_move,
        outputs=prediction,
        api_name="predict_next_obstruction",
    )
    demo.load(fn=render_prediction, inputs=last_move, outputs=prediction)


if __name__ == "__main__":
    demo.launch()
