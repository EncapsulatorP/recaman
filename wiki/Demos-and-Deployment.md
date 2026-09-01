# Demos and CI

[Home](Home.md) · [Findings](Findings.md) ·
[Reproduce](Reproducing-the-Research.md) ·
[Repository guide](Repository-Guide.md) · [Open questions](Open-Questions.md)

The repository contains two separate Gradio applications because the two
meanings of obstruction must remain distinct.

## Applications

| App | Subject | What it does not claim |
| --- | --- | --- |
| [Value-side hole explorer](https://github.com/EncapsulatorP/recaman/tree/main/apps/claude_ai_holes) | Catalogue counts, runs, span density, and model scores | It does not certify a submitted number as permanently absent |
| [Process-bit explorer](https://github.com/EncapsulatorP/recaman/tree/main/apps/space) | Next-bit baseline, sequence prefixes, and phase slips | It does not identify missing integers |
| [Independent comparison visualizer](https://github.com/EncapsulatorP/recaman/tree/main/apps/comparison) | Exact embedding/recurrence checks and Chaffin horizon coverage | It does not treat catalogue events outside the finite embedding span as predictions |

The repository does not advertise public hosted URLs. This page links to the
versioned source and documents local execution.

## Run locally

### Value-side explorer

```bash
python -m pip install -r apps/claude_ai_holes/requirements.txt
python apps/claude_ai_holes/app.py
```

### Process-side explorer

```bash
python -m pip install -r apps/space/requirements.txt
python apps/space/app.py
```

### Independent comparison visualizer

```bash
python -m pip install -r apps/comparison/requirements.txt
python apps/comparison/app.py
```

The comparison app uses hash-pinned NPZ files from the public independent-check
dataset. Its validation panel shows exact reconstruction counts and makes the
finite-horizon boundary with Chaffin's catalogue explicit.

Gradio prints the local address after startup.

## Data flow

```text
obstructions.txt + saved value results
    └── sync_claude_ai_holes.py
        └── apps/claude_ai_holes/{holes.txt, results.json, assets/}

outputs/recaman_wheel_results.json
    └── build_space_measurements.py
        └── apps/space/measurements.json
```

Verify both applications are synchronized:

```bash
python scripts/sync_claude_ai_holes.py --check
python scripts/make_claude_ai_holes_infographic.py --check
python scripts/build_space_measurements.py --check
python scripts/make_infographic.py --check
```

## Continuous integration

[`.github/workflows/ci-cd.yml`](https://github.com/EncapsulatorP/recaman/blob/main/.github/workflows/ci-cd.yml)
runs tests, generated-data drift checks, and isolated smoke checks for all three
applications. It has no publication jobs and requires no hosting credentials.

See [`DEPLOYMENT.md`](https://github.com/EncapsulatorP/recaman/blob/main/DEPLOYMENT.md)
for SDK pins, regeneration, and CI details.

---

[← Open questions](Open-Questions.md) · [Home](Home.md)
