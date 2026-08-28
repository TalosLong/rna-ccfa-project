# Selective Refiner v3 Legacy121 Development Results

## Scope and integrity

This experiment used only the normalized Legacy121 development set and the
authoritative v1 `POOLED_SOURCE_AGNOSTIC` validation/test probabilities. No
neural network was trained, v1/v2 models were not modified, and external77 was
not accessed. There were 25 matched fold×seed score realizations, four
conditions, and 100 condition-level outcomes. All deletion accounting checks
passed.

The v3 hypothesis was that exact agreement of both other predictors is better
used as a KEEP/protection veto on the high-recall v1 deletion score than as a
replacement classifier.

## Primary and matched results

| Condition | Mod. precision | DELETE recall | Preservation | Macro ΔF1 | Micro ΔF1 | Beneficial | Harmful | Modified pairs | Deployable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V3_BASE | 0.847814 | 0.351848 | 0.987173 | +0.014761 | +0.018770 | 1,571 | 282 | 1,853 | 20/25 |
| V3_VETO2_FIXED | 0.956281 | 0.347816 | 0.996771 | +0.017160 | +0.023046 | 1,553 | 71 | 1,624 | 20/25 |
| V3_VETO2_RECALIBRATED | 0.895257 | 0.507279 | 0.987946 | +0.019960 | +0.029775 | 2,265 | 265 | 2,530 | 22/25 |
| AGREEMENT_ZERO_SUPPORT_RULE | 0.841270 | 0.474804 | 0.981806 | +0.016780 | +0.026615 | 2,120 | 400 | 2,520 | 25/25* |

`*` Agreement-only has no threshold and the repeated 25-fold-seed reporting is
for matched denominators; its unique biological five-fold result is also
preserved in `agreement_rule_comparison.csv`.

The preregistered primary condition was `V3_VETO2_RECALIBRATED`. It failed the
frozen gate because only 22/25 validation-selected thresholds were deployable
and held-out pooled preservation was 0.987946, below 0.99. The other primary
criteria resolved as passing, including pooled precision, recall, paired
macro/micro nonnegative gains, and the recall-drop limit. The final decision is
**V3_DEVELOPMENT_GATE_FAIL**.

## Mechanistic veto result

Relative to V3_BASE, `V3_VETO2_FIXED` prevented exactly 211 harmful deletions
and 18 beneficial deletions:

- harmful deletions rescued: 211/282 = 74.82%;
- beneficial deletions sacrificed: 18/1,571 = 1.15%.

The fixed veto raised preservation from 0.987173 to 0.996771 and improved
macro/micro ΔF1 from +0.014761/+0.018770 to +0.017160/+0.023046, while DELETE
recall changed only from 0.351848 to 0.347816. This is strong mechanistic
support for the protection interpretation. It is not a pass of the primary
v3 gate because the fixed condition is an ablation, not the primary
recalibrated condition.

## Recalibration behavior

The consensus veto allowed a lower threshold than BASE in all 20 runs where
BASE was deployable. Two BASE-abstaining runs became deployable after veto
recalibration; three remained nondeployable. Thus primary deployability was
22/25, not 25/25. No recalibration threshold was chosen from held-out results.

Recalibration recovered and exceeded BASE DELETE recall (0.507279 versus
0.351848) and increased mean macro/micro ΔF1, but the increased edit volume
also produced 265 harmful deletions and missed the pooled 0.99 preservation
criterion. The exact per-run validation search and thresholds are in
`threshold_recalibration_summary.csv`.

## Source-specific primary result

| Source | Precision | DELETE recall | Preservation | Macro ΔF1 | Micro ΔF1 | Modified-RNA fraction |
|---|---:|---:|---:|---:|---:|---:|
| RNAfold | 0.726131 | 0.262727 | 0.985200 | -0.000533 | +0.005064 | 0.1471 |
| PETfold | 0.831818 | 0.303734 | 0.989884 | +0.004820 | +0.011151 | 0.1950 |
| trRosettaRNA2 native SS | 0.951537 | 0.745370 | 0.988775 | +0.055592 | +0.071119 | 0.7488 |

The non-trRosetta requirement was met through PETfold, but RNAfold macro ΔF1
remained slightly negative. The positive structure effect was still largest
for trRosettaRNA2; v3 did not establish source-independent gains.

## Agreement-only comparator

The zero-support rule achieved pooled precision 0.841270, recall 0.474804,
preservation 0.981806, macro ΔF1 +0.016780, and micro ΔF1 +0.026615. Relative
to this simple rule, the v1 learned score had slightly higher precision and
preservation but lower recall and lower ΔF1. The learned score therefore adds
risk control, but does not dominate the comparator on every endpoint.

## Answers to the preregistered questions

1. **Does a hard support=2 veto remove most BASE harmful edits?** Yes: 211 of
   282, or 74.82%.
2. **How many beneficial edits are lost?** 18 of 1,571, or 1.15%.
3. **Does fixed veto improve preservation and structure F1?** Yes, on these
   Legacy121 held-out rotations.
4. **Does recalibration recover recall?** Yes; recall rises to 0.507279, but
   held-out preservation remains below 0.99.
5. **Does the primary condition achieve 25/25 safe thresholds?** No; 22/25.
6. **Does it improve RNAfold or PETfold, not only trRosettaRNA2?** PETfold
   has positive macro and micro ΔF1; RNAfold has positive micro but negative
   macro. The strongest effect remains trRosettaRNA2.
7. **Does the learned score outperform zero-support rule?** It improves
   precision and preservation, while the rule has higher recall and ΔF1.
8. **Does v3 pass every frozen gate?** No.
9. **Is external77 authorized?** No. It remains locked.

These are Legacy121 development findings after protocol motivation and must
not be presented as independent generalization evidence. No model-agnostic
claim is made. The next external decision cannot be informed by external77
until a separately authorized protocol permits it.

