# Timeline — Project Reboot v2

Last updated: 2026-08-31

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

Completion gate:

Strongest non-learned comparator must be frozen before R4 training.

---

## R4 — Clean Learned Evidence Reconciliation

Goal:

Test whether a simple learned post-hoc method uses clean sparse evidence better than all frozen baselines.

Requirements before training:

- R2 complete;
- R3 complete;
- new R4 protocol frozen;
- B0/B1/B2/B4 comparison fixed;
- calibration and operating-point procedure fixed;
- external77 still locked.

Candidate implementation:

Reuse the historical E2 candidate/evidence encoder as a starting architecture, but under new reboot success criteria.

Primary Go/No-Go:

At a prospectively frozen high-preservation operating point, learned reconciliation must improve FP removal over the strongest frozen non-learned baseline and not be driven by one source only.

---

## R5 — Controlled Noise Robustness

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
-> R3 reliability baselines
-> R4 learned clean evidence reconciliation
```

**Historical Stage E2 training is not an authorized next step.**
