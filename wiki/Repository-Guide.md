# Repository guide

[Home](Home.md) · [Findings](Findings.md) ·
[Methods](Methods-and-Validation.md) ·
[Reproduce](Reproducing-the-Research.md) · [Open questions](Open-Questions.md)

## Layout

```text
.
├── README.md               concise project landing page
├── obstructions.txt        value-side catalogue
├── run_all.py              experiment orchestrator
├── scripts/                research and generation scripts
├── outputs/                saved measurements and figures
├── apps/
│   ├── claude_ai_holes/    value-side catalogue explorer
│   └── space/              process-bit predictor and explorer
├── supporting_docs/        extended papers and source documents
├── tests/                  unit, provenance, and smoke tests
└── wiki/                   this navigable documentation
```

## Main research scripts

| Script | Purpose |
| --- | --- |
| `321_210_version_c.py` | Event-structured value modeling and forward validation |
| `321_210_randmat.py` | Expanded-value features, matched controls, and random projections |
| `recaman_wheel_validator.py` | Real-sequence wheel, bit-history, and phase-slip measurements |
| `recaman_wheel_honest.py` | Null comparisons and honest wheel validation |
| `recaman_heldout.py` | Held-out checks for candidate process predictors |
| `recaman_modm_scan.py` | Modular-state scan |
| `recaman_real_vs_fake.py` | Real-versus-synthetic obstruction comparison |
| `recaman_phase_space_3d.py` | Delay, spatiotemporal, and arc-lift embeddings |
| `recaman_carry_wheel.py` | Carry-wheel coordinate exploration |
| `recaman_grassmannian_tower.py` | Grassmannian/tower exploration |
| `densities.py` | Sequence and obstruction-density summaries |

Browse the complete
[`scripts/` directory](https://github.com/EncapsulatorP/recaman/tree/main/scripts)
for supporting summaries and generators.

## Generated-data scripts

| Script | Product |
| --- | --- |
| `build_space_measurements.py` | `apps/space/measurements.json` |
| `make_infographic.py` | Process-side SVG infographic |
| `sync_claude_ai_holes.py` | Value-side app catalogue, results, and assets |
| `make_claude_ai_holes_infographic.py` | Value-side SVG infographic |

All support `--check` so CI can detect drift without rewriting files.

## Result families

| Prefix or file | Subject |
| --- | --- |
| `version_c_*` | Value-side event and gap modeling |
| `best_obstructions_random*` | Expanded-value random-feature models |
| `recaman_wheel_*` | Process-bit and phase-slip results |
| `recaman_real_vs_fake_*` | Synthetic-control studies |
| `recaman_1e7_*` | Large-horizon phase-slip and gap summaries |
| `recaman_phase_*` | 3D embeddings |
| `carry_wheel_*` | Carry-wheel plots |

The most important saved files are indexed in
[Data and provenance](Data-and-Provenance.md).

## Applications

| Path | Audience | Boundary |
| --- | --- | --- |
| [`apps/claude_ai_holes/`](https://github.com/EncapsulatorP/recaman/tree/main/apps/claude_ai_holes) | Explore catalogue structure and value-model scores | Does not provide per-number certification |
| [`apps/space/`](https://github.com/EncapsulatorP/recaman/tree/main/apps/space) | Explore and predict the next process bit | Says nothing about permanent holes |

See [Demos and CI](Demos-and-Deployment.md) for local launch and automated checks.

## Extended documents

- [`recaman_final_math.md`](https://github.com/EncapsulatorP/recaman/blob/main/supporting_docs/recaman_final_math.md)
  is the long mathematical narrative and conjecture record.
- PDF, TeX, and Word variants live in
  [`supporting_docs/`](https://github.com/EncapsulatorP/recaman/tree/main/supporting_docs).
- [`DEPLOYMENT.md`](https://github.com/EncapsulatorP/recaman/blob/main/DEPLOYMENT.md)
  documents CI and local application checks.

The long note contains exploratory and historical claims. For the current
evidence hierarchy, use [Findings](Findings.md).

---

[← Reproducing the research](Reproducing-the-Research.md) ·
[Next: Open questions →](Open-Questions.md)
