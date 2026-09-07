# Clean Learned Evidence Reconciliation R4 Implementation Plan

## Status

**`R4_IMPLEMENTATION_PLANNED_NOT_IMPLEMENTED_NOT_EXECUTED`**

Plan date: 2026-09-07

Governing protocol:
`docs/clean_learned_evidence_reconciliation_r4_protocol.md`.

This document designs the implementation and artifact contract only. No R4
model, feature builder, calibration job, threshold selector, or evaluation is
implemented or executed by this task. Historical
`evidence_guidance_stage_e2_v1` is not executed, external77 remains locked,
and the frozen R2/R3 artifacts remain read-only inputs.

## 1. Planned modules and scripts

The next task should add the smallest implementation needed for the frozen
protocol:

- `src/rna_ccfa/evidence_reconciliation.py`: frozen feature encoders, separate
  pair/unpaired DeepSets ERN modules, B4 masking, serialization, and deterministic
  inference;
- `scripts/audit_clean_learned_evidence_reconciliation_r4_protocol.py`:
  preflight paths, manifests, hashes, split roles, allowlists, and environment;
- `scripts/build_clean_learned_evidence_reconciliation_r4_features.py`:
  construct immutable candidate and evidence-item artifacts without fitting a
  model;
- `scripts/train_clean_learned_evidence_reconciliation_r4.py`: train ERN and
  paired B4 for every frozen channel/fold/seed combination;
- `scripts/calibrate_and_lock_r4_thresholds.py`: fit validation-only Platt
  calibrators and select/lock the dual-preservation operating points;
- `scripts/evaluate_clean_learned_evidence_reconciliation_r4.py`: score held-out
  folds once under locked artifacts and generate complete edit accounting;
- `scripts/summarize_clean_learned_evidence_reconciliation_r4.py`: produce
  reliability, utility, scope, efficiency, source, B4, P3/E1, and B2 trade-off
  summaries.

Each script must support a dry-run/audit mode. The full runner must refuse to
start unless the protocol and input hashes match the frozen contract. It must
also reject paths containing independent, noisy, or real-evidence assets.

## 2. Historical E2 asset audit and legal reuse

The following implementation assets may be reused after line-by-line audit:

| Asset | Legal R4 reuse | Boundary |
| --- | --- | --- |
| `src/rna_ccfa/selective_refiner.py` | Exact source-agnostic 78-dimensional candidate encoding and categorical vocabularies | No historical score, threshold, or success criterion |
| `src/rna_ccfa/simulated_evidence.py` | Clean manifest parsing, validation, IDs, and evidence semantics | Do not call corruption/noise generation |
| `scripts/run_reliability_baseline_r3.py` | P2 exact support, P4 BPP joins, E1 conflict, R2 eligibility, and hash checks | Frozen R3 outputs remain immutable; P1/P3/P4 are not retuned |
| `scripts/summarize_reliability_baseline_r3.py` | AUPRC/AUROC/Brier/ECE, utility accounting, and validation-threshold utilities | R4 calibration and threshold rules come only from the R4 protocol |
| `results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv` | Exact grouped RNA folds | Hash must equal the value frozen in the R4 protocol |
| Historical Stage E2 protocol/JSON contracts | 17/8-dimensional evidence geometry and audited DeepSets design provenance | No historical E2 success criteria and no historical execution |

The historical E2 Python runner/model source is not present in the repository;
only stale bytecode cache files were found. Bytecode is not an auditable source
asset and must not be imported, decompiled, or treated as authoritative. The
next task must implement the small ERN directly from the newly frozen protocol
and test it against the documented E2 feature contracts. This is an
implementation requirement, not a scientific blocker.

## 3. Feature artifacts

Planned immutable layout:

```text
results/clean_learned_evidence_reconciliation_r4/
  integrity/
  features/
    feature_contract.json
    candidate_rows.parquet
    positive_pair_items.parquet
    unpaired_nucleotide_items.parquet
    preprocessing/<channel>/fold_<k>.json
```

`feature_contract.json` records schema version, protocol SHA256, code commit,
input paths and hashes, feature names/order/dtypes, categorical vocabularies,
normalization rules, forbidden columns, and creation command.

`candidate_rows.parquet` contains one row per candidate realization with:

- identity: `manifest_id`, `manifest_payload_sha256`, `rna_id`,
  `source_model`, `fold_id`, `split_role`, `channel`, density/evidence-seed
  metadata, and candidate `i,j`;
