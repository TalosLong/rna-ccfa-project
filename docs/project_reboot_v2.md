# Project Reboot v2

Status: **FROZEN BEFORE NEW LEARNED TRAINING**  
Date: 2026-08-29

## 1. Why the project is being rebooted

The original mainline was:

```text
error analysis
-> rule baseline
-> learned selective refiner
-> cross-model transfer
-> evidence guidance
```

That sequence produced useful negative and mechanistic evidence, but the intended
paper story is no longer strong enough as originally framed.

Immutable historical results remain:

- selective-refiner v1: `DEVELOPMENT_GATE_FAIL`;
- selective-refiner v2: `V2_DEVELOPMENT_GATE_FAIL`;
- selective-refiner v3 primary: `V3_DEVELOPMENT_GATE_FAIL`;
- Stage E1 clean hard evidence baseline: direct/local utility is positive, but
  `NON_EVIDENCED_EFFECT == 0` by construction;
- external77 historical three-source protocol gate is PASS and the 42-RNA x
  three-source normalized matrix is complete (126/126).

No historical result is deleted or reinterpreted as a pass.

The literature review also changes the novelty boundary:

- RNA base-pair probability/confidence is established prior art;
- structural cleanup such as isolated-pair removal is established prior art;
- thermodynamic + evolutionary evidence fusion is established prior art;
- predictor consensus is established prior art;
- evidence-constrained global refolding is established prior art;
- pair-level post-hoc quality estimation exists as an analogous problem in
  protein contact-map quality assessment.

Therefore the project must not claim that pair confidence, post-processing,
constraint propagation, or generic pair-level QA is novel by itself.

## 2. New working title

> **Post-hoc Evidence Reconciliation for RNA Secondary Structure Predictions**

`Model-agnostic`, `unseen-predictor`, `real-evidence`, and `3D benefit` remain
candidate claims that require explicit experiments.

## 3. Core scientific question

> Given an RNA sequence, an already-computed secondary-structure prediction from
> an existing predictor, and sparse external structural evidence, can a post-hoc
> method identify and selectively correct residual pair errors while preserving
> predictor information that is already correct?

The central comparison is no longer only:

```text
Original vs Refined
```

It is:

```text
Original predictor
vs
local evidence enforcement
vs
global evidence-constrained refolding
vs
post-hoc evidence reconciliation
```

The project must answer why preserving and reconciling an existing predictor
output is useful compared with simply refolding from sequence under the same
evidence.

## 4. Task definition

For sequence `x`, original predicted pair set `S`, evidence set `E`, and an
original predicted pair `p=(i,j) in S`, estimate an error probability:

```text
q_ij = P(p is incorrect | x, S, E)
```

Primary edit space remains conservative:

- `KEEP` an original pair;
- `DELETE` an original pair;
- `ABSTAIN` when evidence is insufficient.

Primary v2 does **not** add absent pairs, reassign partners, recursively rebuild
stems, or run a decoder that creates new pairs. Those operations would turn the
method back toward full secondary-structure prediction rather than post-hoc
quality control.

## 5. Research questions

### RQ1 — Is post-hoc reconciliation necessary?

Does the original predictor output contain useful correct information that is
lost or overwritten by global evidence-constrained refolding?

### RQ2 — Can sparse evidence improve residual-error detection safely?

Can evidence increase false-positive removal while maintaining a high
correct-pair preservation rate?

### RQ3 — Can evidence help beyond directly evidenced/local-conflict pairs?

Non-local change alone is not a contribution because constrained folding can
already propagate constraints. The relevant question is whether non-evidenced
changes have a better beneficial/harmful trade-off.

### RQ4 — Does the reliability signal generalize?

Test pooled multi-source development, source-wise behavior, leave-one-model-out
transfer, and one locked independent dataset. Do not claim model agnosticism
unless these tests support it.

### RQ5 — What happens when evidence is noisy or real?

Controlled noise is required before any real-evidence claim. Real SHAPE/DMS/PARS
or related evidence is a later stage, not an assumption of the clean simulated
study.

## 6. Data roles

### Legacy121 v1

Role: **development only**.

Use for:

