# Recamán Obstruction Research

[![CI](https://github.com/EncapsulatorP/recaman/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/EncapsulatorP/recaman/actions/workflows/ci-cd.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Computational research into values that Recamán's sequence may never reach—or
at least avoids for exceptionally long periods—and the blocked moves that
create its distinctive dynamics.

Recamán's sequence starts at `a(0) = 0`. At step `n` it subtracts `n` when the
result is positive and has not appeared before; otherwise it adds `n`:

```text
a(n) = a(n - 1) - n    if the result is positive and unvisited
a(n) = a(n - 1) + n    otherwise
```

The repository tests whether persistent gaps have detectable structure,
whether blocked moves can be predicted without temporal leakage, and which
patterns survive honest validation.

> **Research status:** this is empirical work, not a proof that any integer is
> absent forever. Here, a *catalogued hole* means membership in
> [`obstructions.txt`](obstructions.txt). The catalogue is evidence for
> candidate absolute obstructions. It is Benjamin Chaffin's published list of
> holes below `2^32` after computing beyond `10^612` terms; that result is a
> verified frontier, not a resumable checkpoint included in this repository.

## Two questions, two meanings

| Side | Question | Object |
| --- | --- | --- |
| **Value** | Which integers remain unvisited? | Catalogue membership in [`obstructions.txt`](obstructions.txt) |
| **Process** | When is the attempted backward move blocked? | The step bit `b(n)`: blocked/up = `1`, free/down = `0` |

A blocked step is not a missing integer. Predicting `b(n)` does not identify
which values are permanently absent.

## Interactive applications

The repository includes three locally runnable Gradio tools:

- [Recamán Obstruction Compression Lab](apps/claude_ai_holes/README.md) — lossless range/delta codecs, phase-slip encoding and exact round-trip checks.
- [Recamán Next-Move Model Lab](apps/space/README.md) — inferred agents, chronological holdouts, tower/modular ablations and predictive code length.
- [Recamán Independent Check Visualizer](apps/comparison/README.md) — exact NPZ-versus-recurrence checks, Chaffin horizon coverage, downloadable Parquet tables, and source-hash validation.

They are not advertised as public hosted demos. See [Demos and CI](wiki/Demos-and-Deployment.md)
for local launch commands and automated checks.

## Current picture

- The catalogue expands to **1,277,400 values** in **3,103 events**, spanning
  `852,655` to `4,293,242,951`. These are exact statements about the file, not
  a theorem about the infinite sequence.
- Across 24 equal multiplicative value bins after `852,655`, deeper contiguous
  obstruction runs become more frequent at every tested threshold (Holm-adjusted
  permutation `p ≤ 0.00060`); this supports the pattern, not its proposed
  visited-set-saturation mechanism.
- Beyond frequency, run severity is extremely concentrated (Gini `0.9849`;
  the largest 1% of events contain `77.6%` of missing values), and median
  nearest-neighbour distance is `5.1%` of a magnitude-matched null. No tested
  small-prime divisibility effect survives Holm correction.
- The strongest leakage-reduced value-side result is dataset `D` with mean AUC
  **0.7588** under forward-chaining validation. It shows statistical
  separation, not a per-integer test.
- On a saved **10,000,000-step** run, the proposed `Theta_3` wheel has
  essentially no predictive separation (`|delta q| = 0.000011`).
- The process bit is instead almost alternating: same-bit phase slips occur at
  rate **0.001084** in that run. Explaining where those rare slips occur remains
  open.

See [Findings](wiki/Findings.md) for the measurements and their limits.

## Navigate the research

| If you want to… | Start here |
| --- | --- |
| Understand the purpose and terminology | [Concepts and scope](wiki/Concepts-and-Scope.md) |
| Review the best-supported results | [Findings](wiki/Findings.md) |
| Audit the hole catalogue and saved outputs | [Data and provenance](wiki/Data-and-Provenance.md) |
| Understand controls, leakage, and validation | [Methods and validation](wiki/Methods-and-Validation.md) |
| Reproduce an experiment | [Reproducing the research](wiki/Reproducing-the-Research.md) |
| Find a script or output | [Repository guide](wiki/Repository-Guide.md) |
| See what remains unresolved | [Open questions](wiki/Open-Questions.md) |
| Run the interactive apps | [Demos and CI](wiki/Demos-and-Deployment.md) |

The full entry point is the [research wiki](wiki/Home.md).

## Quick start

Python 3.10–3.12 is covered by CI.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest -q
python run_all.py --dry-run
```

Focused reproductions:

```powershell
# Leakage-reduced value-side benchmark
python .\scripts\321_210_version_c.py --input-file .\obstructions.txt --datasets D

# Long-run process-side wheel and phase-slip validation
python .\scripts\recaman_wheel_validator.py
```

The long-run experiments can be compute-intensive. Commands for individual
results and generated assets are listed in
[Reproducing the research](wiki/Reproducing-the-Research.md).

## Repository map

| Path | Purpose |
| --- | --- |
| [`obstructions.txt`](obstructions.txt) | Catalogued value-side holes and ranges |
| [`scripts/`](scripts/) | Generators, feature searches, validators, and plots |
| [`outputs/`](outputs/) | Saved measurements and generated figures |
| [`apps/`](apps/) | Three separate Gradio explorers |
| [`supporting_docs/`](supporting_docs/) | Extended mathematical notes and papers |
| [`wiki/`](wiki/) | Navigable research documentation |
| [`tests/`](tests/) | Unit, provenance, and smoke checks |

## Further reading

- [Extended mathematical note](supporting_docs/recaman_final_math.md)
- [CI and local apps](DEPLOYMENT.md)
- [MIT License](LICENSE)

<img src="assets/online-presence.svg" alt="Online presence" width="160">

<sub>The online-presence mark is project artwork and does not modify the MIT License.</sub>
