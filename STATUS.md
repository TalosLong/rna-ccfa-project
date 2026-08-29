# Current Status

Last updated: 2026-08-29

## Current Stage

**PROJECT REBOOT v2 — R2_PROTOCOL_AMENDED — READY_FOR_R2_EXECUTION**

Current working direction:

> **Post-hoc Evidence Reconciliation for RNA Secondary Structure Predictions**

R0 literature/novelty freeze is complete. R1 documentation/task redefinition is complete. R2 environment/interface audit, crossing-policy amendment, coverage audit, matched-universe freeze, and aggregation freeze are complete. Formal R2 execution is authorized on eligible manifests only; crossing manifests remain excluded as a solver-capability condition.

The historical `evidence_guidance_stage_e2_v1` protocol remains frozen as provenance but was superseded **before training**. It must not be executed as the current next step.

## Rebooted Scientific Question

> Given an RNA sequence, an already-computed secondary-structure prediction from an existing predictor, and sparse external structural evidence, can a post-hoc method identify and selectively correct residual pair errors while preserving predictor information that is already correct?

Mandatory comparison:

```text
B0 Original predictor
vs
B1 local hard evidence enforcement
vs
B2 global evidence-constrained refolding
vs
future B4/R4 post-hoc learned evidence reconciliation
```

The project must explicitly answer:

> **Why not simply refold the RNA under the same evidence?**

## Novelty Boundary

Do not claim novelty for these components by themselves:

- basic RNA pairing/stem/stacking rules;
- isolated-pair or short-stem cleanup;
- pair probability/confidence;
- thermodynamic + evolutionary evidence fusion;
- predictor consensus;
- evidence-constrained global folding;
- generic pair-level post-hoc QA as an abstract ML task;
- benchmark normalization/evaluator infrastructure.

Current candidate contribution:

> **Predictor-output-preserving evidence reconciliation for RNA secondary-structure predictions.**

`Model-agnostic`, `unseen-predictor`, `real-evidence robust`, and `3D benefit` remain candidate claims only.

## Preserved Historical Results

No prior result is deleted or reinterpreted.

### Infrastructure and error analysis

- Legacy121 v1: 121 RNAs, 363 normalized source predictions.
- RNAfold / PETfold / trRosettaRNA2 native SS each have 121 valid records.
- shared exact canonical-pair evaluator complete.
- pair-level missing/FP/wrong-partner analysis complete.
- strict stem extraction/matching taxonomy complete.
- sequence-separation analysis complete.

### Legacy121 infrastructure baseline

| Predictor | Macro F1 | Micro F1 | TP | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| RNAfold | 0.905818 | 0.874443 | 1473 | 220 | 203 |
| PETfold | 0.896849 | 0.865680 | 1463 | 241 | 213 |
| trRosettaRNA2 native SS | 0.842871 | 0.818717 | 1461 | 432 | 215 |

These are infrastructure baselines, not refinement claims.

### Prediction-only refinement development

- Rule baseline: complete.
- selective-refiner v1: `DEVELOPMENT_GATE_FAIL`.
- selective-refiner v2: `V2_DEVELOPMENT_GATE_FAIL`.
- selective-refiner v3 primary: `V3_DEVELOPMENT_GATE_FAIL`.
- prediction-only cross-model mainline: **CLOSED FOR CURRENT MAINLINE**.
- no Legacy121 v4/v5 rescue tuning is authorized.

### Simulated evidence development

- clean simulated evidence generator: complete/reproducible.
- Stage E1 local hard baseline: complete.
- direct/local utility: positive under clean evidence semantics.
- `NON_EVIDENCED_EFFECT == 0` because B1 is local by construction.
- historical E2 architecture remains a candidate implementation asset only.

## Independent Test

external77-derived 42-RNA set is ready and locked:

- RNAfold: 42/42 valid;
- PETfold: 42/42 valid under reproduced historical single-sequence condition;
- trRosettaRNA2 native SS: 42/42 valid under recovered query-only condition;
- normalized matrix: **126/126 PASS**.

Role: **R7 one-shot independent evaluation only**. No development/tuning access.

## Evidence Ladder

- **E0 clean symbolic**: positive pair / unpaired nucleotide; mechanism and upper-bound development.
- **E1 controlled noisy symbolic**: robustness/trust testing.
- **E2 real experimental evidence**: candidate SHAPE/DMS/PARS after dedicated audit.

