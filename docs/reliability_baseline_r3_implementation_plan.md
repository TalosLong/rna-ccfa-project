# Pair-Reliability Baseline Suite R3 Implementation Plan

Status: **PLANNED — NO FORMAL R3 EXECUTION PERFORMED**

Date: 2026-09-02

Governing protocol:
`docs/reliability_baseline_r3_protocol.md` (`FROZEN BEFORE R3 EXECUTION`).

This plan describes a future implementation. It does not authorize training,
retuning, Legacy121 R3 metric generation, external77 access, R4, noisy or real
evidence, a pseudoknot branch, or 2D-to-3D work.

## 1. Proposed entry points

Future implementation should add only:

```text
scripts/run_reliability_baseline_r3.py
scripts/summarize_reliability_baseline_r3.py
```

The runner should perform deterministic input joins and emit normalized pair-
score/decision records. The summarizer should consume only those frozen records
to compute discrimination, calibration-eligible diagnostics, risk–utility,
aggregation, source-wise summaries, and strongest-comparator records.

Training code must not be called. Historical checkpoints may be used only for
frozen inference if validation scores needed for P1 are absent, after exact
reproduction of stored held-out scores is demonstrated.

## 2. Reusable frozen inputs

Prefer the following existing assets rather than rebuilding benchmark state:

| Role | Frozen asset |
| --- | --- |
| Legacy121 normalized source predictions | `normalized/legacy121_v1/predictions.jsonl` |
| Grouped folds | `results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv` |
| Clean evidence | `results/evidence_guidance/e0/clean_manifests.jsonl` and `clean_manifest_index.csv` |
| Historical v1 raw scores | `results/selective_refiner/v1/POOLED_SOURCE_AGNOSTIC/**/per_pair_scores.csv` |
| Historical v1 frozen checkpoints/configs | matching `POOLED_SOURCE_AGNOSTIC/fold_*/seed_*` directories |
| Historical V3 fixed decisions/support | `results/selective_refiner/v3/veto2_fixed/**/per_pair_decisions.csv` |
| V3 frozen semantics | `results/selective_refiner/v3_protocol_audit/v3_conditions.json` |
| R2 eligibility | `results/global_constrained_refolding_r2/integrity/r2_manifest_eligibility_v1_0_2.csv` |
| R2 B2 structures | `results/global_constrained_refolding_r2/parsed/b2_structures_v1_0_2.csv` |
| R2 matched B0/B1 views | `results/global_constrained_refolding_r2/integrity/r2_matched_b0_view_v1_0_2.csv` and `r2_matched_b1_view_v1_0_2.csv` |
| E1 scope definition | `docs/evidence_guidance_protocol_v1.md` and existing Stage E1 evaluation logic |
| Shared exact evaluator | `src/rna_ccfa/metrics.py::evaluate_pairs` |
| Canonical validation | `src/rna_ccfa/structure.py::validate_pairs` |

Current read-only availability audit found 363 normalized source records, 121
grouped-fold assignments, 25 authoritative v1 pooled source-agnostic score
files, 25 `V3_VETO2_FIXED` decision files, 7,260 clean manifests, and 7,153
validated R2 B2 structures. The latter comprise 3,523 pair-channel and 3,630
unpaired-channel manifests.

## 3. Output layout

```text
results/reliability_baseline_r3/
    integrity/
        input_inventory.json
        input_hashes.json
        environment_audit.json
        bpp_cli_audit.json
        join_integrity.json
        leakage_audit.json
        metric_accounting.json
        execution_completion.json
    pair_scores/
        track_p_pair_scores.csv
        track_e_pair_scores.csv
        p1_seed_inventory.csv
        binary_operating_points.csv
    risk_curves/
        track_p_risk_curves.csv
        track_e_risk_curves.csv
        validation_threshold_search.csv
        locked_thresholds.csv
        high_preservation_summary.csv
    calibration/
        probability_like_metrics.csv
        reliability_bins.csv
        calibration_scope_warnings.json
    summaries/
        discrimination_event_pooled.csv
        discrimination_rna_balanced.csv
        source_wise_summary.csv
        strongest_prediction_only_baseline.json
        strongest_evidence_conditioned_baseline.json
        r3_summary.json
```

