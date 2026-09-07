# Conservative Evidence Reconciliation Protocol

## Status

**`CONSERVATIVE_RECONCILIATION_PROTOCOL_FROZEN_NOT_EXECUTED`**

**`CONSERVATIVE_RECONCILIATION_NOT_EXECUTED`**

**`R4_GATE_B_FAIL_UNCHANGED`**

**`R5_NOT_AUTHORIZED`**

**`EXTERNAL77_LOCKED`**

Protocol date: 2026-09-08

Formal method name: **Conservative Evidence Reconciliation (CER)**.

Primary mechanism: **Context-Corroborated Evidence Gate (CCEG)**.

This document prospectively freezes a new hypothesis and development protocol
after the completed R4 postmortem. CER is not an R4 threshold change, channel
selection, feature rescue, model-capacity rescue, or reinterpretation of the
failed R4 Gate B. This task does not implement or train CER, rerun ERN/B4,
compute new Legacy121 performance, open external77, begin R5, use noisy or real
evidence, or execute historical E2.

## 1. Scientific provenance and hypothesis

### 1.1 What frozen R4 established

R4 supports only the following development-level premises:

- source-agnostic original-prediction context contains substantial pair-error
  signal;
- usable clean evidence adds discrimination and calibration signal beyond a
  matched evidence-masked model;
- `LOCAL_CONFLICT` correction is extremely safe under the clean symbolic
  evidence semantics;
- `NON_EVIDENCED` propagation contains both useful FP correction and harmful TP
  deletion;
- the post-hoc operating region is non-dominated by B2 full refolding; and
- FP-removal improvement over P3 occurred in all three current predictor
  sources.

R4 does not support safe learned correction under its frozen Gate B, a claim
that a different R4 threshold would pass, positive-pair-only rescue, a larger-
model rescue, independent generalization, unseen-predictor transfer, noisy- or
real-evidence robustness, or downstream 3D benefit. The frozen decision remains
`R4_GATE_B_FAIL`.

### 1.2 New hypothesis

CER tests the prospectively stated hypothesis:

> **Most evidence-attributable useful correction can be retained while
> suppressing unsafe NON_EVIDENCED propagation.**

For this protocol, “most” means strictly more than 50% of the frozen R4
ERN-minus-B4 FP-removal increment under both event-pooled and RNA-balanced
aggregation. “Suppressing unsafe propagation” requires both high
`NON_EVIDENCED` TP preservation and no evidence-attributable reduction in that
preservation relative to the new matched evidence-masked control. These are
falsifiable development criteria, not predicted outcomes.

The causal design question is narrower than “can another model fit
Legacy121?” It is whether explicit evidence can retain incremental correction
when a non-local deletion must also be corroborated by the immutable original-
prediction context.

## 2. Candidate, label, and edit space

For RNA sequence `x`, immutable original predicted pair set `S`, delivered
evidence set `E`, and candidate pair `p=(i,j) in S`, the learned branches
estimate DELETE/FP risk. The primary candidate unit remains one original
predicted pair under one clean evidence realization.

- positive label: `DELETE/FP = 1`, meaning the original pair is absent from GT;
- negative label: `KEEP/TP = 0`, meaning the original pair is present in GT;
- GT is used for development labels and evaluation only;
- missing GT pairs are not candidates;
- the corrected pair set must remain a subset of `S`.

CER is deletion-only. It may not add a pair, inject an absent evidence pair,
reassign a partner, rebuild a stem, invoke a global decoder, or refold inside
the learned method.

## 3. Frozen evidence scopes and action semantics

Operational scope is computed from the delivered evidence using exactly the R4
scope definitions. The precedence is `DIRECT`, then `LOCAL_CONFLICT`, then
`NON_EVIDENCED`; a semantic inconsistency that prevents a unique scope fails
closed to `ABSTAIN`. Evaluation scope is stored separately and may contain GT
labels for analysis, but GT never enters the action engine.

### 3.1 DIRECT

