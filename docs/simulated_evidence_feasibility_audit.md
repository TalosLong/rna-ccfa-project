# Simulated Evidence v1 Feasibility Audit

Status: **STAGE E0 COMPLETE — READY_FOR_EVIDENCE_STAGE_E1**

This audit used the 121 unique sequence/GT rows reconstructed from the 363
normalized Legacy121 records. The generator received only RNA ID, sequence,
and exact GT pairs. No source prediction, score, or error annotation was
inspected for sampling or feasibility.

## Universe feasibility

All 121/121 RNAs have at least one positive-pair item and all 121/121 have at
least one unpaired-nucleotide item. Pair universes contain 1,676 items total
(median 11, range 4–60). Unpaired universes contain 1,686 positions total
(median 10, range 3–104). There are no zero-universe RNAs in either channel.

The clean suite contains exactly 7,260 manifests:
`2 channels × 6 densities × 5 seeds × 121 RNAs`. Across the seed-replicated
suite, 16,450 evidence items are selected.

| Channel | Density | Items per seed | Items across 5 seeds | Minimum-one RNAs per seed |
|---|---:|---:|---:|---:|
| Positive pair | 0% | 0 | 0 | 0 |
| Positive pair | 1% | 121 | 605 | 119 |
| Positive pair | 5% | 130 | 650 | 53 |
| Positive pair | 10% | 180 | 900 | 1 |
| Positive pair | 20% | 338 | 1,690 | 0 |
| Positive pair | 50% | 875 | 4,375 | 0 |
| Unpaired nucleotide | 0% | 0 | 0 | 0 |
| Unpaired nucleotide | 1% | 121 | 605 | 119 |
| Unpaired nucleotide | 5% | 134 | 670 | 48 |
| Unpaired nucleotide | 10% | 185 | 925 | 4 |
| Unpaired nucleotide | 20% | 333 | 1,665 | 0 |
| Unpaired nucleotide | 50% | 873 | 4,365 | 0 |

Low densities are feasible but coarse for small RNAs. At 1%, minimum-one
behavior applies to 119/121 RNAs in each channel; 53 pair universes and 48
unpaired universes contain fewer than ten items. Such rows provide one
observation rather than a precise 1% dose and must be interpreted using actual
item counts as well as nominal density.

## Noise mechanism validation

The deterministic validation sample used the largest eligible universe in
each channel, both from `9G7C_224_4wj_cryoEM_A`, at 50% density and evidence
seed 101. It generated ten manifests: clean plus 5/10/20/30% noise for each
channel. Pair evidence selected 30 observations; unpaired evidence selected
52. Across nonzero noise levels, all 54 requested corruptions were generated
and zero were unavailable. This validates the mechanism, not full-dataset
noise performance or universal corruption availability. The protocol retains
explicit `CORRUPTION_UNAVAILABLE` handling for other RNAs.

All manifests passed coordinate, ordering, uniqueness, one-partner, source
universe, and payload-hash validation. Corrupted pair items passed the frozen
canonical nucleotide-type and non-GT checks. Invalid-coordinate, duplicate,
canonical-pair, and manifest-validation failure counts were all zero.

## Reproducibility and conclusion

Two independent in-process generations produced identical canonical JSONL
bytes with SHA256
`c743913d8d0b44cbccaba74b68bebaeb1551a4095d1ae51782435c12e96d11ca`.
The frozen fold assignment hash remains
`810b04a3963acc7637b60fcb5c2246c765fac334f809a5af9f8f050824ed974f`.

Both channels are sufficiently populated for controlled clean hard-baseline
evaluation. E0 is complete and the project is
`READY_FOR_EVIDENCE_STAGE_E1`. This conclusion does not establish that the
evidence improves any prediction; no Stage E1 transformation or structure
metric was evaluated, and external77 was not accessed.
