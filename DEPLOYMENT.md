# CI and local Gradio apps

## What CI checks

The GitHub Actions workflow in `.github/workflows/ci-cd.yml` runs:

- Python 3.10, 3.11 and 3.12 test coverage;
- source compilation and unit tests;
- that the generated app measurements and the infographic are both in step
  with `outputs/recaman_wheel_results.json` (`--check` modes below);
- smoke tests for the experiment runner, density analysis, forward validation,
  and phase-space rendering;
- separate jobs that install the pinned Gradio versions, verify the pins match
  the app metadata, import all three applications, and exercise their public functions.

The workflow intentionally stops after verification. It does not publish to an
external hosting service or depend on repository deployment secrets.

## The three applications

The repository ships three independent Gradio apps. Two explore distinct
research objects; the third compares published reference and inferred evidence:

| directory | product |
| --- | --- |
| `apps/space/` | forward-held-out next-move model arena |
| `apps/claude_ai_holes/` | lossless obstruction compression lab |
| `apps/comparison/` | independent sequence/hole comparison and dataset-contract audit |

Each application is self-contained and runs with its directory as the import
root, so its modules are top-level there (`import predictor`, not
`import apps.space.predictor`).
`tests/conftest.py` puts the two original directories on `sys.path`; their
module names are deliberately distinct so they can coexist. The comparison app
is imported in isolation and pins its own pandas, PyArrow, Plotly, Gradio, and
Hugging Face Hub dependencies.

The apps intentionally use different product language and experiments. The
next-move app ranks inferred process models on a future block. The obstruction
app measures lossless catalogue/process compression and verifies every custom
codec by decoding it.

## Regenerating the derived files

The app data files in the tree are generated, and CI fails if any drifts:

```bash
python scripts/build_space_measurements.py            # apps/space/measurements.json
python scripts/make_infographic.py                    # outputs/recaman_next_move_infographic.svg
python scripts/sync_claude_ai_holes.py                # apps/claude_ai_holes/{holes.txt,results.json,assets/}
python scripts/make_claude_ai_holes_infographic.py    # outputs/recaman_holes_infographic_claude-ai.svg
python scripts/build_obstruction_tower_space.py       # apps/space/{holes.txt,tower_measurements.json}
```

The first two read `outputs/recaman_wheel_results.json`; the last two read
`obstructions.txt` plus the saved Version C and random-matrix runs. Re-run the
relevant pair whenever a run is refreshed. Add `--check` to any of them to
verify without writing, which is what CI does.

### Bumping the Gradio pin

Each app pins the Gradio version in two places, and CI asserts each pair agrees.
The original apps use `5.50.0`; the comparison app uses `6.26.0`:

1. `<app>/requirements.txt` — `gradio==5.50.0`
2. `<app>/README.md` — `sdk_version: 5.50.0`

Change both together, then run that app's smoke job locally if you can.
Moving across a major version (5 → 6) is a breaking change for the SDK and
should be its own commit.

### Licensing

The repository is MIT-licensed ([`LICENSE`](LICENSE)), and both app metadata blocks
declare `license: mit` to match. If the root licence ever changes, change both
cards' `license:` keys in the same commit.

## Run locally

```bash
python -m pip install -r apps/claude_ai_holes/requirements.txt
python apps/claude_ai_holes/app.py
```

Or, in a separate environment:

```bash
python -m pip install -r apps/space/requirements.txt
python apps/space/app.py
```

Gradio prints the local address after startup.

Run the comparison app in its own environment:

```bash
python -m pip install -r apps/comparison/requirements.txt
python apps/comparison/app.py
```

It reads `kugguk/recaman-independent-check-bundle` by default. The Overview tab
reports `PASS`, `PARTIAL`, `WAITING`, or `FAIL` for the published table contract.
