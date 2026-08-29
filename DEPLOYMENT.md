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

## Regenerating the derived files

Two files in the tree are generated, and CI fails if they drift:

```bash
python scripts/build_space_measurements.py   # apps/space/measurements.json
python scripts/make_infographic.py           # outputs/recaman_next_move_infographic.svg
```

Both read `outputs/recaman_wheel_results.json`, so re-run them whenever the
validator run is refreshed. Add `--check` to either to verify without writing,
which is what CI does.

## The Space

`apps/space/` is deployed on its own, with that directory as the Space root.
Its modules are therefore top-level there (`import predictor`, not
`import apps.space.predictor`); `tests/conftest.py` puts the same directory on
`sys.path` so the tests exercise the deployed layout. The Space depends on
Gradio alone — the figures are SVG generated at request time, so there is no
plotting stack and no image asset to keep in sync.

### Bumping the Gradio pin

The version appears in two places and CI asserts they agree:

1. `apps/space/requirements.txt` — `gradio==5.50.0`
2. `apps/space/README.md` — `sdk_version: 5.50.0`

Change both together, then run the Space job locally if you can. Moving across
a major version (5 → 6) is a breaking change for the SDK and should be its own
commit.

### Licensing

The repository is MIT-licensed ([`LICENSE`](LICENSE)), and the Space card
declares `license: mit` to match. If the root licence ever changes, change the
card's `license:` key in the same commit.

## Enable Hugging Face deployment

1. Create the target Hugging Face Space.
2. Add the GitHub repository variable `HF_SPACE_REPO_ID` with a value such as
   `username/recaman-next-move`.
3. Add the GitHub Actions secret `HF_TOKEN`. Use a fine-grained Hugging Face
   token with write access only to the target Space.
4. Optionally configure protection or required reviewers for the
   `huggingface-space` GitHub environment.
5. Push to `main`, or run the workflow manually after merging a tested change.

If `HF_SPACE_REPO_ID` is absent, deployment is skipped while CI continues to
run normally.

## PyPI publishing

PyPI deployment should be added only after the reusable code has been moved
into an installable package with `pyproject.toml`. At that point, use PyPI
Trusted Publishing from a protected GitHub release environment rather than a
long-lived API token.
