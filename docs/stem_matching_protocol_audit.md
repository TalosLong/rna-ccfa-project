# Legacy121 Stem-Matching Protocol Audit

Frozen: 2026-08-27. This is a read-only candidate audit; no stem-error labels
or final counts were generated.

## Audit scope

The audit examined all 363 normalized Legacy121 records (121 RNAs × 3
predictors), using strict stems v1. The normalized input SHA-256 is
`e8ce10ce2670739be70b1f98c02604b8d19e783497ce05e4d11d3282aebe5c22`.
There were 1,005 repeated GT stem instances and 933 predicted stem instances.

## Candidate alternatives

For every stem pair, exact overlap, arm overlaps, pair union, and register
displacement were computed. The following filters were compared:

| filter | candidate edges | zero-overlap shift candidates | ambiguous predicted stems |
|---|---:|---:|---:|
| exact overlap only | 860 | 0 | 53 |
| bilateral arm overlap ≥1 | 880 | 20 | 55 |
| bilateral arm overlap ≥2 | 871 | 11 | 53 |
| ≥2 and each arm ≥ half shorter | 871 | 11 | 53 |
| ≥2 and each arm ≥ 75% shorter | 871 | 11 | 53 |
| **all-but-one shorter arm (chosen)** | **871** | **11** | **53** |
| full shorter-arm coverage | 869 | 9 | 53 |

The chosen rule requires at least two overlapping nucleotides on each arm and
allows at most one unmatched nucleotide on each arm of the shorter stem. It
retains the audited positive register-shift examples while excluding the nine
weak bilateral-one candidates; the equivalent half/75% rules gave the same
Legacy121 graph, but the all-but-one statement is directly interpretable.

## Assignment and ambiguity diagnostics

Greedy exact-overlap matching and maximum-weight bipartite assignment (objective
ordered as exact overlap, minimum arm overlap, matched-edge count, then inverse
union size) selected 811 edges in both approaches, with zero differing records.
Nevertheless, 53 predicted stems were candidates for multiple GT stems. Under
the chosen graph there were 758 isolated one-to-one edges and 53 ambiguous
components; 113 GT stems and 53 predicted stems occurred in those components.
There were 134 zero-candidate GT stems and 122 zero-candidate predicted stems.

Representative pathological cases include a long predicted stem overlapping
two GT stems (1E4P), equal-overlap ties from a predicted stem spanning two GT
stems (1P5O), and a shift candidate competing with exact overlaps (1P5M).
For this reason the protocol gates ambiguous components to `complex_mismatch`
rather than allowing a global optimizer to manufacture a biological relation.

The 11 potential shifts comprise 10 isolated candidates and one ambiguous
candidate. They include the documented register-displacement cases A and B;
the shared-register mixed-boundary case C is not a shift.

## Rejected alternatives and limitations

Pure greedy assignment was rejected as the normative rule because local ties
are not a stable scientific criterion. Unfiltered nearest/arm-overlap matching
was rejected because it admits weak or merged-stem relations. Full shorter-arm
coverage was rejected because it discards two audited positive candidates.
The protocol does not bridge gaps, classify pseudoknots, or infer biological
causes. Strict stems are intentionally conservative, and ambiguous components
remain residual states pending later extraction.

The reproducible audit is
`scripts/audit_legacy121_stem_matching_candidates.py`; its machine-readable
output is `results/error_analysis/stem_matching_candidate_audit.json`.