An original pair exactly supported by delivered positive-pair evidence is
`DIRECT`. CER assigns `KEEP` regardless of learned risk. This encodes the
scientific priority of protecting an explicitly supported original pair. The
unpaired-nucleotide channel has no exact positive-pair DIRECT action.

### 3.2 LOCAL_CONFLICT

An original pair that conflicts with delivered evidence under the frozen E1/R4
definition is `LOCAL_CONFLICT`. CER assigns `DELETE` directly. This retains the
clean, explicit evidence consequence and preserves a direct comparison with E1
`LOCAL_CONFLICT`; it is not claimed as novel learned propagation.

### 3.3 NON_EVIDENCED

Every remaining original pair is `NON_EVIDENCED`. It is not deleted by default
and does not inherit R4's unrestricted evidence-conditioned decision. It is
subject to the single CCEG rule defined below.

### 3.4 KEEP, DELETE, and ABSTAIN

- `KEEP` is a positive operational decision: a DIRECT pair is protected, or
  both CCEG branches agree below the locked risk threshold.
- `DELETE` is permitted only for an explicit LOCAL_CONFLICT or a
  NON_EVIDENCED pair for which both CCEG branches agree at or above the locked
  threshold.
- `ABSTAIN` is the normal conservative decision when the two branches disagree,
  or when a required input, calibrator, threshold, or scope is invalid. The
  original pair remains unchanged.

ABSTAIN is defined before evaluation and reported as its own coverage state. It
may not be invoked after viewing a difficult RNA, source, density, seed,
channel, or result, and it may not remove a failed sample from any denominator.

## 4. The one frozen conservative mechanism: CCEG

CCEG uses two separately trained, equal-capacity R4-family risk branches:

- `EVIDENCE_BRANCH` produces calibrated risk `q_E` from the exact R4 candidate
  representation plus usable delivered evidence;
- `CONTEXT_BRANCH` produces calibrated risk `q_C` from the identical candidate
  representation while the complete usable-evidence block is exactly zero.

For a `NON_EVIDENCED` candidate, define one raw corroborated score:

```text
r_CCEG = min(q_E, q_C)
```

Because the minimum of two calibrated probabilities is not necessarily itself
calibrated, fit one validation-only monotone policy calibrator:

```text
q_CCEG = sigmoid(a_G * logit(clip(r_CCEG, epsilon, 1-epsilon)) + b_G)
a_G > 0
epsilon = 1e-7
```

`q_CCEG` is the reported CER DELETE probability used for Brier/ECE. The
calibrator is monotone, so it does not change the conjunctive ranking. Given
one validation-locked calibrated threshold `tau`, its inverse defines one raw
corroboration cutoff `c`. The action is:

```text
DELETE   iff q_E >= c AND q_C >= c
KEEP     iff q_E <  c AND q_C <  c
ABSTAIN  otherwise
```

Equality enters the DELETE block. Both classes must be present, calibration
must converge, and `a_G` must be strictly positive; otherwise the run fails
closed to ABSTAIN. The threshold artifact stores both `tau` and its derived
`c`. The `min` construction is a logical
conjunction, not a learned fusion layer, attention mechanism, ensemble
selection, or third model.

The independent scientific rationale is that evidence without a direct or
local-conflict relation does not logically entail that a distant candidate is
wrong. A non-evidenced deletion therefore requires corroboration from
candidate-local prediction context. This rationale follows from the task's
causal semantics and the pre-existing distinction between explicit and
propagated effects; it is not derived from a favorable held-out stratum.

CCEG must not use sequence-separation 10--19, a P2/P4 diagnostic bin, the
calibrated R4 `[0.6,0.8)` interval, an ERN-minus-B4 risk-difference interval,
stem-boundary postmortem strata, evidence density, source identity, or a
positive-pair-only condition as a hard-coded gate. No alternate primary gate
is permitted in the first CER development execution.

## 5. Feature contract

CER reuses the exact R4 feature allowlist and ordering without addition,
deletion, or selection:

- 80-dimensional candidate vector: the historical source-agnostic 78 features,
  P2 exact cross-model support divided by two, and P4 RNAfold BPP;