- baseline design;
- architecture selection;
- calibration/threshold selection under frozen grouped splits;
- ablation;
- controlled simulated evidence;
- Go/No-Go decisions.

It must not be presented as independent confirmation.

### external77-derived 42-RNA set

Role: **locked independent test**.

Current state:

- RNAfold 42/42 valid;
- PETfold 42/42 valid under reproduced historical single-sequence condition;
- trRosettaRNA2 native SS 42/42 valid under the recovered query-only condition;
- normalized matrix 126/126 valid.

Do not access this set for model selection, feature redesign, threshold tuning,
or rescue analyses before the independent-test gate is reached.

## 7. Evidence ladder

Evidence is separated into three levels.

### E0 — Clean symbolic evidence

- known positive base pair;
- known unpaired nucleotide.

Purpose: mechanism and upper-bound development only.

### E1 — Controlled noisy symbolic evidence

Use frozen corruption mechanisms and noise levels. Purpose: quantify robustness
and determine whether a learned trust/reconciliation mechanism is necessary.

### E2 — Real experimental evidence

Candidate modalities include SHAPE, DMS, PARS, and other experimentally grounded
signals after a dedicated data/provenance audit. Experimental probing is
probabilistic evidence, not ground truth.

## 8. Required baselines

### B0 — Original predictor

No modification.

### B1 — Local hard evidence transformation

The completed Stage E1 transformations remain the local baseline. Their direct
and local effects are useful, but their non-evidenced effect is structurally
zero.

### B2 — Global evidence-constrained refolding

**New mandatory baseline before learned training.**

Use the same sequence and the same delivered sparse evidence but allow a
classical RNA folding algorithm to re-optimize the whole structure. Initial
implementation should use a reproducible ViennaRNA/RNAfold hard-constraint
protocol. Soft-constraint/restraint variants are introduced only after the hard
baseline is frozen.

This baseline answers:

> Why not simply refold the RNA under the evidence?

### B3 — Prediction-only reliability/refinement baselines

Retain as mechanistic comparators:

- rule-based conditions;
- v1 topology-only score;
- v3 fixed consensus-veto comparator;
- simple pair confidence/BPP where available and protocol-compatible;
- simple cross-model agreement where appropriate.

Historical failed primary gates remain failures.

### B4 — Evidence-masked learned control

A learned model must be compared against a matched condition in which evidence
is unavailable/masked, so any gain can be attributed to delivered evidence
rather than model capacity alone.

## 9. Learned method family

Working internal name: **Evidence Reconciliation Network (ERN)**.

The previously frozen E2 candidate/evidence architecture may be reused as an
implementation starting point because it already supports:

- source-agnostic candidate features;
- permutation-invariant evidence-set encoding;
- one score per original predicted pair;
- global access from every delivered evidence item to every candidate pair.

However, the historical `evidence_guidance_stage_e2_v1` success criteria are
superseded before training. A new R4 protocol must compare ERN against B0, B1,
B2, and B4 under the reboot metrics and Go/No-Go rules.

No Transformer/GNN/foundation model is justified until a simple architecture
shows a reproducible signal beyond the strongest non-learned baselines.

## 10. Evaluation

### 10.1 Pair reliability

Primary candidate metrics:

- AUPRC for the minority `DELETE`/FP class;
- AUROC as secondary discrimination metric;
- Brier score;
- Expected Calibration Error (ECE);
- reliability diagrams;
- precision among the highest-risk predicted pairs.

### 10.2 Refinement utility

Mandatory metrics:

```text
TP_preservation = TP_after / TP_before
FP_removal = (FP_before - FP_after) / FP_before
modification_precision = beneficial_edits / modified_pairs
```

Also retain Precision, Recall, macro/micro F1, edit counts, and beneficial/harmful
accounting.

### 10.3 Risk–utility curves

The main comparison should sweep a validation-selected risk/abstention policy
and plot correction utility against damage, e.g.:

```text
x-axis: TP loss or 1 - TP preservation
y-axis: FP removal
```

A useful post-hoc method should dominate or improve on global constrained
refolding at matched preservation/risk levels, not merely increase aggregate F1
by a small amount.

### 10.4 Non-evidenced effects

Report separately:

- non-evidenced modification precision;
- non-evidenced FP removal;
- non-evidenced TP loss.