- provenance: sequence, GT, original-prediction, R2 eligibility, and frozen BPP
  artifact hashes, plus the original-pair membership flag;
- features: the ordered historical 78 candidate values, normalized P2 exact
  support, and P4 BPP;
- label/evaluation fields held outside the feature matrix: `label_delete`,
  original TP/FP status, and evidence-scope assignment.

The two item tables are keyed by candidate-row ID and `item_index`. Pair items
store the ordered frozen 17 values; unpaired items store the ordered frozen 8
values. They also retain evidence-item identity for accounting, but the model
loader exposes only the numerical allowlist. Empty sets are represented by no
item rows plus an explicit zero count, never by a fabricated evidence item.

Training-fold preprocessing artifacts contain only statistics learned from
training RNAs. They record fit RNA IDs, row counts, feature order, means/scales,
constant-column handling, and input/parameter hashes. Labels and metadata must
never enter preprocessing feature selection.

## 4. Train, validation, and held-out artifacts

For each channel and held-out fold, create an immutable split manifest:

```text
splits/<channel>/fold_<k>.json
```

It records the exact RNA IDs, candidate-row IDs, and counts for `train`,
`validation`, and `held_out_test`; the grouped-fold source hash; all feature
artifact hashes; and pairwise disjointness results. All three predictor-source
records and every evidence realization for one RNA must have the same role.

Model rows may repeat a candidate under distinct delivered evidence contexts,
but reporting must retain RNA as the biological unit. The held-out role may be
read for inference only after checkpoint, calibrator, and threshold artifacts
are locked.

## 5. Checkpoint provenance

Planned run path:

```text
runs/<condition>/<channel>/fold_<k>/seed_<s>/
  run_config.json
  training_history.csv
  checkpoint.pt
  checkpoint_provenance.json
```

`condition` is exactly `ERN` or `B4_EVIDENCE_MASKED`. Provenance records:

- protocol, feature-contract, split, preprocessing, and input hashes;
- git commit and dirty-tree flag;
- Python/PyTorch/numpy package versions, device, deterministic settings, and
  model seed;
- exact architecture and parameter count;
- optimizer, loss, class weight, batch size/order seed, epoch/patience, and
  clipping settings;
- train/validation RNA and row counts;
- chosen epoch, validation log loss/AUPRC, tie-break trace, checkpoint SHA256,
  command, start/end timestamps, and exit status.

ERN/B4 paired-run metadata must prove equal candidate rows, labels, split,
architecture, nominal capacity, initialization seed, optimizer, batches, and
selection procedure. The only permitted input difference is the exact evidence
mask. Large checkpoint files must remain ignored unless the repository's
artifact policy explicitly authorizes them; their cryptographic hashes and
durable storage location remain mandatory.

## 6. Calibration and locked-threshold artifacts

Per run, write:

```text
calibration/<condition>/<channel>/fold_<k>/seed_<s>.json
thresholds/<condition>/<channel>/fold_<k>/seed_<s>.json
```

The calibration artifact records the fitted monotone Platt parameters,
optimizer/convergence, validation class counts and log loss before/after,
checkpoint and validation-score hashes, and an explicit assertion that no
held-out labels were loaded.

The threshold artifact records the complete validation candidate set, dual
TP-preservation eligibility check, ordered tie-break trace, selected threshold
or fail-closed abstention reason, validation metrics, and hashes of the
calibrator and validation predictions. It is written and sealed before the
held-out evaluation command becomes eligible. No held-out threshold rewrite is
allowed.

## 7. Results and integrity layout

```text
results/clean_learned_evidence_reconciliation_r4/
  integrity/
    preflight.json
    path_access_log.json
    input_hash_inventory.json
    split_leakage_audit.json
    feature_firewall_audit.json
    ern_b4_pairing_audit.json
    threshold_lock_audit.json
    edit_accounting_audit.json
    reproducibility_audit.json
  pair_scores/<condition>/<channel>/fold_<k>/seed_<s>.parquet
  risk_curves/<condition>/<channel>/fold_<k>/seed_<s>.csv
  evaluation/<condition>/<channel>/fold_<k>/seed_<s>.json
  summaries/
    reliability_summary.csv
    utility_summary.csv
    scope_summary.csv
    evidence_efficiency_summary.csv
    source_wise_summary.csv
    ern_vs_b4_summary.csv
    r4_vs_frozen_baselines.json
    gate_b.json
    gate_a_comparison.json
    r4_results.md
```

