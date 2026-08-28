# Selective Refiner Protocol v3

Status: **FROZEN BEFORE V3 DEVELOPMENT EVALUATION — READY_FOR_V3_DEVELOPMENT_EVALUATION**

v3 is a new Legacy121 development experiment motivated by the immutable v1
`DEVELOPMENT_GATE_FAIL` and v2 `V2_DEVELOPMENT_GATE_FAIL`. It does not revise
either result. Its hypothesis is:

> **H3: Cross-model exact agreement is more useful as a safety veto on a
> high-recall single-source deletion score than as a replacement learned
> classifier.**

No neural network is trained in v3. The frozen score backbone is the existing
authoritative v1 `POOLED_SOURCE_AGNOSTIC` model probability `p(DELETE)` for
each original predicted pair.

## Scientific decomposition

- v1 score: error-likelihood and recall signal;
- exact cross-model consensus: protection/safety evidence;
- validation calibration: risk-control mechanism.

The primary cross-model mechanism is only the boolean veto
`support_other_count == 2`. Partner conflict, stem support, zero-support
policies, confidence matrices, source-specific handcrafted rules, additional
MLPs, and Transformers are excluded. The veto uses sequence-independent exact
pair membership in the other two immutable source predictions and requires no
GT or pair confidence.

All three source predictions are required. If any source prediction is
missing, the affected RNA is `ABSTAIN_NO_REFINEMENT`; no support value is
imputed and the RNA is not removed.

## Frozen data, folds, and score realizations

- Data: normalized Legacy121 v1 only.
- RNA folds: the existing frozen five grouped folds, unchanged.
- Score seeds: the existing v1 realizations `17,29,41,53,67`.
- Outcomes: 5 folds × 5 frozen score seeds = 25 matched outcomes.
- Unit: one pair in the immutable original source prediction.
- Labels: exact TP=`KEEP`, exact FP=`DELETE`, used only for validation
  calibration and held-out evaluation.

The v1 backbone is never retrained. All comparisons pair the same fold and
seed. The agreement-only comparator does not depend on seed; repeating it over
the five score-seed slots preserves matched denominators but is not additional
stochastic evidence.

## Conditions

### Control: `V3_BASE`

Reuse the authoritative v1 source-agnostic held-out probabilities and original
validation-selected global threshold. If that threshold does not exist, apply
the frozen v2.0.1 `ABSTAIN_NO_REFINEMENT` behavior.

### Mechanistic ablation: `V3_VETO2_FIXED`

Start from the exact `V3_BASE` threshold. Delete a pair iff:

`p_DELETE >= BASE_threshold AND support_other_count < 2`.

Every support=2 pair is forced `KEEP`. If BASE has no deployable threshold,
abstain without attempting a replacement threshold. This condition isolates
the direct effect of adding the veto to otherwise identical BASE decisions.

### Primary: `V3_VETO2_RECALIBRATED`

For each fold×seed, use validation rows only:

1. force every support=2 pair to `KEEP`;
2. among support=0/1 pairs, consider thresholds
   `0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95`;
3. compute preservation and DELETE F1 over the complete validation pair
   universe, including forced-KEEP support=2 pairs;
4. retain thresholds with overall validation correct-pair preservation
   `>=0.99`;
5. maximize validation DELETE F1;
6. break ties by higher threshold, then fewer edits;
7. apply the selected threshold and fixed veto to the held-out fold.

If no eligible threshold exists, deploy `ABSTAIN_NO_REFINEMENT`. Test labels
or metrics may never select or revise the threshold.

### Secondary comparator: `AGREEMENT_ZERO_SUPPORT_RULE`

Delete an original predicted pair iff `support_other_count == 0`. This
non-learned, GT-free rule uses no score or threshold and tests whether the v1
learned score adds value beyond simple disagreement. It is not the primary v3
condition and cannot authorize external evaluation.

## Abstention and edit semantics

v2.0.1 semantics are unchanged. An abstaining run returns ORIGINAL unchanged:
zero modified pairs/RNAs, beneficial edits, harmful edits, and DELETE recall;
preservation 1; macro/micro ΔF1 0; modification precision NA. Threshold 0.5 is
never used as a fallback.

All active conditions are deletion-only. They cannot add pairs, reassign
partners, recursively rebuild stems, or globally decode a new structure. The
standard deletion identities are hard assertions:

- `beneficial + harmful = modified`;
- `TP_after = TP_before - harmful`;
- `FP_after = FP_before - beneficial`;
- `FN_after = FN_before + harmful`.

## Aggregation

The v2.0.1 definitions are retained exactly:

- event-pooled modification precision;
- event-pooled DELETE recall;
- event-pooled correct-pair preservation;
- unweighted mean of 25 per-run macro ΔF1 values;
- unweighted mean of 25 per-run micro ΔF1 values;
- event-pooled modified-RNA fraction;
- the same definitions within each source;
- matched changes from identical fold×seed outcomes.

Abstentions add no edit events but retain all original FP and TP opportunities
in recall and preservation denominators. Required NA comparisons resolve to
FAIL.

## Frozen primary development gate

Only `V3_VETO2_RECALIBRATED` is eligible. Every criterion must pass.

### Absolute requirements

1. An actual validation-selected threshold exists in 25/25 runs.
2. Pooled modification precision is at least 0.80.
3. Pooled DELETE recall is at least 0.10.
4. Pooled preservation is at least 0.99; every source is at least 0.98.
5. Macro and micro ΔF1 are both strictly positive for at least two sources.
6. Every source counted toward item 5 must modify at least 10% of its eligible
   held-out RNA instances. Descriptive results below this coverage cannot be
   called a useful source effect.

### Matched requirements versus `V3_BASE`

1. Event-pooled preservation is strictly greater than BASE.
2. Event-pooled modification precision is at least BASE.
3. Event-pooled DELETE recall decreases by no more than 0.05 absolute.
4. Mean paired macro ΔF1 difference is at least zero.
5. Mean paired micro ΔF1 difference is at least zero.

BASE has observed edit events, so its event-pooled precision is defined. More
generally, any required NA comparison is a gate failure.

### Source and safety requirements

- At least one of RNAfold or PETfold must have macro ΔF1 >0 and micro ΔF1 >0.
- No source may have preservation <0.98, macro ΔF1 <-0.005, or micro ΔF1
  <-0.005.

Any missing outcome, accounting failure, missing primary threshold, false
criterion, or required NA yields `V3_DEVELOPMENT_GATE_FAIL`. Only all criteria
passing yields `V3_DEVELOPMENT_GATE_PASS` and authorizes a separate external77
v3 evaluation protocol and commit.

## Independence and external lock

v3 was designed after inspecting v1/v2 Legacy121 outcomes. A Legacy121 pass
would therefore be development evidence, never independent generalization.
external77 remains the only currently frozen independent evaluation and is
locked during veto design, threshold design, gate design, and this protocol
freeze. No external77 file or outcome may influence v3. Actual external
evaluation is a separate future task even if v3 passes.

At protocol freeze, no v3 development condition has been executed and no new
network has been trained.
