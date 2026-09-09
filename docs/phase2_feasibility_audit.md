# Phase II Feasibility Audit

Status: **`PHASE2_M0_FEASIBILITY_AUDIT_COMPLETE_WITH_BLOCKERS`**

Audit date: **2026-09-09 UTC**

Scope: formulas, frozen-contract logic, synthetic counterexamples, local
artifact presence, and public source metadata only.

This is **not** a software-validation result, Development-v2 result, predictor
benchmark, biological performance result, real-evidence experiment, or
independent evaluation.

## 1. Evidence labels

| Label | Meaning in this audit |
| --- | --- |
| **CONFIRMED_LOCAL** | Directly observed in the repository or current local environment |
| **FORMULA_DERIVED** | Deterministic arithmetic from a stated frozen formula |
| **PUBLIC_METADATA** | Reported by an official resource or primary publication; not independently materialized here |
| **ESTIMATE** | Planning approximation, never an observed cohort count or performance value |
| **UNKNOWN** | Cannot be established without a later authorized build/audit; no value is imputed |

## 2. Frozen risk-bound arithmetic

For six fixed complete policies, `alpha=0.10`, `delta=0.05`, and `n`
independent biological calibration clusters, the frozen simultaneous one-sided
Hoeffding bound is

\[
U_k=\min\left(1,\bar L_k+
\sqrt{\frac{\log(6/0.05)}{2n}}\right).
\]

The largest empirical mean that can satisfy `U_k <= 0.10` is `alpha` minus
the radius.

| n biological clusters | Hoeffding radius | Largest certifiable empirical mean | Zero-risk UCB | Status |
| ---: | ---: | ---: | ---: | --- |
| 240 | 0.099869620660 | 0.000130379340 | 0.099869620660 | **FORMULA_DERIVED** |
| 500 | 0.069191702846 | 0.030808297154 | 0.069191702846 | **FORMULA_DERIVED** |
| 1,000 | 0.048925922285 | 0.051074077715 | 0.048925922285 | **FORMULA_DERIVED** |

Thus 240 is a formal readiness boundary, not evidence of practical risk-control
power. At 240 clusters, even one nontrivial average loss can exhaust the
available margin. Larger `n` permits a nonzero empirical loss, but coverage
still matters: no-edit RNAs contribute loss zero and coverage zero. Replicates,
predictor outputs, pair candidates, evidence realizations, and random seeds do
not increase `n` when they belong to the same biological cluster.

### 2.1 Cluster-budget audit

The frozen source audit reports source-level quantities such as 4,028 RNASSTR
folds, 4,227 Rfam 15.1 families, and a PDB-derived RNA3DB-2D candidate pool.
Those values are neither Development-v2 records nor independent risk clusters.
The 80/80 sequence rule, higher-priority family/provenance connected
components, date/structure filters, predictor-overlap filtering, Legacy121
exclusion and five-way role allocation can only reduce the usable budget.

| Quantity | Current state |
| --- | --- |
| Raw source-level records/families | **PUBLIC_METADATA**, heterogeneous and not additive |
| Eligible Development-v2 records | **UNKNOWN** |
| Connected biological components after all firewalls | **UNKNOWN** |
| Components available to each of the five roles | **UNKNOWN** |
| RISK_CALIBRATION components | **UNKNOWN**; must be at least 240 for the frozen formal route |
| Expected useful policy coverage/HarmRate | **UNKNOWN**; requires future development data and cannot be inferred from source scale |

Required later output: an authorized manifest build that records exact artifact
hashes, every filter attrition count, connected-component construction, role
allocation, and a pre-outcome decision on whether the frozen risk route is
ready. No role merging or bound change is implied here.

## 3. E0 hard-evidence versus S0 fallback

### 3.1 Synthetic counterexample

Use sequence `GAAAAAAACU` (length 10), source structure
`S0={(0,9)}`, and valid E0 item `POSITIVE_PAIR_SUPPORT(0,8)`.

- `(0,9)` is a legal GU pair and `(0,8)` is a legal GC pair.
- Both satisfy `j-i>3` and are individually valid noncrossing structures.
- The E0 fact is internally valid, but it conflicts with the old partner at
  nucleotide 0.
- Satisfying E0 requires `DELETE(0,9) + ADD(0,8)`, reported as REPLACE with
  edit cost 2.
- Reverting that component, all-abstaining, or failing closed to `S0` restores
  `(0,9)` and removes mandatory `(0,8)`.

Therefore the two universal statements below cannot both hold:

```text
every valid E0 package is exactly satisfied by the returned structure
every component/RNA failure may return S0 with zero committed edits
```

This contradiction follows from frozen semantics; it is not a decoder bug and
cannot be hidden by a greedy repair.

### 3.2 Prospective semantic candidates — not selected

