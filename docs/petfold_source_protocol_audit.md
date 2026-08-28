# PETfold Legacy121 source-protocol audit

Status: **CORRECTED — REPRODUCED_HISTORICAL_SINGLE_SEQUENCE_CONDITION**.

The prior audit classified PETfold as nonreproducible because it assumed that
the Legacy121 `.db` files came from an unrecoverable multi-sequence alignment
workflow. That assumption was incorrect. The migrated current-server
installation and the user-confirmed historical workflow use single-sequence
FASTA input. Direct reruns reproduce 10/10 audit RNAs and 121/121 Legacy121
canonical pair sets exactly.

## Evidence recovered

* The validated migrated executable is `/root/autodl-tmp/PETfold/bin/PETfold` (PETfold v2.0; SHA-256 `eb0636da9e1a5a2d28d0e8b14f7c35512eceeafdd46fbcbd5523125ee3bb3446`).
* Its grammar and rate files are `/root/autodl-tmp/PETfold/bin/article.grm` (SHA-256 `8ecfd9b8c96f0e5b1d60c4bd672ef327d9b14c7c11a3f7103c97ca37a7e6fa27`) and `/root/autodl-tmp/PETfold/bin/scfg.rate` (SHA-256 `1304ee9d519d03ca280e29ab8043afcdcff953c186fc4454c28751fcc854159f`).
* The earlier DRfold wrapper invokes the same direct-FASTA interface: `PETfold -f <fasta> -r <pair_reliability>` and reads the final PETfold structure line. The migrated `src/petfold.c` is byte-identical to the prior local source.
* Legacy121 sequence files are single-record FASTA. The current runner uses one ungapped query row, `PETFOLDBIN=/root/autodl-tmp/PETfold/bin PETfold -f <input.fasta> -r <output.petfoldrr>`, with PETfold defaults.

## Component classification

| Component | Status | Finding |
|---|---|---|
| PETfold binary/package | REPRODUCED | Migrated PETfold v2.0 binary and source are present; binary reports v2.0 through `--help`. |
| thermodynamic/model assets | REPRODUCED | `article.grm` and `scfg.rate` are present and hashed. |
| exact historical command | REPRODUCED_WITH_EVIDENCE | Direct single-sequence command is consistent with the retained wrapper and gives 121/121 exact output reproduction. |
| input format and row/query semantics | REPRODUCED | One-record FASTA / one ungapped query row; no biological MSA dependency. |
| alignment generation/database | NOT_APPLICABLE | No biological alignment is used for the historical single-sequence condition. |
| gap projection to ungapped query coordinates | NOT_APPLICABLE | The input row has no gaps; output positions map directly to query positions. |
| coordinate conversion | REPRODUCED | Structure characters are parsed zero-based into canonical pairs without a one-based shift. |
| external77 execution under identical semantics | REPRODUCED | Frozen single-sequence protocol ran successfully on 42/42 external RNAs. |

## Decision

The previous MSA/gap-projection blocker is closed as an incorrect assumption.
The corrected frozen protocol is defined in
`docs/petfold_single_sequence_source_protocol_v1.md`. Historical outputs were
not modified; all rerun outputs and comparisons are separate artifacts.
