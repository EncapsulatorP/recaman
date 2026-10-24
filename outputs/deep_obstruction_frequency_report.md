# Deep Recamán obstruction frequency test

## Result: catalogue-level proxy supported

Across 24 equal-width `log10(value)` bins from `852,655` to `2^32`, the number
of catalogued obstruction events increases with multiplicative value scale at
every predeclared run-length threshold. All five one-sided permutation tests
remain significant after Holm correction.

| Minimum contiguous run | Events | Spearman ρ | Holm p | Early-half events | Late-half events | Late/early | Verdict |
|---:|---:|---:|---:|---:|---:|---:|---|
| ≥ 1 | 3,103 | 0.905 | 0.0005 | 415 | 2,688 | 6.48× | supports |
| ≥ 2 | 567 | 0.833 | 0.0005 | 75 | 492 | 6.56× | supports |
| ≥ 10 | 184 | 0.702 | 0.0005999 | 23 | 161 | 7.00× | supports |
| ≥ 100 | 168 | 0.685 | 0.0005999 | 21 | 147 | 7.00× | supports |
| ≥ 1,000 | 104 | 0.690 | 0.0005999 | 3 | 101 | 33.67× | supports |

Event severity also has a small positive association with scale:
`Spearman(log10(start), log10(length)) = 0.101`
(`p = 1.989e-08`).

An exploratory bin-count sensitivity check preserves a positive association at
every depth threshold:

| Equal-log bins | Minimum ρ across thresholds | Maximum ρ |
|---:|---:|---:|
| 16 | 0.714 | 0.939 |
| 20 | 0.750 | 0.950 |
| 28 | 0.612 | 0.895 |
| 32 | 0.632 | 0.909 |

## Interpretation

The evidence supports the repository's narrow descriptive hypothesis:
catalogued obstruction events—and events meeting increasingly deep contiguous-
run thresholds—occur more often per equal multiplicative value interval after
the first known hole. This can coexist with declining events per fixed million
integers because logarithmic bands contain progressively wider linear ranges.

## Boundary of the result

This does **not** yet test why the pattern occurs. Chaffin's hole catalogue has
no denominator for Recamán landing opportunities and no survivor-time depth.
Consequently, visited-set saturation remains a mechanism hypothesis. Testing
it requires Chaffin's landing stream or an equivalent trajectory summary
aligned with the hole candidates.

## Reproduce

```bash
python scripts/test_deep_obstruction_frequency.py
```

Source: `obstructions.txt` (`SHA-256 5cbf0ada7b909a937282a19281f8d9c4de3ce3cdbcc4f8f4677852e40fd6497e`),
verified against https://benchaffin.com/recaman/rec-holes-2_32.txt.
