# Timeline — Project Reboot v2

Last updated: 2026-09-08

This timeline supersedes the original Phase 0-8 schedule. Historical Phase 0/1/rule/v1-v3/E1 work is preserved as completed development evidence; the current mainline restarts at R1/R2.

## Historical Work — Complete / Closed

- Phase 0 normalization/evaluator infrastructure: complete.
- Phase 1 error taxonomy and descriptive analysis: complete.
- Rule-based refinement pilot: complete.
- Selective-refiner v1: `DEVELOPMENT_GATE_FAIL`.
- Selective-refiner v2: `V2_DEVELOPMENT_GATE_FAIL`.
- Selective-refiner v3 primary: `V3_DEVELOPMENT_GATE_FAIL`.
- Prediction-only cross-model mainline: closed; no Legacy121 v4/v5 rescue tuning.
- Simulated evidence Stage E1: complete.
- Historical Stage E2 protocol: frozen but untrained; superseded before training by Reboot v2.
- external77 historical source-protocol gate: PASS; 126/126 normalized independent records complete and locked.

---

## R0 — Literature & Novelty Freeze

**Status: COMPLETE FOR REBOOT**

Goal: define what is already prior art and what the rebooted project may legitimately test.

Frozen boundary:

- basic RNA structural rules are not novelty;
- pair probability/confidence is not novelty;
- predictor consensus is not novelty;
- evidence-constrained global folding is not novelty;
- generic post-hoc pair QA as an abstract task is not novelty.

Candidate research gap:

> predictor-output-preserving evidence reconciliation for RNA secondary-structure predictions.

---

## R1 — Task and Protocol Redefinition

**Target: immediate / current**

Goal: update all authoritative documents before new training.

Tasks:

- [x] Create `docs/project_reboot_v2.md`.
- [x] Replace project scientific question in `CONTEXT.md`.
- [x] Replace `plan/research_plan.md`.
- [x] Update `STATUS.md`.
- [x] Update `tasks/TODO.md`.
- [x] Update `docs/decisions.md` and claim boundary.
- [x] Update `AGENTS.md` execution rules.
- [x] Mark historical E2 as superseded-before-training everywhere it appears as the next action.

Completion gate:

No authoritative file should instruct Codex to train historical E2.

---

## R2 — Global Evidence-Constrained Refolding Baseline

**Status: COMPLETE — PROTOCOL v1.0.2**

Goal:

Answer the foundational question:

> Why not simply refold the RNA from sequence under the same sparse evidence?

Primary baseline:

- reproducible ViennaRNA/RNAfold hard-constraint global refolding;
- same Legacy121 RNAs;
- same clean symbolic evidence manifests where constraint semantics match;
- no learned model;
- no external77 access.

Required analyses:

- Original vs local-hard vs global-refold;
- exact pair metrics;
- TP preservation;
- FP removal;
- modification precision;
- direct/local/non-evidenced decomposition;
- evidence efficiency;
- source-wise effects;
- constraint compliance and output validity.

Completion gate:

R2 protocol must be frozen before execution. Results determine whether post-hoc preservation has enough headroom to justify R4.

Completion checkpoint: protocol v1.0.2 prospectively refroze 7,153 eligible
rows (3,523 pair; 3,630 unpaired). All were validated at 100% constraint
satisfaction, formal matched B0/B1/B2 analysis completed, and the 107
capability exclusions were kept outside the metric universe. Gate A remains
undecided because R4 does not yet exist.

---

## R3 — Reliability Baseline Suite

**Status: COMPLETE**

Goal:

Place all simple confidence/reliability alternatives under one evaluation framework.

Candidate comparators:

- structural/rule score;
- historical v1 topology score;
- historical v3 fixed consensus veto;
- compatible thermodynamic BPP;
- cross-model agreement.

Metrics:

- AUPRC;
- Brier score;
- ECE;
- risk–utility curves;
- TP preservation / FP removal.

Frozen execution contract:

- separate Track P prediction-only and Track E evidence-conditioned settings;
- original predicted pair as the unit and DELETE/FP as the positive class;
- AUPRC primary, AUROC secondary, and positive prevalence always reported;
- event-pooled and RNA-balanced summaries with RNA as biological cluster;
- deletion-only risk–utility and validation-only
  `TP_preservation >= 0.99` threshold selection;
- frozen RNAfold 2.4.17 BPP CLI, historical v1/v3, exact agreement, local
  conflict, and B2 disagreement baselines;
- no retraining, retuning, external77, or R4.

Completion gate:

