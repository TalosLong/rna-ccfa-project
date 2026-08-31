# Global Evidence-Constrained Refolding R2 Results

Status: **`R2_GLOBAL_CONSTRAINED_REFOLDING_COMPLETE`**

Next state: **`READY_FOR_R2_INTERPRETATION_AND_R3_PROTOCOL`**

Date: 2026-08-31

## Scope and interpretation boundary

R2 is the first formal global-refolding experiment in Project Reboot v2. It
compares B0 Original, B1 matched local hard evidence transformation, and B2
standard ViennaRNA global hard-constrained MFE refolding under the same frozen
clean delivered evidence. B2 receives sequence and evidence only; source
identity and source prediction are not folding inputs.

These results establish the strongest classical comparator required by future
Gate A. They do not evaluate a learned reconciler, decide Gate A, establish
model agnosticism, test noisy or real evidence, access external77, or support a
2D-to-3D claim.

## Protocol amendments

- v1.0 froze the initial standard ViennaRNA 2.4.17 protocol.
- v1.0.1 prospectively excluded whole pair manifests whose delivered exact
  pairs cross and are not representable by the standard non-PK solver.
- v1.0.2 prospectively excluded whole pair manifests containing any exact pair
  with `j-i<=3`, the frozen solver's minimum-loop incompatibility boundary.

The v1.0.2 amendment was frozen before any formal R2 performance metric was
computed. It did not change the binary, command, parameters, evidence, or
aggregation rules. See
`docs/global_constrained_refolding_r2_minimum_loop_policy.md`.

## Capability coverage

The coordinate-only v1.0.2 audit found no overlap between crossing and
minimum-loop exclusions.

| Channel/outcome | Manifests |
| --- | ---: |
| Pair total | 3,630 |
| Pair `R2_ELIGIBLE` | 3,523 |
| Crossing-ineligible | 87 |
| Minimum-loop-ineligible | 20 |
| Multiple-capability-ineligible | 0 |
| Unpaired total / eligible | 3,630 / 3,630 |
| Combined eligible B2 realizations | 7,153 |

Pair-channel coverage by density was:

| Density | Eligible manifests | Eligible RNAs | Missing RNAs |
| ---: | ---: | ---: | ---: |
| 0% | 605 | 121 | 0 |
| 1% | 605 | 121 | 0 |
| 5% | 603 | 121 | 0 |
| 10% | 595 | 121 | 0 |
| 20% | 570 | 118 | 3 |
| 50% | 545 | 113 | 8 |

The unpaired channel retained 605 manifests and all 121 RNAs at every
density. Eleven pair RNA-by-density strata had zero eligible realization:
`2M8K`, `6UES`, and `9G7C` at 20%; and `1A60`, `1E95`, `1RNK`, `2K95`,
`2M8K`, `2TPK`, `6UES`, and `9G7C` at 50% (full IDs are in the coverage
artifact). These strata are `NA_MISSING_ELIGIBILITY` and are not imputed.

The 20 minimum-loop exclusions occur in `2ES5_23_hp_nmr_A` (6),
`2MTJ_47_3wj_nmr_A` (3), `2N3Q_62_3wj_nmr_A` (3), and
`8JHP_27_hpbulge_nmr_A` (8).

## Execution integrity

All 7,153 v1.0.2-eligible outputs were reused from the previous fixed-command
run only after row-level validation of manifest membership, sequence/evidence
hashes, constraint, command/config hash, parser output, canonical pairs,
constraint satisfaction, and output hash. No new RNAfold call was needed.

- eligible PASS outputs: 7,153/7,153;
- eligible hard-constraint satisfaction: 100%;
- validation, parser, edit-accounting, and scope-partition failures: zero;
- capability-ineligible manifests entering metrics: 0/107;
- historical 87 crossing skips and 20 minimum-loop failures remain preserved;
- 0% reproducibility: 121/121 RNAs passed across both channels and five seeds;
- historical RNAfold versus R2 0% exact identity: 121/121, reported only as
  provenance context.

## B0/B1/B2 primary structure results

The overall table pools the complete matched source-realization universe
(21,459 rows per method). Macro first pools eligible realizations within RNA
and then weights RNAs equally; Micro pools pair-event counts.

| Method | Macro F1 | Micro F1 | Macro delta vs B0 | Micro delta vs B0 |
| --- | ---: | ---: | ---: | ---: |
| B0 Original | 0.878635 | 0.861068 | 0 | 0 |
| B1 Local hard | 0.889352 | 0.872422 | +0.010717 | +0.011354 |
| B2 Global refold | **0.924648** | **0.904747** | **+0.046012** | **+0.043679** |

| Channel | Method | Macro F1 | Micro F1 |
| --- | --- | ---: | ---: |
| Pair | B0 | 0.878635 | 0.870247 |
| Pair | B1 | 0.887848 | 0.879850 |
| Pair | B2 | **0.926124** | **0.914774** |
| Unpaired | B0 | 0.878635 | 0.852297 |
| Unpaired | B1 | 0.891343 | 0.865213 |
| Unpaired | B2 | **0.923142** | **0.895070** |

