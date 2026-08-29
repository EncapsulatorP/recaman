# Data and provenance

[Home](Home.md) · [Concepts](Concepts-and-Scope.md) ·
[Findings](Findings.md) · [Methods](Methods-and-Validation.md) ·
[Reproduce](Reproducing-the-Research.md)

## Hole catalogue

[`obstructions.txt`](https://github.com/EncapsulatorP/recaman/blob/main/obstructions.txt)
is the value-side source file. Each non-comment line is either a single
positive integer or an inclusive range:

```text
930058
1137508 - 1137509
```

The analysis code compresses those lines into events or expands them into
individual values, depending on the experiment.

### What is reproducible now

The repository can reproduce and test:

- parsing of the catalogue;
- event, singleton, range, span, and run-length totals;
- generated copies used by the hole explorer;
- saved feature-model measurements;
- infographic values derived from the catalogue and saved outputs.

### What the source file does not record

The file begins with a short label but contains no machine-readable record of:

- the upstream source URL or publication;
- the date retrieved;
- the exact Recamán convention used;
- the largest sequence index or value checked;
- the generator and algorithm version;
- a checksum for the upstream data;
- independent reproduction or a mathematical certificate.

Some code and interface copy associates the list with Chaffin, but the
catalogue itself does not carry enough metadata to audit that attribution or
the word “certified.” Until those fields are added, the file should be treated
as a research catalogue of persistent or candidate holes, not self-contained
proof of permanent absence.

## Catalogue size versus saved modeling size

Two counts appear in the repository and refer to different artifacts:

| Count | Meaning |
| --- | --- |
| 1,277,399 | Current catalogue after expanding all encoded ranges |
| 194,358 | Positives recorded in the saved random-feature experiment |

The second number comes from
[`outputs/best_obstructions_random_20260512_172100.json`](https://github.com/EncapsulatorP/recaman/blob/main/outputs/best_obstructions_random_20260512_172100.json).
It must not be presented as the current catalogue total. A refreshed model run
should record the exact input checksum so later catalogue changes are visible.

## Saved outputs

| File | Role |
| --- | --- |
| [`version_c_obstructions_results.json`](https://github.com/EncapsulatorP/recaman/blob/main/outputs/version_c_obstructions_results.json) | Event totals and `A/B/C/D` validation |
| [`best_obstructions_random_20260512_172100.json`](https://github.com/EncapsulatorP/recaman/blob/main/outputs/best_obstructions_random_20260512_172100.json) | Random-projection and random-forest run |
| [`recaman_wheel_results.json`](https://github.com/EncapsulatorP/recaman/blob/main/outputs/recaman_wheel_results.json) | 10-million-step process-bit validation |
| [`recaman_real_vs_fake_results.json`](https://github.com/EncapsulatorP/recaman/blob/main/outputs/recaman_real_vs_fake_results.json) | Real-versus-synthetic comparisons |
| [`recaman_grassmannian_tower.json`](https://github.com/EncapsulatorP/recaman/blob/main/outputs/recaman_grassmannian_tower.json) | Geometric exploration |

Saved JSON is a measurement record, not automatically a proof of how it was
produced. Exact commands are documented where known in
[Reproducing the research](Reproducing-the-Research.md).

## Recommended provenance record

A future catalogue release should include a small manifest with:

```yaml
sequence: OEIS A005132
rule_convention: positive-unvisited backward candidate
source_url: ...
retrieved_at: ...
verified_through_step: ...
max_visited_value: ...
generator_commit: ...
catalogue_sha256: ...
independently_reproduced: false
```

For every model output, also record the catalogue checksum, command, seed,
Python version, dependency versions, wall time, and code commit. That would
turn “long-lasting” into a precisely reproducible statement and make stronger
inference possible.

---

[← Findings](Findings.md) ·
[Next: Methods and validation →](Methods-and-Validation.md)
