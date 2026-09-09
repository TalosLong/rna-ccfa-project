# TODO — Project Reboot v2

Last updated: 2026-09-09

## R0 — Literature & Novelty Freeze

- [x] Establish basic RNA structural rules as prior art, not novelty.
- [x] Establish pair probability/confidence as prior art.
- [x] Establish multi-predictor consensus as prior art.
- [x] Establish evidence-constrained global folding as prior art.
- [x] Identify post-hoc pair-level QA analogues in structural bioinformatics.
- [x] Freeze candidate gap as predictor-output-preserving evidence reconciliation for RNA secondary-structure predictions.

## R1 — Project Reboot / Documentation Freeze

- [x] Create `docs/project_reboot_v2.md`.
- [x] Rewrite `CONTEXT.md` around the rebooted scientific question.
- [x] Rewrite `plan/research_plan.md`.
- [x] Rewrite `plan/timeline.md`.
- [x] Replace the execution TODO with the R0-R9 roadmap.
- [x] Update `STATUS.md` to make R2 the next experiment.
- [x] Add `docs/reboot_v2_decisions.md` as the current-mainline decision supplement.
- [x] Add `docs/reboot_v2_claim_evidence_map.md` as the reboot claim map.
- [x] Update `AGENTS.md` so Codex cannot run historical E2 training.
- [x] Remove historical E2 training as an authorized next step from current authoritative documents.

**R1 gate: PASS.**

## R2 — Global Evidence-Constrained Refolding Baseline — COMPLETE

### Protocol freeze

- [x] Audit installed ViennaRNA/RNAfold version and exact hard-constraint syntax/API; `/usr/bin/RNAfold` 2.4.17 supports the required noncrossing hard forms, with no Python `RNA` binding installed.
- [x] Define mapping from `POSITIVE_PAIR_EVIDENCE` to hard pair constraints as matching `()` plus `--enforceConstraint`; exact partner semantics verified on toys.
- [x] Define mapping from `UNPAIRED_NUCLEOTIDE_EVIDENCE` to hard unpaired constraints as `x`; exact semantics verified on toys.
- [x] Define behavior for incompatible/unsatisfiable constraints before evaluation: fail closed and retain an explicit status; never drop or reinterpret evidence.
- [x] Freeze pair and unpaired channels as separate primary R2 channels.
- [x] Audit reuse of frozen Legacy121 clean manifests; 87/3,630 pair manifests contain crossing evidence unsupported by standard non-PK ViennaRNA.
- [x] Freeze prospective v1.0.1 crossing policy: exclude whole crossing manifests without modifying delivered evidence.
- [x] Freeze prospective v1.0.2 minimum-loop policy before formal metrics:
  exclude whole pair manifests containing any `j-i<=3` exact pair without
  changing ViennaRNA or evidence.
- [x] Rebuild the coordinate-only eligibility audit: 3,523 pair eligible, 87
  crossing-ineligible, 20 minimum-loop-ineligible, no overlap; unpaired
  3,630/3,630 eligible.
- [x] Freeze matched B0/B1/B2 manifest universe and generate the manifest-ID-filtered B1 view.
- [x] Freeze coverage reporting and RNA-balanced macro / event-pooled micro aggregation semantics.
- [x] Freeze output parser, validity checks, and provenance fields in the blocked protocol/implementation plan.
- [x] Create `docs/global_constrained_refolding_r2_protocol.md`; status is `R2_PROTOCOL_BLOCKED` before full execution because of the crossing-evidence semantic blocker.

### Implementation

- [x] Implement the constrained RNAfold adapter and formal runner without modifying raw historical predictions or passing source identity/predictions into folding.
- [x] Add unit/toy tests for hard pair constraints.
- [x] Add unit/toy tests for hard unpaired constraints.
- [x] Add explicit tests/reporting for unsatisfiable and crossing constraints.
- [x] Validate toy output length, pair legality and canonical parser compatibility.
- [x] Freeze the required RNAfold version/config/command/stdout/stderr provenance fields.

### Evaluation

- [x] Invoke the frozen command for all 7,173 `R2_ELIGIBLE` realizations and retain all 87 frozen crossing skips.
- [x] Record 7,153 PASS realizations and 20 fail-closed minimum-loop constraint-satisfaction failures without deleting or substituting rows.
- [x] Verify all 1,210 zero-density realizations are identical within RNA across both channels and five seeds.
- [x] Verify historical RNAfold vs R2 0% exact pair-set identity is 121/121 as provenance context only.
- [x] Prospectively resolve the minimum-loop representability blocker through
  v1.0.2 capability eligibility, without changing evidence or ViennaRNA.