B2 improved matched F1 over both B0 and B1 in both channels. Pair B2 exceeded
B1 by +0.038276 Macro / +0.034924 Micro; unpaired B2 exceeded B1 by +0.031800
Macro / +0.029857 Micro.

## TP preservation, FP removal, and full-refold edits

Across all matched source-realizations, B2 produced:

| Quantity | Count or rate |
| --- | ---: |
| Preserved original TP | 255,871 |
| Lost TP | 4,752 |
| Removed FP | 32,433 |
| New TP | 11,042 |
| New FP | 10,823 |
| Beneficial changes | 43,475 |
| Harmful changes | 15,575 |
| TP preservation, Micro / Macro | 0.981767 / 0.975358 |
| FP removal, Micro / Macro | 0.645883 / 0.775728 |
| Modification precision, Micro / Macro | 0.736240 / 0.824449 |

Thus B2 made substantially more correction than B1, but unlike B1 it was not
preservation-perfect: B1 retained all original TP under the clean local
semantics, whereas B2 lost 4,752 original TP events while also recovering
11,042 new TP and removing 32,433 original FP.

## DIRECT, LOCAL_CONFLICT, and NON_EVIDENCED effects

The frozen scope partition was exhaustive over `G union S union R`. Direct
pair additions and local-conflict deletions were completely beneficial under
clean evidence. All collateral harm occurred in the non-evidenced scope.

| Scope | Modified | Beneficial | Harmful | Modification precision (Micro) |
| --- | ---: | ---: | ---: | ---: |
| DIRECT pair | 1,470 | 1,470 | 0 | 1.000000 |
| LOCAL_CONFLICT pair | 5,978 | 5,978 | 0 | 1.000000 |
| NON_EVIDENCED pair | 51,602 | 36,027 | 15,575 | 0.698171 |

NON_EVIDENCED decomposed into 26,455 removed FP, 9,572 new TP, 4,752 lost TP,
and 10,823 new FP. Its Macro modification precision was 0.779642. By channel,
NON_EVIDENCED Micro modification precision was 0.715653 for pair evidence and
0.681514 for unpaired evidence. Global propagation was therefore net
beneficial, but materially harmful rather than uniformly safe.

## Density response

Within each density, all deltas below use the same matched eligible rows.

| Channel | Density | B2 Macro F1 | B2 Micro F1 | Macro delta vs B0 | Macro delta vs B1 | Micro TP preservation | Micro FP removal | Micro modification precision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Pair | 0% | 0.905818 | 0.874443 | +0.027182 | +0.027182 | 0.980669 | 0.487122 | 0.653800 |
| Pair | 1% | 0.919811 | 0.886777 | +0.041175 | +0.034876 | 0.975847 | 0.578275 | 0.685091 |
| Pair | 5% | 0.926049 | 0.900083 | +0.047414 | +0.040467 | 0.975101 | 0.659351 | 0.716543 |
| Pair | 10% | 0.930776 | 0.918080 | +0.052141 | +0.043597 | 0.982615 | 0.692974 | 0.762033 |
| Pair | 20% | 0.944850 | 0.949394 | +0.053518 | +0.039571 | 0.986242 | 0.693949 | 0.810198 |
| Pair | 50% | 0.969208 | 0.971492 | +0.057590 | +0.033345 | 0.996673 | 0.741039 | 0.892234 |
| Unpaired | 0% | 0.905818 | 0.874443 | +0.027182 | +0.027182 | 0.980669 | 0.487122 | 0.653800 |
| Unpaired | 1% | 0.918559 | 0.883640 | +0.039923 | +0.032310 | 0.981760 | 0.565957 | 0.693453 |
| Unpaired | 5% | 0.918805 | 0.884048 | +0.040170 | +0.032063 | 0.979168 | 0.602912 | 0.679783 |
| Unpaired | 10% | 0.924845 | 0.895158 | +0.046210 | +0.036808 | 0.982488 | 0.664502 | 0.722285 |
| Unpaired | 20% | 0.927191 | 0.903602 | +0.048556 | +0.032406 | 0.979213 | 0.741769 | 0.740874 |
| Unpaired | 50% | 0.946599 | 0.930554 | +0.067964 | +0.031187 | 0.982215 | 0.890034 | 0.838912 |

B2's matched advantage over B0 increased with density in both channels. Its
increment over B1 stayed positive but was not monotonic. Pair evidence reached
higher F1 and modification precision at high density; unpaired evidence
removed a larger fraction of FP at 50% but retained lower TP preservation.

## Source-specific response

Because B2 excludes source identity and prediction, its absolute structure/F1
for a given RNA/evidence realization is source-independent. The relative
effect and preservation/correction accounting differ against each source.

