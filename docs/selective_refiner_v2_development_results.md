# Selective Refiner v2 Legacy121 Development Results

## Scope

This was the preregistered Legacy121 grouped-development experiment only. It
trained 50 new CROSS backbones (two feature variants, five frozen folds, and
five seeds) and reconstructed the 50 pooled v1 BASE backbones. The 200
condition-level outcomes cover global and source-conditional calibration for
source-aware and source-agnostic models. external77 was not read or evaluated.

All new training runs used `cuda` on an NVIDIA GeForce RTX 3090 with CUDA
11.8 and PyTorch 2.5.1+cu118. The frozen v1 architecture, optimizer,
hyperparameters, folds, seeds, and thresholds were unchanged.

## Primary preregistered result

The primary comparison was
`V2A_CROSS_SOURCE_AGNOSTIC_GLOBAL` versus the authoritative reconstructed
`V2A_BASE_SOURCE_AGNOSTIC_GLOBAL`, paired by fold and seed.

| quantity | BASE | CROSS |
|---|---:|---:|
| event-pooled modification precision | 0.8478 | 0.9141 |
| event-pooled DELETE recall | 0.3518 | 0.1550 |
| event-pooled preservation | 0.9872 | 0.9970 |
| mean macro ΔF1 | 0.0148 | 0.0068 |
| mean micro ΔF1 | 0.0188 | 0.0100 |

CROSS global threshold deployability was only 8/25, so the mandatory 25/25
criterion failed. The precision and preservation criteria passed, but recall
fell by 0.1969, paired mean macro/micro gains were -0.0080/-0.0087, and the
useful-source fraction was below 10% for RNAfold and PETfold. The primary
decision is therefore **V2_DEVELOPMENT_GATE_FAIL**.

Source-specific CROSS macro/micro ΔF1 were RNAfold +0.0004/+0.0017, PETfold
+0.0015/+0.0028, and trRosettaRNA2 +0.0185/+0.0246. Thus the positive source
effects are strongly concentrated in trRosettaRNA2, although the two weaker
sources have small positive aggregate deltas. CROSS preservation was 0.9966,
0.9969, and 0.9977, respectively.

## Secondary factorial results

The source-aware global CROSS condition had precision 0.9108, recall 0.1006,
preservation 0.9980, macro ΔF1 +0.0044, and micro ΔF1 +0.0064. The
source-conditional agnostic CROSS condition had precision 0.9093, recall
0.0786, preservation 0.9984, macro ΔF1 +0.0041, and micro ΔF1 +0.0057.
The source-conditional aware CROSS condition had precision 0.8993, recall
0.0820, preservation 0.9981, macro ΔF1 +0.0035, and micro ΔF1 +0.0049.
These secondary conditions do not alter the failed primary decision.

## Diagnostics and interpretation

Cross-model support remains a strong descriptive observable: the prediction-
only support audit found pooled correct fractions 0.1587, 0.3686, and 0.9764
for zero, one, and two other-model exact supports. In the primary CROSS test
predictions, zero-support pairs were preferentially deleted, with source-wise
deletion precision of 1.00 for RNAfold, 1.00 for the small PETfold zero-support
subset, and 0.975 for trRosettaRNA2; the complete breakdown is in
`summary/cross_feature_diagnostics.csv`. These are post-hoc development
descriptions, not tuning evidence.

The v2 result answers the scientific questions cautiously. CROSS features can
produce high-precision, high-preservation deletion behavior, but in this
frozen experiment they are too conservative and do not improve the matched
baseline's pooled recall or mean structure effect. They improve RNAfold and
PETfold only slightly in absolute delta terms, not relative to the matched
BASE on both macro and micro criteria. Source awareness and conditional
calibration do not rescue the primary gate. LOMO/model-agnostic claims remain
unsupported by v1 and were not reinterpreted here.

## External lock and limitations

The external77 learned-refiner evaluation remains locked because the primary
v2 development gate failed. Legacy121 results are development evidence only,
not independent generalization evidence. No external result, architecture
change, threshold change, or v1 reinterpretation is authorized by this
commit. Evidence Guidance and 3D experiments remain unstarted.

