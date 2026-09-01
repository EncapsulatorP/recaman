---
title: Recamán Independent Check Visualizer
emoji: 🧭
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 6.26.0
python_version: "3.11"
app_file: app.py
pinned: false
license: mit
short_description: Trace how early Recamán holes were actually missed
---

# Recamán Independent Check Visualizer

Source-backed visual validation for the
[`kugguk/recaman-independent-check-bundle`](https://huggingface.co/datasets/kugguk/recaman-independent-check-bundle)
embeddings, an independently regenerated Recamán prefix, and Benjamin
Chaffin's checked-in obstruction catalogue.

## What is compared

- The 2,801 published `recaman_sequence.npz` values against an independent
  implementation of the recurrence.
- The 2,801 published blocked-step labels against independently regenerated
  labels.
- Every row of the delay, spatiotemporal, and arc-lift embeddings against a
  fresh reconstruction from the regenerated sequence.
- All 3,103 Chaffin catalogue intervals against the embedding's actual
  finite value span.
- Every proposal involving the 103 catalogue values at or below 10,000,000
  during an exact ten-million-step recurrence.
- Adjacent non-catalogue controls and the exact branch outcome: chosen
  subtraction, forced addition, or bypassed addition candidate.

The embedding covers steps `0…2800` and values `0…10,163`. Chaffin's
catalogue begins at `852,655`, so none of its events lies inside this
embedding's value span. The Space displays that boundary explicitly: it does
not turn non-overlap into a hole prediction.

The mechanism trace finds that 23 early holes were addition candidates when a
legal subtraction took precedence, while 80 were never proposed through the
finite horizon. Addition opportunities for a value `m` are complete after
step `m`; subtraction opportunities remain right-censored, so this does not
prove permanent absence.

## Generated tables

| Table | Rows | Meaning |
|---|---:|---|
| `viewer/sequence/sequence.parquet` | 2,801 | Reference and embedded values/bits, deltas, exact-match flags |
| `viewer/holes/chaffin_events.parquet` | 3,103 | Exact catalogue intervals and embedding-span coverage |
| `viewer/fits/embedding_checks.parquet` | 6 | Exact reconstruction checks and source hashes |
| `viewer/summary/summary.parquet` | 1 | Coverage and validation totals |
| `viewer/obstructions/features.parquet` | 3,103 | Interpretable coordinates for every catalogue event |
| `viewer/obstructions/frequency_bands.parquet` | 5 | Normalised event and missing-value rates by value scale |
| `viewer/obstructions/deep_frequency_tests.parquet` | 5 | Corrected log-scale trend tests by run-depth threshold |
| `viewer/mechanisms/trace.parquet` | 301 | Exact proposal histories for 103 holes and 198 adjacent controls |
| `viewer/mechanisms/pairs.parquet` | 198 | Hole-to-adjacent-control comparisons |
| `viewer/mechanisms/summary.parquet` | 1 | Scope, invariants, causes, and interpretation boundary |

The sequence embedding remains a finite pipeline diagnostic; it is not used as
evidence that the Chaffin holes are predicted. The obstruction feature map has
100% catalogue-event coverage and is descriptive rather than predictive.

`viewer/manifest.json` records the source URLs and SHA-256 hashes. The four
NPZ files and their upstream metadata are retained under `source/embeddings/`
so the checks remain reproducible without network access.

## Regenerate and verify

From the repository root:

```bash
python scripts/build_comparison_tables.py
python scripts/build_comparison_tables.py --check
python scripts/analyze_hole_mechanisms.py --check
```

CI runs the check mode and the Space tests. Any source-hash mismatch, sequence
or blocked-bit mismatch, embedding-coordinate drift, catalogue drift, or stale
Parquet file fails the build.

## Run locally

```bash
python -m pip install -r apps/comparison/requirements.txt
python apps/comparison/app.py
```

Maintained for the [`kugguk`](https://huggingface.co/kugguk) Hugging Face
account. Released under the MIT License.