| Source | Channel | B2 Macro delta vs B0 | B2 Macro delta vs B1 | Macro TP preservation | Macro FP removal | Macro modification precision |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| PETfold | Pair | +0.029275 | +0.019205 | 0.980748 | 0.359293 | 0.850780 |
| PETfold | Unpaired | +0.026293 | +0.018408 | 0.996419 | 0.475228 | 0.882291 |
| RNAfold | Pair | +0.020306 | +0.010904 | 0.981463 | 0.151727 | 0.832657 |
| RNAfold | Unpaired | +0.017325 | +0.010588 | 0.997229 | 0.308401 | 0.872810 |
| trRosettaRNA2 native SS | Pair | +0.083252 | +0.075867 | 0.969404 | 0.911100 | 0.775964 |
| trRosettaRNA2 native SS | Unpaired | +0.080271 | +0.060247 | 0.959629 | 0.934751 | 0.781854 |

The largest relative B2 gains and FP removal occurred against trRosettaRNA2,
but that source also had the lowest preservation. RNAfold had the smallest
relative gain and FP removal, consistent with B2 being the same frozen
RNAfold model at 0% and increasingly constrained versions at nonzero density.

## Evidence efficiency

Zero-density efficiency is NA and excluded. Event-pooled B2 FP removals per
delivered evidence item were:

| Density | Pair | Unpaired |
| ---: | ---: | ---: |
| 1% | 1.422590 | 1.392287 |
| 5% | 1.514403 | 1.339303 |
| 10% | 1.092150 | 1.069189 |
| 20% | 0.479745 | 0.663063 |
| 50% | 0.181835 | 0.303475 |

Correction per item diminished at high density in both channels. The frozen
RNA-balanced `delta_F1 / evidence_item_count` likewise declined from 0.002745
to 0.001132 for pair evidence and from 0.002662 to 0.000664 for unpaired
evidence between 1% and 50%. Full source-specific Micro/Macro values are in
`evidence_efficiency_summary.csv`.

## Empirical findings

1. B2 was the strongest tested classical structure baseline: overall Macro F1
   was 0.924648 versus 0.889352 for B1 and 0.878635 for B0.
2. Global refolding delivered large correction (32,433 removed FP and 11,042
   new TP) but destroyed 4,752 original TP and introduced 10,823 new FP; its
   benefit is therefore not equivalent to safe source-output preservation.
3. Non-evidenced propagation was net beneficial (36,027 beneficial versus
   15,575 harmful changes) but only 0.698171 precise in pooled pair events.
4. Relative B2 benefit was strongly source-dependent: largest against
   trRosettaRNA2 and smallest against RNAfold, with a corresponding
   correction-versus-preservation trade-off.
5. More evidence generally increased matched B2 utility, while correction per
   evidence item declined, showing diminishing efficiency.

## Limitations

- Evidence is clean, sparse, symbolic, and GT-derived; no noisy- or
  real-evidence conclusion is supported.
- Pair-channel primary results exclude 87 crossing and 20 minimum-loop
  manifests solely for frozen solver capability. No ineligible performance is
  imputed.
- Pair coverage changes at 20% and 50%. Absolute cross-density comparisons are
  composition-sensitive; within-density matched B2-minus-B0/B1 comparisons are
  the primary density evidence.
- The 0% B2 result is an unconstrained RNAfold baseline and can outperform
  non-RNAfold source predictions without using evidence.
- R2 does not compare a learned reconciler. Gate A cannot be marked PASS or
  FAIL until a future R4 result is compared against this frozen B2 baseline.

## Historical blocker record retained

Under v1.0.1, the fixed command attempted all 7,173 then-eligible rows. It
produced 7,153 valid PASS rows and 20 fail-closed constraint-satisfaction
failures. Each failure contained a forced `j-i=3` pair that ViennaRNA omitted
under its minimum loop size of three enclosed nucleotides. This was correctly
reported as `R2_EXECUTION_PARTIAL_BLOCKED_MINIMUM_LOOP_CONSTRAINT`; no partial
scientific metric was computed. The v1.0.2 coordinate-only amendment then
resolved representability prospectively, without rewriting that history or
changing solver settings.

## Reproducible artifacts

- eligibility and coverage:
  `results/global_constrained_refolding_r2/integrity/r2_manifest_eligibility_v1_0_2.csv`
  and `r2_eligibility_summary_v1_0_2.json`;
- matched universe: `r2_matched_b0_view_v1_0_2.csv`,
  `r2_matched_b1_view_v1_0_2.csv`, and
  `r2_matched_universe_summary_v1_0_2.json`;
- reuse/completion gate: `execution_completion_v1_0_2.json`;
- structures: `results/global_constrained_refolding_r2/parsed/b2_structures_v1_0_2.csv`;
- per-realization metrics and edit/scope decompositions:
  `results/global_constrained_refolding_r2/metrics/`;
- formal aggregate tables: `results/global_constrained_refolding_r2/summaries/`;
- formal integrity and output hashes:
  `results/global_constrained_refolding_r2/integrity/formal_summary_integrity_v1_0_2.json`.

The original repeated stdout/stderr provenance remains locally retained in
the Git-ignored `raw/execution_records.jsonl`; versioned parsed records carry
the row-level hashes and validation state.