- [x] Validate and reuse all 7,153 amended eligible B2 outputs; no new
  RNAfold call required and eligible constraint compliance is 100%.
- [x] Evaluate B0 Original vs B1 local hard evidence vs B2 global constrained refolding on the complete amended Legacy121 universe.
- [x] Report exact Precision/Recall/F1.
- [x] Report TP preservation.
- [x] Report FP removal.
- [x] Report modification precision.
- [x] Map/reuse DIRECT / LOCAL_CONFLICT / NON_EVIDENCED scopes where valid.
- [x] Report non-evidenced modification precision, FP removal and TP loss.
- [x] Report evidence efficiency (`FP_removed / evidence_items` and `Delta_F1 / evidence_items`).
- [x] Report source-wise and density-wise summaries.
- [x] Verify accounting identities, scope partitions, 0% reproducibility, and
  100% amended eligible constraint compliance.
- [x] Expand `docs/global_constrained_refolding_r2_results.md` into the formal
  R2 result while retaining the historical blocker section.

### Gate A

- [x] Freeze `POSTHOC_HEADROOM_PLAUSIBLE`: B2 is strong but falls below the
  future `TP_preservation >= 0.99` safety point in both Macro and Micro
  summaries and causes material lost TP/new FP.
- [x] Record `GATE_A_DEFERRED_R4_REQUIRED`; do not assign PASS or FAIL before a
  future prospectively frozen R4 comparison.

## R3 — Reliability Baseline Suite — COMPLETE

- [x] Freeze `docs/reliability_baseline_r3_protocol.md` before execution.
- [x] Separate Track P prediction-only from Track E evidence-conditioned
  inference and freeze original predicted pair as the primary unit.
- [x] Freeze DELETE/FP as the positive label and exclude absent GT pairs from
  the candidate universe.
- [x] Freeze event-pooled and RNA-balanced summaries with RNA as the biological
  cluster/unit.
- [x] Freeze AUPRC as primary discrimination and AUROC as secondary, with
  positive prevalence always reported.
- [x] Freeze deletion-only risk–utility curves and validation-only threshold
  selection at `TP_preservation >= 0.99`.
- [x] Freeze Track P and Track E strongest-comparator selection rules.
- [x] Evaluate historical v1 topology score without retuning.
- [x] Evaluate historical v3 fixed consensus veto without retuning.
- [x] Add simple exact cross-model agreement score.
- [x] Audit predictor-independent thermodynamic BPP feasibility using only the
  existing `/usr/bin/RNAfold` 2.4.17 CLI and a toy sequence.
- [x] Freeze the feasible RNAfold BPP interface, parsing, model settings, and
  non-probabilistic-correctness interpretation; do not implement the formal
  Legacy121 run in this task.
- [x] Implement the frozen RNAfold BPP baseline without installing/upgrading
  ViennaRNA or adding the Python RNA binding.
- [x] Evaluate frozen E1 local evidence-conflict risk on R2 matched manifests.
- [x] Evaluate frozen E2 B2 survival/disagreement risk on R2 v1.0.2 matched
  manifests only.
- [x] Compute AUPRC for DELETE/FP.
- [x] Compute AUROC as secondary metric.
- [x] Compute Brier score.
- [x] Compute ECE/reliability bins under the prospective fixed-bin amendment.
- [x] Produce risk–utility curves.
- [x] Freeze both strongest no-new-training comparators before R4.

## Historical Stage E2 — Superseded Before Training

- [x] `evidence_guidance_stage_e2_v1` remains an immutable historical protocol/design artifact.
- [x] Its architecture may be reused later as a candidate implementation asset.
- [x] It is **not authorized for execution** under its historical success criteria.
- [x] Any future learned clean-evidence experiment is prospectively frozen as
  R4 after R2/R3, without executing historical E2.

## R4 — Clean Learned Evidence Reconciliation

- [x] Complete the frozen R3 scientific interpretation; retain
  `GATE_A_DEFERRED_R4_REQUIRED` without assigning PASS or FAIL.