Completion checkpoint: the prospective ECE amendment preceded formal metrics;
all P0--P4 and E1/E2 baselines completed. P3 `V3_VETO2_FIXED` is the strongest
Track P no-new-training comparator and E1 local conflict is the strongest
Track E comparator at the frozen safety point. R4 remains unstarted.

---

## R4 — Clean Learned Evidence Reconciliation

**Status: `R4_COMPLETE` — `R4_GATE_B_FAIL`**

Goal:

Test whether a simple learned post-hoc method uses clean sparse evidence better than all frozen baselines.

Protocol-freeze requirements:

- [x] R2 complete;
- [x] R3 complete and scientifically interpreted;
- [x] new R4 protocol frozen;
- [x] B0/B1/B2, R3-P3, R3-E1, and B4 comparisons fixed;
- [x] calibration and validation-only operating-point procedure fixed;
- [x] exact Gate B and multi-source rule fixed;
- [x] external77 remains locked;
- [x] implement and execute frozen R4 (100/100 runs).

Frozen starting implementation:

Reuse the historical E2 candidate/evidence encoder as a starting architecture, but under new reboot success criteria.

Primary Go/No-Go:

Held-out event-pooled and RNA-balanced TP preservation must both be at least
0.99; RNA-balanced FP removal must be strictly above 0.489748 and event-pooled
FP removal strictly above 0.347816. Improvement over P3 must occur in at least
two sources, including RNAfold or PETfold. Paired B4 is a mandatory separate
evidence-attribution control, not an additional numerical Gate B bar. Failure
does not authorize automatic architecture escalation.

Completion checkpoint: ERN primary combined event/RNA preservation was
0.989682/0.991936 and FP removal was 0.475531/0.660806. The event preservation
condition failed; all other numerical and source-consistency Gate B conditions
passed. Gate A is `GATE_A_PASS_POSTHOC_NONDOMINATED`; Gate B is
`R4_GATE_B_FAIL`. Historical E2 remains superseded, and R5/noisy evidence,
external77, and real evidence are not authorized.

---

## R4 Postmortem — Failure Mechanism and Future Path

**Status: `R4_POSTMORTEM_COMPLETE`**

Frozen-output diagnostics attributed 56.0% of ERN's net additional FP removal
over matched B4 to perfectly precise `LOCAL_CONFLICT`, and 44.0% to
`NON_EVIDENCED`. All material additional TP loss occurred in
`NON_EVIDENCED`; DIRECT evidence protected TP. Loss and benefit were
source-broad, while the positive-pair preservation advantage was not stable
across folds. These observations do not alter `R4_GATE_B_FAIL`.

Future-path decision:

```text
NEW_HYPOTHESIS_JUSTIFIED_PROTOCOL_NOT_FROZEN
```

At that checkpoint, the only next authorized task was
`FREEZE_NEW_PROSPECTIVE_CONSERVATIVE_RECONCILIATION_PROTOCOL`. The possible
Trust-Gated / Locality-Aware Evidence Reconciliation concept is an untested
hypothesis, not an authorized implementation or R4 rescue.

Legacy121 is development/hypothesis-generation data for any post-R4
method. external77 remains unopened and reserved for one-shot independent
evaluation only after the complete future method and analysis plan are frozen.

---

## Conservative Evidence Reconciliation Development

**Status: `CONSERVATIVE_RECONCILIATION_DEVELOPMENT_COMPLETE` — `CONSERVATIVE_DEV_GATE_FAIL`**

Hypothesis:

> Most evidence-attributable useful correction can be retained while
> suppressing unsafe NON_EVIDENCED propagation.

The sole frozen primary mechanism is Context-Corroborated Evidence Gate
(CCEG). It protects DIRECT support, retains explicit E1 LOCAL_CONFLICT
deletion, and permits a NON_EVIDENCED deletion only when separately calibrated
usable-evidence and evidence-masked candidate-context risks agree above one
new validation-locked threshold. Disagreement is ABSTAIN. CER uses the exact R4
features and simple branch architecture; no postmortem-bin rule or capacity
escalation is permitted.

Legacy121 roles are development train/validation/assessment. The new
`CONSERVATIVE_DEV_GATE` retains the dual 0.99 safety philosophy, P3 FP-removal
bars and source consistency, and adds NON_EVIDENCED safety plus matched
evidence-attribution/gain-retention requirements. It is a development decision,
not independent confirmation.

Completion checkpoint:

```text
200/200 training runs complete
200/200 branch calibrations complete
100/100 policy calibrations and threshold seals complete
100/100 sealed development-assessment evaluations complete
CONSERVATIVE_DEV_GATE_FAIL
```