| Candidate | Definition | Consequence/trade-off |
| --- | --- | --- |
| A. Non-abstainable direct feasibility edits | Mandatory E0 edits are committed before risk abstention; only LOCAL/PROPAGATED components may revert | Preserves hard E0, but no longer permits all edits to return to S0 and requires direct-edit harm/coverage accounting |
| B. E0-feasible fallback anchor | Construct a deterministic minimum-edit `S_E0` satisfying valid E0 and fall back to it rather than S0 | Preserves hard E0 and a fail-closed structure, but changes the baseline/failure contract and matched-control definition |
| C. Defeasible/soft E0 | Permit risk/failure to override an E0 item | Preserves S0 fallback but abandons the current hard-intervention meaning |
| D. Admit only S0-compatible E0 | Reject any E0 requiring ADD/REPLACE | Preserves both current fallback and admitted hard facts, but defeats the frozen ADD/REPLACE purpose of positive E0 |

No candidate is adopted by this audit. A prospective versioned amendment must
choose one, define invalid-E0 versus valid-but-S0-incompatible behavior, define
matched evidence-masked controls and coverage denominators, update fixtures,
and regenerate hashes before implementation.

Affected contracts include at minimum:

- `docs/phase2_dataset_and_task_protocol.md` Sections 10--13;
- `docs/phase2_structured_decoder_protocol.md` Sections 6, 9 and 10;
- `docs/phase2_risk_control_design.md` selective/fail-closed policy semantics;
- `docs/phase2_p3_minimal_baseline_implementation_plan.md`; and
- `docs/phase2_protocol_freeze_manifest.md` through a new prospective version,
  never by silently editing the v1.0 historical record.

Current blocker: **`PHASE2_E0_ABSTENTION_PROTOCOL_CONFLICT`**.

## 4. Exact DP applicability

The interval DP is exact when all of the following hold:

1. candidate scores are fixed before decoding and the objective is a sum of
   selected pair terms;
2. `EditCost(S,S0)` is the additive pair symmetric difference, so it can be
   absorbed into pair weights;
3. feasibility consists of the frozen one-partner, canonical/Wobble,
   minimum-loop, noncrossing and pair/unpaired E0 restrictions; and
4. deterministic full-solution tie-breaking is represented exactly.

Contextual neural or foundation-model features may produce the fixed pair
scores upstream. That does not authorize the decoder to optimize arbitrary
higher-order terms. The current recurrence is not, without an expanded state
and prospective proof, exact for pseudoknots, whole-stem rewards, pair-pair
potentials, arbitrary component-risk penalties, or objectives whose score for
a pair changes with other selected pairs. Post-decoding component ABSTAIN is a
separate operation and its recombined output still requires an independent
validity audit.

Conclusion: exactness is **CONFIRMED_LOCAL at the contract level only** for the
stated decomposable objective. Implementation equality with an exhaustive
oracle remains untested because P3 code is not part of this task.

## 5. Sampling assumptions and metric separation

The Hoeffding/union-bound statement requires bounded cluster losses, a fixed
six-policy family, and independent or appropriately exchangeable biological
cluster observations from the target calibration population. Risk-calibration
labels cannot have selected the data split, model, features, score calibrator,
policy family, or policy parameters. Within-cluster RNAs may be averaged into
one cluster loss, but do not become independent samples. Family, predictor and
time shift are not covered by a marginal same-population guarantee merely
because the split is family-aware.

| Quantity | Denominator and role | Why it cannot substitute for the others |
| --- | --- | --- |
| Original TP preservation | True pairs already present in S0 | Directly exposes damage to correct source information; says little about new ADD quality |
| HarmRate | Harmful committed atoms divided by `max(1, all committed atoms)`, then RNA/cluster balanced | Measures conditional quality of edits; zero-edit units lower mean loss |
| Edit-atom coverage | Eligible/proposed atoms actually committed under a frozen definition | Shows whether low harm is achieved by doing almost nothing |
| RNA coverage | Fraction of RNAs with at least one committed edit | Detects concentration of edits in a small subset of RNAs |

All-abstain has HarmRate zero but atom and RNA coverage zero. It is a safe
failure behavior, not a useful-policy success. M2/M4 must prospectively freeze
both utility and coverage requirements before relevant outcomes are exposed.

## 6. RMDB-to-SHAPE source route

This audit selected one route only: SHAPE measurements represented in the RNA
Mapping Database (RMDB). It inspected public metadata and documentation, not a
locked cohort or measurement values.

### 6.1 Public metadata findings

