# Evidence Guidance Stage E2 Pretraining Review

Status: **READY_FOR_E2_TRAINING**

Review target: `evidence_guidance_stage_e2_v1`, frozen before training.

## E1 justification and scope

The immutable Stage E1 result supports E2 protocol development: clean
simulated evidence produced useful direct and local-conflict corrections on
all three Legacy121 sources, including PAIR_PROTECT_ONLY without pair
insertion. E1's 54,450 non-evidenced pair sets were unchanged and its
non-evidenced delta F1 was exactly zero. E2 is therefore a prospective test of
learned propagation, not a reinterpretation of E1.

The primary output remains deletion-only. Positive-pair evidence cannot be
inserted, and the masked same-checkpoint control—not ORIGINAL—is the causal
evidence-input comparator.

## Input and leakage audit

The model-facing allowlist is sequence, immutable original predicted pairs,
and delivered clean evidence items. The manifest adapter excludes nominal
density, evidence seed, eligible-universe size, source-GT hash, unselected
evidence-universe members, and original-clean-item metadata. Source identity,
confidence, error annotations, full GT beyond the delivered items, noise,
external77, and real-modality data are forbidden.

The unchanged evidence generator remains untargeted. No prediction, error,
loss, disagreement, confidence, or source identity can influence sampling.
GT is used for training labels and development evaluation only; at inference,
the allowed simulated observation is the delivered item itself.

## Evidence-set and architecture audit

The frozen source-agnostic candidate vector is 78 dimensions: 11 numeric,
62 exact historical vocabulary indicators, and five explicit unknown-bucket
indicators. The historical inward-neighbor vocabulary omission of `GG` is
retained, with `GG` mapped to its existing unknown bucket. `E2_PAIR` item input is 17 dimensions and
`E2_UNPAIRED` item input is 8. Both pass through the shared-width
item encoder `input -> 32 -> 32`, followed by mean and max pooling to 64.

Candidate encoding still produces 64 dimensions. The two evidence count descriptors
make the complete evidence block 66 dimensions; fusion is therefore exactly
130. The explicit `Linear(130,128)` projection is followed by 128-to-64 and a
single DELETE logit. ReLU and dropout locations are fully specified. Empty
evidence is an exact zero 66-vector after preprocessing. No dimension,
pooling, padding, or zero-evidence behavior remains implicit.

At deterministic inference, the 0% WITH_EVIDENCE and EVIDENCE_MASKED paths
must be bit-identical. The masked condition uses the same checkpoint and
threshold, and cannot be retrained or recalibrated.

## Split and repeated-realization audit

The frozen fold file hash is
`810b04a3963acc7637b60fcb5c2246c765fac334f809a5af9f8f050824ed974f`.
It contains 121 unique RNAs with fold counts 25/24/24/24/24, no duplicate RNA,
and no identity component crossing a fold. Rotation train/validation/test RNA
sets are disjoint. All sources, densities, evidence seeds, and candidate pairs
for an RNA remain together.

Each channel has 158,700 full-data pair-realization rows before partitioning:
5,290 original pairs times six densities times five evidence seeds. The five
evidence seeds are augmentation and the five model seeds are training
realizations; neither is a biological replicate. The aggregation contract
first reassembles the five held-out folds, preserves RNA as the biological
unit, and reports variability without selecting a seed.

## Training and checkpoint audit

Optimization retains the frozen v1 settings: class-weighted BCE, AdamW,
learning rate 1e-3, weight decay 1e-4, batch size 256, 100 epochs, patience 12,
gradient clipping 5, dropout 0.10, and model seeds 17/29/41/53/67. All five
rotations contain DELETE training examples. Preprocessing and class weights
are training-only.

The checkpoint metric is pooled validation DELETE F1 at 0.5 across all clean
density/evidence realizations for that channel, tie-broken by preservation and
then earlier epoch. No held-out test metric enters checkpoint selection.

## Threshold and gate audit

One global validation threshold is frozen per channel/fold/model seed. It must
meet validation preservation >=0.99 separately at all six densities, then
maximize pooled DELETE F1. WITH and MASKED share it. Failure to find one gives
a defined no-edit abstention outcome but fails deployability.

The 25/25 threshold requirement is stringent in light of v1--v3 history, but
it is mathematically possible and explicitly part of the prospective safety
hypothesis. It is retained without relaxation.

All channel gates resolve uniquely. Event-pooled ratios, matched macro/micro
differences, source breadth, non-evidenced safety, responsiveness denominator,
NA handling, missing-run handling, and overall channel/experiment outcomes
are defined. Required NA, missing threshold/run, or integrity failure means
FAIL. One channel cannot rescue the other's channel-specific failure; overall
pass requires at least one independently passing channel.

## Artifact and claim audit

The future per-run, evaluation, and summary artifact layout is frozen. Large
checkpoints may follow repository ignore policy, but configs and summaries
remain required. Required ablations isolate masking, count descriptors,
candidate-relative geometry, and the historical v1 topology-only baseline;
they cannot rescue the primary gate.

An E2 pass is Legacy121 development evidence only. It can justify a statement
about simulated sparse structural evidence, and a propagation statement only
if the non-evidenced criteria pass. It cannot authorize external77, noisy or
real evidence, assay-specific language, independent validation, or
model-agnostic transfer.

## Final review decision

All specified protocol components are internally complete and machine
auditable. The project is `READY_FOR_E2_TRAINING`. This status authorizes only
the separately requested clean Legacy121 E2 implementation/training task. No
model was trained, no noisy experiment was run, and external77 was not
accessed during this protocol freeze.