CER passed the overall safety/utility, source, evidence-gain, and gain-retention
conditions. It failed the two matched-control NON_EVIDENCED preservation
conditions. At that checkpoint the next authorized task was
`PAPER_STORY_AND_RESULTS_CONSOLIDATION`. R5 remains unauthorized; external77
remains locked and one-shot.

---

## Paper Story and Results Consolidation

**Status: `PAPER_STORY_AND_RESULTS_CONSOLIDATION_COMPLETE` —
`PAPER_STORY_VIABLE_WITH_CURRENT_RESULTS`**

The consolidated paper is viable as a bounded reliability/mechanistic study,
with correction–preservation evaluation as a secondary contribution. It is not
a successful CER method paper. The frozen story links B2 non-dominance,
prediction-context signal, ERN-versus-B4 evidence attribution, scope-localized
`NON_EVIDENCED` harm, and the prospective CER matched-control failure.

The next authorized task is
`DRAFT_MANUSCRIPT_OUTLINE_AND_ASSEMBLE_FIGURE_DATA`, limited to writing and
assembling existing frozen outputs. No new experiment, R5, external77, noisy or
real evidence, R6, or 3D analysis is authorized.

---

## R5 — Controlled Noise Robustness

**Status: NOT AUTHORIZED AFTER R4 GATE B FAIL**

Goal:

Determine whether evidence reconciliation remains useful when symbolic evidence is imperfect.

Candidate noise levels:

```text
5%, 10%, 20%, 30%
```

Analyze:

- performance degradation;
- harmful edit growth;
- calibration shift;
- evidence trust/conflict behavior.

Gate:

If low noise already destroys utility/safety, do not advance to real-evidence claims without freezing a new trust mechanism first.

---

## R6 — Cross-Predictor Transfer

Goal:

Test whether the learned reliability signal transfers across source predictors.

Experiments:

- pooled multi-source;
- source-wise;
- leave-one-model-out.

Rule:

`Model-agnostic` or `unseen-predictor transfer` becomes a paper claim only if supported prospectively. Failure is reported as source dependence, not rescued by repeated Legacy121 tuning.

---

## R7 — Locked Independent Test

Dataset:

`external77`-derived 42 RNAs x 3 predictors = 126 records.

Goal:

One-shot independent evaluation after model, feature set, calibration, thresholds and analysis are frozen.

Rule:

Do not tune on external77. If the effect does not preserve direction, no cross-dataset generalization claim.

---

## R8 — Real Evidence

Goal:

Evaluate one or more experimentally grounded evidence modalities only after R4-R7 justify continuation.

Candidate modalities:

- SHAPE;
- DMS;
- PARS;
- other audited probing data.

Requirements:

- explicit dataset provenance;
- mapping from measurement to evidence representation;
- missingness/noise semantics;
- separation from GT labels.

---

## R9 — Final Calibrated Selective Correction

Goal:

Freeze final `KEEP / DELETE / ABSTAIN` policy and paper-level analysis.

Deliverables:

- final reliability calibration;
- risk–utility curves;
- evidence-efficiency curves;
- source-wise/generalization results;
- independent-test result;
- noise/real-evidence result if authorized;
- exact + flexible-match robustness;
- final statistical analysis;
- claim–evidence map.

---

## Optional — 2D -> 3D Downstream Validation

Only after the rebooted 2D task is stable.

Candidate design:

```text
Original 2D -> frozen 3D pipeline
Reconciled 2D -> same frozen 3D pipeline
GT 2D -> same frozen 3D pipeline
```

No 3D claim without reproducible paired downstream benefit.

---

## Current Immediate Sequence

```text
R1 documentation freeze
-> R2 protocol freeze
-> R2 minimum-loop blocker resolution
-> complete R2 global constrained-refolding baseline
-> R2 interpretation and R3 protocol freeze
-> execute frozen R3 reliability baselines
-> interpret R3 and prospectively decide/freeze R4 protocol
-> complete frozen R4 learned clean evidence reconciliation
-> diagnose frozen R4 outputs and choose the future path
-> freeze the prospective CER/CCEG development protocol
-> implement and execute frozen CER on Legacy121 development CV only
-> consolidate the bounded reliability/mechanistic paper story
-> draft the manuscript outline and assemble figure data from frozen artifacts
```

**Only `DRAFT_MANUSCRIPT_OUTLINE_AND_ASSEMBLE_FIGURE_DATA` is authorized next.
It may use existing frozen artifacts only. Historical Stage E2, R4/CER rescue
tuning, new scientific experiments, R5, and external77 access remain
prohibited.**
