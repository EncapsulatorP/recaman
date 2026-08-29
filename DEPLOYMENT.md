# CI/CD and the Hugging Face Space

## What CI checks

The GitHub Actions workflow in `.github/workflows/ci-cd.yml` runs:

- Python 3.10, 3.11 and 3.12 test coverage;
- source compilation and unit tests;
- that the generated Space measurements and the infographic are both in step
  with `outputs/recaman_wheel_results.json` (`--check` modes below);
- smoke tests for the experiment runner, density analysis, forward validation,
  and phase-space rendering;
- a Space job that installs the pinned Gradio, verifies the pin matches the
  Space card, imports the app and exercises both API endpoints;
- guarded deployment to Hugging Face after all CI jobs pass on `main`.

## The two Spaces

The repository ships two independent Gradio apps, because it studies two
different things and they must not be confused:

| directory | product | target Space | isolated secret |
| --- | --- | --- | --- |
| `apps/space/` | forward-held-out next-move model arena | `kugguk/recaman-next-move` via `HF_SPACE_REPO_ID` | `HF_RECAMAN` |
| `apps/claude_ai_holes/` | lossless obstruction compression lab | `kugguk/recaman-obstruction-lab` via `HF_HOLES_SPACE_REPO_ID` | `HF_HOLES_TOKEN` |

Each is deployed on its own, with its directory as the Space root, so its
modules are top-level there (`import predictor`, not `import apps.space.predictor`).
`tests/conftest.py` puts both directories on `sys.path`; their module names are
deliberately distinct so they can coexist. Both depend on Gradio alone — the
figures are SVG generated at request time, so there is no plotting stack and no
image asset to keep in sync.

The apps intentionally use different product language and experiments. The next-move
Space ranks inferred process models on a future block. The obstruction Space measures
lossless catalogue/process compression and verifies every custom codec by decoding it.

## Regenerating the derived files

The Space data files in the tree are generated, and CI fails if any drifts:

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

Each Space pins the version in two places, and CI asserts the pair agrees:

1. `<space>/requirements.txt` — `gradio==5.50.0`
2. `<space>/README.md` — `sdk_version: 5.50.0`

Change both together, then run that Space's smoke job locally if you can.
Moving across a major version (5 → 6) is a breaking change for the SDK and
should be its own commit.

### Licensing

The repository is MIT-licensed ([`LICENSE`](LICENSE)), and both Space cards
declare `license: mit` to match. If the root licence ever changes, change both
cards' `license:` keys in the same commit.

## Enable Hugging Face deployment

1. Create the target Hugging Face Space.
2. Add the GitHub repository variable `HF_SPACE_REPO_ID` with a value such as
   `username/recaman-next-move`.
3. Add the GitHub Actions secret `HF_RECAMAN`. Use a fine-grained Hugging Face
   token with write access only to the `HF_SPACE_REPO_ID` target Space. Do not
   reuse tokens belonging to other Spaces.
4. Optionally configure protection or required reviewers for the
   `huggingface-space` GitHub environment.
5. Push to `main`, or run the workflow manually after merging a tested change.

Set `HF_HOLES_SPACE_REPO_ID=kugguk/recaman-obstruction-lab` for the compression
Space. The two deploy jobs are independent, and its credential remains separately
configured as `HF_HOLES_TOKEN`. Neither token should grant access to the sibling
Space or to any other kugguk Space. If a variable is absent, that deployment is
skipped while CI continues to run normally.

## PyPI publishing

PyPI deployment should be added only after the reusable code has been moved
into an installable package with `pyproject.toml`. At that point, use PyPI
Trusted Publishing from a protected GitHub release environment rather than a
long-lived API token.
