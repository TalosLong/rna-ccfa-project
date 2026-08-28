# PETfold single-sequence source protocol v1

Status: **FROZEN / REPRODUCED_HISTORICAL_SINGLE_SEQUENCE_CONDITION**

## Installation

- Executable: `/root/autodl-tmp/PETfold/bin/PETfold`
- Version: PETfold v2.0 (reported by `--help`)
- Binary SHA-256: `eb0636da9e1a5a2d28d0e8b14f7c35512eceeafdd46fbcbd5523125ee3bb3446`
- Grammar: `/root/autodl-tmp/PETfold/bin/article.grm`, SHA-256 `8ecfd9b8c96f0e5b1d60c4bd672ef327d9b14c7c11a3f7103c97ca37a7e6fa27`
- Rate file: `/root/autodl-tmp/PETfold/bin/scfg.rate`, SHA-256 `1304ee9d519d03ca280e29ab8043afcdcff953c186fc4454c28751fcc854159f`
- Migrated source checkout: `/root/autodl-tmp/PETfold`; its `src/petfold.c` is byte-identical to the prior local PETfold source. The migrated binary is the frozen executable because it was the installation validated against all historical outputs.
- Runtime dependencies: glibc (`libc.so.6`), libm (`libm.so.6`), and OpenMP (`libgomp.so.1`) as reported by `ldd`; no external database is read.
- Required environment: `PETFOLDBIN=/root/autodl-tmp/PETfold/bin`.

## Input and command

Each input is a single-record FASTA containing exactly the query sequence:

```text
>{rna_id}
{ungapped RNA sequence}
```

PETfold accepts this through its `-f/--fasta` interface. It is syntactically a
one-row alignment because PETfold's interface is alignment-oriented, but it
has no biological MSA dependency, no alignment-generation database, and no
alignment gaps. The exact command is:

```text
PETFOLDBIN=/root/autodl-tmp/PETfold/bin \
  /root/autodl-tmp/PETfold/bin/PETfold \
  -f <input.fasta> -r <output.petfoldrr>
```

No GT structure is supplied. No non-default `-p`, `-u`, `-a`, `-b`, or `-g`
parameters are supplied; PETfold defaults are therefore frozen. Standard
output is retained as the raw PETfold result and the `PETfold RNA structure:`
line is the prediction source. The `-r` reliability file is retained as a
raw sidecar and is not used to alter the structure.

## Coordinate conversion and validation

PETfold emits one structure character per input residue. The project parser
enumerates that string from position zero and converts each matched bracket
to canonical `(i, j)` with `i < j`. There is no 1-based correction and no
alignment-gap projection for this ungapped single-sequence condition. The
parser rejects length mismatches, self-pairs, out-of-range coordinates,
duplicates, and multiple partners.

## Reproducibility evidence

The migrated installation reproduced the frozen historical PETfold canonical
pair sets exactly for the required 10-RNA audit subset and for all 121
Legacy121 RNAs. Per-RNA comparison tables are:

- `results/petfold_reproduction/legacy121_reproduction_10.csv`
- `results/petfold_reproduction/legacy121_reproduction_121.csv`

The external77 execution retains per-RNA inputs, raw output, reliability
sidecar, parsed JSON, logs, hashes, command, exit code, and runtime under
`results/external77_independent_test/petfold/`.

## Failure policy

An execution is invalid if the process exits nonzero, the final PETfold
structure line is absent, the structure length differs from the input, the
reliability sidecar is missing, or canonical pair validation fails. No RNA is
excluded for prediction quality. Historical outputs under
`/root/autodl-tmp/data/ss/petfold/` remain read-only.