- [x] Require R2 complete, R3 complete, and Gate A not terminating the mainline.
- [x] Freeze a new R4 protocol before training.
- [x] Define pair-level calibrated error probability as the primary learned output.
- [x] Keep `KEEP / DELETE / ABSTAIN`; no pair addition in primary R4.
- [x] Define matched evidence-masked control B4.
- [x] Freeze train-only preprocessing and validation-only calibration,
  checkpoint, and operating-point selection.
- [x] Freeze simultaneous event-pooled and RNA-balanced
  `TP_preservation >= 0.99` requirements.
- [x] Freeze exact FP-removal bars and source-consistency criteria for Gate B.
- [x] Write the implementation and artifact plan without implementing or
  executing R4.
- [x] Implement and execute the frozen simple ERN/B4 protocol (100/100 runs).
- [x] Compare B0/B1/B2, R3-P3, R3-E1, B4, and learned R4.
- [x] Report AUPRC/Brier/ECE and risk–utility curves.
- [x] Report direct/local/non-evidenced behavior and evidence efficiency.
- [x] Report source-wise behavior.
- [x] Complete R4 without accessing the external77 independent matrix.

### Gate B

- [x] Prospectively freeze Gate B as event/RNA TP preservation at least 0.99,
  RNA-balanced FP removal strictly above 0.489748, and event-pooled FP removal
  strictly above 0.347816.
- [x] Prospectively freeze the requirement that improvement not be driven by
  only one source; require matched B4 as a separate evidence-attribution test.
- [x] Freeze the rule that failure does not authorize architecture-complexity
  escalation as a rescue.
- [x] Evaluate Gate B only after the complete frozen R4 execution:
  `R4_GATE_B_FAIL` because event TP preservation was 0.989682; all other
  numerical and source-consistency conditions passed.
- [x] Apply Gate A after R4/B2 comparison:
  `GATE_A_PASS_POSTHOC_NONDOMINATED` because neither operating point dominates
  the correction-preservation plane.
- [x] Record that Gate B failure does not authorize rescue or R5.

### R4 postmortem and future-path decision

- [x] Verify frozen R4 candidate/held-out artifact hashes before diagnostics.
- [x] Quantify the 0.000318 Gate B miss and descriptive lost-TP event scale.
- [x] Decompose ERN/B4 FP-removal and TP-loss differences by scope and source.
- [x] Decompose `NON_EVIDENCED` behavior by channel, density, separation, stem
  position/boundary, pair type, P2 agreement, P4 risk, ERN risk, and ERN–B4
  risk shift.
- [x] Test whether the positive-pair preservation difference is stable across
  seeds and folds without selecting a channel.
- [x] Freeze the supported/unsupported R4 claim boundary.
- [x] Record that post-R4 methods cannot use Legacy121 held-out folds as
  pristine confirmation.
- [x] Select `NEW_HYPOTHESIS_JUSTIFIED_PROTOCOL_NOT_FROZEN` without authorizing
  implementation, training, threshold rescue, R5, or external77 access.

## Prospective Conservative Reconciliation — Protocol Frozen

- [x] Freeze a new scientific hypothesis around trust-gated/locality-aware
  reconciliation before any code or training.
- [x] Prospectively define trust/locality semantics, permitted inputs, action
  space, controls, splits, calibration, thresholds, metrics, and failure gate.
- [x] Explicitly treat Legacy121 as development/hypothesis-generation data.
- [x] Keep external77 unopened until the complete future method and analysis
  plan are frozen; preserve it as one-shot independent evaluation.
- [x] Do not frame the protocol as an R4 threshold move, positive-pair channel
  selection, held-out-error tuning, or larger-model rescue.
- [x] Freeze the sole primary mechanism as Context-Corroborated Evidence Gate
  over the exact R4 features and simple ERN branch family.
- [x] Freeze DIRECT protection, E1-compatible LOCAL_CONFLICT deletion, and
  corroborated NON_EVIDENCED DELETE/KEEP/ABSTAIN semantics.
- [x] Freeze the matched `CER_EVIDENCE_MASKED` condition and complete 200-run
  development matrix.
- [x] Freeze `CONSERVATIVE_DEV_GATE` without altering R4 Gate B.
- [x] Write the implementation/artifact plan without implementation or
  training.

### Conservative reconciliation development execution — complete / gate failed

