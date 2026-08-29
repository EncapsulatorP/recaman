---
title: Recamán Obstruction Compression Lab
emoji: 🗜️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.50.0
python_version: "3.11"
app_file: app.py
license: mit
pinned: false
short_description: Lossless compression of Recamán holes and phase slips
tags:
  - mathematics
  - number-theory
  - recaman
  - oeis-a005132
  - chaffin-holes
  - reproducible-research
---

# 🗜️ Recamán Obstruction Compression Lab

**How many bits does Recamán's structure really save?**
Certified holes · range codecs · phase-slip codes · held-out predictive compression

[![KuggUK](https://img.shields.io/badge/KuggUK-kugguk.com-0969da)](https://kugguk.com)
[![Research](https://img.shields.io/badge/Research-EncapsulatorP-6f42c1)](https://encapsulatorp.github.io/)
[![Source](https://img.shields.io/badge/Source-recaman__obstructions-00859b)](https://github.com/kugguk2022/recaman_obstructions)
[![Catalogue](https://img.shields.io/badge/Holes-1%2C277%2C399-b14da7)](https://github.com/kugguk2022/recaman_obstructions/blob/main/obstructions.txt)
[![Best honest AUC](https://img.shields.io/badge/best%20honest%20AUC-0.7586-9e671a)](https://github.com/kugguk2022/recaman_obstructions)
[![Variant](https://img.shields.io/badge/variant-Claude.ai-10263d)](https://github.com/kugguk2022/recaman_obstructions/tree/main/apps/claude_ai_holes)

---

## The question

Recamán starts at `a(0) = 0` and, at every step, tries to jump **backward**:

```text
a(n) = a(n-1) - n     if that value is positive and not yet visited
a(n) = a(n-1) + n     otherwise
```

It hops back when it can and forward when it cannot — and it never lands on
everything. An integer the sequence misses **at every step, forever** is an
**absolute hole**. This Space is about the shape of that missing set.

> 🔭 A different quantity from the sibling Space in `apps/space/`, which predicts
> the process-side obstruction bit `b(n)`. A blocked step is **not** a hole.
> Same sequence, different object — the two must not be confused.

---

## What the catalogue looks like

```text
1,277,399 integers that Recamán never reaches
│
├── 3,102 events           · spanning 930,058 → 4,293,242,951
│   ├── 2,535 singletons   · a lone missing integer
│   └──   567 runs         · consecutive missing integers
│
├── 97.2% of the mass      · inside just 104 runs of 1,001+
│   └── longest run        · 368,058 consecutive integers, all missed
│
└── density               · 1 integer in 3,360, across the covered span
```

| 🎨 Tab | What it shows |
| --- | --- |
| **The hole set** | counts, run-length structure, gap percentiles, missing integers per power of ten |
| **Compression engine** | expanded values versus range/delta/general codecs, all with exact round-trip checks |
| **Explore the span** | a density strip you slide across the range, recomputed live for any window |
| **What is predictable** | every measured AUC on one axis, anchored at chance |
| **Method and sources** | the rule, the provenance, the completeness claim, and the boundary with `b(n)` |

---

## The honest part

Compression supplies a hard falsifiable target. A structural claim matters only when
it shortens an exact encoding or reduces held-out code length. The Space compares:

- expanded uint32 hole values;
- fixed-width interval endpoints;
- delta-varint range events;
- zlib, bzip2, and LZMA controls;
- packed process bits and a phase-slip delta codec;
- a train/frozen-test ideal arithmetic-code bound for the inferred alternation model.

Every custom serialized codec is decoded before its result is displayed, and the
decoded obstruction signs must reconstruct the exact final Recamán term.

| Task | Mean AUC | Reading |
| --- | ---: | --- |
| Version C **D** · gap dynamics | `0.7586` | 🟢 the headline — leakage-reduced, forward CV |
| random-matrix · RF cross-validation | `0.6633` | 🟢 194,358 holes vs digit-matched controls |
| random-matrix · best linear code | `0.5994` | 🟢 single projection, 42 features |
| Version C **A / B / C** | `0.99+` | 🟡 easier question — a ceiling, not a result |

**This Space gives no per-number verdict.** Not for your favourite integer, not
for any integer. A best honest separation of `0.7586` is real signal and
nowhere near a test, and pretending otherwise would misrepresent the work.

Three more boundaries, stated plainly:

- 🔒 The catalogue is **complete** over `930,058 – 4,293,242,951` — inside that
  span, an integer that is not listed **is** reached. Outside it, silence.
- 📏 The structural counts are **exact** over the catalogue. The AUCs are
  **measurements** from saved runs, not proofs about the sequence.
- 🧭 The arc picture in *Method and sources* draws the first 40 steps. Nothing
  in that range is a hole — the smallest one here sits at `930,058`.

---

## Provenance

Nothing in this Space is a hand-typed constant.

```text
obstructions.txt                    → holes.txt        (verbatim, byte-identical)
outputs/version_c_*.json            ─┐
outputs/best_obstructions_*.json    ─┴→ results.json   (scripts/sync_claude_ai_holes.py)
holes.txt                            → every count on screen, recomputed at load
```

The structural totals are asserted against the saved
`outputs/version_c_obstructions_results.json` run by the test suite — events,
singletons, ranges, longest run, span endpoints, gap min/max — so the Space
cannot drift from the research that produced it. The hole catalogue itself is
Benjamin Chaffin's certified list of values the sequence never reaches.

| File | Role |
| --- | --- |
| `app.py` | Gradio interface |
| `holes.py` | catalogue parsing and structural summaries |
| `hole_figures.py` | SVG figures and the watermarked poster |
| `theme.py` | the Repo Galaxy palette, shared with the figures |
| `sequence.py` | a short Recamán walk, for the arc picture only |
| `holes.txt` | the hole catalogue, synced verbatim |
| `results.json` | measured model scores, synced from `outputs/` |

---

## Look and feel

Palette lifted from the **Repo Galaxy** artwork on the
[kugguk2022](https://github.com/kugguk2022) profile — neon cyan `#22e0ff` and
amber `#ffb457` over deep-space navy `#07101a`, with magenta and green as
supporting accents. Figures and interface share one token set, so the SVG and
the Gradio chrome are a single design.

Colour never carries meaning on its own: exactly two hues encode anything, and
every mark is labelled beside its swatch. Both data slots clear the
colour-vision and contrast checks in light and dark.

---

## Elsewhere

- **Research:** [encapsulatorp.github.io](https://encapsulatorp.github.io/) · [github.com/EncapsulatorP](https://github.com/EncapsulatorP)
- **Umbrella:** [kugguk.com](https://kugguk.com)
- **This repo:** [recaman_obstructions](https://github.com/kugguk2022/recaman_obstructions)

## License

Released under the MIT License.

<img src="assets/online-presence.svg" alt="Online presence" width="180">

<sub>The "online presence" mark is kugguk project artwork and does not modify or restrict the MIT License.</sub>
