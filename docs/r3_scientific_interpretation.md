# R3 Scientific Interpretation

Status: **FROZEN — `R3_INTERPRETATION_COMPLETE`**

Date: 2026-09-07

Authoritative result basis:

- `docs/reliability_baseline_r3_protocol.md`;
- `docs/reliability_baseline_r3_results.md`;
- `results/reliability_baseline_r3/summaries/r3_summary.json`;
- `results/reliability_baseline_r3/summaries/strongest_baselines.json`;
- `results/reliability_baseline_r3/summaries/source_wise_summary.csv`;
- `results/reliability_baseline_r3/integrity/`.

This interpretation is restricted to the frozen Legacy121 development data,
the R2 v1.0.2 matched evidence universe, and clean symbolic evidence. It does
not report an R4 result, access external77, introduce noisy or real evidence,
or revise any frozen R2/R3 baseline, score, threshold, metric, split, or
evaluation universe.

## Interpretation contract

The statements below use three non-interchangeable labels:

- **EMPIRICAL RESULT**: directly reported by the frozen R3 artifacts.
- **INTERPRETATION**: a bounded scientific reading of those results.
- **R4 HYPOTHESIS / REQUIREMENT**: an unverified, prospectively frozen test for
  R4; it is not an expected result.

No interpretation or hypothesis may be restated as an observed result.

## A. Prediction-only pair reliability contains usable signal

### EMPIRICAL RESULT

Prediction-only P1, P2, and P4 all discriminated DELETE/FP pairs above their
held-out prevalence references. P4 had the strongest discrimination, with
event-pooled/RNA-balanced AUPRC `0.777283/0.915326` and AUROC
`0.913608/0.951250`. P3's fixed policy removed `0.347816/0.489748` of FP under
event-pooled/RNA-balanced aggregation while preserving `0.996771/0.997588` of
original TP.

### INTERPRETATION

Original-prediction topology, cross-predictor agreement, and sequence-derived
thermodynamic support contain information about residual pair error. The R3
result therefore rejects the narrow proposition that prediction-only
reliability is entirely uninformative. It does not establish a source-general
or calibrated correction policy.

### R4 HYPOTHESIS / REQUIREMENT

R4 may reuse prospectively allowed inference-time prediction context, but it
must demonstrate an evidence-conditioned gain over the frozen prediction-only
comparator rather than relabel prediction-only signal as evidence utility.

## B. Strong discrimination is not equivalent to safe selective correction

### EMPIRICAL RESULT

P4 ranked pair errors best but its validation-selected held-out policy achieved
RNA-balanced TP preservation `0.986219`, below the frozen `0.99` requirement.
P1 missed the event-pooled safety requirement, while P2's coarse score could
meet the safety constraint only by selecting delete-none. No held-out threshold
was moved to rescue any result.

### INTERPRETATION

AUPRC and AUROC measure ordering across risk scores; they do not determine
whether a validation-selected threshold remains safe across held-out RNAs.
Class imbalance, tied/coarse scores, calibration error, between-RNA variation,
and predictor-source shift can all convert useful ranking into unacceptable TP
loss. Reliability discrimination and deployed correction utility must therefore
remain separate endpoints.

### R4 HYPOTHESIS / REQUIREMENT

R4 must produce a validation-only operating point that independently satisfies
both event-pooled and RNA-balanced TP preservation. Held-out discrimination
cannot compensate for a failed preservation constraint, and held-out labels
cannot select a rescue threshold.

## C. P3 is the frozen high-preservation prediction-only comparator

### EMPIRICAL RESULT

P3 `V3_VETO2_FIXED` was the only nontrivial prespecified Track P operating
point that satisfied both held-out preservation summaries. Its frozen values
are:

| Quantity | Event-pooled | RNA-balanced |
| --- | ---: | ---: |
| TP preservation | 0.996771 | 0.997588 |
| FP removal | 0.347816 | 0.489748 |
| Modification precision | 0.956346 | 0.965504 |
| Coverage | 0.061399 | 0.055930 |

The historical `V3_DEVELOPMENT_GATE_FAIL` remains unchanged. R3 did not retrain
or retune P3.

### INTERPRETATION

P3 is the frozen comparator because it supplies the strongest eligible
prediction-only correction point under the prespecified R3 selection rule, not
because it has the highest discrimination or because its historical model is
being reclassified as intrinsically non-learned.

### R4 HYPOTHESIS / REQUIREMENT

R4 must exceed P3's frozen FP-removal bars at the same dual-preservation safety
level. Improvement over B0 or E1 alone is insufficient for Gate B.

## D. P3 source dependence limits the allowed claim

### EMPIRICAL RESULT

At the same fixed P3 policy, RNA-balanced FP removal was `0.013109` for
RNAfold, `0.099320` for PETfold, and `0.630129` for trRosettaRNA2. The
RNA-balanced delta F1 was slightly negative for RNAfold and strongly positive
for trRosettaRNA2. P3 is therefore frozen with the flag
`SOURCE_DEPENDENT_COMPARATOR`.

