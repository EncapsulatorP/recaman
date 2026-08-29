# Concepts and scope

[Home](Home.md) · [Findings](Findings.md) ·
[Data](Data-and-Provenance.md) · [Methods](Methods-and-Validation.md) ·
[Reproduce](Reproducing-the-Research.md)

## The sequence

Let `V(n)` be the values already visited before step `n`. Starting from
`a(0) = 0`, Recamán's rule is

```text
candidate = a(n - 1) - n

if candidate > 0 and candidate is not in V(n):
    a(n) = candidate
else:
    a(n) = a(n - 1) + n
```

The rule is deterministic but history-dependent: legality depends on the
entire visited set, not only on the last value.

## What “obstruction” can mean

The repository studies two objects. They share a cause—the legality of the
backward move—but they are not interchangeable.

### Value-side obstruction

A positive integer `h` is an **absolute obstruction** only if
`a(n) != h` for every step `n`. This is an infinite statement. Failing to see
`h` in a finite run establishes only that it is unvisited through the checked
horizon.

The checked-in [catalogue](https://github.com/EncapsulatorP/recaman/blob/main/obstructions.txt)
provides labelled examples for value-side experiments. The following evidence
levels keep the language precise:

| Level | Meaning |
| --- | --- |
| Unseen through `N` | Direct result of a stated finite computation |
| Persistent or long-lasting hole | Still unseen at a comparatively large, stated horizon |
| Catalogued hole | Represented in this repository's input file |
| Candidate absolute obstruction | Hypothesised to remain absent forever |
| Proved absolute obstruction | Permanent absence established mathematically |

The current repository verifies catalogue structure and derived results, but
the catalogue file does not record its generating horizon or a proof
certificate. It therefore supports the middle levels, not the final one.

### Process-side obstruction

Define the step bit

| Bit | Meaning |
| --- | --- |
| `b(n) = 0` | The backward move is legal; the sequence moves down |
| `b(n) = 1` | The backward move is blocked; the sequence moves up |

This bit describes an event at a step. A blocked move does not imply that the
rejected value is absent forever, and a value-side hole is not itself a
blocked step.

## Research scope

The repository asks:

1. Do catalogued holes differ statistically from carefully matched controls?
2. Does local event context predict value-side gap structure?
3. Can the real obstruction bit be predicted without looking into the future?
4. What state explains the rare failures of the near-alternating bit pattern?
5. Can geometric embeddings generate testable hypotheses about those events?
6. What additional evidence would promote a long-lasting hole to a credible
   candidate for absolute obstruction?

It does not currently claim:

- a proof that any listed integer is missed forever;
- a reliable yes/no classifier for an arbitrary integer;
- a closed-form law for the location of phase slips;
- a validated geometric closure of the sequence.

## Why the distinction matters

High scores can answer the wrong question. Identifying a conspicuous range
endpoint after an obstruction event is much easier than forecasting local gap
dynamics, and predicting the next process bit is different again. Each result
in this wiki is labelled by object, dataset, horizon, and validation scheme.

---

[← Home](Home.md) · [Next: Findings →](Findings.md)
