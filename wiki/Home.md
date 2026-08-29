# Recamán Obstruction Research

[Concepts](Concepts-and-Scope.md) · [Findings](Findings.md) ·
[Data](Data-and-Provenance.md) · [Methods](Methods-and-Validation.md) ·
[Reproduce](Reproducing-the-Research.md) · [Repository guide](Repository-Guide.md)

This wiki is the detailed map of the repository. The short
[project README](https://github.com/EncapsulatorP/recaman/blob/main/README.md)
is the landing page; these pages hold the definitions, evidence, methods,
provenance, commands, and open problems.

## Purpose

The project investigates two related but distinct features of Recamán's
sequence:

1. **Value-side gaps:** integers that remain unvisited and may be candidate
   absolute obstructions.
2. **Process-side blocks:** steps where the normal backward move is illegal and
   the sequence must move forward.

The main scientific goal is to distinguish durable structure from finite-run
artifacts. That means using matched controls, temporal validation, saved
measurements, and explicit limits on every claim.

## Choose a route

| Goal | Page |
| --- | --- |
| Learn the rule and the two meanings of obstruction | [Concepts and scope](Concepts-and-Scope.md) |
| See the strongest positive and negative results | [Findings](Findings.md) |
| Audit what the catalogue does—and does not—establish | [Data and provenance](Data-and-Provenance.md) |
| Understand the experimental designs | [Methods and validation](Methods-and-Validation.md) |
| Set up the environment and rerun work | [Reproducing the research](Reproducing-the-Research.md) |
| Locate code, apps, outputs, and papers | [Repository guide](Repository-Guide.md) |
| Explore the unresolved research programme | [Open questions](Open-Questions.md) |
| Use or deploy the Gradio interfaces | [Demos and deployment](Demos-and-Deployment.md) |

## Evidence in one minute

| Statement | Status |
| --- | --- |
| The catalogue contains 1,277,399 values across 3,102 encoded events | Verified from the checked-in file |
| Dataset `D` reaches mean AUC 0.7586 | Measured in a saved forward-validation run |
| The `Theta_3` wheel predicts the real process bit | Falsified in the saved 10-million-step run |
| The process bit nearly alternates, with rare same-bit slips | Strong finite-run observation |
| A listed value is never reached at any future step | Not proved by this repository |

## Terminology policy

The wiki uses **catalogued hole** for a value represented in
[`obstructions.txt`](https://github.com/EncapsulatorP/recaman/blob/main/obstructions.txt).
It uses **candidate absolute obstruction** when discussing the hypothesis of
permanent absence. Until a reproducible horizon and provenance record—or a
mathematical proof—is attached, **long-lasting unvisited value** is the safest
interpretation.

This distinction is expanded in [Concepts and scope](Concepts-and-Scope.md) and
[Data and provenance](Data-and-Provenance.md).

## Publishing this wiki

The canonical pages are versioned in the repository's `wiki/` directory so
changes can be reviewed with the code. GitHub's Wiki tab uses the separate
`recaman.wiki.git` repository; the contents of this directory, including
`_Sidebar.md` and `_Footer.md`, are ready to sync there when the Wiki is
enabled.

---

[Next: Concepts and scope →](Concepts-and-Scope.md)