- 17-dimensional positive-pair evidence item;
- 8-dimensional unpaired-nucleotide evidence item;
- four evidence descriptors: item count, item count divided by sequence length,
  E1 local-conflict indicator, and direct-pair-support indicator;
- separate permutation-invariant positive-pair and unpaired evidence sets.

The feature contract is the frozen R4
`results/clean_learned_evidence_reconciliation_r4/features/feature_contract.json`
(SHA256
`154d9e2a59c2d571369edc516c0932b41adb8bea62943a3de6920431e9c7ad28`).
Future implementation may construct an immutable referenced view but may not
rewrite the artifact.

All inputs must be inference-time available, GT-free except for explicitly
delivered simulated clean evidence, and source-agnostic. Predictor identity,
dataset/family identity, nominal density, evidence seed, GT annotations,
postmortem bins, R4 decisions, R4 calibrated risk, and B2 disagreement are not
features. Predictor source remains evaluation metadata only.

Operational scope and CCEG are action semantics over already permitted
evidence relationships and calibrated outputs; they do not add a feature to a
branch tensor.

## 6. Model capacity and matched evidence control

### 6.1 Branch architecture

Both CCEG branches use the exact simple R4 ERN family for their channel:

```text
candidate: Linear(80,64) -> ReLU
item:      Linear(item_dim,32) -> ReLU -> Linear(32,32) -> ReLU
pool:      masked mean || masked max
fusion:    Linear(132,128) -> ReLU -> Dropout(0.10)
           -> Linear(128,64) -> ReLU -> Dropout(0.10)
           -> Linear(64,1)
```

`item_dim` is 17 for positive-pair evidence and 8 for unpaired evidence. The
channels remain separate model families and are combined only by concatenating
their development-assessment rows for the primary Track E summary. Neither
channel may be selected.

No Transformer, GNN, RNA language model, foundation model, attention layer,
pretrained predictor, learned gate, source embedding, new decoder, or model-
size search is allowed. The second branch exists only to make the evidence-
propagation decision explicit and auditable.

### 6.2 Matched control

The primary conditions are:

- `CER`: EVIDENCE_BRANCH receives usable evidence; CONTEXT_BRANCH receives an
  exact-zero evidence block;
- `CER_EVIDENCE_MASKED`: both logical branches receive exact-zero evidence
  blocks, including item tensors, masks, counts, channel indicators, direct
  support, local conflict, density, seed, and every other evidence proxy.

Both conditions instantiate two branches with identical architecture,
parameter capacity, base model seeds, initialization procedure, optimizer,
splits, labels, batches, checkpoint selection, calibration, CCEG formula, and
threshold selection. Within each condition/branch pairing, the only allowed
difference is whether usable evidence is exposed to EVIDENCE_BRANCH and its
operational scope engine. Evaluation-only true scopes remain hidden until
reporting.

The five base model seeds remain `17, 29, 41, 53, 67`. Each condition x branch
x channel x fold x seed run must be retained. No seed is selected. The nominal
matrix is:

```text
2 conditions x 2 branches x 2 channels x 5 folds x 5 seeds = 200 runs
```

The two branches within a condition use the same base seed and batch order;
their pairing audit must prove equality of all non-evidence contracts. In the
fully masked control, duplicate branch outputs are expected under deterministic
execution and must be verified rather than omitted, so nominal capacity and
action mechanics remain matched.

## 7. Legacy121 data role and development splits

Legacy121 is permanently **development / hypothesis-generation data** for CER.
Its R4 held-out outputs were observed and used to formulate CCEG. No Legacy121
fold or CER result may be described as pristine, independent, external, or
confirmatory validation.

CER retains the existing grouped split file:
`results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv`, SHA256
`810b04a3963acc7637b60fcb5c2246c765fac334f809a5af9f8f050824ed974f`.
For rotation `k`:

```text
development_assessment = fold k
development_validation = fold (k+1) mod 5
development_train      = the remaining three folds
```

