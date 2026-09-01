# Recamán obstruction anatomy

## Result

The catalogue is not merely becoming more frequent by multiplicative scale.
Its missing values are extremely concentrated in a small number of long runs,
and those long runs occur inside denser event neighbourhoods rather than as
isolated outliers.

- Run-length Gini: **0.9849**.
- Largest 1% of events contain **77.6%** of all catalogued missing values.
- Run length versus nearest-event isolation: **rho = -0.243**, `p = 7.62e-43`.
- Median log-neighbour distance is **5.1%** of the magnitude-matched null (`p = 0.000999`, 1,000 replicates).

## Scale stability

| Equal-log scale third | Events | Range-event share | Mean run | Maximum run | Median isolation gap |
|---|---:|---:|---:|---:|---:|
| early | 132 | 3.8% | 1.0 | 2 | 2,862 |
| middle | 722 | 18.1% | 36.9 | 3,887 | 4,488 |
| late | 2,249 | 19.2% | 556.1 | 368,058 | 28,029 |

## Arithmetic screen

| Divisor | Observed | Uniform expectation | Observed/expected | Holm p | Survives 0.05? |
|---:|---:|---:|---:|---:|---|
| 2 | 50.18% | 50.00% | 1.004 | 1 | no |
| 3 | 32.48% | 33.33% | 0.975 | 1 | no |
| 5 | 19.24% | 20.00% | 0.962 | 1 | no |
| 7 | 14.47% | 14.29% | 1.013 | 1 | no |
| 11 | 7.77% | 9.09% | 0.854 | 0.05721 | no |
| 13 | 7.86% | 7.69% | 1.022 | 1 | no |

**0 of 6**
predeclared divisibility tests survive family-wise correction. This is useful
negative evidence against a simple small-prime explanation of event starts.

## Interpretation boundary

The supported statement is structural: severity concentrates and clusters on
the value axis. The catalogue does not contain survivor times or landing
opportunities, so this analysis cannot identify the causal Recamán state that
creates those clusters.

## Reproduce

```bash
python scripts/analyze_obstruction_anatomy.py
python scripts/analyze_obstruction_anatomy.py --check
```
