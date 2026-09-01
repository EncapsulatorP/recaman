# Reproducing the research

[Home](Home.md) · [Findings](Findings.md) ·
[Data](Data-and-Provenance.md) · [Methods](Methods-and-Validation.md) ·
[Repository guide](Repository-Guide.md)

Run commands from the repository root. Python 3.10, 3.11, and 3.12 are covered
by CI.

## Environment

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Verify the checkout

```bash
python -m compileall -q run_all.py scripts apps/space apps/claude_ai_holes tests
python -m pytest -q
python run_all.py --dry-run
```

The dry run lists the experiment pipeline without starting the expensive
steps.

## Reproduce focused results

### Deep-obstruction frequency by multiplicative scale

```bash
python scripts/test_deep_obstruction_frequency.py
python scripts/test_deep_obstruction_frequency.py --check
```

This deterministic test uses 24 equal-width `log10(value)` bins, five fixed
contiguous-run thresholds, 10,000 one-sided permutations, and Holm correction.
It writes CSV, JSON, and Markdown artifacts under `outputs/`.

### Obstruction anatomy beyond frequency

```bash
python scripts/analyze_obstruction_anatomy.py
python scripts/analyze_obstruction_anatomy.py --check
```

This produces event-level severity/isolation data, equal-log scale profiles,
six corrected arithmetic tests, and a 1,000-replicate magnitude-matched
clustering null.

### Value-side Version C

Run only the harder gap-dynamics dataset:

```bash
python scripts/321_210_version_c.py \
  --input-file obstructions.txt \
  --datasets D \
  --save-json outputs/reproduction_version_c_D.json
```

The checked-in headline file was generated with all four datasets:

```bash
python scripts/321_210_version_c.py \
  --input-file obstructions.txt \
  --datasets ABCD \
  --save-json outputs/version_c_obstructions_results.json
```

### Random matched-control search

```bash
python scripts/321_210_randmat.py \
  --input-file obstructions.txt \
  --controls-per-positive 1 \
  --save-best-file outputs/reproduction_random.json
```

This search is substantially more expensive than the smoke tests. Seeds and
search settings are stored in the resulting JSON.

### Process-side wheel and phase slips

```bash
python scripts/recaman_wheel_validator.py
python scripts/recaman_wheel_honest.py
```

The validator's main saved horizon is 10 million steps. Runtime and memory use
depend on the machine.

### 3D phase-space images

```bash
python scripts/recaman_phase_space_3d.py \
  --steps 2800 --mode delay --tau 2 \
  --save outputs/reproduction_phase_delay.png

python scripts/recaman_phase_space_3d.py \
  --steps 2800 --mode arc-lift --twist 1.8 \
  --save outputs/reproduction_phase_arc.png
```

## Verify generated application assets

CI treats the derived products below as synchronized with their sources:

```bash
python scripts/build_space_measurements.py --check
python scripts/make_infographic.py --check
python scripts/sync_claude_ai_holes.py --check
python scripts/make_claude_ai_holes_infographic.py --check
python scripts/test_deep_obstruction_frequency.py --check
python scripts/analyze_obstruction_anatomy.py --check
```

Remove `--check` only when intentionally regenerating those files.

## Full experiment runner

```bash
python run_all.py --dry-run
python run_all.py --only version_c
python run_all.py --skip randmat
python run_all.py
```

Use `--only` while developing. The unrestricted runner executes multiple
large experiments and writes into `outputs/`.

## Reproducibility checklist

When publishing a refreshed result, preserve:

- the command and working directory;
- the Git commit;
- the catalogue checksum;
- Python and dependency versions;
- random seeds;
- horizon and control-generation policy;
- the complete output JSON, including fold scores;
- whether generated files were checked by the test suite.

The present output files do not all contain every item. See
[Data and provenance](Data-and-Provenance.md) for the recommended manifest.

---

[← Methods and validation](Methods-and-Validation.md) ·
[Next: Repository guide →](Repository-Guide.md)