- [x] Snapshot and audit all frozen inputs before implementation.
- [x] Implement only the frozen CCEG/action/accounting contract and planned
  synthetic/unit tests.
- [x] Build immutable feature references and grouped development split
  manifests without regenerating evidence.
- [x] Complete all 200 condition x branch x channel x fold x seed runs.
- [x] Fit validation-only branch calibrators and lock new CCEG thresholds.
- [x] Run one sealed development-assessment pass; do not call it independent.
- [x] Produce all reliability, utility, action, scope, evidence-attribution,
  source, comparator, integrity, and reproducibility artifacts.
- [x] Apply `CONSERVATIVE_DEV_GATE` once with no rescue:
  `CONSERVATIVE_DEV_GATE_FAIL` because both matched-control NON_EVIDENCED
  preservation conditions failed.
- [x] Update state to the exact PASS/FAIL consequence without automatically
  starting R5 or external77.

## Paper Story and Results Consolidation — COMPLETE

- [x] Reorganize R2/R3/R4/CER around scientific questions rather than project
  chronology.
- [x] Build one action-space-aware master results table spanning B0, B1/E1,
  B2, P3, R4 B4/ERN, and CER masked/CER.
- [x] Freeze H1--H10 outcomes against the reboot claim–evidence map.
- [x] Compare method, reliability/mechanistic, and benchmark/evaluation
  framings without promoting either failed gate.
- [x] Select reliability/mechanistic study as the primary framing and the
  correction–preservation evaluation framework as a secondary contribution.
- [x] Freeze the central claim, claim firewall, limitations, five-main-figure
  plan, and main/supplementary table plan.
- [x] Decide `PAPER_STORY_VIABLE_WITH_CURRENT_RESULTS` under the bounded
  Legacy121 clean-evidence development scope.
- [x] Preserve Legacy121 as Phase I development evidence, external77 as locked,
  R5 as unauthorized, and both R4/CER failures unchanged.

## Phase II P0 — Novelty and Method Design — COMPLETE

- [x] Preserve all Phase I results and failed gates without rescue or
  reinterpretation.
- [x] Redefine Legacy121 as `PHASE1_HISTORICAL_DIAGNOSTIC_DATA` for Phase II.
- [x] Complete a fresh literature/novelty audit through 2026-09-08 covering RNA
  refinement, evidence-guided folding, graph/structured decoding, selective and
  conformal risk control, foundation models, and cross-domain post-processing.
- [x] Record that pair graphs, GNNs, constrained decoders, evidence fusion,
  abstention, conformal prediction, and foundation models are not novel alone.
- [x] Compare three model families and select risk-controlled structured
  refinement as the primary design direction.
- [x] Define a candidate KEEP/DELETE/ADD/REPLACE/ABSTAIN action space with exact
  primary noncrossing validity enforcement.
- [x] Draft Development-v2, predictor-family transfer, E0/E1/E2 evidence, risk
  control, evaluation, gate, roadmap, and venue strategies.
- [x] Decide `PHASE2_PRIMARY_DIRECTION_JUSTIFIED` while keeping
  `PROTOCOL_NOT_FROZEN` and `PHASE2_IMPLEMENTATION_NOT_AUTHORIZED`.
- [x] Keep external77 `ONE_SHOT_LOCKED`; no data access, code, training, or new
  scientific evaluation occurred.

## Phase II P1/P2 — Dataset and Task Protocol Freeze — COMPLETE

- [x] Re-audit exact source datasets, licenses, releases, annotation provenance,
  Legacy121 overlap, and predictor-training overlap without opening external77.
- [x] Freeze Development-v2 identity, family, temporal, length/type, and
  pseudoknot eligibility rules.
- [x] Audit and freeze a minimal deployable predictor-family panel and LOPFO
  grouping; do not treat NuFold as a like-for-like 2D source predictor.
- [x] Freeze candidate generation, labels, action semantics, structured
  validity, exact decoder, edit cost/accounting, and ABSTAIN level.
- [x] Freeze clean symbolic evidence semantics for ADD/REPLACE-compatible
  structured editing; do not run noisy or real evidence.
- [x] Determine whether the proposed risk loss/policy family permits valid
  formal control; otherwise freeze a finite-policy or explicitly empirical
  fallback.
- [x] Freeze splits, calibration units, model/control comparisons, metrics,
  gate definitions, hashes, leakage guards, and reproducibility checks.
