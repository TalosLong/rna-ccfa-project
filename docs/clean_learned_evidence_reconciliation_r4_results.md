# Clean Learned Evidence Reconciliation R4 Results

## Status

**`R4_COMPLETE`**

**`R4_GATE_B_FAIL`**

**`GATE_A_PASS_POSTHOC_NONDOMINATED`**

Execution date: 2026-09-07

Governing frozen protocol:
`docs/clean_learned_evidence_reconciliation_r4_protocol.md` (SHA256
`81ce3923c19a99094418dc5fb568c7081192ac84c542b33dbb4bafa888c739e4`).

This result uses only Legacy121 and the frozen clean Track E universe. It does
not access the external77 independent matrix, noisy evidence, or real
SHAPE/DMS/PARS data. It does not execute historical
`evidence_guidance_stage_e2_v1`, retune P1/P3/P4, or perform rescue tuning.

## EMPIRICAL RESULT

### Execution and integrity

The frozen grouped split hash was
`810b04a3963acc7637b60fcb5c2246c765fac334f809a5af9f8f050824ed974f`.
Feature construction retained 121 RNAs, 363 source records, 3,523 eligible
positive-pair manifests, 3,630 eligible unpaired manifests, and all 310,838
original-pair realization events. The model tensor contained exactly the
source-agnostic 80 candidate features, 17- or 8-dimensional evidence items,
and four evidence descriptors specified by the frozen protocol.

All 100 expected training runs completed:

```text
2 conditions x 2 channels x 5 held-out folds x 5 seeds = 100
```

Every run used train-only preprocessing and class weighting. Checkpoint
selection, monotone Platt calibration, and threshold selection used validation
only. All 100 checkpoints, calibrators, and thresholds were sealed before
held-out access; all 100 repeated held-out inferences were deterministic.
The 50 ERN/B4 pairs passed the exact matching audit. A second complete summary
build reproduced 543 deterministic output hashes exactly.

### Primary combined Track E

Values are held-out five-seed mean, population SD, and seed range. The primary
combined track concatenates the separately trained positive-pair and unpaired
held-out rows; it is not a third model or an ensemble.

| Metric | ERN mean ± population SD [min, max] | B4 evidence-masked mean ± population SD [min, max] |
| --- | --- | --- |
| Event AUPRC | 0.811406 ± 0.007119 [0.800810, 0.818027] | 0.771726 ± 0.006865 [0.760806, 0.781152] |
| Event AUROC | 0.930254 ± 0.000929 [0.929089, 0.931479] | 0.915677 ± 0.001153 [0.913977, 0.917558] |
| Event Brier | 0.061184 ± 0.001357 [0.059677, 0.063361] | 0.067810 ± 0.001194 [0.066213, 0.069319] |
| Event ECE | 0.018252 ± 0.001943 [0.015626, 0.020292] | 0.024127 ± 0.002841 [0.020467, 0.028048] |
| RNA-balanced AUPRC | 0.897194 ± 0.002826 [0.892363, 0.900902] | 0.884302 ± 0.001686 [0.881963, 0.886408] |
| Event TP preservation | 0.989682 ± 0.000717 [0.988854, 0.990803] | 0.991886 ± 0.001553 [0.989115, 0.993458] |
| RNA-balanced TP preservation | 0.991936 ± 0.001450 [0.989770, 0.993668] | 0.993570 ± 0.001844 [0.990686, 0.996074] |
| Event FP removal | 0.475531 ± 0.016809 [0.452415, 0.499233] | 0.386622 ± 0.016255 [0.358439, 0.403644] |
| RNA-balanced FP removal | 0.660806 ± 0.006670 [0.652221, 0.669945] | 0.615236 ± 0.016370 [0.593888, 0.633327] |
| Event modification precision | 0.898838 ± 0.005151 [0.893523, 0.905539] | 0.902350 ± 0.014159 [0.875723, 0.913469] |
| RNA-balanced modification precision | 0.944218 ± 0.007319 [0.935986, 0.957304] | 0.947388 ± 0.004871 [0.942047, 0.956335] |
| Event delta F1 | 0.030235 ± 0.001125 [0.029009, 0.031656] | 0.024509 ± 0.000884 [0.023148, 0.025539] |
| RNA-balanced delta F1 | 0.027922 ± 0.000530 [0.027174, 0.028587] | 0.024784 ± 0.000791 [0.024076, 0.025791] |

ERN removed a mean 23,878.8 FP events and lost a mean 2,689.0 TP events per
seed. Resulting event precision, recall, and F1 were 0.907364, 0.875807, and
0.891304; coverage was 0.085472. Complete per-seed counts and all
RNA-balanced precision/recall/F1 values are in `summaries/per_seed_summary.csv`
and `summaries/utility_summary.csv` under the R4 result directory.

