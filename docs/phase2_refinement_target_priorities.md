# Phase 2 Refinement Target Priorities

Status: **Frozen target priorities; edit rules are not yet defined**

Basis: Legacy121 v1, 121 RNAs, RNAfold/PETfold/trRosettaRNA2 native SS.
Counts from different analysis units are never ranked together.

## Priority criteria

Targets are assessed by frequency, cross-model presence, operational clarity,
whether a deterministic edit could be specified, destructive-edit risk,
available confidence, and later suitability for selective refinement. Historical
RNAfold/PETfold records expose no retained pair confidence; trRosettaRNA2 has
normalized pair scores, so confidence-dependent rules would not be uniformly
available in the first baseline.

## PRIORITY A — first specification candidates

### `stem_extension`: conservative boundary trimming

Extension occurs in 44/335 RNAfold, 42/335 PETfold, and 103/335 trRosettaRNA2
GT-side stem dispositions. Extension stems contain 50, 49, and 146 FP pairs,
respectively. The state has explicit outer/inner/both boundaries and suggests a
minimal deletion-only target. The main risk is trimming a correct boundary when
the error state cannot be identified without GT; Phase 2 must therefore freeze
an observable trigger and measure correct-pair preservation.

### `unmatched_predicted_stem`: cautious removal baseline

Unmatched rates are similar across models: 42/326 (12.88%), 44/312 (14.10%),
and 36/295 (12.20%). These stems contain 142, 146, and 125 FP pairs. Removal is
operationally simple, but “unmatched” is an evaluation state requiring GT and
cannot itself be used at inference. A practical structural proxy may delete TP
pairs or GT-singleton-overlapping pairs; this target therefore requires a
naive, explicitly high-risk removal baseline rather than presumed correction.

## PRIORITY B — important but not first minimal edits

### Pure false-positive pairs

Pure FP comprises 40.91%, 43.57%, and 60.88% of FP pairs. It is frequent and
especially prominent for trRosettaRNA2, but the frozen label is unavailable
without GT and RNAfold/PETfold lack historical confidence. A later rule may use
an observable isolation or confidence proxy only after its semantics are
frozen.

### `wrong_partner`

Wrong-partner events comprise 59.09%, 56.43%, and 39.12% of FP pairs. They are
shared and structured, but replacing a partner requires choosing an alternative
pair and can destroy a correct local configuration. Deletion-only diagnosis may
be tested before any reassignment rule.

### `stem_missing`

Missing-stem rates are stable at 13.73%, 14.33%, and 11.94% of GT stems.
Recovery requires candidate generation/addition rather than conservative
cleanup, and retained confidence is not uniformly available. It is important
for later recall-oriented refinement but is not a first deletion baseline.

## DEFER

- `stem_truncation`: only 5/4/1 instances; restoration requires adding pairs.
- `stem_shift`: only 2/2/6 isolated instances; partner reassignment is risky.
- isolated `complex_mismatch`: only 1/1/5 instances and no simple edit follows
  from the residual label.
- ambiguous components: 10/35/68 GT stems are involved, but the frozen protocol
  intentionally declines pairwise assignment; simple forced edits would violate
  that uncertainty.
- pseudoknot-aware targets: moved to a separate side track requiring predictors
  with explicit crossing-pair output capability.

## Frozen Phase 2 hypotheses

### H1 — extension trimming

A conservative, observable rule targeting predicted stem-boundary excess can
increase Precision while preserving most TP pairs. Endpoints: ΔPrecision,
ΔRecall, ΔF1, correct-pair preservation rate, beneficial/harmful edit fractions,
and modified-pair count.

### H2 — unmatched-stem removal trade-off

Naive removal of an observable proxy for unmatched predicted stems may improve
Precision but risks Recall loss. Endpoints: ΔPrecision, ΔRecall, ΔF1,
correct-pair preservation rate, beneficial/harmful edit fractions, and number of
removed pairs.

### H3 — source-dependent rule response

Identical frozen rules will have different effects across source predictors
because the observed conditional error profiles differ, especially for
trRosettaRNA2 extension and pure-FP patterns. Endpoints: all metric deltas and
edit-quality fractions reported separately by source model.

These are testable hypotheses, not empirical results. The next task must freeze
the minimal rule specification before implementing any edit.
