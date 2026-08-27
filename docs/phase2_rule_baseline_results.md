# Phase 2 Rule-Based Baseline v1 — Legacy121 Pilot

## Scope

This is a pilot/feasibility evaluation on the same Legacy121 v1 dataset used
for Phase 1 characterization: 121 RNAs and three historical source predictors.
No predictor was rerun, no pair confidence was used, and no rule was changed
after results were observed. The six deployable conditions are exactly
`ORIGINAL`, `R1`, `R2`, `R3`, `R1_R2`, and `R1_R3`.

All rules used the immutable original prediction snapshot. GT was consulted
only after edits to annotate a deletion as beneficial (former FP) or harmful
(former TP) and to run the frozen shared evaluator. This pilot is not
independent generalization evidence, a model-agnostic result, or a paper-level
performance claim. No significance testing was performed.

## Complete model-condition results

P/R/F1 entries are `Precision / Recall / F1`. ΔF1 entries are relative to the
same model's `ORIGINAL`. `B/H` gives beneficial/harmful edit counts; Benefit is
the pooled beneficial edit fraction. Preservation is pooled
`TP_after / TP_before`. Undefined edit fractions for zero-edit conditions are
reported as `NA`, not zero.

| Model | Condition | Macro P/R/F1 | Micro P/R/F1 | Macro/Micro ΔF1 | Edits (B/H) | Benefit | Preservation | Modified RNAs | Frozen outcome |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| RNAfold | ORIGINAL | 0.906937/0.913867/0.905818 | 0.870053/0.878878/0.874443 | +0.000000/+0.000000 | 0 (0/0) | NA | 1.000000 | 0 | REFERENCE |
| RNAfold | R1 | 0.909061/0.909408/0.904392 | 0.872619/0.874702/0.873659 | -0.001426/-0.000784 | 13 (6/7) | 46.15% | 0.995248 | 11 | NO USEFUL SIGNAL |
| RNAfold | R2 | 0.917534/0.888907/0.896634 | 0.883405/0.854415/0.868668 | -0.009184/-0.005775 | 72 (31/41) | 43.06% | 0.972166 | 28 | NO USEFUL SIGNAL |
| RNAfold | R3 | 0.906937/0.913867/0.905818 | 0.870053/0.878878/0.874443 | +0.000000/+0.000000 | 0 (0/0) | NA | 1.000000 | 0 | NO USEFUL SIGNAL |
| RNAfold | R1_R2 | 0.919682/0.884449/0.895088 | 0.886194/0.850239/0.867844 | -0.010729/-0.006599 | 85 (37/48) | 43.53% | 0.967413 | 35 | NO USEFUL SIGNAL |
| RNAfold | R1_R3 | 0.909061/0.909408/0.904392 | 0.872619/0.874702/0.873659 | -0.001426/-0.000784 | 13 (6/7) | 46.15% | 0.995248 | 11 | NO USEFUL SIGNAL |
| PETfold | ORIGINAL | 0.895256/0.907779/0.896849 | 0.858568/0.872912/0.865680 | +0.000000/+0.000000 | 0 (0/0) | NA | 1.000000 | 0 | REFERENCE |
| PETfold | R1 | 0.898287/0.907467/0.898304 | 0.862456/0.871718/0.867062 | +0.001454/+0.001382 | 10 (8/2) | 80.00% | 0.998633 | 8 | USEFUL SIGNAL |
| PETfold | R2 | 0.908073/0.887319/0.891037 | 0.874083/0.853222/0.863527 | -0.005812/-0.002154 | 68 (35/33) | 51.47% | 0.977444 | 28 | TRADE-OFF |
| PETfold | R3 | 0.895256/0.907779/0.896849 | 0.858568/0.872912/0.865680 | +0.000000/+0.000000 | 0 (0/0) | NA | 1.000000 | 0 | NO USEFUL SIGNAL |
| PETfold | R1_R2 | 0.911522/0.887007/0.892472 | 0.878229/0.852029/0.864930 | -0.004378/-0.000750 | 78 (43/35) | 55.13% | 0.976077 | 31 | TRADE-OFF |
| PETfold | R1_R3 | 0.898287/0.907467/0.898304 | 0.862456/0.871718/0.867062 | +0.001454/+0.001382 | 10 (8/2) | 80.00% | 0.998633 | 8 | USEFUL SIGNAL |
| trRosettaRNA2 native SS | ORIGINAL | 0.790564/0.912085/0.842871 | 0.771791/0.871718/0.818717 | +0.000000/+0.000000 | 0 (0/0) | NA | 1.000000 | 0 | REFERENCE |
| trRosettaRNA2 native SS | R1 | 0.805164/0.900664/0.845366 | 0.790710/0.863365/0.825442 | +0.002495/+0.006725 | 63 (49/14) | 77.78% | 0.990418 | 43 | USEFUL SIGNAL |
| trRosettaRNA2 native SS | R2 | 0.795265/0.899574/0.838595 | 0.780422/0.860979/0.818723 | -0.004276/+0.000007 | 44 (26/18) | 59.09% | 0.987680 | 16 | TRADE-OFF |
| trRosettaRNA2 native SS | R3 | 0.794750/0.912085/0.845196 | 0.780032/0.871718/0.823331 | +0.002325/+0.004614 | 20 (20/0) | 100.00% | 1.000000 | 17 | USEFUL SIGNAL |
| trRosettaRNA2 native SS | R1_R2 | 0.810511/0.888152/0.841183 | 0.800112/0.852625/0.825534 | -0.001689/+0.006818 | 107 (75/32) | 70.09% | 0.978097 | 54 | TRADE-OFF |
| trRosettaRNA2 native SS | R1_R3 | 0.809626/0.900664/0.847765 | 0.799448/0.863365/0.830178 | +0.004894/+0.011461 | 83 (69/14) | 83.13% | 0.990418 | 51 | USEFUL SIGNAL |

