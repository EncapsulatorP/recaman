from __future__ import annotations

import os
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from huggingface_hub import hf_hub_download, list_repo_files


DATASET_ID = os.getenv(
    "RECAMAN_DATASET_ID",
    "kugguk/recaman-independent-check-bundle",
)
DATASET_REVISION = os.getenv("RECAMAN_DATASET_REVISION", "main")
HF_TOKEN = os.getenv("HF_TOKEN") or None

EXPECTED_PREFIXES = {
    "sequence": "viewer/sequence/",
    "holes": "viewer/holes/",
    "fits": "viewer/fits/",
    "summary": "viewer/summary/",
}

EXPORT_DIR = Path(tempfile.gettempdir()) / "recaman-space-exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

LOCK = threading.RLock()


@dataclass
class Store:
    sequence: pd.DataFrame = field(default_factory=pd.DataFrame)
    holes: pd.DataFrame = field(default_factory=pd.DataFrame)
    fits: pd.DataFrame = field(default_factory=pd.DataFrame)
    summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    files: list[str] = field(default_factory=list)
    status: str = "Not loaded yet."
    loaded_ok: bool = False


STORE = Store()


# ---------------------------------------------------------------------
# Data loading / validation
# ---------------------------------------------------------------------

def _repo_files() -> list[str]:
    return list(
        list_repo_files(
            repo_id=DATASET_ID,
            repo_type="dataset",
            revision=DATASET_REVISION,
            token=HF_TOKEN,
        )
    )


def _files_for_prefix(repo_files: list[str], prefix: str) -> list[str]:
    return sorted(
        name
        for name in repo_files
        if name.startswith(prefix) and name.lower().endswith(".parquet")
    )


