# external77 source-protocol gate

This gate is evaluated before any three-source normalization. The frozen
membership is the 42-row `external77_GT_CON_v1_nonredundant` manifest; no GT
structure is an input to source prediction.

| Dependency | PETfold | trRosettaRNA2 native SS |
|---|---|---|
| Historical code/binary | REPRODUCED: `/root/autodl-tmp/PETfold/bin/PETfold`, PETfold v2.0, SHA-256 `eb0636da9e1a5a2d28d0e8b14f7c35512eceeafdd46fbcbd5523125ee3bb3446` | Local standalone pathway is present in the trRosettaRNA2 checkout; source condition is query-only native SS |
| Model/checkpoint assets | REPRODUCED: `article.grm` and `scfg.rate` hashes are frozen in the single-sequence protocol | Three retained `model_{1,2,3}_finetune.pth.tar` checkpoints; hashes are recorded in the JSON gate |
| Required input | REPRODUCED: direct FASTA with one ungapped query row; no biological MSA/database | One-row, ungapped A3M containing the query sequence; external A3Ms are generated directly from the frozen manifest |
| Historical row/query semantics | REPRODUCED: 121/121 exact canonical pair-set reproduction | REPRODUCED: the query is the only/first row for the recovered native-SS condition |
| Gap/coordinate semantics | REPRODUCED: no gaps; structure positions map directly to zero-based query coordinates | Not applicable to the query-only condition |
| Decoder/output authority | REPRODUCED: final PETfold structure line, project parser, one-partner canonical validation | REPRODUCED: ensemble mean dense `ss` matrix, threshold `>0.5`, strongest-probability one-partner greedy decoder; raw matrix is authoritative and DBN is derived |
| External coverage | 42/42 valid; raw output, reliability sidecar, parsed JSON, logs, and hashes retained | 42/42 valid; finite `[L,L]` matrices and canonical pairs validated |
| Gate status | **REPRODUCED_HISTORICAL_SINGLE_SEQUENCE_CONDITION** | **REPRODUCED source condition** |

## Decision

The overall gate is **PASS** for the historical source conditions. The prior
PETfold blocker was caused by an incorrect MSA assumption and is closed by the
121/121 exact reproduction. The trRosettaRNA2 query-only native-SS condition
remains separately identified and fully provenance-audited.

The machine-readable copy is
`results/external77_independent_test/source_protocol_gate.json`. Detailed
forensic evidence is in
`docs/petfold_source_protocol_audit.md` and
`docs/trrosettarna2_native_ss_source_protocol_audit.md`.
