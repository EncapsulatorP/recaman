# Methods and validation

[Home](Home.md) · [Concepts](Concepts-and-Scope.md) ·
[Findings](Findings.md) · [Data](Data-and-Provenance.md) ·
[Reproduce](Reproducing-the-Research.md)

## Value-side pipelines

### Random matched-control search

[`scripts/321_210_randmat.py`](https://github.com/EncapsulatorP/recaman/blob/main/scripts/321_210_randmat.py)
expands catalogue entries, encodes arithmetic, digit, and residue features,
matches controls by digit length, searches random linear projections, and
reranks candidates with random-forest cross-validation.

This asks whether catalogue membership has broad numerical structure. It does
not model the sequence step at which a value might be visited.

### Event-structured Version C

[`scripts/321_210_version_c.py`](https://github.com/EncapsulatorP/recaman/blob/main/scripts/321_210_version_c.py)
compresses the catalogue into events:

| Dataset | Target |
| --- | --- |
| `A` | Singleton event starts |
| `B` | Range starts |
| `C` | Range ends |
| `D` | Gap dynamics between successive events |

The current default uses forward-chaining cross-validation, a purge window
between training and test contexts, information visible only at the simulated
time, and matched controls per event context.

## Process-side pipelines

### Wheel validation

[`scripts/recaman_wheel_validator.py`](https://github.com/EncapsulatorP/recaman/blob/main/scripts/recaman_wheel_validator.py)
generates the real Recamán sequence, records `b(n)`, tests the `Theta_3` wheel,
compares it with previous-bit conditioning, counts phase slips, and saves
horizon checkpoints.

[`scripts/recaman_wheel_honest.py`](https://github.com/EncapsulatorP/recaman/blob/main/scripts/recaman_wheel_honest.py)
adds null and held-out comparisons.

### Phase-slip and alternative-state studies

Modular scans, held-out predictors, carry-wheel coordinates, and
real-versus-fake experiments test whether additional state explains the rare
same-bit events. None currently supplies a closed, independently validated
locator for future slips.

## Geometric exploration

[`scripts/recaman_phase_space_3d.py`](https://github.com/EncapsulatorP/recaman/blob/main/scripts/recaman_phase_space_3d.py)
creates delay, spatiotemporal, and lifted-arc embeddings. Related scripts
explore Grassmannian, logistic-tower, and carry-wheel coordinates.

These views are hypothesis generators. A geometric picture becomes evidence
only when it defines a fixed numerical feature, uses matched controls, and
improves held-out prediction.

## Validation principles

### Preserve time order

Random folds can train on future obstruction contexts and test on the past.
Forward-chaining evaluation is the default for temporal claims.

### Purge adjacent contexts

Neighbouring events share local state. A purge gap reduces direct overlap
between training and test examples.

### Generate controls from visible information

Controls must be constructible from what was known at that point. Using future
blocked values leaks the answer into the task.

### Prefer local controls

Broad digit-matched controls test coarse separability. Nearby, same-context
controls test the harder claim that the method sees local obstruction
structure.

### Separate ranking from proof

AUC measures whether positives tend to rank above controls. It does not certify
individual values and cannot convert finite non-observation into an infinite
claim.

### Report negative results

The `Theta_3` wheel result is scientifically useful because it eliminates a
seductive but uninformative state representation.

## Reading a saved score

Before comparing two numbers, check:

1. Which object is labelled: value, event, gap, or process bit?
2. How were controls chosen?
3. Was evaluation forward in time?
4. Was there a purge gap?
5. What horizon and catalogue checksum were used?
6. Is the score held out, cross-validated, or fitted in-sample?
7. Does the output support ranking, forecasting, or only description?

---

[← Data and provenance](Data-and-Provenance.md) ·
[Next: Reproducing the research →](Reproducing-the-Research.md)
