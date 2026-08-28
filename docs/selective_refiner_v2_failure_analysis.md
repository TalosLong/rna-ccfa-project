# Selective Refiner v2 Failure Analysis

Status: **FROZEN RETROSPECTIVE LEGACY121 DEVELOPMENT INTERPRETATION**

This document interprets the immutable v1 and v2 development results and the
authoritative v1 `POOLED_SOURCE_AGNOSTIC` held-out score files. It does not
alter either experiment, train another model, evaluate a v3 condition, or
access external77. Legacy121 is development evidence only.

## Why v2 failed

The primary v2 CROSS condition improved safety but did not improve the matched
risk-controlled refinement system as a whole.

| Pooled quantity | BASE | CROSS | CROSS − BASE |
| --- | ---: | ---: | ---: |
| Beneficial deletions | 1,571 | 692 | -879 |
| Harmful deletions | 282 | 65 | -217 |
| Modification precision | 0.847814 | 0.914135 | +0.066320 |
| DELETE recall | 0.351848 | 0.154983 | -0.196865 |
| Correct-pair preservation | 0.987173 | 0.997043 | +0.009870 |
| Mean macro ΔF1 | +0.014761 | +0.006780 | -0.007981 |
| Mean micro ΔF1 | +0.018770 | +0.010043 | -0.008727 |

Four aspects must be distinguished.

1. **Feature utility.** CROSS increased event-pooled deletion precision by
   0.0663 and preservation by 0.00987. Agreement evidence therefore contained
   useful information about deletion risk.
2. **Excessive conservatism.** CROSS removed 879 fewer false-positive pairs;
   DELETE recall fell by 0.1969, far beyond the frozen allowed drop of 0.02.
   The resulting macro and micro gains were positive but substantially smaller
   than BASE.
3. **Calibration/deployability.** Only 8/25 primary CROSS runs obtained an
   actual validation-safe global threshold, versus the mandatory 25/25.
   Abstention correctly protected structures but could not satisfy the
   deployability criterion.
4. **Source effect.** RNAfold and PETfold changed from weakly negative BASE
   effects to weakly positive CROSS effects. trRosettaRNA2, however, lost most
   of BASE's useful recall and structure gain. The pooled precision gain did
   not compensate for the lost structure-level benefit.

The immutable decision remains `V2_DEVELOPMENT_GATE_FAIL`.

## Source decomposition

| Source | Quantity | BASE | CROSS | Change |
| --- | --- | ---: | ---: | ---: |
| RNAfold | Beneficial / harmful | 48 / 90 | 74 / 25 | +26 / -65 |
|  | Modification precision | 0.347826 | 0.747475 | +0.399649 |
|  | DELETE recall | 0.043636 | 0.067273 | +0.023636 |
|  | Preservation | 0.987780 | 0.996606 | +0.008826 |
|  | Macro / micro ΔF1 | -0.002059 / -0.003661 | +0.000379 / +0.001671 | +0.002439 / +0.005332 |
| PETfold | Beneficial / harmful | 118 / 108 | 94 / 23 | -24 / -85 |
|  | Modification precision | 0.522124 | 0.803419 | +0.281295 |
|  | DELETE recall | 0.097925 | 0.078008 | -0.019917 |
|  | Preservation | 0.985236 | 0.996856 | +0.011620 |
|  | Macro / micro ΔF1 | -0.000346 / -0.001480 | +0.001492 / +0.002830 | +0.001838 / +0.004309 |
| trRosettaRNA2 | Beneficial / harmful | 1,405 / 84 | 524 / 17 | -881 / -67 |
|  | Modification precision | 0.943586 | 0.968577 | +0.024990 |
|  | DELETE recall | 0.650463 | 0.242593 | -0.407870 |
|  | Preservation | 0.988501 | 0.997673 | +0.009172 |
|  | Macro / micro ΔF1 | +0.046689 / +0.059598 | +0.018469 / +0.024580 | -0.028220 / -0.035017 |

RNAfold received the largest precision improvement, but its absolute edit
coverage remained small. PETfold crossed from slightly negative to slightly
positive structure effect. trRosettaRNA2 still supplied the largest CROSS
gain, but its beneficial deletions fell from 1,405 to 524 and its macro/micro
effect fell by 0.0282/0.0350.

## Where BASE edits conflict with consensus

Every deletion made by the authoritative v1 source-agnostic BASE under v2.0.1
abstention semantics was annotated using only the two other immutable source
predictions. Counts are fold×seed edit events; repeated score seeds are
separate development events.

| Other-model support | BASE deletions | Beneficial | Harmful | Precision | Share of harmful | Share of beneficial |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1,403 | 1,384 | 19 | 0.9865 | 6.74% | 88.10% |
| 1 | 221 | 169 | 52 | 0.7647 | 18.44% | 10.76% |
| 2 | 229 | 18 | 211 | 0.0786 | 74.82% | 1.15% |

The mechanistic result is unusually concentrated: protecting support=2 pairs
would intercept 211 of 282 BASE harmful deletions while also preventing only
18 of 1,571 beneficial deletions. Source-specific support=2 harmful/beneficial
counts are RNAfold 68/6, PETfold 90/6, and trRosettaRNA2 53/6. The complete
source table is machine-readable in `base_edit_support_breakdown.csv`.

This is not a v3 outcome. It is a retrospective audit that motivates one fixed
mechanism for prospective grouped development evaluation.

## Interpretation

The evidence supports the narrower interpretation that exact cross-model
consensus is primarily a **KEEP/protection signal**, rather than a complete
replacement DELETE classifier. Three observations align:

- support=2 pairs are 97.64% correct in the full Legacy121 pair inventory;
- most BASE harmful deletions, but almost none of its beneficial deletions,
  occur in the support=2 stratum;
- replacing the score model with CROSS features increased safety but severely
  reduced recall and structure gain.

This interpretation does not prove that a veto will pass a development gate.
It justifies freezing the minimal v3 test: retain the high-recall v1 score,
use exact three-model consensus only as a hard safety veto, and retain
validation-only risk calibration.

## Scientific limits

v1 and v2 remain failed preregistered baselines. v3 is explicitly motivated by
their Legacy121 outcomes, so Legacy121 can no longer provide independent
evidence. No model-agnostic, cross-dataset, or external generalization claim is
supported. external77 remains untouched and locked.
