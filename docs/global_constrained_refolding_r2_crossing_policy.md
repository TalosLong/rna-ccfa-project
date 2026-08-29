# R2 Crossing-Evidence Policy Amendment

## Status

**`PROSPECTIVE AMENDMENT v1.0.1 — FROZEN BEFORE R2 EXECUTION`**

Protocol v1.0 was frozen before execution. Its representability blocker was
discovered before any formal R2 metric. This amendment resolves only the
standard solver's inability to represent crossing delivered pair constraints;
it is a solver-capability exclusion, never a performance- or GT-based sample
selection rule.

## Frozen policy

R2/B2 remains the standard pseudoknot-free ViennaRNA global constrained-
refolding baseline. No pseudoknot-capable solver, evidence modification,
maximum noncrossing subset, sequential refolding, or evidence resampling is
allowed. Every delivered item remains in its manifest.

For `POSITIVE_PAIR_EVIDENCE`, a manifest is `R2_ELIGIBLE` exactly when its
complete delivered exact-pair set is noncrossing. If any pair relation
`i < k < j < l` exists, the entire manifest is
`R2_INELIGIBLE_CROSSING_EVIDENCE`; B2 is not run for that manifest. Crossing
items are not deleted or rewritten. `UNPAIRED_NUCLEOTIDE_EVIDENCE` remains
eligible under v1.0 semantics unless a separate ViennaRNA expression blocker
is found.

The deterministic checker is `scripts/audit_r2_manifest_eligibility.py` and
uses only delivered coordinates and manifest metadata. It does not read GT,
prediction quality, labels, source identity, performance, or external77.

## Matched comparison universe

Primary B0/B1/B2 comparisons use exactly the same `R2_ELIGIBLE` manifest IDs.
The existing E1/B1 full-universe results are immutable. The audit creates
`r2_matched_b1_view.csv` by manifest-ID filtering only; it does not rerun or
retune B1.

## Coverage audit

The audit reports totals and eligible RNA counts by density, evidence seed,
density×seed, RNA, and RNA×density. A zero-coverage RNA×density stratum is
reported as missing; it is never imputed and cannot be selected after seeing
results. Coverage statistics do not change the eligibility policy.

## Aggregation freeze

Event-pooled/micro-like summaries concatenate eligible realization events.
Primary macro-style summaries first aggregate eligible evidence realizations
within each RNA (for the specified channel, density, source and other frozen
factor), then give each RNA equal weight. The denominator and eligible-
realization count are retained. If an RNA×density stratum has no eligible
realization, that stratum is `NA_MISSING_ELIGIBILITY` and is excluded from the
macro mean with its missing count reported; no imputation or post-hoc policy
change is allowed. Micro-like summaries remain sums over eligible events.

## Authorization

After the deterministic checker, coverage audit, matched-universe artifact,
aggregation rules, and tests pass, R2 is authorized to proceed on eligible
manifests only. This amendment does not authorize pseudoknot handling,
external77 access, learned training, or any R3/R4 work.