### INTERPRETATION

The pooled P3 benefit is dominated by the source with the highest FP prevalence
and strongest score response. A future pooled improvement could likewise be
misleading if it arose from only one predictor. R3 does not establish
model-agnostic reliability.

### R4 HYPOTHESIS / REQUIREMENT

R4 must use one source-independent policy and report RNAfold, PETfold, and
trRosettaRNA2 separately. Its improvement over P3 must be positive in at least
two sources, including at least one of RNAfold or PETfold; source-specific
held-out thresholds are prohibited. This requirement prevents a single-source
gain from satisfying Gate B.

## E. E1 is safe but coverage-limited

### EMPIRICAL RESULT

E1 `LOCAL_CONFLICT` deleted 5,978 FP pair-realizations and zero TP
pair-realizations. It achieved TP preservation and modification precision of
`1.0` in both aggregation families, but RNA-balanced coverage was only
`0.018623` and RNA-balanced FP removal was `0.142946`.

### INTERPRETATION

Under clean evidence semantics, direct endpoint conflict is a safe deletion
rule. Its utility is inherently local: it cannot identify residual FP outside
the delivered evidence's frozen conflict neighborhood. Perfect precision here
does not imply broad correction capacity.

### R4 HYPOTHESIS / REQUIREMENT

R4 must compare against E1 at `RNA-balanced FP removal = 0.142946` and
`TP preservation = 1.0`. Its scientific value must include safe additional
coverage, especially in the `NON_EVIDENCED` scope, rather than merely relearn
the E1 conflict rule.

## F. E2/B2 exposes correction signal but is not a safe post-hoc policy

### EMPIRICAL RESULT

E2 B2 disagreement achieved event-pooled/RNA-balanced AUPRC
`0.620550/0.778937` and removed `0.645883/0.775728` of FP. Its corresponding
TP preservation was only `0.981767/0.975358`. The full B2 refold also lost
4,752 original TP and introduced 10,823 new FP while making many beneficial
changes.

### INTERPRETATION

Sparse clean evidence contains substantial correction information when
propagated through global refolding. However, B2 changes a larger action space:
it may remove, add, or replace pairs. E2 merely projects B2 disagreement onto
original pairs and inherits B2's collateral TP loss. Neither B2 nor E2 is a
safe deletion-only post-hoc policy at the frozen `0.99` point.

### R4 HYPOTHESIS / REQUIREMENT

R4 must test whether direct access to delivered evidence and original-predictor
context can isolate a safer subset of residual FP. B2 remains a
`FULL_REFOLD_REFERENCE`; R4 and B2 must be compared on the
correction-preservation trade-off, not by delta F1 alone.

## G. R3 supports proceeding to a prospectively frozen R4 test

### EMPIRICAL RESULT

R3 found all three ingredients needed to motivate, but not validate, R4:
prediction context ranks errors; local clean evidence gives perfectly precise
but narrow deletions; and global evidence propagation gives broad but unsafe
correction. No R3 baseline combines broad evidence use with the frozen dual
`0.99` safety requirement and source-consistent improvement.

### INTERPRETATION

There is a specific unresolved correction-preservation gap. This constitutes
reasonable R4 headroom, not evidence that a learned reconciler will succeed.
The simple learned experiment is justified because its failure would also be
informative and would constrain architecture escalation.

### R4 HYPOTHESIS / REQUIREMENT

Proceed to protocol freeze and, only in a later task, implementation/execution
of a simple Evidence Reconciliation Network (ERN). Do not train the historical
Stage E2 protocol and do not access external77.

## H. Minimum scientific question for R4

### R4 HYPOTHESIS / REQUIREMENT

> Can a simple, source-identity-free, deletion-only ERN use sparse clean
> delivered evidence together with inference-time original-prediction context
> to remove more residual FP than the frozen P3 comparator while preserving at
> least 99% of original TP under both event-pooled and RNA-balanced aggregation,
> with improvement not attributable to one predictor source or to model capacity
> without usable evidence?

The frozen primary R4 targets are conjunctive:

```text
event-pooled TP_preservation       >= 0.99
RNA-balanced TP_preservation       >= 0.99
primary RNA-balanced FP_removal    >  0.489748
companion event-pooled FP_removal  >  0.347816
compare with E1 RNA-balanced FP_removal = 0.142946 at TP_preservation = 1.0
improvement must not be driven by a single predictor source
```

## Gate A and frozen interpretation state

R3 does not compare an executed R4 with B2 and therefore cannot decide Gate A.

```text
R3_INTERPRETATION_COMPLETE
R4_HEADROOM_REASONABLE_BUT_UNTESTED
GATE_A_DEFERRED_R4_REQUIRED
```

Gate A is neither PASS nor FAIL. It may be decided only after a separately
executed R4 is compared with the frozen B2 full-refold reference.