- [x] Decide prospectively whether external77 remains a Phase I bridge asset or
  can participate in a later sealed Phase II multi-cohort plan; do not inspect
  it.
- [x] Do not implement or train a Phase II model in this task.

Outcome:

```text
PHASE2_DATASET_AND_TASK_PROTOCOL_FROZEN
FINITE_FAMILY_RISK_CONTROLLING_POLICY_SELECTION
EXTERNAL77 = PHASE1_BRIDGE_INDEPENDENT_ASSET / LOCKED
Independent-v2 = future Phase II primary one-shot set
```

## Phase II M0 — Roadmap and Feasibility Audit — COMPLETE WITH BLOCKERS

- [x] Adopt the revised M0--M6 sequence and distinguish M1/P3 software
  correctness from M2 biological/scientific validation.
- [x] Recompute the six-policy Hoeffding radius for 240, 500 and 1,000
  biological clusters; record exact post-firewall role counts as `UNKNOWN`.
- [x] Demonstrate the hard-E0 versus `S0` fallback conflict with a valid
  synthetic ADD/REPLACE counterexample; do not silently choose new semantics.
- [x] Audit the decomposable-objective boundary of exact interval DP and the
  sampling assumptions of the frozen finite-family risk statement.
- [x] Separate TP preservation, HarmRate, edit coverage and RNA coverage.
- [x] Audit RMDB/RDAT as one prospective SHAPE metadata route without reading
  a locked cohort, generating evidence or computing performance.
- [x] Preserve `PHASE2_DTP_V1.0` and its manifest unchanged.

Outcome:

```text
PHASE2_ROADMAP_REVISED
PHASE2_M0_FEASIBILITY_AUDIT_COMPLETE_WITH_BLOCKERS
PHASE2_E0_ABSTENTION_PROTOCOL_CONFLICT
PHASE2_IMPLEMENTATION_NOT_AUTHORIZED
```

## Phase II Protocol Amendment — NEXT PROPOSED

- [ ] Begin only after explicit authorization.
- [ ] Resolve whether hard E0 uses non-abstainable direct edits, an E0-feasible
  fallback anchor, defeasible evidence, or restricted E0 admission.
- [ ] Define valid-E0/S0 incompatibility, component boundaries, failure output,
  matched masked control and risk/coverage accounting consistently.
- [ ] Update every affected contract as a prospective version and publish a new
  manifest; never overwrite the historical v1.0 freeze silently.
- [ ] Do not implement P3 or inspect biological outcomes in this task.

## Phase II M1 / P3 — Data and Minimal Software — BLOCKED / NOT STARTED

- [ ] Start only after the E0/ABSTAIN amendment is frozen and separately
  authorized.
- [ ] Build exact source/checkpoint/license/determinism preflight; do not
  silently replace missing primary predictors.
- [ ] Materialize Development-v2 and five roles only under separate data-build
  authorization; record exact biological cluster budgets and leakage audits.
- [ ] Implement schema/candidate/exact-DP/action/component/risk-bound
  infrastructure using synthetic fixtures first.
- [ ] Verify exhaustive short-sequence equivalence, validity, determinism,
  fail-closed behavior, leakage firewall and edit accounting.
- [ ] Keep primary learned models, training, Development-v2 performance,
  evidence generation and independent data out of the software-correctness
  subtask.

## Phase II M2 — Structured-Baseline Scientific Validation — NOT AUTHORIZED

- [ ] Freeze a separate development-only comparison and utility/coverage gate
  before outcomes.
- [ ] Compare S0, direct/local evidence, constrained refolding, deletion-only
  and full minimum-edit structured refinement on matched inputs.
- [ ] Continue to M3 only if ADD/REPLACE shows additional useful value at
  comparable harm; otherwise narrow the question without model escalation.

## R5 — Controlled Noise Robustness

- [ ] Freeze noisy-evidence protocol using controlled 5%, 10%, 20%, 30% corruption where valid.
- [ ] Evaluate calibration shift, risk–utility degradation and harmful-edit growth.
- [ ] Apply Gate C at 5-10% noise.
- [ ] Do not advance to real-evidence claims if low noise destroys safety/utility without a prospectively frozen trust mechanism.

## R6 — Cross-Predictor Transfer

