# TODO — Project Reboot v2

Last updated: 2026-08-29

## R0 — Literature & Novelty Freeze

- [x] Establish that basic RNA structural rules are prior art, not novelty.
- [x] Establish that pair probability/confidence is prior art.
- [x] Establish that multi-predictor consensus is prior art.
- [x] Establish that evidence-constrained global folding is prior art.
- [x] Identify post-hoc pair-level QA analogues in structural bioinformatics.
- [x] Freeze candidate gap as predictor-output-preserving evidence reconciliation for RNA secondary-structure predictions.

## R1 — Project Reboot / Documentation Freeze

- [x] Create `docs/project_reboot_v2.md`.
- [x] Rewrite `CONTEXT.md` around the rebooted scientific question.
- [x] Rewrite `plan/research_plan.md`.
- [x] Rewrite `plan/timeline.md`.
- [x] Replace this TODO with the R0-R9 roadmap.
- [ ] Update `STATUS.md` to set R2 as the next experiment.
- [ ] Append reboot decisions to `docs/decisions.md`.
- [ ] Update `docs/claim_evidence_map.md` to reflect the new novelty boundary and superseded E2 claim.
- [ ] Update `AGENTS.md` so Codex does not run historical E2 training.
- [ ] Verify no authoritative document still says historical E2 training is the next step.

### R1 completion gate

No new learned training is authorized until all authoritative project documents point to R2.

## R2 — Global Evidence-Constrained Refolding Baseline

### Protocol freeze

- [ ] Audit installed ViennaRNA/RNAfold version and exact constraint syntax/API.
- [ ] Define mapping from `POSITIVE_PAIR_EVIDENCE` to hard pair constraints.
- [ ] Define mapping from `UNPAIRED_NUCLEOTIDE_EVIDENCE` to hard unpaired constraints.
- [ ] Define behavior for incompatible/unsatisfiable constraint sets before any evaluation.
- [ ] Freeze whether pair and unpaired channels remain separate in primary R2.
- [ ] Reuse exactly the frozen Legacy121 RNA splits/evidence manifests where semantically valid.
- [ ] Freeze output parser/validation and provenance fields.
- [ ] Freeze `docs/global_constrained_refolding_r2_protocol.md` before executing the full evaluation.

### Implementation

- [ ] Implement constrained RNAfold adapter without touching raw historical predictions.
- [ ] Add unit tests for hard pair constraints.
- [ ] Add unit tests for hard unpaired constraints.
- [ ] Add tests for unsatisfiable constraints and explicit failure reporting.
- [ ] Validate output length, one-partner legality and canonical parser compatibility.
- [ ] Retain raw RNAfold stdout/stderr, command/config and version provenance.

### Evaluation

- [ ] Evaluate B0 Original vs B1 local hard baseline vs B2 global constrained refolding on Legacy121 only.
- [ ] Report exact Precision/Recall/F1.
- [ ] Report TP preservation.
- [ ] Report FP removal.
- [ ] Report modification precision.
- [ ] Reuse/directly map DIRECT / LOCAL_CONFLICT / NON_EVIDENCED scope definitions where valid.
- [ ] Report non-evidenced modification precision, FP removal and TP loss.
- [ ] Report evidence efficiency (`FP_removed / evidence_items`, optional `Delta_F1 / evidence_items`).
- [ ] Report source-wise and evidence-density summaries.
- [ ] Verify all accounting identities and constraint-compliance checks.
- [ ] Write `docs/global_constrained_refolding_r2_results.md`.

### R2 decision

- [ ] Decide whether there is plausible post-hoc preservation headroom after seeing B2.
- [ ] If B2 dominates any reasonable post-hoc correction-preservation target, record Gate A failure and stop the post-hoc mainline.

## R3 — Reliability Baseline Suite

- [ ] Freeze pair-reliability evaluation protocol.
- [ ] Re-evaluate historical v1 topology score as a reliability baseline without retuning it.
- [ ] Re-evaluate historical v3 fixed consensus veto as a mechanistic comparator without retuning it.
- [ ] Add simple exact cross-model agreement score.
- [ ] Audit feasibility of predictor-independent thermodynamic BPP for every predicted pair.
- [ ] If feasible, implement RNAfold BPP baseline with frozen protocol.
- [ ] Compute AUPRC for DELETE/FP class.
- [ ] Compute AUROC as secondary discrimination metric.
- [ ] Compute Brier score.
- [ ] Compute ECE and reliability bins.
- [ ] Produce risk–utility curves under validation-defined operating points.
- [ ] Freeze strongest non-learned comparator before R4.

## Historical Stage E2 — Superseded

- [x] Historical `evidence_guidance_stage_e2_v1` protocol was frozen before training.
- [x] Historical E2 architecture remains a candidate implementation asset.
- [ ] **DO NOT execute historical E2 training.** It is superseded by Reboot v2 before training.
- [ ] Any future learned clean-evidence experiment must be frozen as R4 and include B2/R3 comparators.

## R4 — Clean Learned Evidence Reconciliation

### Prerequisites

- [ ] R2 complete.
- [ ] R3 complete.
- [ ] Gate A does not terminate the mainline.

### Protocol

