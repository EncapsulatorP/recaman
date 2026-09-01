# Mechanism-first trace of early Recamán holes

## Question

How were the earliest catalogue holes missed by the exact recurrence, rather
than merely how the catalogue is distributed?

## Finite-run evidence

- Exact recurrence horizon: **10,000,000 steps**.
- Catalogue targets: **103 values** from
  **852,655** through **9,585,306**.
- Adjacent non-catalogue controls: **198**.
- Holes bypassed as an addition candidate at least once:
  **23**.
- Holes with no observed proposal: **80**.
- Total bypass events involving catalogue holes: **23**.
- Adjacent controls visited: **110 /
  198**
  (55.6%).

The recurrence itself decomposed all 10,000,000 transitions into
**4,999,986 legal subtractions**,
**2,121,439 collision-forced additions**, and
**2,878,575 boundary-forced additions**.

## What this means

For these targets, the observed explanation is now inspectable per value:
either the target never became a candidate, or it appeared as the addition
candidate but was bypassed because the subtraction candidate was legal.  A
positive, unvisited subtraction candidate cannot be ignored by Recamán's rule;
it would be chosen immediately.

## What this does not mean

This is not a proof that any target is permanently absent.  Addition
opportunities for a value `m` are complete after step `m`, but a future
subtraction opportunity can still occur beyond the 10,000,000-step
horizon.  The trace therefore establishes finite causal transition history,
not infinite-horizon causation or permanence.

## Reproduce

```bash
python scripts/analyze_hole_mechanisms.py
python scripts/analyze_hole_mechanisms.py --check
```