Real probing signals are evidence, not GT.

## Reboot Evaluation

### Pair reliability

Planned primary metrics:

- AUPRC for DELETE/FP;
- Brier score;
- ECE / reliability diagrams;
- high-risk-pair precision;
- AUROC as secondary.

### Refinement utility

Mandatory:

```text
TP_preservation = TP_after / TP_before
FP_removal = (FP_before - FP_after) / FP_before
modification_precision = beneficial_edits / modified_pairs
```

Also retain Precision, Recall, macro/micro F1 and complete edit accounting.

### Risk–utility

Primary method comparison emphasizes TP loss versus FP removal rather than only aggregate `Delta F1`.

### Non-evidenced effect

Report non-evidenced modification precision, FP removal and TP loss. The question is whether propagation is useful rather than merely present.

### Evidence efficiency

Report correction benefit per delivered evidence item.

### Matching

Exact canonical-pair equality remains primary. Final paper-level robustness may separately add +/-1 endpoint flexible matching without rewriting historical exact results.

## Roadmap

```text
R0 Literature & novelty freeze              COMPLETE
R1 Task/protocol redefinition               COMPLETE
R2 Global constrained-refolding baseline    PROTOCOL_AMENDED / READY_FOR_R2_EXECUTION
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

If matched global constrained refolding dominates the relevant TP-preservation / FP-removal trade-off, stop the post-hoc mainline.

### Gate B — Learned utility

At a prospectively frozen high-preservation operating point (current target `TP_preservation >= 0.99`), a future learned R4 method must improve FP removal over the strongest frozen non-learned baseline and not be driven by one source only.

### Gate C — Noise robustness

If 5-10% controlled evidence noise causes negative structure utility or unsafe TP loss, do not advance to a real-evidence claim without a prospectively frozen trust mechanism.

### Gate D — Independent generalization

Open external77 once. If the development effect does not preserve direction, no cross-dataset generalization claim and no external77 rescue tuning.

## Current Task — R2 Protocol Freeze

Before any full R2 run:

1. audit installed ViennaRNA/RNAfold version and hard-constraint interface;
2. define `POSITIVE_PAIR_EVIDENCE` -> hard pair constraint mapping;
3. define `UNPAIRED_NUCLEOTIDE_EVIDENCE` -> hard unpaired constraint mapping;
4. define unsatisfiable/incompatible constraint behavior;
5. freeze whether pair and unpaired channels remain separate;
6. reuse the clean Legacy121 evidence manifests without external77 access;
7. freeze parser/validation/provenance requirements;
8. create `docs/global_constrained_refolding_r2_protocol.md` before full evaluation.

### R2 audit and amendment result

- `/usr/bin/RNAfold`, version 2.4.17, is the frozen candidate executable;
  Python `RNA` bindings are absent in all three probed environments.
- `()` with `--enforceConstraint` expresses a specific forced partner, and
  `x` expresses forced unpaired; project coordinates use the unique
  `project_position + 1` ViennaRNA conversion.
- Seven toy/coordinate/unsatisfiable-constraint checks passed, including
  parser round-trip and nested-pair checks.
- The clean suite has 7,260 manifests; 87/3,630
  `POSITIVE_PAIR_EVIDENCE` manifests across 11 RNAs contain crossing delivered
  pairs. Standard non-pseudoknot ViennaRNA DBN constraints cannot express these
  pairs simultaneously. Prospective amendment v1.0.1 excludes those whole
  manifests without modifying evidence.
- Eligibility, density/seed/RNA coverage, matched B1 filtering, and
  RNA-balanced macro aggregation are frozen before execution.
- Authoritative state is `R2_PROTOCOL_AMENDED — READY_FOR_R2_EXECUTION`.

## Current Restrictions

- **Do not train historical Stage E2.**
- **Do not access external77.**
- **Do not introduce a larger learned architecture before R2/R3 and a new frozen R4 protocol.**
- **Do not retune v1/v2/v3 on Legacy121 to rescue old claims.**
- **Do not begin formal R2 execution until the crossing-evidence semantics are
  resolved by a new prospective decision.**

Detailed current-mainline documents:

- `docs/project_reboot_v2.md`
- `docs/reboot_v2_decisions.md`
- `docs/reboot_v2_claim_evidence_map.md`
- `plan/research_plan.md`
- `plan/timeline.md`
- `tasks/TODO.md`
