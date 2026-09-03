# TODO — Project Reboot v2

Last updated: 2026-09-03

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
- [ ] Any future learned clean-evidence experiment must be frozen as R4 after R2/R3.

## R4 — Clean Learned Evidence Reconciliation

- [ ] Require R2 complete, R3 complete, and Gate A not terminating the mainline.
- [ ] Freeze a new R4 protocol before training.
- [ ] Define pair-level calibrated error probability as the primary learned output.
- [ ] Keep `KEEP / DELETE / ABSTAIN`; no pair addition in primary R4.
- [ ] Define matched evidence-masked control B4.
- [ ] Freeze train-only preprocessing/calibration and validation-only operating-point selection.
- [ ] Freeze high-preservation operating point; current candidate target `TP_preservation >= 0.99`.
- [ ] Compare B0/B1/B2/B3/B4 vs learned R4.
- [ ] Report AUPRC/Brier/ECE and risk–utility curves.
- [ ] Report direct/local/non-evidenced behavior and evidence efficiency.
- [ ] Report source-wise behavior.
- [ ] Do not access external77.

### Gate B

- [ ] Learned method must beat the strongest frozen non-learned baseline in FP removal at the frozen high-preservation operating point.
- [ ] Improvement must not be driven by only one source.
- [ ] If failed, do not escalate architecture complexity as a rescue.

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

> **Interpret the frozen R3 results and make the prospective R4 protocol
> decision. Do not train R4, access external77, or begin noise/real-evidence
> work automatically.**

No new learned training is authorized until a new R4 protocol is frozen.
