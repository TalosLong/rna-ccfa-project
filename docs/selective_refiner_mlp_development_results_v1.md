# Selective-refiner MLP development results v1

Status: **DEVELOPMENT_GATE_FAIL**

This experiment used Legacy121 grouped development cross-validation only. The
external77 matrix was not read, used for preprocessing, or evaluated.

All 8 preregistered variants completed 5 folds × 5 seeds = 200 successful
training runs. The frozen pair pipeline produced exactly 5,290 examples:
RNAfold 1,693 (1,473 KEEP / 220 DELETE), PETfold 1,704 (1,463 / 241), and
trRosettaRNA2 native SS 1,893 (1,461 / 432). Pooled counts were 4,397 KEEP /
893 DELETE. Features used only sequence plus immutable predicted pairs; DELETE
was the positive class. Train-only standardization/class weights and
validation-only thresholds passed the leakage audit.

The final run used `cuda` on an NVIDIA GeForce RTX 3090 (CUDA 11.8,
PyTorch 2.5.1+cu118). Model and training/evaluation tensors were moved to the
selected device; the frozen batch size remained 256. Device metadata is stored
in every run configuration. Earlier interrupted CPU/full-batch attempts are
retained separately as non-final provenance and are not included below.

| Variant | Mode | DELETE precision | DELETE recall | Preservation | Macro ΔF1 | Micro ΔF1 |
|---|---|---:|---:|---:|---:|---:|
| POOLED_SOURCE_AWARE | selective | 0.875 | 0.440 | 0.988 | +0.018 | +0.024 |
| POOLED_SOURCE_AGNOSTIC | selective | 0.857 | 0.428 | 0.985 | +0.018 | +0.023 |
| LOMO RNAfold | selective | 0.314 | 0.022 | 0.994 | −0.001 | −0.002 |
| LOMO PETfold | selective | 0.659 | 0.102 | 0.988 | +0.001 | −0.000 |
| LOMO trRosettaRNA2 | selective | 0.908 | 0.490 | 0.983 | +0.034 | +0.042 |

Pooled selective precision and recall pass their frozen thresholds, but pooled
preservation is below 0.99 for both pooled variants; source-wise positive
macro and micro ΔF1 is not achieved for at least two sources; and LOMO does not
show all-source transfer. The development gate is therefore **FAIL**.

Selective gating improves modification precision and preservation over its
ungated backbones, but learned deletion is source-dependent and does not
establish a universal advantage over R1/R3/R1_R3. RQ1 is positive only for
selected sources, RQ2 is positive, RQ4–RQ5 are negative for pooled/all-source
criteria, and RQ7 is negative under LOMO. These are Legacy121 development
findings, not independent generalization evidence.

No external77 evaluation, larger architecture, Evidence Guidance, or 3D
experiment is authorized by this result.

The complete machine-readable outputs are under
`results/selective_refiner/v1/`, including 200 checkpoints/configurations,
raw pair scores, per-RNA edited structures, fold/seed summaries, source-wise
diagnostics, threshold summaries, and the frozen development-gate decision.

Post-hoc diagnostics covering singleton versus stem pairs, two-pair stems,
boundary versus interior pairs, canonical pair type, separation bins, source
condition, source-aware versus source-agnostic training, and model-specific
versus LOMO behavior are in `summary/posthoc_feature_diagnostics.csv`. They
are descriptive only and were not used for tuning.
