# R3 Reliability Baseline Calibration Amendment

Status: **`FROZEN BEFORE R3 PERFORMANCE EVALUATION`**

Amendment date: 2026-09-03

Original R3 protocol freeze: 2026-09-02

This prospective amendment resolves only the Expected Calibration Error (ECE)
definition left unspecified by the original frozen R3 protocol. It was frozen
before any Legacy121 R3 performance number was generated. It does not change a
baseline, score, score orientation, threshold, split, evaluation universe,
aggregation rule outside ECE, or any other metric definition.

## 1. Eligible scores and orientation

ECE and reliability-bin outputs are permitted only for the three probability-
like scores already authorized by the R3 protocol:

- P0: training-partition DELETE prevalence;
- P1: historical raw `p_delete`, labeled `RAW_UNCALIBRATED`;
- P4: thermodynamic probability-derived DELETE risk
  `1 - P_RNAfold(i,j)`.

The calibration label is `y=1` exactly when an original predicted pair is an
FP/DELETE-positive and `y=0` exactly when it is a TP/KEEP. P2, P3, E1, and E2
are ordinal or binary indicators and must not receive ECE, Brier, or arbitrary
probability mappings.

P4 uses `1-BPP`, never BPP itself, against the DELETE-positive label. Its ECE
describes the mismatch between a thermodynamic pair-probability-derived risk
and empirical FP frequency; it does not establish empirical correctness
calibration.

## 2. Frozen ten-bin ECE

All scores must be finite and lie in `[0,1]`. Invalid values fail closed and
are never clipped.

Use ten equal-width bins with immutable edges:

```text
B0 = [0.0, 0.1)
B1 = [0.1, 0.2)
B2 = [0.2, 0.3)
B3 = [0.3, 0.4)
B4 = [0.4, 0.5)
B5 = [0.5, 0.6)
B6 = [0.6, 0.7)
B7 = [0.7, 0.8)
B8 = [0.8, 0.9)
B9 = [0.9, 1.0]
```

Thus bins are left-closed and right-open except that the final bin includes
`score == 1.0`. Equal-frequency/quantile bins, data-dependent edges, bin
merging, interpolation, and imputation are prohibited.

For non-empty bin `m`:

```text
n_m                  = number of evaluation examples in bin m
mean_score_m         = mean DELETE-risk score in bin m
observed_delete_rate = number of DELETE-positive labels in bin m / n_m
calibration_gap_m    = abs(mean_score_m - observed_delete_rate_m)
ECE contribution     = (n_m / N) * calibration_gap_m
```

The frozen ECE is:

```text
ECE = sum_{m=0}^{9} (n_m / N)
                        * abs(mean_score_m - observed_delete_rate_m)
```

The observed rate is bin-specific and may not be replaced by global positive
prevalence.

All ten bins remain in every reliability artifact. An empty bin has
`count=0`, `weight=0`, `mean_score=NA`, `observed_delete_rate=NA`,
`absolute_gap=NA`, and `ece_contribution=0`.

## 3. Event-pooled and RNA-balanced ECE

`EVENT_POOLED_ECE` applies the frozen ten-bin calculation directly to all
evaluation events in the relevant stratum. Track P events are original
predicted pairs. P1 historical model seeds are evaluated separately and are
not biological replicates.

`RNA_BALANCED_ECE` is calculated by first computing an independent ten-bin
`ECE_r` from all relevant events within each RNA. An RNA with at least one
event has defined `ECE_r`; an RNA without an event has `ECE_r=NA`. The RNA-
balanced value is the unweighted mean of defined `ECE_r` values, accompanied
by `number_of_defined_RNAs`. It is not computed by event-weighting bins across
RNAs.

The same immutable edges apply to pooled, source-wise, fold-wise, and P1 seed-
wise strata.

## 4. Brier and interpretation labels

Brier score retains the original definition:

```text
Brier = (1/N) * sum_i (score_i - y_i)^2
```

P0 is a constant training-prevalence reference against held-out DELETE
frequency and has no ranking interpretation. P1 calibration artifacts are
labeled `RAW_UNCALIBRATED`; R3 performs no temperature, Platt, isotonic, bin,
or other post-hoc calibration. P4 artifacts are labeled as a descriptive
thermodynamic reliability relationship, not an empirical correctness
probability assessment.

## 5. Machine-readable reliability schema

Reliability-bin rows retain:

```text
baseline, track, source, fold, seed_if_applicable, aggregation,
bin_index, bin_left, bin_right, right_inclusive, count, weight,
mean_score, observed_delete_rate, absolute_gap, ece_contribution
```

The amendment state is:

```text
R3_CALIBRATION_AMENDMENT_FROZEN
READY_TO_RESUME_R3_EXECUTION
```
