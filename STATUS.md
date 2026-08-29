# Current Status

Last updated: 2026-08-29

## Current Stage

**PROJECT REBOOT v2 ACTIVE**

The previous mainline `Evidence-Guided Selective Refinement for RNA Secondary Structure Prediction` has been superseded at the planning level by:

> **Post-hoc Evidence Reconciliation for RNA Secondary Structure Predictions**

The reboot occurred **before any historical Stage E2 model was trained**.

Current execution state:

- R0 Literature & novelty freeze: **COMPLETE FOR REBOOT**.
- R1 Task/protocol redefinition: **IN PROGRESS / DOCUMENT FREEZE**.
- R2 Global evidence-constrained refolding baseline: **NEXT EXPERIMENT**.
- Historical `evidence_guidance_stage_e2_v1`: **FROZEN BUT SUPERSEDED BEFORE TRAINING**.
- No new learned model is authorized until R2 and R3 are completed and a new R4 protocol is frozen.

## Rebooted Scientific Question

> Given an RNA sequence, an already-computed secondary-structure prediction from an existing predictor, and sparse external structural evidence, can a post-hoc method identify and selectively correct residual pair errors while preserving predictor information that is already correct?

The mandatory comparison is now:

```text
Original predictor
vs
local evidence enforcement
vs
global evidence-constrained refolding
vs
post-hoc evidence reconciliation
```

The project must explicitly answer:

> **Why not simply refold the RNA under the same evidence?**

## Novelty Boundary

The project no longer treats the following as candidate main contributions by themselves:

- basic RNA pairing/stem/stacking rules;
- isolated-pair or short-stem cleanup;
- thermodynamic pair probability/confidence;
- thermodynamic + evolutionary evidence fusion;
- multi-predictor consensus;
- evidence-constrained global folding;
- generic pair-level post-hoc quality assessment as an abstract ML formulation.

The current candidate contribution is narrower:

> **Predictor-output-preserving evidence reconciliation for RNA secondary-structure predictions.**

`Model-agnostic`, `unseen-predictor`, `real-evidence robust`, and `3D benefit` remain unconfirmed candidate claims.

## Preserved Historical Results

No prior result is deleted or reinterpreted.

### Infrastructure / Error Analysis

- Legacy121 v1 manifest and normalization complete.
- 121 RNAs x 3 sources = 363 normalized prediction records valid.
- Shared exact canonical-pair evaluator complete.
- Pair-level missing/FP/wrong-partner analysis complete.
- Strict stem extraction/matching taxonomy complete.
- Sequence-separation analysis complete.

### Legacy121 Infrastructure Baseline

| Predictor | Macro F1 | Micro F1 | TP | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| RNAfold | 0.905818 | 0.874443 | 1473 | 220 | 203 |
| PETfold | 0.896849 | 0.865680 | 1463 | 241 | 213 |
| trRosettaRNA2 native SS | 0.842871 | 0.818717 | 1461 | 432 | 215 |

These are infrastructure baselines, not refinement claims.

### Rule / Learned Prediction-Only Development

- Rule-based pilot: complete.
- selective-refiner v1: `DEVELOPMENT_GATE_FAIL`.
- selective-refiner v2: `V2_DEVELOPMENT_GATE_FAIL`.
- selective-refiner v3 primary: `V3_DEVELOPMENT_GATE_FAIL`.
- Prediction-only cross-model mainline: **CLOSED FOR THE CURRENT MAINLINE**.
- No post-hoc Legacy121 v4/v5 rescue tuning is authorized.

The v1-v3 sequence established that prediction-only topology/agreement contains some error/protection signal, but not enough to support a preregistered source-general safe refiner.

### Simulated Evidence Development

- simulated-evidence generator: complete and reproducible.
- Stage E1 clean hard-baseline evaluation: complete.
- Clean evidence has strong direct/local correction utility.
- `NON_EVIDENCED_EFFECT == 0` for Stage E1 because the transformations are local by construction.
- Stage E1 is retained as the rebooted B1 local-hard baseline.

### Historical Stage E2

- `evidence_guidance_stage_e2_v1` was frozen before training.
- It contains a usable candidate branch + DeepSets-style evidence encoder design.
- **It must not be executed as originally planned.**
- Its architecture may be reused later as an implementation starting point for R4, but its original success criteria are superseded by Reboot v2 because they did not include the mandatory global constrained-refolding comparator.

## Independent Test Status

The former PETfold external blocker is closed.

external77-derived 42-RNA independent set:

- RNAfold: 42/42 valid.
- PETfold: 42/42 valid under reproduced historical single-sequence condition.
- trRosettaRNA2 native SS: 42/42 valid under recovered query-only condition.
- normalized matrix: **126/126 PASS**.

