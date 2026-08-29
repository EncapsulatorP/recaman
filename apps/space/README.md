---
title: Recaman Next-Move Predictor
emoji: 🔁
colorFrom: blue
colorTo: yellow
sdk: gradio
sdk_version: 5.50.0
python_version: "3.11"
app_file: app.py
pinned: false
short_description: One-step obstruction-bit baseline for the Recaman sequence
tags:
  - mathematics
  - number-theory
  - recaman
  - oeis-a005132
  - time-series
  - reproducible-research
---

# Recamán Next-Move Predictor

The Recamán sequence starts at `a(0) = 0` and, at every step `n`, first tries
the backward move `a(n-1) - n`. It takes that move when the result is positive
and unvisited; otherwise it is **obstructed** and moves forward to
`a(n-1) + n`. The **obstruction bit** records which of the two happened:

| bit | meaning |
| --- | --- |
| `b(n) = 0` | the backward move was free — DOWN / FREE |
| `b(n) = 1` | the backward move was blocked — UP / BLOCKED |

## What this Space does

**Predict** — given the previous obstruction bit, it returns the next one with
the conditional probability measured over a saved 10,000,000-step run.

**Explore the real sequence** — it generates the sequence live in your browser
session and recomputes the same statistics on your own prefix, so you can watch
the phase-slip rate fall as the horizon grows.

**Method and limits** — the definitions, the measured numbers, and an explicit
statement of what the result does not claim.

## What it does not claim

* **It is not a proof.** Every number is an empirical measurement at a stated
  horizon. The same-bit slip rate fell from 2.37% at N = 10⁴ to 0.108% at
  N = 10⁷ and is still falling, so no limiting value is asserted.
* **It does not locate the slips.** Predicting *where* the rare defects occur is
  the open part of the problem.
* **It says nothing about permanently missing integers.** That is a separate,
  value-side question in the research repository.

## API

Both endpoints are callable with `gradio_client`:

```python
from gradio_client import Client

client = Client("<owner>/<space-name>")

client.predict(previous_move="DOWN / FREE  (b = 0)", api_name="/predict_next_obstruction")
client.predict(steps=64, api_name="/simulate_obstruction_bits")
```

`predict_next_obstruction` returns the predicted move together with its
confidence, the slip probability and the horizon the numbers were measured at.
`simulate_obstruction_bits` returns the terms, the obstruction bits and the slip
positions for a prefix of up to 5,000 steps.

## Provenance

Every displayed number is read from `measurements.json`, which
`scripts/build_space_measurements.py` derives from
`outputs/recaman_wheel_results.json` in the research repository. Nothing in this
Space is a hand-typed constant, and the figures are generated from the same
data at request time rather than shipped as images.

Source, methods and the full result set:
<https://github.com/kugguk2022/recaman_obstructions>

## Files

| file | role |
| --- | --- |
| `app.py` | Gradio interface and API endpoints |
| `predictor.py` | the one-step predictor, loaded from `measurements.json` |
| `recaman.py` | sequence and obstruction-bit generation |
| `figures.py` | SVG figures, theme-aware, no plotting dependency |
| `measurements.json` | generated measurements from the 10⁷-step run |