CSV schemas and stable sort keys must be frozen in code tests before the first
formal R3 run. Raw extracted scores/decisions and aggregate summaries remain
separate.

## 4. Canonical record keys

### Track P

```text
(rna_id, source_model, i, j, fold, partition, baseline_id[, historical_seed])
```

### Track E

```text
(manifest_id, rna_id, source_model, i, j, channel,
 density_percent, evidence_seed, fold, partition, baseline_id)
```

Every pair must be canonical zero-based `i<j` and must occur in the immutable
original source prediction. Duplicate full keys are fatal. A pair absent from
the original prediction is never emitted.

Each record should retain `label_delete`, but integrity checks must show that
label construction occurred after risk computation and that no GT-derived
field entered the scoring function.

## 5. Planned implementation stages

### Stage I — Fail-closed input inventory

1. Hash every input named above.
2. Verify 121 unique Legacy121 RNAs and the complete three-source matrix.
3. Verify one frozen grouped-fold assignment per RNA and the historical
   train/validation/test rotation rule.
4. Verify R2 v1.0.2 eligibility counts: pair 3,523; unpaired 3,630.
5. Verify every eligible manifest has exactly one validated B2 structure and
   every ineligible manifest is absent from Track E.
6. Record `external77_accessed=false` and fail if an input path resolves into
   the locked dataset.

### Stage II — Track P score materialization

- P0: compute training-only prevalence for each rotation and permitted
  reporting stratum, then attach the constant to held-out rows.
- P1: load only authoritative `POOLED_SOURCE_AGNOSTIC` `p_delete` values from
  the matching historical fold/seed. Preserve seeds as repeated model runs.
- P2: construct exact pair-set membership for the other two frozen source
  predictions and store `support_other_count` plus `2-support` risk.
- P3: load the historical `V3_VETO2_FIXED` binary decision and verify its
  coordinates, score, support count, fold, seed, and decision semantics against
  the v3 audit files.
- P4: compute one BPP matrix per unique RNA sequence and reuse it by exact
  `(rna_id,i,j)` join for all three source predictions.

No score orientation may be inferred from held-out labels.

### Stage III — BPP adapter

Use an isolated temporary working directory per RNA and a deterministic safe
FASTA identifier. Execute without a shell using the exact protocol argv:

```text
/usr/bin/RNAfold
--noPS
--partfunc=1
--bppmThreshold=0
--temp=37
--dangles=2
```

Set `LC_ALL=C` in the subprocess environment. Capture version, argv, stdin
hash, stdout, stderr, return code, runtime, sequence hash, and dot-plot hash.
Parse only `ubox` records, square `sqrt(p)`, convert indices to zero-based, and
require a complete `n(n-1)/2` upper triangle. Validate finite probabilities in
`[0,1]` and deterministic parsed equality on a repeated toy before formal use.

The BPP adapter must not import the unavailable Python `RNA` binding and must
not approximate missing probabilities. No constraint or source prediction is
passed to RNAfold.

### Stage IV — Track E score materialization

For every exact R2 v1.0.2 manifest ID and source prediction:

- emit one candidate per original predicted pair;
- E1: derive binary local-conflict risk from delivered evidence coordinates
  using the frozen Stage E1 rules, without GT;
- E2: parse the matched B2 pair set and emit risk one iff the original pair is
  absent from B2;
- attach channel, density, evidence seed, manifest hash, fold, and partition;
- verify the same original pair may repeat only through explicit evidence
  context keys.

### Stage V — Labels and discrimination

After all risks are frozen, join exact GT membership to create
`label_delete`. Implement the protocol's tied-score, non-interpolated average
precision and standard tie-aware AUROC. Report held-out prevalence beside each
AUPRC and retain NA rather than inventing values for single-class strata.

