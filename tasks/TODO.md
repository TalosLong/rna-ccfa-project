# TODO

## P0 — Current

- [x] Create `docs/benchmark_inventory.md` listing every current benchmark dataset, its path, structure format, and whether pseudoknots are represented.
- [x] Create `docs/model_inventory.md` listing every runnable predictor, input format, output format, checkpoint/version, and availability of pair probabilities/logits/confidence.
- [x] Locate all existing ground-truth secondary-structure files and document their paths without modifying originals.
- [ ] Locate all existing prediction outputs and document their paths without modifying originals.
- [ ] Define a normalized prediction schema with `rna_id`, `sequence`, `ground_truth_structure`, `source_model`, `predicted_structure`, and optional `pair_scores`.
- [ ] Implement a parser that converts every supported structure representation into a canonical base-pair list.
- [ ] Add validation for malformed structures and sequence/structure length mismatches.
- [ ] Implement shared Precision, Recall, and F1 from canonical base-pair lists.
- [ ] Implement MCC only if a consistent benchmark definition is available; otherwise document why it is omitted.
- [ ] Implement per-sample TP, FP, and FN extraction.
- [ ] Re-evaluate at least three runnable source predictors with the shared evaluator.
- [ ] Save per-sample baseline metrics in a machine-readable table.
- [ ] Document every mismatch between reproduced and existing benchmark metrics before continuing.

## P1 — Next

- [ ] Implement `missing_pair` extraction.
- [ ] Implement `false_positive_pair` extraction.
- [ ] Implement `wrong_partner` extraction.
- [ ] Define a deterministic stem extraction procedure in `docs/error_taxonomy_v1.md`.
- [ ] Define operational criteria for `stem_missing`, `stem_truncation`, `stem_extension`, and `stem_shift`.
- [ ] Implement stem-level error extraction after definitions are frozen.
- [ ] Add `abs(i-j)` sequence separation to every true/predicted pair record.
- [ ] Produce long-range error summaries using bins chosen from the current data distribution.
- [ ] Verify whether pseudoknot representation is consistent across selected predictors/datasets.
- [ ] If valid, implement pseudoknot-specific pair metrics; otherwise explicitly defer them.
- [ ] Produce `results/error_analysis/error_summary_by_model.csv`.
- [ ] Produce `results/error_analysis/error_summary_by_dataset.csv`.
- [ ] Identify the top three error types for each source predictor.
- [ ] Identify error types shared by multiple predictors.
- [ ] Update `docs/error_taxonomy_v1.md` with actual examples from benchmark records.

## P2 — Later

### Rule-Based Baseline

- [ ] Write a minimal rule-based refinement specification before implementation.
- [ ] Implement incompatible-pair conflict detection.
- [ ] Implement isolated-pair handling only if included in the written baseline specification.
- [ ] Add pair-confidence filtering for predictors that expose confidence values.
- [ ] Log every rule-based edit with RNA ID, original state, new state, triggering rule, and confidence if available.
- [ ] Evaluate Original vs Rule-based using the shared evaluator.
- [ ] Compute the fraction of rule edits that fix errors.
- [ ] Compute the fraction of rule edits that destroy correct pairs.

### Selective Refiner

- [ ] Define leakage-safe refiner train/validation/test splits.
- [ ] Build training records containing source prediction, ground truth, and error labels.
- [ ] Implement a non-selective learned refiner baseline.
- [ ] Implement a first error-detector/modification-mask model.
- [ ] Implement corrected pair-score prediction.
- [ ] Implement a valid-structure decoder if raw outputs can violate pairing constraints.
- [ ] Implement a preservation loss or equivalent penalty for changing correct pairs.
- [ ] Compare Original, Rule-based, Non-selective, and Selective variants on identical splits.
- [ ] Report correct-pair preservation rate.
- [ ] Report modification precision and recall.

### Cross-Model Generalization

- [ ] Select the initial 3-5 source predictors after completing model inventory.
- [ ] Train one pooled refiner on multiple source predictors.
- [ ] Train model-specific refiner baselines.
- [ ] Run leave-one-model-out evaluation for each feasible held-out predictor.
- [ ] Save per-predictor metrics to `results/cross_model/leave_one_model_out.csv`.
- [ ] Compare refinement gains on weak versus strong source predictors.
- [ ] Remove any model-agnostic claim if unseen-model transfer is not reproducible.

### Evidence Guidance

- [ ] Implement a simulated-evidence generator that samples only explicitly selected ground-truth evidence.
- [ ] Generate candidate evidence densities of 0%, 1%, 5%, 10%, 20%, and 50%, unless pilot results justify another grid.
- [ ] Implement a hard-evidence baseline.
- [ ] Add evidence input to the selective refiner.
- [ ] Inject candidate evidence-noise levels of 5%, 10%, 20%, and 30%, unless pilot results justify another grid.
- [ ] Track exact type/location of every corrupted evidence item.
- [ ] Compare hard enforcement with learned evidence-guided refinement.
- [ ] Decide whether a learned prediction-vs-evidence trust mechanism is needed.
- [ ] Evaluate feasibility of real SHAPE/DMS/NMR evidence before adding any real-data claim.

### Candidate 2D -> 3D Validation

- [ ] Identify RNAs with GT 3D structures and compatible 2D inputs.
- [ ] Freeze one 3D inference pipeline before comparison; existing DRfold-related workflow is a candidate.
- [ ] Prepare Original 2D, Refined 2D, and GT 2D conditions for each selected RNA.
- [ ] Run identical 3D inference configuration for all conditions.
- [ ] Aggregate per-sample RMSD if available.
- [ ] Aggregate per-sample TM-score if available.
- [ ] Aggregate per-sample lDDT if available.
- [ ] Test whether corrected long-range or pseudoknot-related errors correlate with 3D improvement.
- [ ] Keep 3D out of the main claim if no reproducible downstream benefit is observed.

## Analysis

- [ ] Produce per-model error-type distributions.
- [ ] Produce per-dataset error-type distributions.
- [ ] Produce performance by RNA length after final datasets are fixed.
- [ ] Produce performance by pair sequence separation.
- [ ] Produce pseudoknot-specific analysis only after representation/evaluator validation.
- [ ] Count edits per RNA for each refiner.
- [ ] Compute beneficial/neutral/harmful edit ratios.
- [ ] Compare selective versus non-selective edit behavior.
- [ ] Compare model-specific versus cross-model refinement.
- [ ] Plot performance versus evidence density.
- [ ] Plot performance versus evidence noise.
- [ ] Add paired statistical tests only after final sample sets are fixed and document the test choice.
- [ ] Preserve all per-sample results used for figures/statistics.

## Paper

- [ ] Maintain `docs/claim_evidence_map.md` mapping each intended claim to completed experiments.
- [ ] Do not list benchmark normalization as a primary paper contribution.
- [ ] Do not claim RNA post-processing/refinement itself is novel.
- [ ] Do not claim model agnosticism before leave-one-model-out evidence exists.
- [ ] Do not claim noisy-evidence robustness before controlled-noise experiments are complete.
- [ ] Do not claim 3D benefit before identical-pipeline downstream validation is complete.
- [ ] Draft Introduction only after selective-refinement signal is confirmed.
- [ ] Draft Method after architecture is frozen.
- [ ] Draft Results around explicit research questions and completed tests.
- [ ] Prepare final ablation table using only implemented components.
- [ ] Re-check CCF-A venue classification, CFP, paper type, and deadline before final venue selection.
- [ ] Select venue based on validated contribution type, not initial preference.