This dataset remains **LOCKED** until R7. It may not be used for feature selection, threshold tuning, architecture selection, or rescue analysis.

## Reboot Data Roles

### Legacy121

Development only:

- baseline design;
- architecture and feature selection;
- calibration/threshold selection;
- ablation;
- simulated evidence;
- Go/No-Go decisions.

### external77-derived 42

Locked independent evaluation only.

## Evidence Ladder

- **E0 Clean symbolic evidence**: positive pair / unpaired nucleotide; mechanism and upper-bound development.
- **E1 Controlled noisy symbolic evidence**: frozen corruption levels; robustness/trust testing.
- **E2 Real experimental evidence**: candidate SHAPE/DMS/PARS or related modalities after dedicated audit.

Real probing measurements are evidence, not ground truth.

## Mandatory Baselines After Reboot

### B0 — Original Predictor

No modification.

### B1 — Local Hard Evidence

Completed Stage E1 conditions.

### B2 — Global Evidence-Constrained Refolding

**NEXT mandatory baseline.**

Use the same sequence and delivered clean evidence while allowing a classical folding algorithm to re-optimize the whole RNA structure. Initial target: reproducible ViennaRNA/RNAfold hard constraints.

### B3 — Prediction-Only Reliability Baselines

Retain frozen/mechanistic comparators such as rule-based scores, historical v1 topology score, historical v3 fixed consensus veto, compatible BPP and simple agreement.

### B4 — Evidence-Masked Learned Control

Required for future R4 learned experiments.

## Reboot Evaluation

### Pair Reliability

Planned primary metrics:

- AUPRC for DELETE/FP;
- Brier score;
- ECE / reliability diagram;
- high-risk-pair precision;
- AUROC as secondary.

### Refinement Utility

Mandatory:

```text
TP_preservation = TP_after / TP_before
FP_removal = (FP_before - FP_after) / FP_before
modification_precision = beneficial_edits / modified_pairs
```

Also report Precision, Recall, macro/micro F1 and full edit accounting.

### Risk–Utility

Primary comparison should emphasize TP-loss vs FP-removal trade-off rather than only aggregate Delta F1.

### Non-Evidenced Effects

Report separately:

- non-evidenced modification precision;
- non-evidenced FP removal;
- non-evidenced TP loss.

The question is whether propagation is useful, not whether it merely occurs.

### Evidence Efficiency

Report correction benefit per delivered evidence item.

### Pair Matching

Exact canonical-pair matching remains primary for continuity. Final paper-level robustness may add a separately reported +/-1 endpoint flexible match analysis without changing historical exact results.

## Reboot Roadmap

```text
R0 Literature & novelty freeze              COMPLETE
R1 Task/protocol redefinition               CURRENT
R2 Global constrained-refolding baseline    NEXT
R3 Reliability baseline suite
R4 Clean learned evidence reconciliation
R5 Controlled noise robustness
R6 Cross-predictor transfer / LOMO
R7 Locked external77 independent test
R8 Real experimental evidence
R9 Final calibrated KEEP/DELETE/ABSTAIN
Optional 2D -> 3D validation
```

## Go / No-Go Gates

### Gate A — Post-hoc necessity

If global constrained refolding dominates the post-hoc approach across relevant TP-preservation / FP-removal trade-offs, stop the post-hoc mainline.

### Gate B — Learned utility

At a prospectively frozen high-preservation operating point (current target `TP_preservation >= 0.99`), the learned method must improve FP removal over the strongest frozen non-learned baseline and must not depend on one source only.

### Gate C — Noise robustness

If 5-10% evidence noise causes negative structure utility or unsafe TP loss, do not advance to a real-evidence claim without a prospectively frozen trust mechanism.

### Gate D — Independent generalization

external77 is opened once under a frozen protocol. If the effect fails to preserve direction, no cross-dataset generalization claim and no tuning on external77.

## Current Blockers

No external-data blocker currently prevents R2.

The main scientific blocker is now intentional:

> The project must establish the behavior of a strong classical global evidence-constrained refolding baseline before any new learned evidence model is trained.

## Immediate Next Steps

1. Finish R1 authoritative-document freeze.
2. Audit installed ViennaRNA/RNAfold version and hard-constraint interface.
3. Freeze `docs/global_constrained_refolding_r2_protocol.md` before executing evaluation.
4. Implement R2 on Legacy121 clean evidence only.
5. Compare B0/B1/B2 using exact metrics, preservation, FP removal, direct/local/non-evidenced decomposition and evidence efficiency.
6. Do not access external77.
7. Do not train historical Stage E2.

Detailed reboot contract: `docs/project_reboot_v2.md`.
