# external77 source-protocol gate

This gate is evaluated before any three-source normalization. The frozen
membership is the 42-row `external77_GT_CON_v1_nonredundant` manifest; no GT
structure is an input to source prediction.

| Dependency | PETfold | trRosettaRNA2 native SS |
|---|---|---|
| Historical code/binary | Local PETfold executable is present, SHA-256 `99deeb0066a246b8f6ac79e13f2c60f62dd63e3f2774fb0649f0dd35ffe980ad`; DRfold checkout `9586990c79e4ca488e5f967fcc8bd5b06cd60273` | Local standalone pathway is present in the trRosettaRNA2 checkout; source condition is query-only native SS |
| Model/checkpoint assets | `article.grm` and `scfg.rate` are present; historical use is not proven | Three retained `model_{1,2,3}_finetune.pth.tar` checkpoints; hashes are recorded in the JSON gate |
| Required input | Legacy121 alignment files and their generation command/database snapshot | One-row, ungapped A3M containing the query sequence; external A3Ms are generated directly from the frozen manifest |
| Historical row/query semantics | UNKNOWN: no Legacy121 alignment or row-order record | REPRODUCED: the query is the only/first row for the recovered native-SS condition |
| Gap/coordinate semantics | BLOCKING: the historical alignment-gap to ungapped-query projection is absent | Not applicable to the query-only condition |
| Decoder/output authority | BLOCKING: historical output mapping cannot be reconstructed | REPRODUCED: ensemble mean dense `ss` matrix, threshold `>0.5`, strongest-probability one-partner greedy decoder; raw matrix is authoritative and DBN is derived |
| External coverage | Not run; no substitute condition permitted | 42/42 valid; finite `[L,L]` matrices and canonical pairs validated |
| Gate status | **NONREPRODUCIBLE / BLOCKING** | **REPRODUCED source condition** |

## Decision

The overall gate is **BLOCKED**. PETfold cannot be run under Legacy121
semantics because the historical alignment inputs and projection map are not
retained. PETfold single-sequence folding would be a separately named new
source condition and is not run here. The trRosettaRNA2 result is retained as
an auditable source-condition result, but it does not authorize the frozen
three-source claim or partial normalization.

The machine-readable copy is
`results/external77_independent_test/source_protocol_gate.json`. Detailed
forensic evidence is in
`docs/petfold_source_protocol_audit.md` and
`docs/trrosettarna2_native_ss_source_protocol_audit.md`.
