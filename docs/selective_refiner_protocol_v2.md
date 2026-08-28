# Selective Refiner Protocol v2

Status: **FROZEN BEFORE V2 TRAINING**

v2 is a new Legacy121 development experiment motivated by the immutable v1
`DEVELOPMENT_GATE_FAIL`. It does not revise v1 results or gates. The hypothesis
is:

> **H2: GT-free cross-model agreement features improve risk-controlled
> selective refinement over the matched frozen v1 single-source topology
> feature model.**

The retrospective audit status is `CROSS_MODEL_SIGNAL_PROMISING`; H2 itself
remains untested until v2 is trained under this protocol.

## Scope and locked data

- Development data: normalized Legacy121 v1 only.
- Splits: the existing frozen five RNA-group folds, unchanged.
- Seeds: `17,29,41,53,67`.
- Pair unit and labels: unchanged from v1; original predicted pair, KEEP=TP,
  DELETE=FP, with DELETE positive and no FN examples.
- external77 is locked and may be evaluated only after the primary v2
  Legacy121 development gate passes. It cannot affect features, calibration,
  architecture, thresholds, or criteria.

## Feature conditions

`V2_BASE` is the exact v1 feature set. `V2_CROSS_MODEL` adds prediction-only
agreement features computed from the two other source predictions.

The symmetric source-agnostic additions are:

- exact support count among other models, any-support, and all-three agreement;
- endpoint-i and endpoint-j different-partner conflict counts and any conflict;
- inward/outward neighboring-coordinate support counts;
- whether one other model supports the complete source strict stem;
- fraction of source-stem pairs supported by at least one other model.

Source-aware variants additionally receive named support flags for RNAfold,
PETfold, and trRosettaRNA2. The source's own named flag is a structural zero;
these flags are prohibited in source-agnostic variants because the zero
position implicitly identifies the source. Endpoint exact-agreement counts
were audited but excluded because the one-partner constraint makes them exact
duplicates of exact support count.

All features require only sequence and three immutable prediction pair sets.
They require no GT, labels, confidence matrix, family, or external data. A
missing source causes `ABSTAIN_NO_REFINEMENT`; values are not imputed and the
RNA is not dropped. Thus primary v2 requires a complete three-source matrix.

| Feature family | Required predictions | Symmetric? | Implicit source identity | Confidence needed? |
| --- | --- | --- | --- | --- |
| support count / any / all-three | source + two others | yes | no | no |
| endpoint conflicts | source + two others | yes | no | no |
| inward/outward support | two others, relative to source coordinates | yes | no | no |
| whole-stem/fraction support | source stem + two others | yes | no | no |
| named per-predictor support flags | named three-source matrix | no | yes; source-aware only | no |

If any required predictor fails, all cross-model feature families are
unavailable and the cross-model condition abstains. This policy avoids making
the number of available predictors an uncontrolled source/domain feature.

## Architecture and optimization

To isolate the feature contribution, v2 keeps the v1 MLP and training protocol:
two width-64 hidden layers, ReLU, dropout 0.10, one DELETE logit, class-weighted
BCE, AdamW (`lr=1e-3`, weight decay `1e-4`), batch size 256, maximum 100 epochs,
patience 12, gradient clipping 5.0, train-only standardization/class weights,
and validation-only checkpoint/threshold selection. The frozen threshold grid
remains `0.50,0.55,...,0.95`. No Transformer is permitted in primary v2.

## Factorial comparison

The design is feature set × source identity × calibration:

- features: `BASE` versus `CROSS`;
- representation: `SOURCE_AGNOSTIC` versus `SOURCE_AWARE`;
- calibration: `GLOBAL` (V2A) versus `SOURCE_CONDITIONAL` (V2B).

Every condition uses identical folds and seeds. The primary comparison is
`V2A_CROSS_SOURCE_AGNOSTIC_GLOBAL` against
`V2A_BASE_SOURCE_AGNOSTIC_GLOBAL`. Source-aware and V2B conditions are
secondary factorial analyses and cannot rescue primary failure.

V2A retains v1 global threshold semantics: on pooled validation rows choose
the threshold with preservation >=0.99 that maximizes DELETE F1, with the v1
tie breaks. V2B selects one threshold per source using that source's validation
rows, requiring validation preservation >=0.99 and using the same objective,
grid, and tie breaks. All three source thresholds must exist before the run is
deployable. Source-conditional calibration is separated because v1 showed
large source calibration differences; it is not merged with the feature test.

LOMO is not a primary v2 condition. The fixed three-predictor evidence contract
does not test generalization to an unseen fourth predictor, and v1 LOMO failed.
Claim C therefore remains unsupported.

## Aggregation and frozen gate

All 25 fold×seed rotations of the primary condition must yield deployable
thresholds. Gate metrics are unweighted arithmetic means over those 25 held-out
runs. Cross-versus-base effects are paired by identical fold and seed and use
the mean paired difference.

The primary condition passes only if all are true:

1. pooled modification precision >=0.80 and DELETE recall >=0.10;
2. pooled correct-pair preservation >=0.99 and every source >=0.98;
3. macro and micro ΔF1 are both positive for at least two sources;
4. any useful-source statement requires >=10% of that source's RNAs modified;
5. versus matched BASE, pooled modification precision improves by >=0.02,
   preservation by >=0.002, and DELETE recall decreases by no more than 0.02;
6. paired mean pooled macro and micro ΔF1 gains are each strictly positive;
7. at least one of RNAfold/PETfold has positive macro and micro ΔF1, and both
   metrics improve strictly over its matched BASE result, preventing a pass
   explained solely by trRosettaRNA2;
8. no source has macro or micro ΔF1 below -0.005, loses more than 0.005 in
   either metric versus BASE, or falls below 0.98 preservation.

Failure of any criterion is `V2_DEVELOPMENT_GATE_FAIL`. Only
`V2_DEVELOPMENT_GATE_PASS` from the primary source-agnostic/global condition
authorizes a separately locked external77 evaluation. Secondary source-aware
or source-conditional success cannot substitute.

## Interpretation and claim hierarchy

- Claim A—selective refinement can identify high-risk predicted pairs—is
  partially supported on Legacy121.
- Claim B—cross-model agreement provides transferable correction evidence—is
  the v2 hypothesis, not an established result.
- Claim C—the refiner generalizes to unseen source predictors—is unsupported.

“Cross-Model Agreement-Guided Selective Refinement” is the more precise
near-term experimental framing because it names the observable being tested.
The broader “Evidence-Guided” framing may remain the project umbrella, but is
not yet supported as a paper-level claim. The project is not renamed here.
