---
title: Recaman Absolute Holes (Claude.ai version)
emoji: 🕳️
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 5.50.0
python_version: "3.11"
app_file: app.py
license: mit
pinned: false
short_description: Structure of the integers the Recaman sequence never reaches
tags:
  - mathematics
  - number-theory
  - recaman
  - oeis-a005132
  - chaffin-holes
  - reproducible-research
---

# Recamán Absolute Holes — Claude.ai version

> This is the **Claude.ai version** of the Recamán obstruction work: a structure
> explorer for the *hole catalogue*. The rendered infographic carries a matching
> watermark. It is a **different quantity** from the sibling Space in
> `apps/space/`, which predicts the process-side obstruction bit `b(n)`.
> A blocked step is not a hole, and the two must not be confused.

## What an absolute hole is

The Recamán sequence starts at `a(0) = 0` and, at every step `n`, first tries
the backward move `a(n-1) - n`. It takes that move when the result is positive
and unvisited; otherwise it moves forward to `a(n-1) + n`. An integer the
sequence **never lands on — at any step, ever** — is an absolute hole.

## What this Space shows

**The hole set** — how many holes there are, how they distribute across powers
of ten, how they clump into runs, and how far apart the events sit.

**Explore the span** — a density strip you can slide across the covered range,
recomputed from the catalogue for whatever window you choose.

**What is predictable** — the measured AUCs of the two model pipelines in the
research repository, on one axis anchored at chance.

**Method and sources** — the rule, the catalogue's provenance and completeness,
and how this differs from the obstruction-bit Space.

## What it does not do

* **No per-number verdict.** This Space will not tell you whether an integer of
  your choosing is a hole. The honest measured separation tops out at AUC
  0.7586 — real signal, nowhere near a test — so offering a verdict would
  misrepresent it.
* **Nothing outside the covered span.** The catalogue is complete over
  930,058 – 4,293,242,951 and silent elsewhere. So is everything here.
* **No proof.** The structural counts are exact over the catalogue; the AUCs
  are measurements from saved runs.

## Provenance

`holes.txt` is a verbatim copy of `obstructions.txt` from the research
repository: Benjamin Chaffin's certified list of values the sequence never
reaches. Every structural number is recomputed from that file at load time, and
matches the saved `outputs/version_c_obstructions_results.json` run exactly —
3,102 events, 2,535 singletons, 567 ranges, longest run 368,058, gaps from 3 to
128,537,156. `results.json` is projected from the saved runs by
`scripts/sync_claude_ai_holes.py`. Nothing here is a hand-typed constant.

Source, methods and the full result set:
<https://github.com/kugguk2022/recaman_obstructions>

## Files

| file | role |
| --- | --- |
| `app.py` | Gradio interface |
| `holes.py` | catalogue parsing and structural summaries |
| `hole_figures.py` | SVG figures and the watermarked poster |
| `sequence.py` | a short Recamán walk, for the arc picture only |
| `holes.txt` | the hole catalogue, synced verbatim |
| `results.json` | measured model scores, synced from `outputs/` |

## License

Released under the MIT License.

<img src="assets/online-presence.svg" alt="Online presence" width="180">

<sub>The "online presence" mark is kugguk project artwork and does not modify or restrict the MIT License.</sub>