All source records, original pairs, evidence channels, densities, evidence
seeds, and evidence realizations for one RNA remain in one role. RNA identity
is the biological grouping unit. Repeated contexts and model/evidence seeds are
not independent biological samples.

Development train fits preprocessing, branch parameters, and class weights.
Development validation selects checkpoints, calibrators, and the CCEG
threshold. Development assessment is inaccessible until those artifacts are
sealed, then supplies internal cross-validated development evidence only. No
assessment result may alter a branch, feature, calibrator, threshold, seed,
channel, or protocol variant.

## 8. Frozen development procedure

The future execution must reuse the R4 clean matched universe without
regenerating evidence: 121 RNAs, 363 source records, 3,523 eligible
positive-pair manifests, 3,630 eligible unpaired manifests, 7,153 combined
manifests, and 310,838 original-pair realization events per complete condition.

Each branch reuses the R4 training contract:

- class-weighted `BCEWithLogitsLoss`, `pos_weight = KEEP_train/DELETE_train`;
- AdamW, learning rate `1e-3`, weight decay `1e-4`;
- batch size 256, maximum 100 epochs, patience 12;
- gradient clipping 5.0;
- lowest validation unweighted binary log loss checkpoint;
- tie-break by higher validation AUPRC, then earlier epoch;
- train-only preprocessing and class weights;
- no label-aware sampling or density/source-specific model.

For every condition x branch x channel x fold x seed, fit a separate monotone
Platt calibrator `sigmoid(a*logit+b)`, `a>=0`, using development validation only.
Both classes and optimization convergence are required or the run fails closed.

For every condition x channel x fold x seed, compute `r_CCEG`, fit the monotone
policy calibrator above on development validation only, and search all unique
calibrated `q_CCEG` validation values plus delete-none. Equal values enter as
one block. A threshold is eligible only if the complete validation policy
satisfies:

```text
event-pooled TP_preservation >= 0.99
RNA-balanced TP_preservation >= 0.99
```

Among eligible thresholds: maximize RNA-balanced FP removal, then
RNA-balanced modification precision, then choose fewer deletions, then the
numerically higher threshold. The selected threshold is hashed and sealed
before development-assessment inference. There is no R4-threshold reuse,
source/density threshold, assessment rescue threshold, or channel-specific
selection. Channel-specific thresholds arise only from the two prespecified
channel model families and both channels enter the combined endpoint.

## 9. Required comparisons and metrics

The complete development report must compare, on exact applicable matched
universes:

- B0 Original predictor;
- E1 `LOCAL_CONFLICT`;
- P3 `V3_VETO2_FIXED`;
- frozen R4 ERN;
- frozen R4 B4;
- B2 `FULL_REFOLD_REFERENCE` with its different action-space warning;
- CER;
- `CER_EVIDENCE_MASKED`.

No frozen comparator is retrained, recalibrated, rethresholded, or rewritten.
R4 ERN/B4 are historical development comparators, not candidates for selection.

### 9.1 Reliability

- AUPRC for DELETE/FP using `q_CCEG`, primary;
- AUROC, secondary;
- Brier score;
- Brier/ECE/reliability diagrams use calibrated `q_CCEG`; branch-level
  `q_E`/`q_C` calibration is reported as a companion audit;
- positive prevalence.

### 9.2 Utility and action accounting

- TP preservation;
- FP removal;
- modification precision;
- total, KEEP, DELETE, and ABSTAIN coverage;
- delta F1, Precision, Recall, and F1;
- beneficial/harmful deletion and complete TP/FP/FN accounting;
- proof that all outputs are subsets of original predicted pairs.

### 9.3 Scope and hypothesis endpoints

Report `DIRECT`, `LOCAL_CONFLICT`, and `NON_EVIDENCED` separately, including
opportunities, KEEP/DELETE/ABSTAIN counts, removed FP, lost TP, preservation,
FP removal, modification precision, coverage, and delta F1. Emphasize:

- `NON_EVIDENCED` lost TP and TP preservation;
- `NON_EVIDENCED` modification precision;
- fraction of all deletions outside DIRECT/LOCAL_CONFLICT;
- CER-minus-masked evidence-attributable FP gain;
- CER-minus-masked evidence-attributable TP harm;
- fraction of frozen R4 evidence-attributable FP gain retained.

Event-pooled and RNA-balanced summaries are mandatory. Report RNAfold,
PETfold, and trRosettaRNA2 separately under the pooled policy. Report mean,
population SD, minimum, and maximum across all five seeds. Do not report pooled
F1 alone.

## 10. CONSERVATIVE_DEV_GATE

`CONSERVATIVE_DEV_GATE` is a development Go/No-Go decision. It is not R4 Gate
B and cannot change `R4_GATE_B_FAIL`. It is evaluated only after the complete
200-run matrix and all five-seed combined development-assessment summaries are
sealed. CER passes only if every criterion below holds.

### 10.1 Overall safety and meaningful correction

```text
event-pooled TP_preservation       >= 0.99
RNA-balanced TP_preservation       >= 0.99
event-pooled FP_removal            >  0.347816
RNA-balanced FP_removal            >  0.489748
```

The preservation philosophy and frozen P3 removal bars are not lowered. CER
must improve RNA-balanced FP removal over P3 in at least two of three sources,
including RNAfold or PETfold. Equality never satisfies a strict improvement.

### 10.2 Conservative NON_EVIDENCED behavior

```text
event-pooled NON_EVIDENCED TP_preservation >= 0.99
RNA-balanced NON_EVIDENCED TP_preservation >= 0.99
CER NON_EVIDENCED TP_preservation >= CER_EVIDENCE_MASKED
    under both event-pooled and RNA-balanced aggregation
```

The complete report must also show that CER's five-seed mean
`NON_EVIDENCED` lost-TP count is strictly below frozen R4 ERN's mean 2,687.8
on the same combined universe. This count comparison is descriptive support
for the gate's preservation criteria, not a threshold-selection target.

### 10.3 Evidence-attributable useful correction

Define:

```text
G_event = CER event FP_removal - CER_EVIDENCE_MASKED event FP_removal
G_RNA   = CER RNA-balanced FP_removal - CER_EVIDENCE_MASKED RNA FP_removal
```

Both gains must be strictly positive in the pooled summary and positive in at
least two of three sources, including RNAfold or PETfold. To operationalize
“most,” require:

```text
G_event / 0.08890968834013739  > 0.50
G_RNA   / 0.045569629647920704 > 0.50
```

The denominators are the immutable frozen R4 ERN-minus-B4 event and
RNA-balanced FP-removal differences from
`ern_vs_b4_summary.csv` (SHA256
`467c4d17adf610edb7c4dc3b3e596ec3793376d885fb01af434c92122e485935`).
They define the hypothesis endpoint; they are not CCEG thresholds or model
features.

All criteria are conjunctive. Missing runs, invalid calibration, invalid
threshold, incomplete accounting, or a scientific-firewall violation yields
`CONSERVATIVE_DEV_GATE_FAIL`.

If the gate fails, the conservative mainline stops and the next task is
`PAPER_STORY_AND_RESULTS_CONSOLIDATION`; no larger model, alternate gate,
threshold rescue, seed/channel selection, or postmortem-bin rule is
automatically authorized. If the gate passes, the status is
`CONSERVATIVE_DEV_GATE_PASS_DEVELOPMENT_ONLY`; this still does not authorize
R5 or external77. The only subsequent task would be a separate prospective
freeze of the final model/policy and validation sequence.

## 11. external77 one-shot contract

external77 remains unopened in this task and is not an input to CER development.
It is reserved as `ONE_SHOT_INDEPENDENT_TEST`. Before any path under external77
may be opened, a separately versioned final-policy seal must freeze and hash:

- final branch checkpoints/model-combination procedure;
- the unchanged feature contract;
- CCEG action and operational-scope rules;
- calibration procedure and all fitted calibration artifacts;
- the exact numeric threshold and ABSTAIN semantics;
- evidence generator and eligibility contracts;
- all metrics, source-wise analyses, comparators, and success/failure rule;
- code commit, environment, inputs, commands, and output layout.