The question is not whether evidence propagates, but whether propagation is
useful rather than collateral damage.

### 10.5 Evidence efficiency

Report benefit per delivered evidence item, such as:

```text
FP_removed / number_of_evidence_items
Delta_F1 / number_of_evidence_items
```

### 10.6 Pair-matching robustness

Keep exact canonical pair equality as the primary metric for continuity with
all frozen historical results. Add a separately reported +/-1-endpoint flexible
matching robustness analysis for final paper-level evaluation. Do not rewrite
historical exact-match results.

## 11. Reboot stages

### R0 — Literature & novelty freeze

Status: **COMPLETE FOR REBOOT**.

Freeze the boundary that the project does not claim novelty for generic RNA
pair rules, pair probability, consensus, constrained folding, or generic
post-hoc QA.

### R1 — Task and protocol redefinition

Status: **CURRENT**.

Freeze this document, update authoritative project state, and supersede the
unexecuted historical E2 training step.

### R2 — Global constrained-refolding baseline

Implement and freeze a hard-constraint global refolding protocol on Legacy121
using exactly the same clean symbolic evidence manifestations as the local
baseline where semantically possible.

### R3 — Reliability baseline suite

Assemble prediction-only confidence/structural/consensus comparators under the
new reliability and risk-control metrics.

### R4 — Clean evidence reconciliation

Train the simple learned evidence-conditioned pair reliability model only after
R2 and R3 are frozen. Compare against B0/B1/B2/B4.

### R5 — Noise robustness

Use controlled evidence corruption. Do not add real evidence yet.

### R6 — Cross-predictor transfer

Run LOMO and source-wise analyses. `Model-agnostic` becomes a claim only if
supported.

### R7 — Locked independent test

Open external77 only after model, features, calibration procedure, thresholds,
and comparison protocol are frozen.

### R8 — Real evidence

Audit and evaluate one or more real probing modalities only if R4-R7 justify
continuation.

### R9 — Final selective correction

Freeze calibrated `KEEP/DELETE/ABSTAIN` policy, final ablations, statistics,
and paper claims.

### Optional — 2D -> 3D validation

Retain as a strengthening experiment only after the 2D post-hoc task is stable.

## 12. Go / No-Go rules

### Gate A — Post-hoc necessity

If global constrained refolding dominates the post-hoc approach across the
relevant TP-preservation / FP-removal trade-off, stop the post-hoc mainline.
There is no reason to preserve source predictions if doing so adds no value.

### Gate B — Learned reconciliation utility

At high preservation (target operating point: `TP_preservation >= 0.99` unless
changed prospectively), the learned method must improve FP removal over the
strongest frozen non-learned baseline and not rely on one source only.
Otherwise do not escalate architecture complexity.

### Gate C — Noise robustness

If low controlled noise (5-10%) causes negative structure utility or unsafe TP
loss, do not advance to a real-evidence claim without a new prospectively frozen
trust mechanism.

### Gate D — Independent generalization

External77 is opened once under a frozen protocol. If the development effect
does not preserve its direction on the independent set, do not claim
cross-dataset generalization and do not tune on external77 to rescue the claim.

## 13. Treatment of historical work

The reboot preserves the following assets:

- normalization/parser/evaluator infrastructure;
- Legacy121 manifest and grouped splits;
- pair/stem/separation error analysis;
- rule-baseline results;
- v1/v2/v3 failed gates and mechanistic analyses;
- simulated evidence generator and noise mechanisms;
- Stage E1 results;
- E2 implementation design as a candidate architecture only;
- external77 frozen independent matrix;
- optional 2D->3D infrastructure.

Historical failed results remain scientifically useful negative evidence. They
must not be retuned after the fact or relabeled as successes.

## 14. Immediate next action

**Do not train the historical Stage E2 protocol.**

R2 global evidence-constrained refolding is complete under protocol v1.0.2.
The next authorized planning action is:

> Interpret the frozen R2 comparator and prospectively freeze the R3
> reliability-baseline protocol. Do not start R3 implementation automatically.

Only after R3 is complete should a new learned R4 protocol be frozen and
trained; R2 alone does not decide Gate A.