- [ ] Freeze source-wise and LOMO protocol.
- [ ] Run pooled, source-specific and leave-one-model-out evaluations.
- [ ] Compare calibration and risk–utility under predictor shift.
- [ ] Promote `model-agnostic` / `unseen-predictor transfer` only if supported.
- [ ] Do not repeatedly retune Legacy121 to rescue LOMO failure.

## R7 — Locked Independent Test

- [x] external77-derived 42-RNA manifest frozen.
- [x] RNAfold 42/42 valid.
- [x] PETfold 42/42 valid under reproduced historical single-sequence condition.
- [x] trRosettaRNA2 native SS 42/42 valid under recovered query-only condition.
- [x] normalized independent matrix 126/126 valid.
- [ ] Keep external77 locked until R7.
- [ ] Freeze model/features/calibration/operating point/analysis before opening it.
- [ ] Run one-shot independent evaluation.
- [ ] Apply Gate D; no tuning on external77 to rescue a failed claim.

## R8 — Real Experimental Evidence

- [ ] Identify candidate structure+probing datasets.
- [ ] Audit provenance, licensing/access and overlap with development/test data.
- [ ] Freeze measurement-to-evidence mapping, missingness and noise semantics.
- [ ] Keep probing measurements distinct from GT labels.
- [ ] Compare classical evidence-constrained folding vs post-hoc reconciliation under the same real evidence.

## R9 — Final Calibrated Selective Correction

- [ ] Freeze final `KEEP / DELETE / ABSTAIN` policy.
- [ ] Produce final reliability diagrams/calibration tables.
- [ ] Produce risk–utility and evidence-efficiency curves.
- [ ] Produce source-wise/generalization/independent-test summaries.
- [ ] Add exact primary + separately reported +/-1-endpoint flexible-match robustness.
- [ ] Freeze paired statistical analysis after final samples/metrics are fixed.
- [ ] Update reboot claim map with only supported paper claims.

## Optional — 2D -> 3D Validation

- [ ] Enter only after rebooted 2D mainline is stable.
- [ ] Freeze one 3D inference pipeline and identical Original/Reconciled/GT-2D conditions.
- [ ] Keep 3D out of claims if paired downstream benefit is absent or inconsistent.

## Paper Constraints

- [x] Benchmark normalization is infrastructure, not main contribution.
- [x] Basic RNA pair/stem rules are not novel.
- [x] Pair confidence is not novel.
- [x] Predictor consensus is not novel.
- [x] Evidence-constrained folding is not novel.
- [x] Generic post-hoc pair QA is not claimed as a new abstract task.
- [ ] No model-agnostic claim before R6.
- [ ] No independent-generalization claim before R7.
- [ ] No noisy/real-evidence claim before R5/R8.
- [ ] No 3D claim before optional downstream validation.

## Immediate Next Task

Current state:

```text
R4_COMPLETE
R4_GATE_B_FAIL
GATE_A_PASS_POSTHOC_NONDOMINATED
R5_NOT_AUTHORIZED
R4_POSTMORTEM_COMPLETE
CONSERVATIVE_RECONCILIATION_PROTOCOL_FROZEN
CONSERVATIVE_RECONCILIATION_DEVELOPMENT_COMPLETE
CONSERVATIVE_DEV_GATE_FAIL
PAPER_STORY_AND_RESULTS_CONSOLIDATION_COMPLETE
PAPER_STORY_VIABLE_WITH_CURRENT_RESULTS
PHASE1_RESEARCH_COMPLETE
PHASE1_PAPER_STORY_VIABLE
PHASE2_INITIATED
PHASE2_NOVELTY_AND_METHOD_DESIGN
PHASE2_PRIMARY_DIRECTION_JUSTIFIED
PHASE2_DATASET_AND_TASK_PROTOCOL_FROZEN
PHASE2_IMPLEMENTATION_NOT_AUTHORIZED
EXTERNAL77_LOCKED
```

The next proposed task, requiring explicit authorization, is:

```text
RESOLVE_PHASE2_E0_ABSTENTION_PROTOCOL_CONFLICT
```

Phase I paper-story viability remains unchanged. The Phase II P1/P2 protocol is
preserved as historical frozen v1.0, but M0 identified an E0/ABSTAIN semantic
conflict requiring a prospective amendment. P3 is blocked/not started; the
primary architecture and all training/performance work remain unauthorized.
No evidence, external77 or old R5/R6/R8 work is authorized. R4 and CER failures
remain frozen.
