# R2 Minimum-Loop Representability Policy Amendment

## Status

**`PROSPECTIVE AMENDMENT v1.0.2 — FROZEN BEFORE ANY FORMAL R2 PERFORMANCE METRIC`**

Protocol history is cumulative and immutable:

- v1.0: initial global hard-constrained refolding protocol;
- v1.0.1: crossing-evidence representability amendment;
- v1.0.2: minimum-loop representability amendment defined here.

The v1.0.2 decision follows the fail-closed partial execution that identified
ViennaRNA minimum-loop incompatibility. No B0/B1/B2 performance metric,
edit/scope analysis, evidence-efficiency result, or Gate A interpretation was
computed before this amendment was frozen.

## Frozen solver and model

B2 remains standard ViennaRNA 2.4.17 global hard-constrained MFE refolding:

```text
/usr/bin/RNAfold --noPS -C --enforceConstraint
```

The model remains linear RNA, 37 C, dangles=2, default parameters, standard
non-pseudoknot dynamic programming, and the default minimum-loop setting. The
amendment does not change the executable, temperature, energy parameters,
minimum-loop model, constraint symbols, or solver. It does not delete,
rewrite, weaken, replace, or resample any delivered evidence item.

## Complete positive-pair capability eligibility

Eligibility is determined only from the complete delivered exact-pair set and
the frozen solver-capability rules. It never reads predictor identity,
prediction quality, B1/B2 output, TP/FP/FN, F1, or any other performance
quantity.

For every `POSITIVE_PAIR_EVIDENCE` manifest, retain two independent flags.

### Crossing representability

`crossing_flag` is true when any two delivered canonical pairs satisfy:

```text
i < k < j < l
```

or the symmetric ordering. This retains v1.0.1 unchanged.

### Minimum-loop representability

ViennaRNA 2.4.17 with the frozen settings requires at least three nucleotides
inside a forced pair. For zero-based canonical `(i,j)`, the enclosed count is
`j-i-1`; therefore the exact capability condition is:

```text
j - i - 1 >= 3
equivalently: j - i > 3
```

`minimum_loop_flag` is true when any delivered exact pair has `j-i<=3`.
Boundary integration checks under the frozen command establish that `j-i=3`
is omitted with a minimum-loop warning while `j-i=4` is satisfied. The checker
implements this general coordinate rule rather than known RNA, pair, or
manifest IDs.

### Existing validity contract

All delivered coordinates must remain in bounds and canonical, with no
duplicate pair, self pair, or endpoint assigned to multiple partners. A
position cannot be simultaneously forced paired and unpaired. Existing clean
pair and unpaired manifests use separate channels, but the adapter retains the
generic conflict check. Invalid inputs fail closed and are not converted into
capability exclusions.

### Primary eligibility status

Each manifest has one primary status while both capability flags are retained:

```text
R2_ELIGIBLE
R2_INELIGIBLE_CROSSING_EVIDENCE
R2_INELIGIBLE_MINIMUM_LOOP_EVIDENCE
R2_INELIGIBLE_MULTIPLE_CAPABILITIES
```

If both flags are true, the multiple-capabilities status is used. Any
capability-ineligible status excludes the entire manifest. No evidence item is
removed and no alternative B2 structure is generated.

## Unpaired channel

`UNPAIRED_NUCLEOTIDE_EVIDENCE` retains v1.0/v1.0.1 semantics and remains fully
eligible unless the deterministic v1.0.2 audit discovers a separate frozen-
solver representability issue. Pair-channel exclusions never alter the
unpaired universe.

## Matched universe and aggregation

Formal B0/B1/B2 comparisons use exactly the v1.0.2 `R2_ELIGIBLE` manifest IDs.
Existing B1 outputs are filtered by manifest ID only; B1 is not rerun or
retuned. B0 joins use the same IDs.

The v1.0.1 aggregation freeze is unchanged. Event-pooled/micro summaries pool
eligible realization counts. RNA-balanced macro summaries first pool eligible
realizations within RNA and then weight RNAs equally. An RNA×density stratum
with no eligible realization is `NA_MISSING_ELIGIBILITY`, excluded from the
macro denominator, and reported explicitly without imputation.

## Execution reuse and completion gate

Previously generated PASS structures may be reused only after row-level
verification of manifest ID, sequence hash, evidence/manifest hash, rebuilt
constraint, frozen command/configuration, folding-input hash, output parser and
validity, hard-constraint satisfaction, and output hash. Historical failed
rows remain immutable provenance and are never relabeled PASS.

Before scientific summarization, every v1.0.2 eligible row must have one fully
validated PASS B2 output and every capability-ineligible row must be absent
from the matched metric universe. Eligible constraint satisfaction must be
100%. Any remaining eligible failure is a new blocker and stops analysis.

## Authorization boundary

After the v1.0.2 coordinate-only audit, coverage audit, matched B0/B1 views,
boundary tests, and execution-reuse gate pass, R2 may resume on the amended
eligible universe. This amendment does not authorize R3/R4, learned training,
historical E2, external77, noisy or real evidence, pseudoknot solvers, evidence
resampling, ViennaRNA parameter tuning, or 2D-to-3D work.