- RMDB describes itself as an archive for mapping data including SHAPE, DMS,
  CMCT, 1M7, mutate-and-map and M2-seq, with downloadable RDAT records
  ([RMDB About](https://rmdb.stanford.edu/about/)).
- The official RDAT specification provides sequence, structure, offset,
  construct/data annotations, `REACTIVITY`, `REACTIVITY_ERROR`, and optional
  trace/read fields. It records condition annotations such as modifier,
  temperature, processing and experiment type
  ([RDAT specification](https://rmdb.stanford.edu/deposit/specs/)).
- RMDB states database content is CC0, while site content is CC BY-SA 4.0; the
  reference `rdat_kit` parser is Apache-2.0
  ([RMDB deposit page](https://rmdb.stanford.edu/deposit/)).
- The primary RMDB description reports curation, error estimates/replicates,
  associated publications and structure annotations as deposition/release
  considerations ([original RMDB paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC3496344/)).

These properties make RMDB/RDAT a plausible discovery and transport format.
They do not prove that any particular entry supplies a compatible accepted
reference structure, complete condition metadata, independent replicate, or
Phase II-eligible biological cluster.

### 6.2 Required admission contract for a future source audit

| Requirement | Prospective rule | Current state |
| --- | --- | --- |
| Exact artifact | Freeze RMDB/RDAT record identifiers, retrieval date, raw bytes and SHA256 | **UNKNOWN** |
| License | Preserve database CC0/source terms and publication attribution; review linked third-party files separately | **PUBLIC_METADATA**, entry audit pending |
| Measurement identity | Require explicit SHAPE reagent/modifier and processing method; do not merge SHAPE, DMS or other modalities | Schema exists; entry completeness **UNKNOWN** |
| Conditions | Preserve temperature, buffer/ions, in vitro/in cellulo state and construct context | Schema/annotations exist; congruence **UNKNOWN** |
| Sequence match | Map exact construct sequence and offset to a versioned accepted reference; normalize only under a frozen rule; reject ambiguous/modified/multistrand mismatch | **UNKNOWN** |
| Reference structure | Require independent accepted 2D provenance and record whether it is experimental, comparative or inferred from the same probing data | **UNKNOWN**; circular labels are prohibited |
| Missingness | Retain missing/invalid positions as missing, never zero reactivity; freeze censoring and normalization before values are used | Rule not frozen |
| Replicates/errors | Preserve replicate IDs and errors; keep technical replicates within one biological cluster and define aggregation prospectively | Entry availability **UNKNOWN** |
| Development/confirmation | Assign biological clusters to a real-evidence development role or a sealed confirmation role before reading values; no cluster/conformer crosses roles | Not built |

Different solution or cellular conditions may represent real conformational
differences rather than predictor errors. A record is not eligible merely
because it has a sequence and a SHAPE vector. No RMDB sample, reactivity value,
or performance metric was downloaded or computed here.

## 7. Limited local predictor observation

This is a presence check, not the formal M1 deployment manifest:

| Frozen primary source | Local observation on 2026-09-09 | State |
| --- | --- | --- |
| RNAfold 2.7.2 | `/usr/bin/RNAfold` reports 2.4.17; a 2.7.2 source directory exists but no installed 2.7.2 binary was identified | version blocker for future deployment |
| MXfold2 v0.1.2 | package/repository not identified in the active Python environment/search scope | missing locally; formal checkpoint/hash audit pending |
| UFold frozen commit/checkpoint | package/repository/checkpoint not identified in the active Python environment/search scope | missing locally; formal hash/license audit pending |
| RiNALMo frozen commit/checkpoint | package/repository/checkpoint not identified in the active Python environment/search scope | missing locally; formal hash/license audit pending |

No predictor was run on biological data. M1 must perform the complete
license/version/commit/checkpoint/hash/determinism preflight and cannot replace
a frozen source silently.

## 8. Audit decision

Confirmed:

- the risk arithmetic matches the frozen formula;
- 240 is only a near-zero-loss formal minimum;
- the DP contract is exact only for the stated decomposable objective;
- TP preservation, HarmRate and coverage answer different questions;
- RMDB/RDAT is a plausible SHAPE metadata route; and
- the E0/S0 counterexample is a real semantic contradiction.

Unknown:

- exact Development-v2 and risk-calibration cluster counts;
- usable risk/coverage operating points;
- eligible RMDB-SHAPE entries and their condition/reference congruence;
- complete deployability of the four primary source predictors; and
- which prospective E0/fallback semantic candidate should be adopted.

Decision:

```text
PHASE2_ROADMAP_REVISED
PHASE2_M0_FEASIBILITY_AUDIT_COMPLETE_WITH_BLOCKERS
PHASE2_E0_ABSTENTION_PROTOCOL_CONFLICT
PHASE2_IMPLEMENTATION_NOT_AUTHORIZED
EXTERNAL77_LOCKED
```

The next proposed task is `RESOLVE_PHASE2_E0_ABSTENTION_PROTOCOL_CONFLICT`.
P3 implementation, data building, predictions, learning, performance work and
independent evaluation remain outside this audit.
