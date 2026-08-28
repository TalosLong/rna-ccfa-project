# trRosettaRNA2 native-SS Legacy121 source-protocol audit

Status: **REPRODUCED for the source condition used here; external execution
is provenance-complete but does not unblock the three-source matrix while
PETfold remains blocked**.

## Recovered pathway

The stored Legacy121 native-SS artifacts are the authoritative pair-score and
DBN outputs under
`/root/autodl-tmp/models/trRosettaRNA2/data/ss_native/<rna_id>/`:
`<rna_id>_ss_prob.npz` (key `ss`) and `<rna_id>.dbn`. All 121 matching input
files under `data/msas/` are query-only A3Ms (one header and one ungapped
sequence row), and their query sequences match the Legacy121 manifest exactly.
This is therefore a single-sequence native-SS condition, not an RNAcentral
homology-MSA condition.

The executable pathway is:

```
/root/autodl-tmp/models/trRosettaRNA2/env_trRNA2/bin/python \
  /root/autodl-tmp/models/trRosettaRNA2/scripts/tools/ss_predictor_standalone.py \
  -i <query-only.a3m> -o <output_dir> --gpu -1 --threshold 0.5
```

The standalone script loads the three frozen SS checkpoints
`model_{1,2,3}_finetune.pth.tar` (SHA-256 respectively
`23defcc04f02613c07cf9ca4653e9367845480e249a4c90e32a61cfa82bb6ec8`,
`79ee6324fcf377950d63643a538b1ecd8f5b768f27f40ac63f83060ad66c25a2`, and
`6ee709e30ff32f7b90791628b8bde7aa8bc877c2e7878b9f3bcb0e66b4af4eb3`). It
averages the three `[L,L]` sigmoid matrices and decodes at `>0.5` with the
existing strongest-probability one-partner greedy decoder. The raw matrix is
retained; DBN is a derived representation and cannot encode crossing pairs.

## Reproduction check

A read-only CPU rerun for `17RA_21_hp_nmr_A` with the stored query-only A3M
produced a DBN with the exact historical SHA-256
`3ac98149c2ef77acd13dc0dc9e2e6ca44cdcf61dba24a27da1bf5fc3dfe59f15` and the
same eight pairs. The NPZ arrays agree within `5.96e-08`; byte hashes differ
only because compressed NumPy serialization is not byte-stable. This validates
the decoder and input condition without modifying historical files.

## Component classification

| Component | Status | Finding |
|---|---|---|
| repository/code | REPRODUCED | local trRosettaRNA2 checkout and standalone script are present. |
| checkpoints | REPRODUCED | all three checkpoint files and hashes are retained. |
| Legacy121 input | REPRODUCED | 121 query-only A3Ms, sequence-identical to the frozen manifest. |
| external input construction | REPRODUCED | same query-only A3M format; no GT or external database is used. |
| score key/shape | REPRODUCED | NPZ key `ss`, dense `[L,L]` matrix. |
| decoder | REPRODUCED | ensemble mean, threshold `>0.5`, greedy one-partner decoder. |
| crossing-pair semantics | LIMITATION | DBN display is parenthesis-only; raw score matrix remains authoritative. |

This source condition is frozen as the query-only native-SS condition for the
42 external RNAs. It does not imply that an unrecovered MSA-based historical
condition would be equivalent.