- [ ] Freeze a new R4 protocol before training.
- [ ] Define primary output as pair-level error probability for original predicted pairs.
- [ ] Keep primary edit space `KEEP / DELETE / ABSTAIN`; no pair addition.
- [ ] Reuse simple source-agnostic candidate features unless R3 provides a prospective reason to change them.
- [ ] Reuse/adapt historical DeepSets evidence encoder if still appropriate.
- [ ] Define matched evidence-masked control B4.
- [ ] Define train-only preprocessing and calibration.
- [ ] Define validation-only operating-point selection.
- [ ] Freeze high-preservation primary operating point; current candidate target is `TP_preservation >= 0.99`.
- [ ] Freeze Gate B criteria before training.

### Evaluation

- [ ] Compare B0/B1/B2/B3/B4 vs learned R4.
- [ ] Report AUPRC/Brier/ECE.
- [ ] Report TP-preservation / FP-removal curves.
- [ ] Report modification precision.
- [ ] Report direct/local/non-evidenced behavior.
- [ ] Report evidence efficiency.
- [ ] Report source-wise behavior.
- [ ] Do not access external77.

### Gate B

- [ ] Learned method must improve FP removal over the strongest frozen non-learned baseline at the frozen high-preservation operating point.
- [ ] Improvement must not be driven by only one source.
- [ ] If failed, do not escalate to Transformer/GNN/foundation-model architecture as a rescue.

## R5 — Controlled Noise Robustness

- [ ] Reuse frozen corruption mechanisms at 5%, 10%, 20%, 30% where still semantically valid.
- [ ] Freeze noisy-evidence protocol before execution.
- [ ] Evaluate calibration shift and risk–utility degradation.
- [ ] Evaluate harmful-edit growth.
- [ ] Compare blind trust vs any prospectively frozen trust mechanism.
- [ ] Apply Gate C at low noise (5-10%).
- [ ] Do not make a real-evidence claim if low noise destroys safety/utility.

## R6 — Cross-Predictor Transfer

- [ ] Freeze source-wise and LOMO protocol.
- [ ] Run pooled multi-source evaluation.
- [ ] Run source-specific evaluation.
- [ ] Run leave-one-model-out evaluation for each feasible held-out predictor.
- [ ] Compare calibration and risk–utility under predictor shift.
- [ ] Promote `model-agnostic` / `unseen-predictor transfer` only if supported.
- [ ] Do not perform repeated Legacy121 rescue tuning if LOMO fails.

## R7 — Locked Independent Test

- [x] external77-derived 42-RNA manifest frozen.
- [x] RNAfold 42/42 valid.
- [x] PETfold 42/42 valid under reproduced historical single-sequence condition.
- [x] trRosettaRNA2 native SS 42/42 valid under recovered query-only condition.
- [x] normalized independent matrix 126/126 valid.
- [ ] Keep external77 inaccessible for model/feature/threshold selection until R7.
- [ ] Freeze final model, calibration, operating point and analysis plan before opening external77.
- [ ] Run one-shot independent evaluation.
- [ ] Apply Gate D.
- [ ] Do not tune on external77 to rescue a failed development claim.

## R8 — Real Experimental Evidence

- [ ] Identify candidate datasets with both structure reference and SHAPE/DMS/PARS or related probing data.
- [ ] Audit license/access/provenance and sample overlap with development/test data.
- [ ] Define measurement-to-evidence mapping prospectively.
- [ ] Define missingness and noise semantics.
- [ ] Keep probing signal distinct from GT labels.
- [ ] Compare classical evidence-constrained folding vs post-hoc reconciliation under the same real evidence.
- [ ] Make no real-evidence claim unless dataset/protocol audit passes.

## R9 — Final Calibrated Selective Correction

- [ ] Freeze final `KEEP / DELETE / ABSTAIN` policy.
- [ ] Produce reliability diagrams and final calibration tables.
- [ ] Produce risk–utility curves.
- [ ] Produce evidence-efficiency curves.
- [ ] Produce source-wise and generalization tables.
- [ ] Add exact-match primary and +/-1-endpoint flexible-match robustness analysis.
- [ ] Perform paired statistical tests only after final sample sets/metrics are frozen.
- [ ] Preserve all per-sample artifacts used by statistics/figures.
- [ ] Update `docs/claim_evidence_map.md` with only supported paper claims.

## Optional — 2D -> 3D Validation

- [ ] Enter only after the rebooted 2D mainline is stable.
- [ ] Freeze one 3D pipeline before comparison.
- [ ] Use identical inference settings for Original 2D / Reconciled 2D / GT 2D.
- [ ] Report paired downstream metrics only if the 3D pipeline supports them reproducibly.
- [ ] Do not keep a 3D claim if benefit is absent or inconsistent.

## Paper Constraints

- [x] Do not claim benchmark normalization as a main contribution.
- [x] Do not claim RNA post-processing itself is novel.
- [x] Do not claim basic pair/stem rules are novel.
- [x] Do not claim pair confidence itself is novel.
- [x] Do not claim evidence-constrained folding itself is novel.
- [x] Do not claim generic post-hoc pair QA is a new abstract task.
- [ ] Do not claim model agnosticism before R6 supports it.
- [ ] Do not claim independent generalization before R7.
- [ ] Do not claim noisy/real-evidence robustness before R5/R8.
- [ ] Do not claim 3D benefit before optional paired downstream validation.
- [ ] Select final CCF-A venue only after the validated contribution type is clear.

## Immediate Next Task

> **R2 protocol freeze: design the global ViennaRNA/RNAfold hard-constraint refolding baseline using the existing clean simulated-evidence manifests.**

No new learned training is authorized before R2 and R3 are completed and a new R4 protocol is frozen.