The future clean-evidence contract is already fixed to
`simulated_evidence_v1`: separate positive-pair and unpaired channels; density
grid `0,1,5,10,20,50`; evidence seeds `101,103,107,109,113`; noise level zero;
the frozen round-half-up count rule and minimum-one behavior; sorted eligible
universes; SHA256-seeded sampling without replacement; and generator inputs
only `rna_id`, sequence, and exact GT pairs. Positive-pair manifests use the R2
v1.0.2 noncrossing and `j-i>3` whole-manifest eligibility rules for the matched
B2 comparison; all unpaired manifests remain eligible. These semantics may not
be changed after external77 access.

Independent confirmation succeeds only if the one-shot external summary uses
the presealed policy and satisfies all of:

- event-pooled and RNA-balanced TP preservation at least 0.99;
- event-pooled and RNA-balanced FP removal strictly above both matched P3 and
  E1 at their immutable policies;
- event-pooled and RNA-balanced `NON_EVIDENCED` TP preservation at least 0.99;
- positive CER-minus-masked FP-removal gain under both aggregations;
- positive CER-minus-P3 RNA-balanced FP-removal improvement in at least two of
  three sources, including RNAfold or PETfold;
- complete runs, accounting, calibration, and integrity checks.

external77 results may not trigger retraining, recalibration, threshold rescue,
feature changes, evidence-semantic changes, method redesign, subset exclusion,
or a second independent attempt. Failure is reported as failure of independent
confirmation.

## 12. Future sequence and claim boundary

The authorized sequence after this protocol freeze is:

```text
implement and execute CER on Legacy121 development CV
-> apply CONSERVATIVE_DEV_GATE once
-> if FAIL: stop conservative mainline and consolidate the bounded story
-> if PASS: prospectively freeze final model/policy and validation sequence
-> only after that freeze may robustness/transfer/independent work be considered
```

Completion of this protocol does not automatically authorize training unless
the authoritative state is updated to the exact next task. A development PASS
does not itself authorize R5, R6, R7, external77 access, noisy evidence, or real
evidence.

Any future Legacy121 result is development evidence. Only a presealed one-shot
external77 result can supply cross-dataset independent confirmation. A future
R6 result can support cross-predictor or unseen-source claims only if its own
prospective protocol warrants them.

CER must not be described in advance as model-agnostic, independently
generalizing, noise-robust, real-evidence-ready, beneficial for 3D prediction,
or safely corrective. The only currently supported statement is that CER is a
frozen, unexecuted hypothesis test motivated by bounded R4 diagnostics.

## 13. Frozen input and non-execution integrity

The development implementation must fail closed if the following immutable
inputs do not match their frozen hashes:

```text
R4 protocol:       81ce3923c19a99094418dc5fb568c7081192ac84c542b33dbb4bafa888c739e4
R4 results:        728e931d4e1329935fe990154940cb0b35900f56d14298d88ef59a7ad8e3fc8c
R4 postmortem:     a7645521b6721eee159c5f009088c742ab5ad053b6bd1a63c9a92b485ab18218
R4 feature schema: 154d9e2a59c2d571369edc516c0932b41adb8bea62943a3de6920431e9c7ad28
R4 gain summary:   467c4d17adf610edb7c4dc3b3e596ec3793376d885fb01af434c92122e485935
grouped split:     810b04a3963acc7637b60fcb5c2246c765fac334f809a5af9f8f050824ed974f
```

Protocol-freeze completion state:

```text
CONSERVATIVE_RECONCILIATION_PROTOCOL_FROZEN
CONSERVATIVE_RECONCILIATION_NOT_EXECUTED
R4_GATE_B_FAIL
R5_NOT_AUTHORIZED
EXTERNAL77_LOCKED
NEXT: IMPLEMENT_AND_EXECUTE_CONSERVATIVE_RECONCILIATION_DEVELOPMENT
```