## RQ1 — Is there useful observable deletion signal?

Yes, but only as a limited, source-dependent feasibility signal. Structure-only
R1 satisfies the preregistered `USEFUL SIGNAL` criterion for PETfold and
trRosettaRNA2, but not RNAfold. Sequence-plus-structure R3 is useful for
trRosettaRNA2 and does not fire for the other two models. No atomic rule is
useful across all three predictors.

## RQ2 — Which rules have high modification precision?

R3 has 20/20 beneficial deletions for trRosettaRNA2, but it fires in only 17 of
121 RNAs and never fires for RNAfold or PETfold. This separates high accuracy
when fired from limited, source-skewed coverage. R1 is 8/10 beneficial for
PETfold and 49/63 for trRosettaRNA2, but only 6/13 for RNAfold. R2 has lower
pooled beneficial fractions of 43.06%, 51.47%, and 59.09%.

## RQ3 — Does any rule improve F1 while preserving correct pairs?

R1 improves both macro/micro F1 for PETfold (+0.001454/+0.001382) and
trRosettaRNA2 (+0.002495/+0.006725), preserving 99.86% and 99.04% of original
TP pairs. R3 improves trRosettaRNA2 macro/micro F1
(+0.002325/+0.004614) while preserving every original TP. The largest observed
gains are for trRosettaRNA2 R1_R3 (+0.004894 macro, +0.011461 micro), with
83.13% beneficial edits and 99.04% TP preservation. RNAfold has no condition
with positive macro and micro ΔF1.

## RQ4 — Shared or source-specific effects?

Effects are source-specific. R1 ranges from 46.15% beneficial on RNAfold to
80.00% on PETfold and 77.78% on trRosettaRNA2. R3 trigger coverage is
RNAfold/PETfold/trRosettaRNA2 = 0/0/20 pairs, so its trRosettaRNA2 result cannot
support a shared or model-agnostic claim. `R1_R3` is identical to R1 for
RNAfold/PETfold because R3 never fires there.

## RQ5 — Is R2 harmful as expected?

R2 confirms the intended high-risk characterization. It reduces macro F1 for
all three models and micro F1 for RNAfold/PETfold. For trRosettaRNA2, micro F1
changes by only +0.000007 while macro F1 decreases by 0.004276, a clear
macro/micro divergence rather than a useful shared improvement. RNAfold is
most directly harmed: 41/72 deletions remove TP pairs and macro/micro F1 fall
by 0.009184/0.005775. The `R1_R2` combination produces the largest RNAfold loss
(-0.010729/-0.006599).

## RQ6 — Proceed to a learned selective refiner?

The pilot supports proceeding to **protocol design and controlled evaluation**
of a learned selective refiner: some observable triggers have favorable
beneficial/harmful ratios, while the same trigger can be useful for one source
and harmful or inactive for another. This is exactly a need for selection, not
evidence that selection is already learnable or that a learned refiner will
generalize. Leakage-safe splits, an independent evaluation dataset, and a
frozen cross-source protocol remain prerequisites before implementation or
stronger claims.

## Validation and limitations

- All 363 normalized records and 2,178 sample-condition evaluations passed
  canonical input/output validation.
- Frozen Original counts were reproduced exactly for every model.
- Every deletion-only TP/FP/FN accounting identity passed.
- The edit log contains 666 unique record-condition-pair deletions.
- Observable trigger regressions match the frozen pre-evaluation audit.
- Undefined fractions remain null/empty rather than zero.
- No pair confidence, source inference, significance test, pair addition,
  partner reassignment, learned model, or pseudoknot-specific logic was used.
