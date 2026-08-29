# Research Plan — Reboot v2

Last updated: 2026-08-29

## 1. Working Direction

> **Post-hoc Evidence Reconciliation for RNA Secondary Structure Predictions**

The project studies whether an already-computed RNA secondary-structure prediction can be selectively quality-controlled using sparse external structural evidence, while preserving useful information already captured by the source predictor.

The primary scientific comparison is:

```text
Original predictor
vs
local evidence enforcement
vs
global evidence-constrained refolding
vs
post-hoc evidence reconciliation
```

The project does not assume that post-hoc reconciliation is useful; R2-R4 must establish that it adds value over simply refolding under the same evidence.

## 2. Core Research Questions

### RQ1 — Post-hoc necessity

Does the original predictor output retain correct information that can be damaged or overwritten by global evidence-constrained refolding?

### RQ2 — Safe correction

Can sparse evidence improve false-positive removal while maintaining high correct-pair preservation?

### RQ3 — Useful non-local effect

Can a method make beneficial corrections outside the directly evidenced/local-conflict region, rather than merely causing global collateral changes?

### RQ4 — Generalization

Does the signal hold across predictors, RNA groups, and a locked independent dataset?

### RQ5 — Robustness and real evidence

How does performance degrade under controlled evidence noise, and does any effect survive real probing evidence?

### Candidate downstream question

Does a validated 2D improvement improve downstream RNA 3D prediction under an identical frozen 3D pipeline?

## 3. Task Definition

For sequence `x`, original predicted pair set `S`, delivered evidence `E`, and an original predicted pair `p=(i,j) in S`, estimate:

```text
q_ij = P(p is incorrect | x, S, E)
```

Primary decisions:

```text
KEEP / DELETE / ABSTAIN
```

The first rebooted mainline is deletion-only. It does not add absent pairs, reassign partners, rebuild stems, or generate a new full structure from scratch.

## 4. Prior-Art Boundary

The following are treated as prior art/baselines rather than contributions:

- RNA canonical-pair/stem/stacking rules;
- isolated-pair and short-stem cleanup;
- thermodynamic base-pair probability/confidence;
- thermodynamic + evolutionary evidence fusion;
- predictor consensus/ensemble confidence;
- evidence-constrained global folding;
- generic post-hoc pair-level quality assessment as an abstract ML problem.

The candidate contribution is narrower:

> **Predictor-output-preserving evidence reconciliation for RNA secondary-structure predictions.**

`Model-agnostic`, `unseen-predictor`, `real-evidence robust`, and `3D benefit` are candidate claims only.

## 5. Historical Evidence Preserved

- Phase 0 normalization/evaluator: complete.
- Phase 1 error taxonomy and descriptive analysis: complete.
- Rule baseline: complete.
- Selective-refiner v1: `DEVELOPMENT_GATE_FAIL`.
- Selective-refiner v2: `V2_DEVELOPMENT_GATE_FAIL`.
- Selective-refiner v3 primary: `V3_DEVELOPMENT_GATE_FAIL`.
- Prediction-only cross-model mainline: closed for the current mainline; no Legacy121 v4/v5 rescue tuning.
- Simulated evidence Stage E1: complete; direct/local utility positive, non-evidenced effect exactly zero.
- Historical Stage E2: frozen but untrained; superseded by Reboot v2 before training.
- external77-derived independent matrix: 42 RNAs x 3 predictors = 126/126 valid; remains locked.

## 6. Data Strategy

### Legacy121 v1

Development-only dataset for:

- baseline design;
- model/feature selection;
- calibration and threshold selection;
- ablation;
- simulated evidence;
- Go/No-Go decisions.

### external77-derived 42-RNA set

Locked independent test only. No feature redesign, model selection, threshold tuning, or rescue analysis may use it before R7.

## 7. Evidence Ladder

### Level E0 — Clean symbolic evidence

- positive base-pair evidence;
- unpaired-nucleotide evidence.

Purpose: mechanism/upper-bound development.

### Level E1 — Controlled noisy symbolic evidence

Frozen corruption mechanisms and candidate noise levels are used to study robustness and the need for learned trust.

### Level E2 — Real experimental evidence

Candidate modalities: SHAPE, DMS, PARS and related probing data after a separate provenance/data audit. Real probing is evidence, not GT.

## 8. Required Baselines

### B0 — Original Predictor

No modification.

### B1 — Local Hard Evidence

Completed Stage E1 local hard transformations.

### B2 — Global Evidence-Constrained Refolding

**Mandatory new baseline before learned training.**

Use the same sequence and the same delivered sparse evidence, but allow a classical folding algorithm to re-optimize the complete structure. The first frozen implementation should use a reproducible ViennaRNA/RNAfold hard-constraint protocol.

This baseline answers:

> Why not simply refold from sequence under the evidence?

### B3 — Prediction-Only Reliability Baselines

Retain as mechanistic comparators:

- rule-based conditions;
- historical v1 topology-only score;
- historical v3 fixed consensus veto;
- compatible pair-confidence/BPP baseline;
- simple cross-model agreement where semantically valid.

