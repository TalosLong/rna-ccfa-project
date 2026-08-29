# TODO — Project Reboot v2

Last updated: 2026-08-29

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

## R2 — Global Evidence-Constrained Refolding Baseline — CURRENT

### Protocol freeze

- [x] Audit installed ViennaRNA/RNAfold version and exact hard-constraint syntax/API; `/usr/bin/RNAfold` 2.4.17 supports the required noncrossing hard forms, with no Python `RNA` binding installed.
- [x] Define mapping from `POSITIVE_PAIR_EVIDENCE` to hard pair constraints as matching `()` plus `--enforceConstraint`; exact partner semantics verified on toys.
- [x] Define mapping from `UNPAIRED_NUCLEOTIDE_EVIDENCE` to hard unpaired constraints as `x`; exact semantics verified on toys.
- [x] Define behavior for incompatible/unsatisfiable constraints before evaluation: fail closed and retain an explicit status; never drop or reinterpret evidence.
- [x] Freeze pair and unpaired channels as separate primary R2 channels.
- [x] Audit reuse of frozen Legacy121 clean manifests; 87/3,630 pair manifests contain crossing evidence unsupported by standard non-PK ViennaRNA.
- [x] Freeze prospective v1.0.1 crossing policy: exclude whole crossing manifests without modifying delivered evidence.
- [x] Freeze matched B0/B1/B2 manifest universe and generate the manifest-ID-filtered B1 view.
- [x] Freeze coverage reporting and RNA-balanced macro / event-pooled micro aggregation semantics.
- [x] Freeze output parser, validity checks, and provenance fields in the blocked protocol/implementation plan.
- [x] Create `docs/global_constrained_refolding_r2_protocol.md`; status is `R2_PROTOCOL_BLOCKED` before full execution because of the crossing-evidence semantic blocker.

### Implementation

- [ ] Implement the complete constrained RNAfold adapter without modifying raw historical predictions (authorized on R2_ELIGIBLE manifests).
- [x] Add unit/toy tests for hard pair constraints.
- [x] Add unit/toy tests for hard unpaired constraints.
- [x] Add explicit tests/reporting for unsatisfiable and crossing constraints.
- [x] Validate toy output length, pair legality and canonical parser compatibility.
- [x] Freeze the required RNAfold version/config/command/stdout/stderr provenance fields.

### Evaluation

- [ ] Evaluate B0 Original vs B1 local hard evidence vs B2 global constrained refolding on Legacy121 only (blocked; not started).
- [ ] Report exact Precision/Recall/F1.
- [ ] Report TP preservation.
- [ ] Report FP removal.
- [ ] Report modification precision.
- [ ] Map/reuse DIRECT / LOCAL_CONFLICT / NON_EVIDENCED scopes where valid.
- [ ] Report non-evidenced modification precision, FP removal and TP loss.
- [ ] Report evidence efficiency (`FP_removed / evidence_items` and optional `Delta_F1 / evidence_items`).
- [ ] Report source-wise and density-wise summaries.
- [ ] Verify accounting identities, constraint compliance and reproducibility.
- [ ] Write `docs/global_constrained_refolding_r2_results.md`.

### Gate A

- [ ] Decide whether source-prediction preservation has plausible headroom versus B2.
- [ ] If B2 dominates the relevant TP-preservation/FP-removal trade-off, record Gate A failure and stop the post-hoc mainline.

## R3 — Reliability Baseline Suite

- [ ] Freeze pair-reliability evaluation protocol.
- [ ] Evaluate historical v1 topology score without retuning.
- [ ] Evaluate historical v3 fixed consensus veto without retuning.
- [ ] Add simple exact cross-model agreement score.
- [ ] Audit feasibility of predictor-independent thermodynamic BPP for predicted pairs.
- [ ] If feasible, freeze and implement RNAfold BPP baseline.
- [ ] Compute AUPRC for DELETE/FP.
- [ ] Compute AUROC as secondary metric.
- [ ] Compute Brier score.
- [ ] Compute ECE/reliability bins.
- [ ] Produce risk–utility curves.
- [ ] Freeze the strongest non-learned comparator before R4.

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

> **Implement and execute the frozen R2 global hard-constraint refolding baseline on the deterministic R2_ELIGIBLE matched universe.**

No new learned training is authorized before R2 and R3 are complete and a new R4 protocol is frozen.
