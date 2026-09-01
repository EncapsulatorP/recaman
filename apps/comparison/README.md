---
title: Recamán Independent Check Visualizer
emoji: 🧭
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 6.26.0
app_file: app.py
pinned: false
license: mit
---

# Recamán Independent Check Visualizer

Interactive companion to:

`kugguk/recaman-independent-check-bundle`

The Space compares:

- real Recamán sequence values against inferred sequence output;
- real Chaffin-hole evidence against inferred-hole candidates;
- the >= 0.99 and >= 0.75 fit views;
- misses, false positives, overlap, precision, recall, F1 and Jaccard;
- raw viewer tables and downloadable filtered CSVs.

## Dataset contract

The dataset repo should publish:

- `viewer/sequence/*.parquet`
- `viewer/holes/*.parquet`
- `viewer/fits/*.parquet`
- `viewer/summary/*.parquet` (optional but recommended)

### Required sequence columns

- `n`
- `a_n_real`

Recommended:

- `a_n_inferred`
- `delta`
- `abs_delta`
- `is_exact_match`
- `fit_score`
- `fit_ge_075`
- `fit_ge_099`
- `run_id`

### Required hole columns

- `value`
- `is_real_chaffin_hole`

Recommended:

- `is_inferred_hole`
- `fit_score`
- `inferred_score`
- `fit_ge_075`
- `fit_ge_099`
- `category`
- `run_id`

All fit scores should use the normalized range `0.0 ... 1.0`.

## Optional environment variables

- `RECAMAN_DATASET_ID`
- `RECAMAN_DATASET_REVISION`
- `HF_TOKEN` (only needed if the dataset becomes private/gated)