### B4 — Evidence-Masked Learned Control

Matched learned condition without usable evidence, required to attribute any gain to evidence rather than model capacity.

## 9. Candidate Learned Method

Internal working name: **Evidence Reconciliation Network (ERN)**.

The historical E2 DeepSets-style architecture may be reused as an implementation starting point because it already supports a source-agnostic candidate branch and permutation-invariant evidence-set encoding.

However, the historical E2 success criteria are superseded. A new R4 protocol must be frozen after R2/R3 and must compare against B0/B1/B2/B4.

No Transformer/GNN/foundation-model escalation is authorized unless a simple architecture first establishes signal beyond the strongest frozen non-learned baseline.

## 10. Metrics

### Pair reliability

Primary candidates:

- AUPRC for `DELETE`/FP;
- Brier score;
- ECE;
- reliability diagrams;
- precision among highest-risk pairs.

AUROC is secondary.

### Refinement utility

Mandatory:

```text
TP_preservation = TP_after / TP_before
FP_removal = (FP_before - FP_after) / FP_before
modification_precision = beneficial_edits / modified_pairs
```

Also report Precision, Recall, macro/micro F1, edit counts, beneficial/harmful decomposition.

### Risk–utility

Primary comparison should use curves/operating points such as:

```text
x-axis: TP loss or 1 - TP preservation
y-axis: FP removal
```

The main question is whether post-hoc reconciliation gives a better correction-preservation trade-off than B2, not whether it achieves a small isolated F1 gain.

### Non-evidenced effects

Report separately:

- non-evidenced modification precision;
- non-evidenced FP removal;
- non-evidenced TP loss.

### Evidence efficiency

Report benefit per delivered evidence item, including `FP_removed / evidence_items` and optionally `Delta_F1 / evidence_items`.

### Matching robustness

Exact canonical-pair matching remains primary. Add +/-1-endpoint flexible matching only as a separate final robustness analysis; never rewrite historical exact results.

## 11. Experimental Stages

### R0 — Literature & novelty freeze

**Status: COMPLETE FOR REBOOT.**

### R1 — Task/protocol redefinition

**Status: CURRENT.**

Freeze project documents and supersede historical E2 training before any learned run.

### R2 — Global constrained-refolding baseline

Freeze and implement a clean hard-constraint global-refolding protocol on Legacy121 using the same clean evidence manifestations as B1 wherever semantics match.

Required outputs:

- full-structure metrics;
- TP preservation;
- FP removal;
- modification precision;
- direct/local/non-evidenced decomposition;
- evidence efficiency;
- source-wise summaries;
- exact identity/constraint compliance checks.

### R3 — Reliability baseline suite

Assemble BPP/structural/consensus/history comparators under the new pair-reliability and risk-control metrics.

### R4 — Clean learned evidence reconciliation

Freeze a new protocol only after R2/R3 are complete. Train simple ERN and compare against B0/B1/B2/B4.

### R5 — Noise robustness

Evaluate controlled symbolic evidence corruption. Decide prospectively whether a trust mechanism is required.

### R6 — Cross-predictor transfer

Run source-wise and LOMO analyses. Promote `model-agnostic` only if supported.

### R7 — Locked independent external test

Open external77 once after model, features, calibration, thresholds, and analysis are frozen.

### R8 — Real evidence

Audit and evaluate real probing modalities only if R4-R7 justify continuation.

### R9 — Final calibrated selective correction

Freeze KEEP/DELETE/ABSTAIN policy, final ablations, statistics, and claims.

### Optional — 2D -> 3D validation

Only after the 2D task is stable.

## 12. Go / No-Go Gates

### Gate A — Post-hoc necessity

If global constrained refolding dominates the post-hoc approach across the relevant TP-preservation / FP-removal trade-off, stop the post-hoc mainline.

### Gate B — Learned reconciliation utility

At a prospectively frozen high-preservation operating point (current target `TP_preservation >= 0.99`), the learned method must improve FP removal over the strongest frozen non-learned baseline and must not depend on only one source.

### Gate C — Noise robustness

If 5-10% controlled evidence noise causes negative structure utility or unsafe TP loss, do not make a real-evidence claim without first freezing a new trust mechanism.

### Gate D — Independent generalization

external77 is opened once. If the development effect does not preserve direction, do not claim cross-dataset generalization and do not tune on external77 to rescue the result.

## 13. Paper Story if Successful

```text
Prediction-only topology/consensus is insufficient for safe correction
-> sparse external evidence has direct/local utility
-> global constrained refolding is a strong traditional comparator
-> post-hoc reconciliation preserves source-predictor information while using evidence
-> calibrated reliability gives a better correction-preservation trade-off
-> effect survives noise, predictor shifts, and locked independent data
-> optional real probing and 3D validation establish practical relevance
```

## 14. Immediate Next Step

**Do not train historical Stage E2.**

Next task:

> **R2 — Freeze and implement the global evidence-constrained refolding baseline.**

Detailed rationale and reboot contract: `docs/project_reboot_v2.md`.
