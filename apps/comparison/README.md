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
short_description: Validate Recamán embeddings against exact evidence
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
- All 3,102 Chaffin catalogue intervals against the embedding's actual
  finite value span.

The embedding covers steps `0…2800` and values `0…10,163`. Chaffin's
catalogue begins at `930,058`, so none of its events lies inside this
embedding's value span. The Space displays that boundary explicitly: it does
not turn non-overlap into a hole prediction.

## Generated tables

| Table | Rows | Meaning |
|---|---:|---|
| `viewer/sequence/sequence.parquet` | 2,801 | Reference and embedded values/bits, deltas, exact-match flags |
| `viewer/holes/chaffin_events.parquet` | 3,102 | Exact catalogue intervals and embedding-span coverage |
| `viewer/fits/embedding_checks.parquet` | 6 | Exact reconstruction checks and source hashes |
| `viewer/summary/summary.parquet` | 1 | Coverage and validation totals |

`viewer/manifest.json` records the source URLs and SHA-256 hashes. The four
NPZ files and their upstream metadata are retained under `source/embeddings/`
so the checks remain reproducible without network access.

## Regenerate and verify

From the repository root:

```bash
python scripts/build_comparison_tables.py
python scripts/build_comparison_tables.py --check
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
