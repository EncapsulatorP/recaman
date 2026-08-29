"""Presentation helpers for the blind next-move replay."""

from __future__ import annotations

from html import escape

import pandas as pd

SERIES_COLOURS = {
    "exact bit": "#ffffff",
    "Historical inference champion": "#8da6bf",
    "Phase-slip hunter": "#43ff9e",
    "Tower scout": "#ff3df0",
    "Tower-augmented challenger": "#ffb457",
    "Forward ensemble": "#22e0ff",
}


def replay_probability_frame(payload: dict) -> pd.DataFrame:
    """Long-form probability history for Gradio's interactive line plot."""
    rows: list[dict] = []
    for event in payload["history"]:
        rows.append(
            {
                "step": event["step"],
                "P(blocked)": float(event["truth"]),
                "agent": "exact bit",
                "phase slip": "yes" if event["phase_slip"] else "no",
            }
        )
        for name, probability in event["probabilities"].items():
            rows.append(
                {
                    "step": event["step"],
                    "P(blocked)": probability,
                    "agent": name,
                    "phase slip": "yes" if event["phase_slip"] else "no",
                }
            )
    return pd.DataFrame.from_records(rows)


def replay_scoreboard_frame(payload: dict) -> pd.DataFrame:
    """Compact live ranking with inference and rare-event metrics."""
    ordered = sorted(payload["scoreboard"], key=lambda row: row["bits_per_step"])
    return pd.DataFrame.from_records(
        {
            "agent": row["name"],
            "bits/step ↓": round(row["bits_per_step"], 5),
            "phase-slip AP ↑": round(row["phase_slip_ap"], 5),
            "AUC ↑": round(row["auc"], 5),
            "accuracy": round(row["accuracy"], 5),
            "precision": round(row["precision"], 5),
            "recall": round(row["recall"], 5),
        }
        for row in ordered
    )


def replay_current_html(payload: dict) -> str:
    """Show the just-revealed truth beside every frozen prediction."""
    current = payload["current"]
    actual = current["actual_bit"]
    move = "UP / BLOCKED" if actual else "DOWN / FREE"
    slip = '<span class="arena-slip">PHASE SLIP</span>' if current["phase_slip"] else ""
    cards = []
    for prediction in current["predictions"]:
        state = "correct" if prediction["correct"] else "wrong"
        cards.append(
            f'''<div class="arena-agent {state}">
<span>{escape(prediction['name'])}</span>
<strong>{prediction['probability_blocked']:.1%}</strong>
<small>P(blocked) · predicted b={prediction['predicted_bit']}</small>
</div>'''
        )
    return f'''<section class="arena-reveal" aria-live="polite">
<div class="arena-truth"><span>REVEALED n={current['step']:,}</span><strong>b={actual} · {move}</strong><small>candidate {current['candidate']:,}</small>{slip}</div>
<div class="arena-agents">{''.join(cards)}</div>
<div class="arena-ledger"><b>{escape(payload['champion_so_far'])}</b> leads after {payload['revealed']:,} blind predictions at <b>{payload['champion_bits_per_step']:.4f} bits/step</b>. {payload['hidden_remaining']:,} labels remain hidden.</div>
</section>'''


def weekly_validation_frame(payload: dict) -> pd.DataFrame:
    """Expose the challenger configuration search without exposing the final block."""
    rows = payload["evaluation"]["validation_search"]
    return pd.DataFrame.from_records(
        {
            "configuration": f"base {row['base']} · mod {row['modulus']}",
            "validation bits/step": row["bits_per_step"],
            "phase-slip AP": row["phase_slip_ap"],
            "family": "Tower challenger",
        }
        for row in rows
    )


def weekly_league_html(payload: dict) -> str:
    """Render the saved, reproducible champion–challenger decision."""
    evaluation = payload["evaluation"]
    champion = evaluation["champion"]
    challenger = evaluation["challenger"]
    decision_class = "promote" if evaluation["promoted"] else "hold"
    margin = evaluation["margin_bits_per_step"]
    return f'''<section class="league-board">
<div class="league-season"><span>SEASON {payload['season']} · EXACT HORIZON n={evaluation['steps']:,}</span><strong class="{decision_class}">{evaluation['decision']}</strong><small>{escape(evaluation['protocol'])}</small></div>
<div class="league-match">
  <div><span>CHAMPION</span><h3>{escape(champion['name'])}</h3><strong>{champion['bits_per_step']:.5f} bits/step</strong><small>phase-slip AP {champion['phase_slip_ap']:.4f}</small></div>
  <b>VS</b>
  <div><span>CHALLENGER · base {challenger['base']} / mod {challenger['modulus']}</span><h3>{escape(challenger['name'])}</h3><strong>{challenger['bits_per_step']:.5f} bits/step</strong><small>phase-slip AP {challenger['phase_slip_ap']:.4f}</small></div>
</div>
<div class="league-verdict">Tower changed sealed-test code length by <b>{margin:+.6f} bits/step</b>. Promotion requires +{evaluation['promotion_margin_required']:.4f} saved bits/step and no material phase-slip AP loss.</div>
</section>'''
