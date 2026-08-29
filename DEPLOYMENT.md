# CI/CD

The GitHub Actions workflow in `.github/workflows/ci-cd.yml` provides:

- Python 3.10, 3.11, and 3.12 test coverage;
- source compilation and unit tests;
- smoke tests for the experiment runner, density analysis, forward validation,
  and phase-space rendering;
- a separate import test for the Gradio Space;
- guarded deployment to Hugging Face after all CI jobs pass on `main`.

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
