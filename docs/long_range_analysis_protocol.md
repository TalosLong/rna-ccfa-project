# Legacy121 v1 Pair Sequence-Separation Protocol

Status: **Frozen for Legacy121 v1 descriptive analysis**

Frozen: 2026-08-27

## Definitions and input semantics

For every canonical zero-based pair `(i,j)`, `i < j`:

```text
sequence_separation = j - i
relative_separation = (j - i) / (sequence_length - 1)
```

The relative value is defined only when sequence length is greater than one.
No loop-length correction or other transformed distance is used.

`pair_separation_by_pair.csv` contains separate `ground_truth` and
`prediction` rows. A TP therefore appears twice per normalized record—once in
each role—to preserve structure provenance. Summaries count TP only from the
GT role, so this representation never doubles a metric count. GT rows have
status TP/FN; prediction rows have status TP/FP.

## GT-only threshold selection

Thresholds were selected from 1,676 pairs in the 121 unique Legacy121 GT
structures. Identical GT structures across the three predictors were verified
and counted once. Model predictions and error distributions were excluded from
threshold selection. Quantiles use NumPy's linear method.

The candidate strategies were:

1. Raw-distance GT quantiles at Q25/Q50/Q75/Q90: 11, 20, 32, and 54 nt.
   The `>54` tail contains 166 pairs but only 20 RNAs, so RNA length strongly
   concentrates membership.
2. Relative-distance GT quantiles at Q25/Q50/Q75/Q90: 0.25,
   0.5142857142857142, 0.8, and 0.9333333333333333. The five bins contain
   428, 412, 418, 251, and 167 GT pairs and cover 92, 116, 116, 107, and 100
   RNAs, respectively.
3. A hybrid upper-tail rule requiring relative separation above relative Q90
   and raw separation above raw Q50. It contains 157 pairs from 90 RNAs but
   adds a length-dependent gate without materially improving sample support.

The relative-quantile strategy is primary because it retains broad RNA
coverage while controlling for sequence-length variation. The raw and hybrid
strategies remain audit diagnostics and are not used to optimize observed
model differences.

## Frozen bins and long-range definition

Values equal to a threshold belong to the lower bin:

| Bin | Relative-separation interval | GT pairs | RNAs |
| --- | --- | ---: | ---: |
| `relative_q00_q25` | `(0, 0.25]` | 428 | 92 |
| `relative_q25_q50` | `(0.25, 0.5142857142857142]` | 412 | 116 |
| `relative_q50_q75` | `(0.5142857142857142, 0.8]` | 418 | 116 |
| `relative_q75_q90` | `(0.8, 0.9333333333333333]` | 251 | 107 |
| `relative_q90_q100_long_range` | `(0.9333333333333333, 1]` | 167 | 100 |

The frozen Legacy121 v1 long-range definition is:

```text
relative_separation > 0.9333333333333333  (GT-only Q90)
```

It contains 167 GT pairs (9.9642%) across 100 RNAs. This is a dataset-derived
descriptive stratum, not a universal biological constant.

## Error and stem summaries

Per-bin TP/FP/FN reuse the frozen exact pair partitions. `gt_pair_count` is
TP+FN and `predicted_pair_count` is TP+FP. `fp_fraction_within_model` uses all
FPs for that model as denominator; `fn_fraction_within_model` analogously uses
all FNs. Wrong-partner labels reuse the frozen relation without redefinition.

Stem linkage is descriptive only. Each strict stem is represented by the
median raw and relative separation of its member pairs. Matched relation states
are reported separately for GT and prediction roles; missing and unmatched
stems use their available side. No long-range stem category is defined.

## Limitations

Legacy121 is small and has a distinctive length/structure distribution.
Discrete values and ties make empirical bin counts differ slightly from exact
nominal quantile fractions. These thresholds require validation or refitting
from GT-only data before use on another dataset. This protocol does not test
biological mechanisms, causality, pseudoknots, or downstream 3D effects.