### Channel-specific results

| Condition / channel | Event TP preservation | RNA TP preservation | Event FP removal | RNA FP removal | Event modification precision | Event delta F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ERN positive-pair | 0.990248 | 0.990204 | 0.487436 | 0.657888 | 0.901059 | 0.030089 |
| ERN unpaired | 0.989130 | 0.993232 | 0.465121 | 0.664779 | 0.897001 | 0.030358 |
| B4 positive-pair | 0.992380 | 0.993514 | 0.399240 | 0.626081 | 0.905578 | 0.024628 |
| B4 unpaired | 0.991403 | 0.993573 | 0.375588 | 0.604421 | 0.899350 | 0.024385 |

The unpaired ERN family was below the event 0.99 preservation level. The
positive-pair family met both mean preservation levels, but the frozen primary
endpoint remains the complete combined Track E; selecting the better channel
after held-out evaluation is prohibited.

### Source-wise combined results

ERN RNA-balanced FP removal exceeded P3 in all three sources.

| Source | ERN event TP preservation | ERN RNA TP preservation | ERN RNA FP removal | Frozen P3 RNA FP removal | ERN − P3 |
| --- | ---: | ---: | ---: | ---: | ---: |
| RNAfold | 0.989035 | 0.992252 | 0.217430 | 0.013109 | +0.204321 |
| PETfold | 0.990178 | 0.993181 | 0.282453 | 0.099320 | +0.183132 |
| trRosettaRNA2 | 0.989838 | 0.993913 | 0.780942 | 0.630129 | +0.150813 |

Thus the frozen source-consistency condition passed: improvement was positive
in 3/3 sources, including both RNAfold and PETfold. Source-specific thresholds
were not used.

### ERN versus matched B4

Across paired seeds, usable evidence changed the primary combined metrics by:

- event AUPRC `+0.039680` and RNA-balanced AUPRC `+0.012891`;
- event AUROC `+0.014577`;
- Brier `-0.006626` and ECE `-0.005874`;
- event FP removal `+0.088910` and RNA-balanced FP removal `+0.045570`;
- event delta F1 `+0.005726` and RNA-balanced delta F1 `+0.003138`;
- event TP preservation `-0.002203` and RNA-balanced TP preservation
  `-0.001634`;
- event modification precision `-0.003512` and RNA-balanced modification
  precision `-0.003171`.

B4 itself had both preservation means above 0.99 and exceeded the P3 FP-removal
bars. Because B4 has no usable evidence, this establishes that much of the
overall improvement over P3 is available from the newly trained candidate-
context model. The paired differences nevertheless show additional evidence-
attributable discrimination and FP removal, accompanied by additional TP loss.

### Scope and evidence efficiency

At ERN's locked policies, `LOCAL_CONFLICT` edits remained perfectly precise:
a mean 4,862.4 of 5,978 opportunities were deleted, all FP, with no lost TP.
Most additional utility and all material safety loss occurred in
`NON_EVIDENCED`: a mean 19,016.4 FP were removed and 2,687.8 TP were lost,
giving scope modification precision 0.876197 and TP preservation 0.988801.
`DIRECT` contained 20,610 correct-pair opportunities; ERN deleted a mean 1.2
of them and removed no FP.

Across 46,770 delivered evidence-item instances, ERN removed 0.510558 FP per
evidence item versus 0.415099 for B4. Event delta F1 per evidence item was
`6.464713e-7` for ERN and `5.240371e-7` for B4. These ratios describe efficiency
within the repeated Track E realization universe; evidence/model seeds are not
biological replicates.

### Frozen comparators

Matched B0 is the unchanged original predictor: event/RNA F1 was
0.861068/0.878635 and no pairs were edited. B1 local hard evidence had
event/RNA F1 0.872422/0.889352, TP preservation 1.0/1.0, FP removal
0.119048/0.142946, and modification precision 1.0/1.0. ERN's resulting
event/RNA F1 was 0.891304/0.906557. Thus ERN improved F1 and FP removal over
B0/B1 but did not retain B1's perfect preservation or edit precision.

ERN's RNA-balanced FP removal 0.660806 exceeded P3's 0.489748 and E1's
0.142946. Its event FP removal 0.475531 exceeded P3's 0.347816 and E1's
0.119048. This came with preservation below P3 (event/RNA 0.996771/0.997588)
and below E1 (1.0/1.0). Therefore ERN exceeds these comparators on removal,
not on the full frozen safety–utility criterion.

