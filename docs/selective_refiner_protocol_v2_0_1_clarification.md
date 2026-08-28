# Selective Refiner Protocol v2.0.1 Clarification

Status: **READY_FOR_V2_TRAINING — CLARIFICATION FROZEN BEFORE TRAINING**

This document resolves one ambiguity in `selective_refiner_protocol_v2.md`.
It changes no v1 result, numerical threshold, fold, seed, model architecture,
or external-data lock. v2 training remains not started.

## Verified ambiguity

The 25 unique `POOLED_SOURCE_AGNOSTIC` threshold files, not the duplicated v1
summary rows, contain 20 deployable runs and five
`NO_DEPLOYABLE_SELECTIVE_THRESHOLD` runs:

`fold_1/seed_17`, `fold_1/seed_29`, `fold_1/seed_41`,
`fold_1/seed_53`, and `fold_1/seed_67`.

For context, `POOLED_SOURCE_AWARE` has 16/25 deployable runs. Its nine
nondeployable identities are all five fold-1 seeds; fold-2 seeds 17, 53, and
67; and fold-4 seed 41. The authoritative reconstruction is
`v1_pooled_threshold_availability_v2_0_1.csv`. No v1 artifact is modified.

## Risk-controlled deployment behavior

For both BASE and CROSS, every fold×seed produces an outcome:

1. If validation selects a threshold satisfying the frozen preservation
   constraint, apply that threshold normally.
2. Otherwise deploy `ABSTAIN_NO_REFINEMENT`: return ORIGINAL unchanged.

Abstention is consistent with the v1/v2 selective design: absence of a safe
validation threshold means the system declines to edit. Threshold 0.5 is not
a fallback and must never replace abstention.

BASE abstention is allowed solely to define all 25 matched comparisons. CROSS
must still obtain an actual validation-selected threshold in 25/25 runs. A
CROSS abstention is recorded as an unchanged outcome but makes the primary
deployability gate fail.

## Abstention metrics

`ABSTAIN_NO_REFINEMENT` has zero beneficial/harmful edits, modified pairs, and
modified RNAs; DELETE recall 0; preservation 1; macro/micro ΔF1 0; and
modification precision NA. NA precision is never converted to zero.

For a matched pair with BASE abstention, macro/micro ΔF1 gains are the CROSS
values minus zero, and the per-run preservation gain is CROSS preservation
minus 1.0.

## Frozen aggregation

The following distinctions are mandatory:

- **Event-pooled modification precision:** total beneficial edits divided by
  total beneficial plus harmful edits over all 25 rotations. Zero-edit runs
  add no events to either count. A zero total denominator is NA.
- **Event-pooled DELETE recall:** total beneficial edits divided by all
  original FP opportunities over 25 rotations. Abstentions retain their FP
  opportunities in the denominator and add zero beneficial edits.
- **Event-pooled preservation:** summed `TP_after / TP_before` counts over all
  rotations. Abstention contributes identical before/after TP counts.
- **Macro/micro ΔF1:** unweighted arithmetic means of the 25 per-run delta
  values. Abstention contributes zero.
- **Modified-RNA fraction:** modified held-out RNA instances divided by all
  eligible held-out RNA instances over 25 rotations. Repeated seeds are
  distinct evaluation instances; abstention contributes zero modified.
- **Per-source metrics:** the same event-pooled definitions within each source
  for precision, recall, preservation, and modified-RNA fraction; per-source
  macro/micro ΔF1 remains an unweighted 25-run mean.

Paired macro/micro ΔF1 and preservation gains are unweighted means of the 25
same-fold/same-seed CROSS-minus-BASE differences. Precision gain is instead
the difference between the two event-pooled precisions. DELETE-recall change
is the difference between event-pooled recalls.

If BASE makes at least one edit over 25 rotations, the frozen precision-gain
gate compares CROSS event-pooled precision against BASE and requires +0.02.
If BASE makes zero edits in all rotations, BASE precision is NA; the comparison
is `NOT_APPLICABLE` and the required gate resolves to **FAIL**, never an
automatic pass. A CROSS zero-edit denominator likewise fails its absolute
precision and recall gates.

## Complete binary gate

All original numerical criteria remain unchanged. Every required gate now
resolves to PASS or FAIL:

- any false criterion, missing primary run, training failure, missing CROSS
  threshold, or required NA comparison gives FAIL;
- all criteria true gives PASS;
- secondary source-aware or source-conditional conditions cannot rescue the
  primary source-agnostic/global condition.

The catastrophic-degradation checks use per-source event-pooled preservation,
per-source 25-run mean macro/micro ΔF1, and paired mean source differences.
The full executable contract is `v2_go_no_go_v2_0_1.json`.

external77 remains locked unless the clarified primary Legacy121 v2 gate
passes. This clarification itself authorizes only v2 Legacy121 training.
