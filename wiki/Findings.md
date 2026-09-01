# Findings

[Home](Home.md) · [Concepts](Concepts-and-Scope.md) ·
[Data](Data-and-Provenance.md) · [Methods](Methods-and-Validation.md) ·
[Reproduce](Reproducing-the-Research.md)

The strongest conclusions are empirical. Values below come from checked-in
catalogues and saved result files; they are not asymptotic proofs.

## Value side: catalogued holes

Structural totals derived from [`obstructions.txt`](https://github.com/EncapsulatorP/recaman/blob/main/obstructions.txt):

| Measurement | Value |
| --- | ---: |
| Expanded catalogue values | 1,277,400 |
| Encoded events | 3,103 |
| Singleton events | 2,535 |
| Range events | 567 |
| Smallest event start | 852,655 |
| Largest event start | 4,293,242,951 |
| Longest encoded range | 368,058 values |
| Values concentrated in 104 runs of at least 1,001 | 97.2% |

These totals describe the file exactly. Whether each value remains unvisited
for all future time is a separate question.

### Predictive measurements

| Experiment | Evaluation | Result | Interpretation |
| --- | --- | ---: | --- |
| Version C, dataset `D` | Forward CV, purged, time-local controls | Mean AUC **0.7588** | Best leakage-reduced value-side signal |
| Random feature search | Random-forest CV | Mean AUC **0.6633** | Moderate separation on a saved 194,358-positive run |
| Random feature search | Best linear code | AUC **0.5994** | Weak-to-moderate single-projection signal |
| Version C, `A/B/C` | Endpoint and anchor tasks | Mean AUC **0.994–0.996** | Easier retrospective discrimination |

Dataset `D` fold AUCs are `0.7884`, `0.7569`, `0.7863`, `0.7618`, and
`0.6997`.

### Why 0.7588 is more informative than 0.99

The `A/B/C` tasks separate known event anchors from broad controls. Raw value,
position, and event geometry can make that easy. Dataset `D` instead models
gap dynamics with forward-chaining validation, a purge between train and test,
and controls built only from context visible at the time.

The lower score is therefore closer to the forecasting question. It still
does not justify a per-number verdict: AUC measures ranking across a dataset,
not proof that a particular integer will never be visited.

## Process side: obstruction bits

Measurements from
[`outputs/recaman_wheel_results.json`](https://github.com/EncapsulatorP/recaman/blob/main/outputs/recaman_wheel_results.json)
at `N = 10,000,000`:

| Measurement | Value |
| --- | ---: |
| `q_210` | 0.500007 |
| `q_321` | 0.499996 |
| `|q_210 - q_321|` | 0.000011 |
| `q(b(n)=1 given b(n-1)=0)` | 0.998919 |
| `q(b(n)=1 given b(n-1)=1)` | 0.001087 |
| Same-bit phase-slip rate | 0.001084 |
| Same-bit pairs | 10,839 of 9,999,999 |
| Saved bit-history accuracy | 0.99645 |

The proposed two-state `Theta_3` wheel is falsified as a predictor of the real
obstruction bit. Previous-bit conditioning is overwhelmingly stronger: the
stream nearly alternates, interrupted by rare same-bit defects.

This sharpens rather than closes the problem. A baseline can predict the usual
alternation; it does not identify where the defects will occur.

## Geometry and broader models

The delay, arc-lift, carry-wheel, Grassmannian, and Markov-shadow views are
exploratory. They are useful for proposing features and visualising
trajectories, but no checked-in result currently turns them into a proved
mechanism for absolute holes or a held-out locator for phase slips.

## Bottom line

- **Supported:** catalogued holes have measurable structure under honest
  controls; the process bit is near-alternating; the `Theta_3` predictor fails.
- **Suggested:** some catalogue values may be exceptionally persistent or
  absolute, and local gap state may contain more signal.
- **Open:** permanence, a reproducible catalogue horizon, per-number inference,
  and predictive localisation of rare phase slips.

---

[← Concepts and scope](Concepts-and-Scope.md) ·
[Next: Data and provenance →](Data-and-Provenance.md)
