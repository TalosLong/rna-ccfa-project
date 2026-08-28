# PETfold Legacy121 source-protocol audit

Status: **NONREPRODUCIBLE for the external77 independent test**.

## Evidence recovered

* The executable is `/root/autodl-tmp/models/DRfold_repo/third_party/PETfold/bin/PETfold` (SHA-256 `99deeb0066a246b8f6ac79e13f2c60f62dd63e3f2774fb0649f0dd35ffe980ad`).
* The checked-out DRfold repository is commit `9586990c79e4ca488e5f967fcc8bd5b06cd60273`; its reproduction notes identify the bundled PETfold build as PETfold 2.0 linked to ViennaRNA 2.0.7.
* The wrapper in `DRfold_repo/scripts/Feature.py` invokes `PETfold -f <fasta> -r <pair_reliability>` and reads the final output structure. This establishes an executable local implementation, but not the historical Legacy121 input semantics.
* Legacy121 manifests point to `/root/autodl-tmp/data/ss/petfold/*.db` outputs. No corresponding alignment files, alignment manifests, command logs, database snapshot, or per-record gap-projection map were found under the project or `/root/autodl-tmp` search roots.

## Component classification

| Component | Status | Finding |
|---|---|---|
| PETfold binary/package | INFERRED_WITH_EVIDENCE | Local binary and DRfold commit are present; binary has no reliable `--version` output. |
| thermodynamic/model assets | REPRODUCED | `bin/article.grm` and `bin/scfg.rate` are present beside the binary. |
| exact historical command | INFERRED_WITH_EVIDENCE | DRfold wrapper command is known, but no evidence proves it produced the Legacy121 `.db` files. |
| alignment format and row order | UNKNOWN | Historical alignment inputs are absent. |
| alignment generation/database | UNKNOWN | No generator command or database snapshot is retained. |
| gap projection to ungapped query coordinates | BLOCKING | PETfold output coordinates can include `-`; the mapping used for Legacy121 cannot be reconstructed. |
| external77 execution under identical semantics | BLOCKING | Choosing a new alignment or projection would define a new source condition. |

## Decision

The historical PETfold source is not reproducible enough to run external77
without changing semantics. A single-sequence invocation using the local
binary could be frozen later as `PETfold_SINGLE_SEQUENCE_NEW_SOURCE`, but it
must not be called historical PETfold and is not run in this task.
