# Open questions

[Home](Home.md) · [Concepts](Concepts-and-Scope.md) ·
[Findings](Findings.md) · [Methods](Methods-and-Validation.md) ·
[Repository guide](Repository-Guide.md)

## 1. Are any holes absolute?

This is the central value-side question. The checked-in catalogue alone cannot
answer it because it does not state the finite horizon from which absence was
inferred.

A defensible programme would:

1. record the catalogue source, convention, checksum, and verification
   horizon;
2. independently generate the sequence at increasing checkpoints;
3. track first-hit times and survival curves for every candidate;
4. distinguish values that are merely beyond the explored range from values
   surrounded by repeatedly visited neighbours;
5. freeze candidate features before evaluating a later horizon;
6. search for mathematical invariants that could exclude a value at every
   future step.

The first four steps establish increasingly strong persistence. Only the sixth
could produce a proof of absolute obstruction.

## 2. Can long-lasting holes be inferred honestly?

The current mean AUC of 0.7586 for dataset `D` is evidence of local structure,
not a hole detector. A next-generation benchmark should predict a precisely
defined target such as:

> Given information available through step `N`, rank values that will remain
> unvisited through step `cN` for a fixed `c > 1`.

That target is finite, auditable, and useful even if permanent absence remains
unknown. It requires:

- controls matched by magnitude, local visit density, and accessibility;
- train/test splits by sequence horizon rather than catalogue row;
- calibration and precision-recall results, not AUC alone;
- ablation of raw value and event-index features;
- independent evaluation on a later, untouched run.

## 3. Where do phase slips occur?

Previous-bit conditioning predicts ordinary alternation. The scientifically
interesting cases are the same-bit defects.

Candidate state should describe the local visited-set geometry near the
attempted backward value: gap width, neighbour density, recency, collision
depth, and nearby legal alternatives. Evaluation should be event-focused,
class-imbalance aware, and strictly forward in time.

## 4. Does value-side structure explain process-side defects?

The two sides may interact, but no result currently joins them. A direct test
would align phase-slip steps with the future persistence of values near the
rejected backward candidate, then compare against matched non-slip steps.

The analysis must avoid using eventual catalogue membership as a feature at an
earlier time; that would leak future information.

## 5. Which geometric ideas survive prediction?

Arc lifts, carry wheels, Grassmannian towers, and Markov-shadow coordinates
should each be converted into fixed numerical features. They earn explanatory
weight only if they improve held-out prediction beyond simple gap, recency, and
previous-bit baselines.

## 6. How stable are the observations?

The same-bit slip rate decreases across the saved checkpoints:

| Horizon | Approximate slip probability inferred from saved conditionals |
| --- | ---: |
| 10,000 | about 0.024 |
| 100,000 | about 0.010 |
| 1,000,000 | about 0.0034 |
| 5,000,000 | about 0.0014 |
| 10,000,000 | about 0.0011 |

This trend makes a fixed limiting rate unsafe to claim. Longer horizons should
test scaling laws with uncertainty intervals and out-of-sample checkpoints.

## Priorities

1. Add a catalogue provenance manifest.
2. Reproduce the catalogue independently at stated horizons.
3. Define the finite “remains unseen through `cN`” forecasting task.
4. Tighten controls and remove trivial anchor features.
5. Build a rare-event phase-slip benchmark.
6. Test geometric features only after the baselines are frozen.

---

[← Repository guide](Repository-Guide.md) ·
[Next: Demos and CI →](Demos-and-Deployment.md)
