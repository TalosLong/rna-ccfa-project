# Legacy121 v1 Benchmark Protocol

Status: **Frozen infrastructure contract**

Frozen: 2026-08-26

## Evaluation Universe

Legacy121 v1 is defined by the 121 primary one-record FASTA files under
`/root/autodl-tmp/data/sequences`. Primary files are the individual `*.fasta`
records after excluding these aggregate/non-primary files:

- `all.fasta`;
- `rna_ligand_sequences.fasta`;
- `rna_protein_sequences.fasta`.

A primary RNA is included only when one sequence, one legacy GT structure,
one historical RNAfold prediction, one historical PETfold prediction, one
historical trRosettaRNA2 native-SS DBN, and its native-SS pair-score NPZ are
all explicitly mapped and valid. The authoritative mapping is
`manifests/legacy121_v1.csv`. Future normalization and evaluation code must
consume this manifest and must not derive independent IDs from filenames.

## GT-Only Exclusions

The GT directory contains 123 files, while the evaluation universe contains
121 primary sequences. These two GT-only files have no primary sequence in the
Legacy121 v1 universe and are excluded:

- `/root/autodl-tmp/data/ss/gt/8Q4O_23_g4_nmr_matrix.db`;
- `/root/autodl-tmp/data/ss/gt/8TNS_24_g4_nmr_matrix.db`.

Both files remain preserved and unmodified. They are documented exclusions,
not failed or silently dropped benchmark samples, and do not appear in the
121-row manifest.

## Frozen ID Mapping Rules

The logical `rna_id` is the exact primary FASTA basename without `.fasta`.
All 121 current primary IDs end in the chain token `_A`. Define
`gt_mapping_key` by removing that final `_A` only.

Paths are mapped as follows:

```text
sequence:
  /root/autodl-tmp/data/sequences/<rna_id>.fasta

ground truth:
  /root/autodl-tmp/data/ss/gt/<gt_mapping_key>_matrix.db

RNAfold historical prediction:
  /root/autodl-tmp/data/ss/rnafold/<rna_id>.db

PETfold historical prediction:
  /root/autodl-tmp/data/ss/petfold/<gt_mapping_key>.db

trRosettaRNA2 native-SS historical prediction:
  /root/autodl-tmp/models/trRosettaRNA2/data/ss_native/<rna_id>/<rna_id>.dbn

trRosettaRNA2 native-SS historical pair scores:
  /root/autodl-tmp/models/trRosettaRNA2/data/ss_native/<rna_id>/<rna_id>_ss_prob.npz
```

The RNAfold and trRosettaRNA2 mappings retain the full chain-qualified
`rna_id`. GT and normal PETfold mappings use `gt_mapping_key`. The chain token
is removed only by the documented final-suffix rule, not by a general filename
substring heuristic.

### PETfold Alias

One explicit exception is frozen:

```text
1A9L_38_hpbulge_nmr_A
  -> /root/autodl-tmp/data/ss/petfold/1A9L.db
```

The manifest records `petfold_source_id=1A9L` and
`petfold_alias_applied=true` for this row. No other alias was found or applied.

## Validation Procedure

The reproducible builder is `scripts/build_legacy121_manifest.py`. From the
repository root, run:

```text
PYTHONPATH=src python scripts/build_legacy121_manifest.py
```

For every attempted primary RNA, the builder:

1. verifies all six required paths exist;
2. reads exactly one FASTA record and checks its header against `rna_id`;
3. validates the sequence against the schema-v1 RNA IUPAC alphabet;
4. parses GT with the canonical extended dot-bracket parser;
5. parses RNAfold, PETfold, and trRosettaRNA2 DBN structures with the canonical
   standard dot-bracket parser;
6. passes sequence length to every parser, making any length mismatch fatal;
7. verifies the expected trRosettaRNA2 NPZ is present and non-empty;
8. writes one audit row even when validation fails;
9. returns a nonzero exit status if the primary count, ID uniqueness, GT-only
   exclusion set, or any row fails acceptance.

The machine-readable audit is
`results/manifest_audit/legacy121_v1_audit.csv`.

## Validation Result

- Manifest rows: 121.
- Unique `rna_id`: 121.
- Fully valid rows: 121.
- Invalid rows: 0.
- Rows with all six required assets: 121.
- Rows whose GT and three predictions passed canonical parsing and length
  validation: 121.
- Preserved GT-only exclusions absent from manifest: 2/2.

All 121 raw FASTA sequences use lowercase `a/c/g/u`. This is recorded as the
nonfatal `raw_sequence_lowercase` warning in every audit row. The builder uses
uppercase only for schema-alphabet and length validation and does not modify
the source FASTA. The future normalized-record step must record the case
normalization in provenance. The `1A9L` row additionally records the PETfold
alias warning.

## Remaining Boundaries

No sample/ID mapping ambiguity remains inside Legacy121 v1. This freeze does
not establish the original dataset publication provenance, reconstruct unknown
historical RNAfold/PETfold settings, or freeze a new trRosettaRNA2 score
decoder. The NPZ files are checked for presence and nonzero size here; score
array normalization and normalized prediction records are the next Phase 0
task and are not produced by this protocol.
