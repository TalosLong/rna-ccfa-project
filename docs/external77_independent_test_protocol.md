# external77 Independent Test Protocol v1

Status: **candidate manifest frozen; source matrix not yet complete**.

## Frozen target and membership

The target is the external77 `GT_CON` structure, not `GT_ALL` or `NMR_PRED`.
The frozen candidate universe is the 42 ACGU-only sequences whose deterministic
global sequence identity to **every** Legacy121 v1 sequence is below 0.80.
Global alignment uses match 1, mismatch 0, gap-open -1, and gap-extension -1;
identity is identities divided by identities + mismatches + gaps, including
terminal gaps. The candidate set was independently recomputed and must match
the existing audit CSV exactly. Excluded external77 rows remain in the audit
inventory.

The frozen manifest is
`manifests/external77_GT_CON_v1_nonredundant_manifest.csv`. Raw external files
remain read-only; the manifest stores their paths and SHA-256 hashes.

## Failure policy (frozen before source execution)

Every one of the 42 frozen RNAs is retained. A source failure is recorded as a
source-specific missing/failed prediction, never silently dropped:

- predictor crash, non-zero exit, timeout, malformed output, duplicate output,
  or missing output: status `failed`, with command, exit status, logs, and
  reason;
- sequence-length mismatch or invalid canonical pair assignment: status
  `invalid`, with no normalized record;
- trRosettaRNA2 length/resource failure: status `failed`, preserving the RNA
  and the exact environment/resource error;
- no retry with altered settings, no exclusion based on predicted quality, and
  no post-hoc subset selection.

The complete primary dataset requires all 42 RNAs × 3 source models = 126
valid normalized records. Dataset-level three-source comparisons are blocked
until complete coverage is achieved. Source-specific diagnostics may report
partial coverage, but must identify the missing source/RNA records and must not
be presented as a complete cross-model test.

The minimum acceptable coverage for a source-specific exploratory report is
100% of the frozen 42 RNAs for that source. A dataset-level claim has no
acceptable partial-coverage substitute. If a source cannot reach 42/42 under
the frozen protocol, preserve all failures and stop the complete-matrix claim.

## Source execution status

RNAfold is executable with the documented historical command
`/usr/bin/RNAfold --noPS input.fasta` (version is captured per run). Its
outputs are validated for sequence length and canonical pair validity only.

PETfold is **blocked** pending a frozen external77 alignment input and
alignment-gap projection protocol. Its legacy command and binary are
documented, but selecting a new alignment or silently projecting gaps would
change prediction semantics.

trRosettaRNA2 native SS is now **reproduced as a query-only native-SS source
condition**. The forensic audit found 121 one-row Legacy121 A3Ms and a
read-only rerun reproduced a stored DBN exactly. External query-only A3Ms,
the three checkpoint hashes, the ensemble mean, and the existing `>0.5`
strongest-pair decoder are retained under the source-prediction audit. The
raw dense score matrix remains authoritative; parenthesis-only DBN cannot
encode crossings losslessly.

PETfold remains **blocked** pending historical alignment input and
alignment-gap projection recovery. No new alignment or projection is used.

The execution audit is generated under `results/external77_independent_test/`:

- `source_runtime.csv` — command, version, environment, status, runtime, and logs;
- `source_coverage.csv` — valid/invalid/blocked counts;
- `provenance_manifest.csv` — hashes for generated valid source outputs;
- `validation_summary.json` — candidate and matrix status.

## Normalization gate

No external normalized JSONL is emitted while the three-source matrix is
incomplete. The directory
`normalized/external77_GT_CON_v1_nonredundant/` contains a status README only.
When all 126 source outputs are available, normalization must use schema v1,
validate GT_CON and predictions with the existing canonical parser, preserve
source hashes and logs, and handle trRosettaRNA2 score sidecars under the same
diagonal-only normalization contract used for Legacy121. No baseline or
refiner evaluation is part of this preparation step.

## Reproducibility and reporting

The manifest, raw source outputs, logs, command lines, versions, environment
identity, and hashes are retained. Failures are reported per source and per
RNA. The independent test set is test-only after learned-refiner features,
hyperparameters, checkpoints, and thresholds have been locked on Legacy121
grouped development folds. No result from this candidate may tune the model.