B2 is a `FULL_REFOLD_REFERENCE`, not an action-matched deletion-only method.
It removed more FP than ERN (event/RNA 0.645883/0.775728 versus
0.475531/0.660806), whereas ERN preserved more original TP
(0.989682/0.991936 versus 0.981767/0.975358) and had higher modification
precision (0.898838/0.944218 versus 0.736240/0.824449). ERN made no additions;
B2 lost 4,752 original TP, removed 32,433 original FP, added 11,042 new TP,
and added 10,823 new FP. Delta F1 alone is not used to rank these different
operating spaces.

## INTERPRETATION

Usable clean evidence provides real incremental pair-reliability signal over
the exactly matched evidence-masked control: discrimination, calibration,
FP removal, and delta F1 all improved consistently in the five-seed summary.
This is not equivalent to a safe selective-correction result. At the locked
validation-selected policies, the extra correction reached into
`NON_EVIDENCED` pairs and reduced event-pooled preservation below the frozen
0.99 requirement.

The result also separates two effects. B4's strong performance shows that a
simple learned model of source-agnostic predictor context and frozen P2/P4
signals already improves substantially over P3. Evidence adds further signal,
especially the perfectly precise local-conflict deletions, but the learned
non-evidenced propagation is not conservative enough for Gate B. The failure
is therefore not evidence absence; it is failure to convert the available
signal into the prospectively required correction–preservation point.

B2 does not dominate ERN on the correction–preservation plane: B2 removes more
FP, while ERN preserves more TP and makes materially more precise edits without
adding pairs. This supports the bounded Gate A conclusion that retaining the
original predictor offers a non-dominated post-hoc operating region. It does
not establish ERN as globally superior to constrained refolding, and it does
not override Gate B.

## GATE DECISION

### Gate B

Gate B uses held-out five-seed means on the primary combined Track E.

| Frozen condition | Observed | Result |
| --- | ---: | --- |
| Event TP preservation `>= 0.99` | 0.989682 | **FAIL** |
| RNA-balanced TP preservation `>= 0.99` | 0.991936 | PASS |
| RNA-balanced FP removal `> 0.489748` | 0.660806 | PASS |
| Event FP removal `> 0.347816` | 0.475531 | PASS |
| Positive improvement in at least 2/3 sources, including RNAfold or PETfold | 3/3; includes both | PASS |

The conjunctive decision is **`R4_GATE_B_FAIL`**. The margin below the event
preservation requirement is approximately 0.000318. Strict inequality and
mean aggregation are applied exactly as frozen. No threshold rescue, seed
selection, channel selection, feature change, retraining, or larger model is
authorized by this failure.

### Gate A

The formal bounded decision is **`GATE_A_PASS_POSTHOC_NONDOMINATED`**. Matched
B2 does not dominate the relevant preservation/removal trade-off: it provides
greater FP removal but lower TP preservation and lower modification precision,
with a different full-refold edit space. This Gate A PASS means only that the
post-hoc operating region is scientifically distinct and non-dominated. It is
not a Gate B PASS or an authorization to promote ERN.

### Next-stage authorization

R5 is **not authorized**. Gate B failed, and the frozen protocol explicitly
forbids architecture escalation or post-hoc rescue. The project state is
`R4_COMPLETE / R4_GATE_B_FAIL / R5_NOT_AUTHORIZED`. Any future scientific
execution would require a new, prospectively justified decision rather than
automatic continuation.

## UNSUPPORTED CLAIMS

These results do not support claims that:

- ERN satisfies the frozen 0.99 preservation requirement;
- sparse evidence yields a safe learned correction policy under R4;
- ERN is uniformly superior to P3, E1, B4, or B2;
- the result is predictor-agnostic or transfers to unseen predictors;
- performance generalizes to external77 or any independent dataset;
- the method is robust to noisy evidence;
- the method works with real SHAPE, DMS, PARS, or other experimental evidence;
- a larger architecture would rescue the failed gate;
- any result justifies proceeding automatically to R5.

## Canonical artifacts

Machine-readable artifacts are under
`results/clean_learned_evidence_reconciliation_r4/`, including:

- `features/feature_contract.json` and the candidate/item Parquet files;
- `runs/` checkpoint provenance, validation scores, calibrators, locked
  thresholds, and held-out evaluation records;
- `calibration/`, `thresholds/`, `pair_scores/`, `risk_curves/`, and
  `evaluation/` canonical views;
- `summaries/reliability_summary.csv`, `utility_summary.csv`,
  `scope_summary.csv`, `evidence_efficiency_summary.csv`,
  `source_wise_summary.csv`, `ern_vs_b4_summary.csv`, `gate_b.json`, and
  `gate_a_comparison.json`;
- `integrity/` preflight, split, feature firewall, ERN/B4 pairing, threshold
  lock, edit accounting, path access, input/output hash, and reproducibility
  audits.
