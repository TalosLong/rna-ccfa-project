# Current Status

Last updated: 2026-09-02

## Current Stage

**PROJECT REBOOT v2 — R2_INTERPRETATION_COMPLETE / R3_PROTOCOL_FROZEN**

**Next state: `READY_FOR_R3_EXECUTION`**

Current working direction:

> **Post-hoc Evidence Reconciliation for RNA Secondary Structure Predictions**

R0 literature/novelty freeze and R1 task redefinition are complete. R2 protocol
v1.0.2 prospectively freezes both crossing and minimum-loop solver-capability
eligibility. The amended universe contains 7,153 eligible B2 realizations:
3,523/3,630 pair and 3,630/3,630 unpaired. All 7,153 existing fixed-command
outputs passed row-level provenance, parsing, validity, and hard-constraint
checks; no new RNAfold calls were required. Formal matched B0/B1/B2
summarization is complete. Overall Macro/Micro F1 is 0.878635/0.861068 for B0,
0.889352/0.872422 for B1, and 0.924648/0.904747 for B2. The formal R2
interpretation is frozen as `POSTHOC_HEADROOM_PLAUSIBLE`: B2 is a strong
comparator but its Macro/Micro TP preservation of 0.975358/0.981767, 4,752
lost TP, and 10,823 new FP leave a plausible high-preservation question.
Gate A is `GATE_A_DEFERRED_R4_REQUIRED`, neither PASS nor FAIL.

The R3 Pair-Reliability Baseline Suite protocol is frozen before execution.
Track P and Track E are separate; the primary label is DELETE/FP on original
predicted pairs, primary discrimination is AUPRC, and the primary safety point
is `TP_preservation >= 0.99`. The frozen ViennaRNA 2.4.17 CLI can export
deterministic parseable BPP matrices on a toy, so P4 is feasible without a
Python RNA binding or software installation. No formal R3 metric has been run.

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
R2 Global constrained-refolding baseline    COMPLETE
R3 Reliability baseline suite               PROTOCOL FROZEN / NOT EXECUTED
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

## Completed Task — R2 Global Constrained Refolding

- Protocol v1.0.2 was frozen before formal metrics. It adds a whole-manifest
  minimum-loop capability rule (`j-i>3`) to the historical v1.0.1 crossing
  rule without changing the solver or delivered evidence.
- The coordinate-only audit found 3,523 eligible, 87 crossing-ineligible, and
  20 minimum-loop-ineligible pair manifests, with no overlap; all 3,630
  unpaired manifests remain eligible.
- Every one of 7,153 amended eligible outputs was validated and reused; no new
  RNAfold call was needed and eligible constraint satisfaction was 100%.
- B2 achieved overall Macro/Micro F1 0.924648/0.904747 versus
  0.889352/0.872422 for B1 and 0.878635/0.861068 for B0.
- B2 preserved 0.975358 Macro / 0.981767 Micro of original TP and removed
  0.775728 Macro / 0.645883 Micro of original FP. It made 43,475 beneficial
  and 15,575 harmful changes.
- NON_EVIDENCED propagation was net beneficial (36,027 beneficial versus
  15,575 harmful) but not uniformly safe (Micro modification precision
  0.698171).
- Full results and the retained historical blocker record are in
  `docs/global_constrained_refolding_r2_results.md`.
- R2 supplies the frozen future Gate A comparator; it does not decide Gate A
  without a future R4 result.

## Completed Task — R2 Interpretation and R3 Protocol Freeze

- `docs/r2_scientific_interpretation.md` strictly separates empirical result,
  interpretation, and future hypothesis.
- R2 interpretation status is `POSTHOC_HEADROOM_PLAUSIBLE`.
- Gate A status is `GATE_A_DEFERRED_R4_REQUIRED`; no PASS/FAIL is assigned
  before a future R4 comparison.
- `docs/reliability_baseline_r3_protocol.md` freezes separate prediction-only
  and evidence-conditioned tracks, original-pair labels, R2 matched-universe
  joins, dual aggregation, calibration restrictions, deletion-only risk curves,
  validation-only threshold selection, and strongest-comparator rules.
- `docs/reliability_baseline_r3_implementation_plan.md` records the future
  scripts, reusable assets, artifact layout, integrity checks, and execution
  gate without implementing or running the formal suite.
- BPP feasibility is `R3_BPP_BASELINE_FEASIBLE_WITH_FROZEN_CLI` using
  `/usr/bin/RNAfold` 2.4.17 and the frozen partition-function interface.

## Current Restrictions

- **Do not train historical Stage E2.**
- **Do not access external77.**
- **Do not introduce a larger learned architecture before R2/R3 and a new frozen R4 protocol.**
- **Do not retune v1/v2/v3 on Legacy121 to rescue old claims.**
- **Do not alter or expand the frozen R2 v1.0.2 comparison universe.**
- **Do not change the frozen R3 score definitions, threshold rule, or
  aggregation semantics after viewing held-out results.**
- **Do not begin R4 until formal R3 execution is complete and a new R4
  protocol is prospectively frozen.**

Detailed current-mainline documents:

- `docs/project_reboot_v2.md`
- `docs/reboot_v2_decisions.md`
- `docs/reboot_v2_claim_evidence_map.md`
- `plan/research_plan.md`
- `plan/timeline.md`
- `tasks/TODO.md`