Pair-score rows retain immutable candidate identity, raw logit, calibrated
DELETE probability, locked action, label for evaluation, scope, and all parent
artifact hashes. The report must distinguish event-pooled, RNA-balanced,
channel, fold, model seed, and predictor-source summaries. `gate_a_comparison`
may be produced only after R4 completes and must preserve B2's
`FULL_REFOLD_REFERENCE` warning.

The primary combined Track E summary is built by concatenating all held-out
rows from the separately trained positive-pair and unpaired families on the
exact 7,153-manifest universe for the same condition/model seed. The builder
must prove each expected row appears exactly once. It may not train a third
model, ensemble channels, or choose a channel from held-out performance.

## 8. Leakage, hash, and reproducibility checks

The implementation must fail closed on any of the following:

1. frozen Legacy121, R2, R3, clean-manifest, or grouped-split hash mismatch;
2. RNA overlap between train, validation, and held-out roles;
3. source records or evidence realizations of one RNA assigned to different
   roles;
4. candidate not present in the immutable original prediction;
5. feature column outside the protocol allowlist or any GT-derived/forbidden
   feature in the model tensor;
6. preprocessing, class-weight, checkpoint, calibrator, or threshold fit using
   a disallowed role;
7. ERN/B4 mismatch other than evidence masking;
8. source- or density-specific model/threshold selection;
9. incomplete channel/fold/seed matrix, dropped failure, or post-hoc run
   selection;
10. any external77, noisy-evidence, SHAPE, DMS, PARS, or historical E2 runner
    path opened by an R4 command;
11. DELETE output not a subset of original pairs or a failed complete edit
    accounting identity;
12. non-deterministic repeated inference from the same checkpoint and inputs.

The implementation task must snapshot all frozen-input hashes before work and
prove those files are unchanged after execution. A second summary build from
the same pair-score artifacts must be byte-identical after excluding declared
timestamp fields.

## 9. Expected unit and toy tests

Before any full R4 training, add tests for:

- exact 78-dimensional candidate feature parity with the historical encoder;
- P2 support and frozen P4 BPP join semantics;
- all 17 positive-pair and 8 unpaired candidate-relative evidence features;
- permutation invariance under evidence-item reorder;
- padding exclusion and exact empty/masked-set zero encoding;
- B4 input/architecture/capacity pairing with ERN;
- RNA-grouped five-fold rotation and source-record co-assignment;
- training-only preprocessing and class-weight estimation;
- monotone Platt fitting, missing-class/convergence fail-closed behavior, and
  held-out-label access denial;
- threshold block ties, dual `0.99` validation constraints, all tie-breaks,
  delete-none, and locked held-out application;
- KEEP/DELETE/ABSTAIN semantics and deletion-only pair-set invariants;
- event-pooled and RNA-balanced AUPRC/AUROC/Brier/ECE calculations;
- complete TP/FP/FN/edit accounting and DIRECT/LOCAL_CONFLICT/NON_EVIDENCED
  partition identities;
- evidence-efficiency zero-denominator handling;
- source-wise reporting without source-specific selection;
- ERN/B4 paired-difference and exact frozen P3/E1/B2 reference joins;
- Gate B strict inequality and multi-source requirements;
- forbidden-path guards for external77, noisy evidence, real evidence, and the
  historical E2 runner;
- checkpoint/config/input hash mismatch rejection and repeatable inference.

A tiny synthetic end-to-end fixture may exercise feature building, training,
calibration, threshold locking, and evaluation. It must not read Legacy121 or
constitute an R4 scientific run.

## 10. Planned execution order for the next task

```text
1. snapshot and audit frozen inputs
2. implement feature/model/evaluation modules and unit/toy tests
3. build and hash feature artifacts
4. freeze per-fold split/preprocessing artifacts
5. train every paired ERN/B4 channel x fold x seed run
6. fit validation-only calibrators
7. select and seal validation-only thresholds
8. unlock held-out inference once
9. summarize all runs and run integrity/reproducibility audits
10. decide Gate B and only then compare R4 with B2 for Gate A
```

No partial result may alter a later fold, seed, feature, architecture,
calibrator, or threshold. Failure is reported under the frozen protocol and
does not authorize automatic architecture escalation.

## 11. Plan completion state

This implementation plan is complete when it is internally consistent with
the frozen R4 protocol and all planned artifacts have explicit provenance and
leakage contracts. It does not itself authorize a scientific result.

```text
R3_INTERPRETATION_COMPLETE
R4_PROTOCOL_FROZEN
R4_NOT_EXECUTED
NEXT: IMPLEMENT_AND_EXECUTE_FROZEN_R4
```
