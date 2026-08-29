---
title: Recamán Next-Move Model Lab
emoji: 🧠
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 5.50.0
python_version: "3.11"
app_file: app.py
license: mit
pinned: false
short_description: Forward-held-out agents for Recamán's next move
tags:
  - mathematics
  - number-theory
  - recaman
  - oeis-a005132
  - dynamical-systems
  - reproducible-research
---

# Recamán Next-Move Model Lab

This is the rigorous sibling of the compression-focused obstruction Space. Its
target is the process-side obstruction bit: whether Recamán's attempted backward
move is free or blocked.

- **Agent Arena** — inferred models fit the first 80% of a prefix and are scored
  only on its untouched final 20%;
- **model evolution** — AUC, calibration, accuracy and predictive code length
  decide which agent earns influence;
- **signed tower** — the exact identity
  `aₙ = Σᵢ≤ₙ i(2bᵢ−1) = Tₙ − 2ΣDₙ`;
- **tower shadows** — saved null-controlled power-of-two rank and
  Grassmannian measurements;
- **power experiment** — an interactive sign-flipping modular power iterator
  displayed against a fixed-sign control and the real obstruction bits.
- **evolution race** — deterministic visited-set evolution against autonomous
  alternation and modular-power rollouts that consume their own predictions.

## What you can do

### Fit, freeze and score inferred agents

Historical, arithmetic, phase-slip, modulo and tower agents compete against a
prevalence-only Skeptic. A train-weighted ensemble is frozen before the future
block is revealed. Models are ranked primarily by held-out bits per step: a
feature that cannot compress future outcomes does not earn influence.

The exact visited-set collision rule is displayed only as an oracle ceiling and
is never allowed into the inferred ensemble. The value-side gap model remains a
first-class registry entry, but its AUC is not blended with the different
next-bit target.

### Race deterministic and model evolution

Choose a shared exact checkpoint and let three paths advance independently:
the deterministic Recamán recurrence, the previous-sign alternation baseline,
and the sign-flipping modular-power shadow. The Space reports the first wrong
sign, bit agreement, final path error, and model moves forbidden by their own
visited histories.

The final value in Chaffin's hole catalogue is shown as a value-side frontier,
not misrepresented as a resumable Recamán state. Exact continuation from his
computation beyond 10^612 terms would require the full visited-range checkpoint.

### Inspect the exact ±n tower

Choose any step up to 200,000 and inspect the layers that reconstruct the
sequence value:

```text
a(n) = T(n) - 2 * sum(down-step indices)
```

The visual sign ribbon shows `−n` for free backward moves, `+n` for blocked
moves, and highlights same-sign phase slips.

### Test a sign-flipping power idea

The modular probe uses a bounded recurrence:

```text
r[h+1] = ((-1)^h * base)^(r[h] + 1) mod modulus
```

Its binary shadow is compared with both the real Recamán obstruction bits and
a fixed-positive-base control. Interactive parameter choice is multiple
testing, so the displayed agreement is hypothesis generation—not a fitted
result.

### Audit the inference boundary

The Space displays the repository's saved measurements under different
information budgets:

- arithmetic-only process features: AUC 0.6791;
- leakage-reduced value-side gap dynamics: AUC 0.7586;
- arithmetic plus the previous sign: AUC 0.9907, dominated by alternation;
- full visited-set collision oracle: AUC 1.0.

## API endpoints

- `/model_arena`
- `/evolution_race`
- `/signed_tower_snapshot`
- `/sign_flipping_power_probe`
- `/power_of_two_rank`
- `/predict_next_obstruction`
- `/simulate_obstruction_bits`

## Provenance and limits

The compact `tower_measurements.json` bundle is generated from saved outputs in
the [research repository](https://github.com/EncapsulatorP/recaman), while
`holes.txt` is synchronized from its root `obstructions.txt`.

Every tab labels whether it is showing an exact identity, a catalogue fact, a
saved empirical measurement, or an exploratory probe.

External provenance: [Benjamin Chaffin's Recamán computation](https://benchaffin.com/recaman/recaman.html).

Released under the MIT License.