The default Python interpreter currently lacks `sklearn`; no installation was
performed. The implementation should therefore use audited project-local
metric code or an already available frozen environment, and verify exact toy
values before formal execution. Dependency changes require a separate
environment decision, not an implicit install.

### Stage VI — Validation-only risk control

For P1, P2, and P4, enumerate unique validation thresholds plus delete-none.
Treat equal scores as one block. Enforce both event-pooled and RNA-balanced
validation TP preservation `>=0.99`, maximize RNA-balanced FP removal, and
apply the frozen tie-breaks. Apply the selected threshold unchanged to the
held-out fold.

P1 validation inference, if needed, is checkpoint inference only. Before it is
accepted, reproduce stored held-out `p_delete` values for the same checkpoint
within a prospectively coded tolerance and record the maximum absolute error.
Failure makes the P1 high-preservation point unavailable; it does not authorize
retraining.

P0 receives no artificial ranking threshold. P3, E1, and E2 retain their
fixed binary points.

### Stage VII — Risk–utility and structure accounting

Starting from the original pair set, simulate deletion only. At each score
block verify:

```text
TP_after = TP_before - lost_TP
FP_after = FP_before - removed_FP
FN_after = FN_before + lost_TP
deleted_pairs = lost_TP + removed_FP
```

Use the shared exact evaluator for resulting Precision, Recall, and F1. Emit
the curve `1-TP_preservation` versus `FP_removal`, plus modification precision,
coverage, counts, and all zero-denominator NA flags.

### Stage VIII — Aggregation and selection

Produce event-pooled and RNA-balanced summaries independently. For RNA-
balanced values, aggregate all repeated contexts inside RNA before equal-
weight averaging. Historical model seeds are summarized as repeated runs, not
pooled pair observations.

Produce pooled and per-source tables at the same locked thresholds. Apply the
protocol's strongest-comparator rule separately to Track P and Track E and
write the exact status records:

```text
STRONGEST_R3_PREDICTION_ONLY_BASELINE
STRONGEST_R3_EVIDENCE_CONDITIONED_BASELINE
```

### Stage IX — Calibration-restriction enforcement

Only P0, raw P1, and P4 may enter the calibration directory. Every row must
carry a score-type warning. P1 is `raw / uncalibrated` unless historical
evidence proves otherwise; P4 is a thermodynamic reliability relationship,
not an empirical correctness-calibrated probability. P2, P3, E1, and E2 must
be rejected by calibration code.

## 6. Tests required before formal execution

Add focused tests for:

- synthetic AUPRC with DELETE as positive and explicit prevalence;
- tied-score AUPRC/AUROC handling;
- deletion-only risk-curve identities;
- the validation-only `>=0.99` selector and all tie-breaks;
- no test-label access during threshold selection;
- exact cross-model support counts and `2-support` orientation;
- B2 survival/disagreement on toy pair sets;
- positive-pair and unpaired local-conflict joins;
- complete BPP upper-triangle parsing, index conversion, squaring, range
  checks, duplicate/missing-record failures, and repeatability;
- manifest eligibility and exact Track E join counts;
- grouped-fold containment for every RNA and evidence context;
- calibration rejection for ordinal/binary baselines;
- source-wise and RNA-balanced denominator handling;
- a path guard that rejects external77 inputs.

Definition-level toys already passed for AUPRC orientation, support
orientation, B2 disagreement, local-conflict join, deletion-only accounting,
and the validation `>=0.99` selector. The RNAfold CLI toy also passed twice.
These checks are interface/protocol audits only and contain no Legacy121 R3
performance result.

## 7. Formal execution gate

Before running `scripts/run_reliability_baseline_r3.py` on Legacy121:

1. review and commit the implementation and tests as a separate coherent task;
2. confirm the protocol file hash and all frozen input hashes;
3. pass every test and integrity audit above;
4. re-confirm no external77 path, training entry point, noise/real-evidence
   input, or R4 code is in the command plan;
5. record the exact command and environment.

This planning task stops before that gate. Its terminal state is
`READY_FOR_R3_EXECUTION`, not formal R3 completion.