def _download_parquets(files: Iterable[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for filename in files:
        local = hf_hub_download(
            repo_id=DATASET_ID,
            filename=filename,
            repo_type="dataset",
            revision=DATASET_REVISION,
            token=HF_TOKEN,
        )
        frames.append(pd.read_parquet(local))

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def _as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)

    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(0).ne(0)

    text = series.astype(str).str.strip().str.lower()
    return text.isin({"1", "true", "yes", "y", "t"})


def _ensure_sequence_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    required = {"n", "a_n_real"}
    missing = required - set(out.columns)
    if missing:
        raise ValueError(
            "viewer/sequence is missing required column(s): "
            + ", ".join(sorted(missing))
        )

    out["n"] = pd.to_numeric(out["n"], errors="coerce")
    out["a_n_real"] = pd.to_numeric(out["a_n_real"], errors="coerce")

    if "a_n_inferred" not in out.columns:
        out["a_n_inferred"] = pd.NA
    out["a_n_inferred"] = pd.to_numeric(out["a_n_inferred"], errors="coerce")

    if "delta" not in out.columns:
        out["delta"] = out["a_n_inferred"] - out["a_n_real"]
    out["delta"] = pd.to_numeric(out["delta"], errors="coerce")

    if "abs_delta" not in out.columns:
        out["abs_delta"] = out["delta"].abs()
    out["abs_delta"] = pd.to_numeric(out["abs_delta"], errors="coerce")

    if "is_exact_match" not in out.columns:
        out["is_exact_match"] = (
            out["a_n_inferred"].notna()
            & out["a_n_real"].notna()
            & out["a_n_inferred"].eq(out["a_n_real"])
        )
    else:
        out["is_exact_match"] = _as_bool(out["is_exact_match"])

    if "fit_score" not in out.columns:
        out["fit_score"] = pd.NA
    out["fit_score"] = pd.to_numeric(out["fit_score"], errors="coerce")

    if "fit_ge_075" not in out.columns:
        out["fit_ge_075"] = out["fit_score"].ge(0.75)
    else:
        out["fit_ge_075"] = _as_bool(out["fit_ge_075"])

    if "fit_ge_099" not in out.columns:
        out["fit_ge_099"] = out["fit_score"].ge(0.99)
    else:
        out["fit_ge_099"] = _as_bool(out["fit_ge_099"])

    if "run_id" not in out.columns:
        out["run_id"] = "default"

    out["run_id"] = out["run_id"].fillna("default").astype(str)

    return (
        out.dropna(subset=["n", "a_n_real"])
        .sort_values(["run_id", "n"])
        .reset_index(drop=True)
    )


def _ensure_holes_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    required = {"value", "is_real_chaffin_hole"}
    missing = required - set(out.columns)
    if missing:
        raise ValueError(
            "viewer/holes is missing required column(s): "
            + ", ".join(sorted(missing))
        )

    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out["is_real_chaffin_hole"] = _as_bool(out["is_real_chaffin_hole"])

    if "is_inferred_hole" not in out.columns:
        out["is_inferred_hole"] = False
    else:
        out["is_inferred_hole"] = _as_bool(out["is_inferred_hole"])

    if "fit_score" not in out.columns:
        for candidate in ("inferred_score", "score", "probability"):
            if candidate in out.columns:
                out["fit_score"] = out[candidate]
                break
        else:
            out["fit_score"] = pd.NA

    out["fit_score"] = pd.to_numeric(out["fit_score"], errors="coerce")

    if "inferred_score" not in out.columns:
        out["inferred_score"] = out["fit_score"]
    out["inferred_score"] = pd.to_numeric(out["inferred_score"], errors="coerce")

    if "fit_ge_075" not in out.columns:
        out["fit_ge_075"] = out["fit_score"].ge(0.75)
    else:
        out["fit_ge_075"] = _as_bool(out["fit_ge_075"])

    if "fit_ge_099" not in out.columns:
        out["fit_ge_099"] = out["fit_score"].ge(0.99)
    else:
        out["fit_ge_099"] = _as_bool(out["fit_ge_099"])

    if "run_id" not in out.columns:
        out["run_id"] = "default"
    out["run_id"] = out["run_id"].fillna("default").astype(str)

    if "category" not in out.columns:
        both = out["is_real_chaffin_hole"] & out["is_inferred_hole"]
        missed = out["is_real_chaffin_hole"] & ~out["is_inferred_hole"]
        false_positive = ~out["is_real_chaffin_hole"] & out["is_inferred_hole"]

        out["category"] = "neither"
        out.loc[both, "category"] = "both"
        out.loc[missed, "category"] = "missed_real_hole"
        out.loc[false_positive, "category"] = "false_positive"
    else:
        out["category"] = out["category"].fillna("unknown").astype(str)

    return (
        out.dropna(subset=["value"])
        .sort_values(["run_id", "value"])
        .reset_index(drop=True)
    )


def _ensure_fits_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    if "run_id" not in out.columns:
        out["run_id"] = "default"

    out["run_id"] = out["run_id"].fillna("default").astype(str)

    for col in (
        "threshold",
        "precision",
        "recall",
        "f1",
        "jaccard",
        "fit_score",
    ):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    if "fit_class" not in out.columns:
        if "threshold" in out.columns:
            out["fit_class"] = out["threshold"].map(
                lambda x: f"{x:.2f}" if pd.notna(x) else "unknown"
            )
        else:
            out["fit_class"] = "unknown"

    return out.reset_index(drop=True)


def load_all_data():
    global STORE

    try:
        repo_files = _repo_files()

        loaded: dict[str, pd.DataFrame] = {}
        missing_groups: list[str] = []

        for name, prefix in EXPECTED_PREFIXES.items():
            files = _files_for_prefix(repo_files, prefix)
            if not files:
                loaded[name] = pd.DataFrame()
                missing_groups.append(name)
                continue
            loaded[name] = _download_parquets(files)

        sequence = _ensure_sequence_columns(loaded["sequence"])
        holes = _ensure_holes_columns(loaded["holes"])
        fits = _ensure_fits_columns(loaded["fits"])
        summary = loaded["summary"].copy()

        status_lines = [
            f"Dataset: `{DATASET_ID}` @ `{DATASET_REVISION}`",
            f"Sequence rows: **{len(sequence):,}**",
            f"Hole rows: **{len(holes):,}**",
            f"Fit rows: **{len(fits):,}**",
            f"Summary rows: **{len(summary):,}**",
        ]

        if missing_groups:
            status_lines.append(
                "Missing viewer table group(s): **"
                + ", ".join(missing_groups)
                + "**. The Space stays online, but those views remain unavailable "
                  "until the dataset repo publishes the corresponding Parquet files."
            )

        if not sequence.empty and "fit_score" in sequence.columns:
            valid = sequence["fit_score"].dropna()
            if not valid.empty and valid.max() > 1.0:
                status_lines.append(
                    "⚠️ Sequence `fit_score` contains values above 1.0. "
                    "This Space expects normalized scores in the range 0–1."
                )

        if not holes.empty and "fit_score" in holes.columns:
            valid = holes["fit_score"].dropna()
            if not valid.empty and valid.max() > 1.0:
                status_lines.append(
                    "⚠️ Hole `fit_score` contains values above 1.0. "
                    "This Space expects normalized scores in the range 0–1."
                )

        loaded_ok = not sequence.empty or not holes.empty or not fits.empty

        with LOCK:
            STORE = Store(
                sequence=sequence,
                holes=holes,
                fits=fits,
                summary=summary,
                files=repo_files,
                status="\n\n".join(status_lines),
                loaded_ok=loaded_ok,
            )

        return (
            STORE.status,
            gr.update(choices=sequence_run_choices(), value=default_sequence_run()),
            gr.update(choices=hole_run_choices(), value=default_hole_run()),
            summary_markdown(),
            summary_table(),
        )

    except Exception as exc:
        message = (
            f"### Dataset load failed\n\n"
            f"`{type(exc).__name__}: {exc}`\n\n"
            f"The app remains available so the repository can be repaired without "
            f"turning the Space itself into a hard failure."
        )
        with LOCK:
            STORE = Store(status=message, loaded_ok=False)

        return (
            message,
            gr.update(choices=["default"], value="default"),
            gr.update(choices=["default"], value="default"),
            summary_markdown(),
            pd.DataFrame(),
        )


# ---------------------------------------------------------------------
# Shared view helpers
# ---------------------------------------------------------------------

def sequence_run_choices() -> list[str]:
    with LOCK:
        df = STORE.sequence.copy()
    if df.empty or "run_id" not in df.columns:
        return ["default"]
    values = sorted(df["run_id"].dropna().astype(str).unique().tolist())
    return values or ["default"]


def hole_run_choices() -> list[str]:
    with LOCK:
        df = STORE.holes.copy()
    if df.empty or "run_id" not in df.columns:
        return ["default"]
    values = sorted(df["run_id"].dropna().astype(str).unique().tolist())
    return values or ["default"]


def default_sequence_run() -> str:
    return sequence_run_choices()[0]


def default_hole_run() -> str:
    return hole_run_choices()[0]


def summary_markdown() -> str:
    with LOCK:
        seq = STORE.sequence.copy()
        holes = STORE.holes.copy()
        fits = STORE.fits.copy()

    if seq.empty and holes.empty and fits.empty:
        return (
            "### Awaiting viewer tables\n\n"
            "Publish the structured Parquet tables under `viewer/sequence/`, "
            "`viewer/holes/`, `viewer/fits/`, and optionally `viewer/summary/` "
            "in the dataset repository."
        )

    seq_points = len(seq)

    if holes.empty:
        real_holes = inferred_075 = inferred_099 = overlap_075 = overlap_099 = 0
    else:
        real_holes = int(holes["is_real_chaffin_hole"].sum())
        inferred_075 = int(
            (holes["is_inferred_hole"] & holes["fit_ge_075"]).sum()
        )
        inferred_099 = int(
            (holes["is_inferred_hole"] & holes["fit_ge_099"]).sum()
        )
        overlap_075 = int(
            (
                holes["is_real_chaffin_hole"]
                & holes["is_inferred_hole"]
                & holes["fit_ge_075"]
            ).sum()
        )
        overlap_099 = int(
            (
                holes["is_real_chaffin_hole"]
                & holes["is_inferred_hole"]
                & holes["fit_ge_099"]
            ).sum()
        )

    return f"""
### Current comparison set

| Measure | Value |
|---|---:|
| Sequence rows | **{seq_points:,}** |
| Real Chaffin holes represented | **{real_holes:,}** |
| Inferred holes ≥ 0.75 | **{inferred_075:,}** |
| Inferred holes ≥ 0.99 | **{inferred_099:,}** |
| Real ∩ inferred ≥ 0.75 | **{overlap_075:,}** |
| Real ∩ inferred ≥ 0.99 | **{overlap_099:,}** |

**Interpretation:** the 0.99 and 0.75 thresholds are displayed as
*inference-confidence / fit filters*. They must not be presented as proof
that an integer is absent from the infinite Recamán sequence.
"""


def summary_table() -> pd.DataFrame:
    with LOCK:
        summary = STORE.summary.copy()
    return summary


def _filter_run(df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    if df.empty or "run_id" not in df.columns:
        return df.copy()
    if run_id not in set(df["run_id"].astype(str)):
        return df.iloc[0:0].copy()
    return df[df["run_id"].astype(str) == str(run_id)].copy()


# ---------------------------------------------------------------------
# Sequence view
# ---------------------------------------------------------------------

def sequence_limits(run_id: str):
    with LOCK:
        df = _filter_run(STORE.sequence, run_id)

    if df.empty:
        return gr.update(minimum=0, maximum=1, value=1, step=1)

    n_min = int(df["n"].min())
    n_max = int(df["n"].max())
    default = min(n_max, max(n_min, min(n_min + 2000, n_max)))

    return gr.update(
        minimum=n_min,
        maximum=n_max,
        value=default,
        step=1,
    )


def plot_sequence(
    run_id: str,
    n_end: int,
    show_real: bool,
    show_inferred: bool,
    mark_divergence: bool,
    min_fit: float,
):
    with LOCK:
        df = _filter_run(STORE.sequence, run_id)

    if df.empty:
        return go.Figure().update_layout(
            title="No sequence table is available for this run."
        ), pd.DataFrame()

    visible = df[df["n"] <= int(n_end)].copy()

    if "fit_score" in visible.columns and visible["fit_score"].notna().any():
        fit_mask = visible["fit_score"].isna() | visible["fit_score"].ge(float(min_fit))
        visible = visible[fit_mask]

    fig = go.Figure()

    if show_real:
        fig.add_trace(
            go.Scattergl(
                x=visible["n"],
                y=visible["a_n_real"],
                mode="lines",
                name="Real Recamán",
                hovertemplate="n=%{x}<br>a(n)=%{y}<extra>Real</extra>",
            )
        )

    if show_inferred and visible["a_n_inferred"].notna().any():
        fig.add_trace(
            go.Scattergl(
                x=visible["n"],
                y=visible["a_n_inferred"],
                mode="lines",
                name="Inferred",
                hovertemplate="n=%{x}<br>inferred=%{y}<extra>Inferred</extra>",
            )
        )

    divergence = visible[
        visible["a_n_inferred"].notna()
        & visible["a_n_real"].notna()
        & ~visible["is_exact_match"]
    ].copy()

    if mark_divergence and not divergence.empty:
        fig.add_trace(
            go.Scattergl(
                x=divergence["n"],
                y=divergence["a_n_real"],
                mode="markers",
                name="Divergence",
                customdata=divergence[
                    ["a_n_inferred", "delta", "abs_delta", "fit_score"]
                ].to_numpy(),
                hovertemplate=(
                    "n=%{x}<br>real=%{y}<br>"
                    "inferred=%{customdata[0]}<br>"
                    "delta=%{customdata[1]}<br>"
                    "|delta|=%{customdata[2]}<br>"
                    "fit=%{customdata[3]}<extra>Divergence</extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"Real vs inferred Recamán sequence — run {run_id}",
        xaxis_title="Sequence index n",
        yaxis_title="a(n)",
        hovermode="closest",
        legend_title="Series",
    )

    cols = [
        c
        for c in [
            "n",
            "a_n_real",
            "a_n_inferred",
            "delta",
            "abs_delta",
            "is_exact_match",
            "fit_score",
            "fit_ge_075",
            "fit_ge_099",
            "run_id",
        ]
        if c in visible.columns
    ]

    divergence_table = (
        divergence[cols].sort_values("abs_delta", ascending=False)
        if not divergence.empty
        else pd.DataFrame(columns=cols)
    )

    return fig, divergence_table.head(1000)


# ---------------------------------------------------------------------
# Hole view
# ---------------------------------------------------------------------

def hole_limits(run_id: str):
    with LOCK:
        df = _filter_run(STORE.holes, run_id)

    if df.empty:
        return gr.update(minimum=0, maximum=1, value=1, step=1)

    value_min = int(df["value"].min())
    value_max = int(df["value"].max())
    default = min(value_max, max(value_min, min(value_min + 10000, value_max)))

    return gr.update(
        minimum=value_min,
        maximum=value_max,
        value=default,
        step=1,
    )


def _threshold_value(label: str) -> float:
    return {
        "All inferred": 0.0,
        "≥ 0.75 fit": 0.75,
        "≥ 0.99 fit": 0.99,
    }.get(label, 0.0)


def _hole_comparison_rows(
    run_id: str,
    max_value: int,
    threshold_label: str,
) -> pd.DataFrame:
    with LOCK:
        df = _filter_run(STORE.holes, run_id)

    if df.empty:
        return df

    out = df[df["value"] <= int(max_value)].copy()
    threshold = _threshold_value(threshold_label)

    if threshold > 0:
        inferred_visible = out["is_inferred_hole"] & out["fit_score"].ge(threshold)
    else:
        inferred_visible = out["is_inferred_hole"]

    real = out["is_real_chaffin_hole"]

    category = pd.Series("neither", index=out.index, dtype="object")
    category.loc[real & inferred_visible] = "real + inferred"
    category.loc[real & ~inferred_visible] = "real only / missed"
    category.loc[~real & inferred_visible] = "inferred only / false positive"
    out["comparison_category"] = category
    out["inferred_visible"] = inferred_visible

    return out


def plot_holes(
    run_id: str,
    max_value: int,
    threshold_label: str,
    only_disagreements: bool,
):
    df = _hole_comparison_rows(run_id, max_value, threshold_label)

    if df.empty:
        return go.Figure().update_layout(
            title="No hole table is available for this run."
        ), pd.DataFrame(), metrics_markdown(pd.DataFrame(), threshold_label)

    display_df = df.copy()
    if only_disagreements:
        display_df = display_df[
            display_df["comparison_category"].isin(
                ["real only / missed", "inferred only / false positive"]
            )
        ]

    rows = []

    real = display_df[display_df["is_real_chaffin_hole"]]
    if not real.empty:
        real_rows = real.copy()
        real_rows["track"] = "Real Chaffin hole"
        real_rows["plot_y"] = 2
        rows.append(real_rows)

    inferred_099 = display_df[
        display_df["is_inferred_hole"] & display_df["fit_ge_099"]
    ]
    if not inferred_099.empty:
        temp = inferred_099.copy()
        temp["track"] = "Inferred ≥ 0.99"
        temp["plot_y"] = 1
        rows.append(temp)

    inferred_075 = display_df[
        display_df["is_inferred_hole"]
        & display_df["fit_ge_075"]
        & ~display_df["fit_ge_099"]
    ]
    if not inferred_075.empty:
        temp = inferred_075.copy()
        temp["track"] = "Inferred 0.75–0.99"
        temp["plot_y"] = 0
        rows.append(temp)

    if rows:
        plot_df = pd.concat(rows, ignore_index=True)
        fig = px.scatter(
            plot_df,
            x="value",
            y="plot_y",
            symbol="track",
            hover_data={
                "plot_y": False,
                "track": True,
                "fit_score": ":.4f",
                "comparison_category": True,
                "run_id": True,
            },
            title=f"Real Chaffin holes vs inferred holes — {threshold_label}",
        )
        fig.update_yaxes(
            tickmode="array",
            tickvals=[0, 1, 2],
            ticktext=[
                "Inferred 0.75–0.99",
                "Inferred ≥ 0.99",
                "Real Chaffin holes",
            ],
            title=None,
        )
        fig.update_xaxes(title="Candidate integer / hole value")
        fig.update_layout(hovermode="closest")
    else:
        fig = go.Figure().update_layout(
            title=f"No displayed hole markers for {threshold_label}"
        )

    cols = [
        c
        for c in [
            "value",
            "is_real_chaffin_hole",
            "is_inferred_hole",
            "fit_score",
            "fit_ge_075",
            "fit_ge_099",
            "comparison_category",
            "run_id",
        ]
        if c in display_df.columns
    ]

    comparison_table = display_df[
        display_df["comparison_category"] != "neither"
    ][cols].sort_values("value")

    return (
        fig,
        comparison_table.head(5000),
        metrics_markdown(df, threshold_label),
    )


def metrics_markdown(df: pd.DataFrame, threshold_label: str) -> str:
    if df.empty:
        return "### Hole metrics\n\nNo hole comparison data available."

    real = df["is_real_chaffin_hole"]
    inferred = df["inferred_visible"]

    tp = int((real & inferred).sum())
    fp = int((~real & inferred).sum())
    fn = int((real & ~inferred).sum())

    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = (
        2 * precision * recall / (precision + recall)
        if pd.notna(precision)
        and pd.notna(recall)
        and (precision + recall) > 0
        else float("nan")
    )
    union = int((real | inferred).sum())
    jaccard = tp / union if union else float("nan")

    def fmt(value: float) -> str:
        return "—" if pd.isna(value) else f"{value:.4f}"

    return f"""
### Hole metrics — {threshold_label}

| Metric | Value |
|---|---:|
| Real holes | **{int(real.sum()):,}** |
| Inferred holes | **{int(inferred.sum()):,}** |
| Overlap / TP | **{tp:,}** |
| False positives | **{fp:,}** |
| Missed real holes | **{fn:,}** |
| Precision | **{fmt(precision)}** |
| Recall | **{fmt(recall)}** |
| F1 | **{fmt(f1)}** |
| Jaccard overlap | **{fmt(jaccard)}** |
"""


# ---------------------------------------------------------------------
# Fit-analysis view
# ---------------------------------------------------------------------

def fit_analysis(run_id: str):
    with LOCK:
        fits = STORE.fits.copy()

    if fits.empty:
        return (
            go.Figure().update_layout(title="No fit summary table is available."),
            pd.DataFrame(),
        )

    if "run_id" in fits.columns and run_id in set(fits["run_id"].astype(str)):
        table = fits[fits["run_id"].astype(str) == str(run_id)].copy()
    else:
        table = fits.copy()

    metric = None
    for candidate in ("jaccard", "f1", "recall", "precision", "fit_score"):
        if candidate in table.columns and table[candidate].notna().any():
            metric = candidate
            break

    if metric and "threshold" in table.columns:
        plot_df = table.dropna(subset=["threshold", metric]).copy()
        fig = px.line(
            plot_df,
            x="threshold",
            y=metric,
            markers=True,
            hover_data=[c for c in ["run_id", "fit_class"] if c in plot_df.columns],
            title=f"{metric} by fit threshold",
        )
        fig.update_xaxes(title="Threshold")
        fig.update_yaxes(title=metric)
    else:
        fig = go.Figure().update_layout(
            title="Fit table loaded; no numeric threshold/metric pair to plot."
        )

    return fig, table


# ---------------------------------------------------------------------
# Raw table + export
# ---------------------------------------------------------------------

def raw_table(name: str, run_id: str):
    with LOCK:
        mapping = {
            "sequence": STORE.sequence.copy(),
            "holes": STORE.holes.copy(),
            "fits": STORE.fits.copy(),
            "summary": STORE.summary.copy(),
        }

    df = mapping.get(name, pd.DataFrame())

    if (
        run_id
        and not df.empty
        and "run_id" in df.columns
        and run_id in set(df["run_id"].astype(str))
    ):
        df = df[df["run_id"].astype(str) == str(run_id)].copy()

    return df.head(10000)


def export_filtered_holes(
    run_id: str,
    max_value: int,
    threshold_label: str,
):
    df = _hole_comparison_rows(run_id, max_value, threshold_label)

    if df.empty:
        empty_path = EXPORT_DIR / "holes-empty.csv"
        pd.DataFrame().to_csv(empty_path, index=False)
        return str(empty_path)

    export = df[df["comparison_category"] != "neither"].copy()

    safe_run = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in run_id)
    safe_threshold = threshold_label.replace("≥", "ge").replace(" ", "_").replace(".", "_")
    path = EXPORT_DIR / f"holes_{safe_run}_{safe_threshold}.csv"
    export.to_csv(path, index=False)
    return str(path)


def export_sequence(run_id: str, n_end: int):
    with LOCK:
        df = _filter_run(STORE.sequence, run_id)

    if not df.empty:
        df = df[df["n"] <= int(n_end)].copy()

    safe_run = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in run_id)
    path = EXPORT_DIR / f"sequence_{safe_run}_to_{int(n_end)}.csv"
    df.to_csv(path, index=False)
    return str(path)


# ---------------------------------------------------------------------
# App
# ---------------------------------------------------------------------

INTRO = f"""
# Recamán Independent Check Visualizer

Interactive comparison for **real Recamán sequence values**, **real Chaffin-hole
evidence**, and the bundle's **inferred sequence / inferred-hole outputs**.

**Dataset:** `{DATASET_ID}`

This Space is a visualization layer over the reproducibility bundle. It does
not reinterpret finite computational evidence as a proof about the infinite
Recamán sequence.

### Intended evidence layers

- **Real sequence** — reference Recamán values present in the viewer table.
- **Inferred sequence** — model/run output stored alongside the reference values.
- **Real Chaffin holes** — hole catalogue supplied by the dataset evidence.
- **≥ 0.99 fit** — high-fit inferred-hole view.
- **≥ 0.75 fit** — broader inferred-hole view.
- **Disagreements** — missed real holes and inferred-only candidates.
"""


with gr.Blocks(title="Recamán Independent Check Visualizer") as demo:
    gr.Markdown(INTRO)

    with gr.Row():
        reload_button = gr.Button("Reload dataset")
        load_status = gr.Markdown("Loading dataset…")

    with gr.Tab("Overview"):
        overview_md = gr.Markdown()
        overview_table = gr.Dataframe(
            label="Dataset-provided summary",
            interactive=False,
            wrap=True,
        )

    with gr.Tab("Sequence"):
        with gr.Row():
            sequence_run = gr.Dropdown(
                choices=["default"],
                value="default",
                label="Inference run",
            )
            sequence_n_end = gr.Slider(
                minimum=0,
                maximum=1,
                value=1,
                step=1,
                label="Display through n",
            )
            sequence_min_fit = gr.Slider(
                minimum=0.0,
                maximum=1.0,
                value=0.0,
                step=0.01,
                label="Minimum fit score for inferred rows",
            )

        with gr.Row():
            show_real = gr.Checkbox(value=True, label="Show real sequence")
            show_inferred = gr.Checkbox(value=True, label="Show inferred sequence")
            mark_divergence = gr.Checkbox(
                value=True,
                label="Mark divergence points",
            )

        sequence_plot = gr.Plot(label="Sequence comparison")
        sequence_divergence_table = gr.Dataframe(
            label="Largest divergence points",
            interactive=False,
            wrap=True,
        )
        sequence_export = gr.DownloadButton(
            label="Export displayed sequence CSV",
        )

        sequence_run.change(
            fn=sequence_limits,
            inputs=sequence_run,
            outputs=sequence_n_end,
        )

        for component in (
            sequence_run,
            sequence_n_end,
            show_real,
            show_inferred,
            mark_divergence,
            sequence_min_fit,
        ):
            component.change(
                fn=plot_sequence,
                inputs=[
                    sequence_run,
                    sequence_n_end,
                    show_real,
                    show_inferred,
                    mark_divergence,
                    sequence_min_fit,
                ],
                outputs=[sequence_plot, sequence_divergence_table],
            )

        sequence_export.click(
            fn=export_sequence,
            inputs=[sequence_run, sequence_n_end],
            outputs=sequence_export,
        )

    with gr.Tab("Chaffin holes"):
        with gr.Row():
            hole_run = gr.Dropdown(
                choices=["default"],
                value="default",
                label="Inference run",
            )
            hole_max_value = gr.Slider(
                minimum=0,
                maximum=1,
                value=1,
                step=1,
                label="Maximum candidate value",
            )
            hole_threshold = gr.Radio(
                choices=["All inferred", "≥ 0.75 fit", "≥ 0.99 fit"],
                value="≥ 0.75 fit",
                label="Inference fit view",
            )

        hole_disagreements = gr.Checkbox(
            value=False,
            label="Show only disagreements",
        )

        hole_metrics = gr.Markdown()
        hole_plot = gr.Plot(label="Hole comparison")
        hole_table = gr.Dataframe(
            label="Real / inferred hole comparison",
            interactive=False,
            wrap=True,
        )
        hole_export = gr.DownloadButton(
            label="Export filtered hole comparison CSV",
        )

        hole_run.change(
            fn=hole_limits,
            inputs=hole_run,
            outputs=hole_max_value,
        )

        for component in (
            hole_run,
            hole_max_value,
            hole_threshold,
            hole_disagreements,
        ):
            component.change(
                fn=plot_holes,
                inputs=[
                    hole_run,
                    hole_max_value,
                    hole_threshold,
                    hole_disagreements,
                ],
                outputs=[hole_plot, hole_table, hole_metrics],
            )

        hole_export.click(
            fn=export_filtered_holes,
            inputs=[hole_run, hole_max_value, hole_threshold],
            outputs=hole_export,
        )

    with gr.Tab("Fit analysis"):
        fit_run = gr.Dropdown(
            choices=["default"],
            value="default",
            label="Run",
        )
        fit_plot = gr.Plot(label="Threshold performance")
        fit_table = gr.Dataframe(
            label="Fit evidence table",
            interactive=False,
            wrap=True,
        )
        fit_run.change(
            fn=fit_analysis,
            inputs=fit_run,
            outputs=[fit_plot, fit_table],
        )

    with gr.Tab("Raw tables"):
        with gr.Row():
            raw_name = gr.Radio(
                choices=["sequence", "holes", "fits", "summary"],
                value="sequence",
                label="Viewer table",
            )
            raw_run = gr.Dropdown(
                choices=["default"],
                value="default",
                label="Run filter",
            )

        raw_df = gr.Dataframe(
            label="First 10,000 rows",
            interactive=False,
            wrap=True,
        )

        raw_name.change(
            fn=raw_table,
            inputs=[raw_name, raw_run],
            outputs=raw_df,
        )
        raw_run.change(
            fn=raw_table,
            inputs=[raw_name, raw_run],
            outputs=raw_df,
        )

    def _reload_and_sync():
        status, seq_update, hole_update, overview, table = load_all_data()

        seq_choices = sequence_run_choices()
        hole_choices = hole_run_choices()

        default_seq = seq_choices[0]
        default_hole = hole_choices[0]

        fit_choices = (
            sorted(
                set(seq_choices)
                | set(hole_choices)
                | (
                    set(STORE.fits["run_id"].astype(str))
                    if not STORE.fits.empty and "run_id" in STORE.fits.columns
                    else set()
                )
            )
            or ["default"]
        )

        raw_choices = sorted(set(seq_choices) | set(hole_choices) | set(fit_choices))
        raw_default = raw_choices[0]

        seq_slider = sequence_limits(default_seq)
        hole_slider = hole_limits(default_hole)

        seq_fig, seq_table = plot_sequence(
            default_seq,
            seq_slider["value"],
            True,
            True,
            True,
            0.0,
        )
        hole_fig, holes_table, holes_metrics = plot_holes(
            default_hole,
            hole_slider["value"],
            "≥ 0.75 fit",
            False,
        )
        fit_fig, fits_df = fit_analysis(fit_choices[0])
        raw = raw_table("sequence", raw_default)

        return (
            status,
            gr.update(choices=seq_choices, value=default_seq),
            seq_slider,
            seq_fig,
            seq_table,
            gr.update(choices=hole_choices, value=default_hole),
            hole_slider,
            hole_fig,
            holes_table,
            holes_metrics,
            gr.update(choices=fit_choices, value=fit_choices[0]),
            fit_fig,
            fits_df,
            gr.update(choices=raw_choices, value=raw_default),
            raw,
            overview,
            table,
        )

    reload_outputs = [
        load_status,
        sequence_run,
        sequence_n_end,
        sequence_plot,
        sequence_divergence_table,
        hole_run,
        hole_max_value,
        hole_plot,
        hole_table,
        hole_metrics,
        fit_run,
        fit_plot,
        fit_table,
        raw_run,
        raw_df,
        overview_md,
        overview_table,
    ]

    reload_button.click(
        fn=_reload_and_sync,
        outputs=reload_outputs,
    )

    demo.load(
        fn=_reload_and_sync,
        outputs=reload_outputs,
    )


if __name__ == "__main__":
    demo.launch()
