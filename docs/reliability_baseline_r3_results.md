# R3 Pair-Reliability Baseline Suite Results

Status: **`R3_RELIABILITY_BASELINE_SUITE_COMPLETE`**

Next state: **`READY_FOR_R3_INTERPRETATION_AND_R4_PROTOCOL_DECISION`**

Date: 2026-09-03

## Scope and interpretation contract

R3 evaluated frozen observable signals for classifying original predicted RNA
pairs as DELETE/FP-positive (`y=1`) or KEEP/TP (`y=0`). It did not train or
retune a model, add pairs, access external77, begin R4, use noisy or real
evidence, invoke a pseudoknot branch, or perform 2D-to-3D analysis.

The statements below use three non-interchangeable labels:

- **EMPIRICAL RESULT**: directly reproduced from the versioned R3 artifacts;
- **INTERPRETATION**: a bounded reading of those results;
- **FUTURE R4 REQUIREMENT**: a comparator or safety requirement for a future
  prospectively frozen R4, not a prediction that R4 will pass.

Gate A remains **`GATE_A_DEFERRED_R4_REQUIRED`**.

## Prospective ECE amendment

The original R3 protocol was frozen on 2026-09-02. Before any Legacy121 R3
performance number was produced, the missing calibration-bin details were
frozen in `docs/reliability_baseline_r3_calibration_amendment.md` on
2026-09-03. ECE uses ten equal-width bins `[0,.1),...,[.9,1]`, with all ten
bins retained, empty bins contributing zero and reporting NA statistics.

Event-pooled ECE bins all evaluation events directly. RNA-balanced ECE first
computes the same fixed-bin ECE within each RNA and then averages defined RNA
values equally. Only P0, P1, and P4 receive Brier/ECE outputs. P1 is
`RAW_UNCALIBRATED`; P4 uses DELETE risk `1-BPP` and remains a thermodynamic
probability-derived relationship rather than an empirical correctness
probability.

## Frozen universes and integrity

### EMPIRICAL RESULT

Track P contained 121 RNAs, 363 source-prediction records, and 5,290 original
predicted pairs:

| Source | Original pairs | KEEP/TP | DELETE/FP | FP prevalence |
| --- | ---: | ---: | ---: | ---: |
| RNAfold | 1,693 | 1,473 | 220 | 0.129947 |
| PETfold | 1,704 | 1,463 | 241 | 0.141432 |
| trRosettaRNA2 | 1,893 | 1,461 | 432 | 0.228209 |
| Pooled | 5,290 | 4,397 | 893 | 0.168809 |

Track E used exactly 3,523 positive-pair and 3,630 unpaired R2 v1.0.2
eligible manifests. Across three sources this gave 21,459 matched
manifest-source contexts and 310,838 original pair-realization events per
baseline. All B0/B1/B2, E1 scope, B2 structure, label, fold, and manifest joins
were complete. None of the 107 crossing/minimum-loop capability exclusions
entered Track E.

RNAfold 2.4.17 generated one complete BPP upper triangle per RNA: 156,989
records across 121 matrices. Every matrix contained exactly `n(n-1)/2`
unique finite probabilities; three RNA matrices and the frozen toy were
deterministically rerun. The same matrix was joined to all three source
predictions.

## Track P discrimination and risk control

### EMPIRICAL RESULT

The table reports event-pooled and RNA-balanced discrimination. P1 and P3 are
means across five separately evaluated historical seeds; seed rows were not
pooled as biological observations. The operating-point columns report the
held-out policies obtained from validation-only fold selection for P1/P2/P4
or the immutable fixed P3 policy.

| Baseline | AUPRC event / RNA | AUROC event / RNA | TP preservation event / RNA | FP removal event / RNA | Modification precision event / RNA | Coverage event / RNA | Delta F1 event / RNA | Safety status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| P1 historical v1 | 0.696542 / 0.849095 | 0.863435 / 0.911577 | 0.985445 / 0.991130 | 0.407391 / 0.576320 | 0.851042 / 0.912766 | 0.080870 / 0.071785 | +0.023923 / +0.021750 | Ineligible: event TP <0.99 |
| P2 exact agreement | 0.719970 / 0.860112 | 0.918803 / 0.921991 | 1.000000 / 1.000000 | 0 / 0 | NA / NA | 0 / 0 | 0 / 0 | Eligible only as delete-none; no selective utility |
| P3 `V3_VETO2_FIXED` | 0.442709 / 0.584113 | 0.672293 / 0.743608 | **0.996771 / 0.997588** | **0.347816 / 0.489748** | **0.956346 / 0.965504** | 0.061399 / 0.055930 | +0.024860 / +0.020751 | Eligible |
| P4 RNAfold BPP risk | **0.777283 / 0.915326** | 0.913608 / **0.951250** | 0.993632 / 0.986219 | 0.434490 / 0.665600 | 0.932692 / 0.946096 | 0.078639 / 0.079714 | +0.030151 / +0.027688 | Ineligible: RNA-balanced TP <0.99 |

P0 used only training-partition prevalence. Pooled training scores by rotation
were 0.185395, 0.137829, 0.143537, 0.186975, and 0.185139; corresponding
held-out prevalences were 0.137708, 0.143025, 0.251969, 0.124869, and
0.150249. Within every rotation/stratum all scores tied, so AUPRC equalled the
held-out prevalence and AUROC was 0.5. Fold-specific constants were not pooled
into a spurious cross-fold ranking.

P1 seed-wise event-pooled AUPRC ranged from 0.688852 to 0.704288 and AUROC
from 0.860954 to 0.865922. Although every threshold was selected only on a
validation fold that satisfied both preservation constraints, all five
held-out seed summaries fell below 0.99 event-pooled TP preservation
(0.982261--0.988629). No held-out rescue threshold was chosen.

P2's three atomic score groups could not delete a nonzero group while meeting
the frozen validation safety rule, so all five rotations selected delete-none.
Its discrimination was strong, but its coarse ordinal resolution supplied no
usable high-preservation deletion policy.

P3 remained the immutable historical binary decision. At its R3 seed-summary
fixed point, DELETE precision equalled event-pooled modification precision
(0.956346), DELETE recall/FP removal was 0.347816, coverage was 0.061399, and
resulting event-pooled F1 was 0.877157. The historical
`V3_DEVELOPMENT_GATE_FAIL` is unchanged; R3 neither recalibrated nor retuned
P3.

P4 had the strongest Track P discrimination and the lowest descriptive Brier
and fixed-bin ECE, but its held-out fold policies failed the RNA-balanced
safety constraint. The failure was concentrated in source behavior rather
than pooled event preservation.

### INTERPRETATION

Prediction-only signals clearly contain pair-error information, but the
ability to rank errors did not automatically yield safe source-general
deletion. P2 was too coarse at the required safety level; P1 missed the held-
out event safety constraint; and P4 missed the held-out RNA-balanced safety
constraint. P3 supplied the strongest valid Track P utility point, but its
benefit was strongly source-dependent.

## Track E discrimination and fixed points

### EMPIRICAL RESULT

| Baseline | AUPRC event / RNA | AUROC event / RNA | TP preservation event / RNA | FP removal event / RNA | Modification precision event / RNA | Coverage event / RNA | Delta F1 event / RNA | Safety status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| E1 local conflict | 0.261363 / 0.286350 | 0.559524 / 0.571473 | **1.000000 / 1.000000** | **0.119048 / 0.142946** | **1.000000 / 1.000000** | 0.019232 / 0.018623 | +0.008588 / +0.007486 | Eligible |
| E2 B2 disagreement | **0.620550 / 0.778937** | **0.813825 / 0.874713** | 0.981767 / 0.975358 | 0.645883 / 0.775728 | 0.872207 / 0.903628 | 0.119628 / 0.116820 | +0.039627 / +0.030007 | Ineligible: both TP summaries <0.99 |

E1 deleted 5,978 FP pair-realizations and zero TP pair-realizations. Its
positive-pair channel fixed point removed 0.057930 of FP event-wise with
0.008920 coverage; its unpaired channel removed 0.172490 with 0.029118
coverage. Both had modification precision and TP preservation of 1.0 under
the frozen clean evidence semantics.

E2 exactly reproduced B2's original-pair disagreement components: event-
pooled TP preservation 0.9817667666 and FP removal 0.6458827044, and RNA-
balanced TP preservation 0.9753577801 and FP removal 0.7757276380. It was not
altered to force the 0.99 safety point. Its deletion-only modification
precision excludes B2 additions; the separate R2 full-refold reference
retains new-TP/new-FP accounting.

### INTERPRETATION

E1 is a perfect-precision but low-coverage clean-evidence rule. Its value is
limited to frozen direct local conflicts and supplies no NON_EVIDENCED
inference. E2 contains much stronger error-discrimination and correction
information, but achieves it at the same non-negligible original-TP loss seen
in R2. E2 therefore sets a high unconstrained evidence-conditioned bar, while
E1 is the valid evidence-conditioned bar at the frozen 0.99 safety point.

## Calibration results

### EMPIRICAL RESULT

| Probability-like score | Brier event / RNA | ECE event / RNA | Semantics |
| --- | ---: | ---: | --- |
| P0 pooled training prevalence | 0.142269 / 0.127523 | 0.001902 / 0.121479 | Constant cross-validated reference |
| P0 source-wise training prevalence | 0.140619 / 0.124927 | 0.021831 / 0.136814 | Source-stratified constant reference |
| P1 historical `p_delete`, mean across seeds | 0.125220 / 0.105181 | 0.124004 / 0.167331 | `RAW_UNCALIBRATED` |
| P4 `1-BPP` | **0.077089 / 0.063935** | 0.040037 / **0.095153** | Thermodynamic-risk/empirical-FP relationship |

P4's numbers compare a thermodynamic ensemble marginal-derived risk with
empirical FP frequency. They do not establish that RNAfold BPP is, or is not,
an empirically calibrated correctness probability because the probability
semantics differ.

## Source-wise results

### EMPIRICAL RESULT — discrimination

Event-pooled AUPRC/AUROC values are:

| Baseline | RNAfold | PETfold | trRosettaRNA2 |
| --- | ---: | ---: | ---: |
| P1 | 0.334144 / 0.771696 | 0.424800 / 0.798598 | **0.898078 / 0.941054** |
| P2 | 0.582389 / 0.891184 | 0.640026 / 0.901857 | **0.783504 / 0.933409** |
| P3 | 0.150433 / 0.517597 | 0.208440 / 0.545243 | **0.714053 / 0.821721** |
| P4 | 0.509427 / 0.858287 | 0.617788 / 0.875931 | **0.949512 / 0.973689** |
| E1 | 0.228856 / 0.560210 | 0.239926 / 0.560771 | **0.311061 / 0.558493** |
| E2 | 0.366632 / 0.658065 | 0.457764 / 0.708171 | **0.820211 / 0.944687** |

### EMPIRICAL RESULT — RNA-balanced operating utility

Each tuple is `TP preservation / FP removal / modification precision /
coverage / delta F1` at the same pooled policy; NA occurs at delete-none.

| Baseline | RNAfold | PETfold | trRosettaRNA2 |
| --- | --- | --- | --- |
| P1 | 0.992813 / 0.028091 / 0.285325 / 0.008275 / -0.002738 | 0.991952 / 0.133524 / 0.611352 / 0.015021 / -0.000232 | 0.989313 / 0.747924 / 0.944482 / 0.161959 / +0.057611 |
| P2 | 1 / 0 / NA / 0 / 0 | 1 / 0 / NA / 0 / 0 | 1 / 0 / NA / 0 / 0 |
| P3 | 0.998616 / 0.013109 / 0.582262 / 0.002300 / -0.000174 | 0.998810 / 0.099320 / 0.877488 / 0.007488 / +0.002512 | 0.996189 / 0.630129 / 0.973718 / 0.131508 / +0.051374 |
| P4 | 1 / 0 / NA / 0 / 0 | 1 / 0.120833 / 1 / 0.007288 / +0.003713 | 0.979314 / 0.866964 / 0.946096 / 0.197350 / +0.066708 |
| E1 | 1 / 0.139992 / 1 / 0.012462 / +0.004308 | 1 / 0.137632 / 1 / 0.014034 / +0.004974 | 1 / 0.142634 / 1 / 0.025541 / +0.011024 |
| E2 | 0.990693 / 0.229784 / 0.838943 / 0.037624 / +0.003778 | 0.989939 / 0.417032 / 0.869655 / 0.054066 / +0.010879 | 0.964466 / 0.923041 / 0.882216 / 0.222083 / +0.060760 |

### INTERPRETATION

P1, P3, P4, and E2 were all materially stronger on trRosettaRNA2 than on the
other sources. P3's RNA-balanced delta F1 was slightly negative for RNAfold
and its FP removal ranged from 0.013109 for RNAfold to 0.630129 for
trRosettaRNA2; the strongest Track P record is therefore flagged
`SOURCE_DEPENDENT_COMPARATOR`. P4 did not show a special ranking advantage on
RNAfold source pairs; its strongest discrimination occurred on
trRosettaRNA2. E1 was comparatively stable in FP-removal fraction across
sources, although its coverage was larger for trRosettaRNA2.

## Strongest comparator freeze

### EMPIRICAL RESULT

The prospectively frozen hierarchy selected:

```text
STRONGEST_R3_PREDICTION_ONLY_BASELINE = R3-P3 V3_VETO2_FIXED
STRONGEST_R3_EVIDENCE_CONDITIONED_BASELINE = R3-E1 LOCAL_CONFLICT
```

P3's primary RNA-balanced point removed 0.489748 of FP at TP preservation
0.997588, modification precision 0.965504, coverage 0.055930, and delta F1
+0.020751. Its event-pooled companion removed 0.347816 of FP at TP
preservation 0.996771, modification precision 0.956346, coverage 0.061399,
and delta F1 +0.024860.

E1's primary RNA-balanced point removed 0.142946 of FP at TP preservation
1.0, modification precision 1.0, coverage 0.018623, and delta F1 +0.007486.
Its event-pooled companion removed 0.119048 of FP at TP preservation 1.0,
modification precision 1.0, coverage 0.019232, and delta F1 +0.008588.

P3 and P1 retain historical learned-score provenance. “No-new-training
comparator” is the correct operational description; neither is reclassified
as an intrinsically non-learned method.

### FUTURE R4 REQUIREMENT

A future R4 must compare with both frozen records. To exceed both at the
primary safety point, its held-out policy must maintain both event-pooled and
RNA-balanced TP preservation at least 0.99 and exceed P3's RNA-balanced FP
removal of **0.489748**; the event-pooled companion bar is **0.347816**. It
must also report comparison with the direct evidence-conditioned E1 bar
(RNA/event FP removal 0.142946/0.119048 at preservation 1.0) and must not rely
on only one source. These are R4 requirements, not evidence that R4 will meet
them.

## R2 full-refold reference

R2 B2 remains a separate **`FULL_REFOLD_REFERENCE`**:

| Quantity | Macro | Micro |
| --- | ---: | ---: |
| TP preservation | 0.975358 | 0.981767 |
| FP removal | 0.775728 | 0.645883 |

B2 can add and replace pairs and therefore changes both original-pair and
absent-pair states. R3 curves only delete original predicted pairs. E2 uses
B2 disagreement as a binary original-pair signal, but neither E2 nor any R3
selective point is the same operation as global refolding. Aggregate B2 F1
and R3 deletion-only delta F1 are not interchangeable endpoints.

## Main empirical findings

1. P4 RNAfold BPP risk supplied the strongest prediction-only discrimination
   (event/RNA AUPRC 0.777283/0.915326), but its held-out RNA-balanced TP
   preservation was 0.986219 and failed the primary safety gate.
2. P3 supplied the strongest valid Track P operating point, removing
   0.489748 RNA-balanced FP at 0.997588 preservation, but was strongly driven
   by trRosettaRNA2 and slightly decreased RNAfold RNA-balanced F1.
3. E1 local conflict was perfectly precise under clean evidence and preserved
   all original TP, but its coverage was only 0.018623 RNA-balanced and it
   removed 0.142946 of FP.
4. E2 B2 disagreement was a strong error signal and removed 0.775728
   RNA-balanced FP, but its 0.975358 preservation made the fixed point
   high-preservation-ineligible.
5. Prediction-only ranking signal was substantial but did not provide a
   source-consistent high-preservation solution: P1 and P4 failed a held-out
   safety summary, P2 selected delete-none, and P3 was source-dependent.

## Implementation findings and reproducibility

Four implementation-only issues were resolved before final reporting: use of
the correct authoritative P1 held-out score source, use of the correct
historical V3 reconstruction provenance, and removal of an invalid cross-fold
P0 ranking and its undefined mixed source-wise constant row. None changed the
frozen baseline definitions, score orientation, threshold rule, universe, or
metric definition. Details are versioned in `integrity/implementation_issue_audit.json`.

Targeted tests passed 33/33. The full suite passed 201 tests and 29 subtests.
Integrity artifacts record all input and output SHA256 hashes, complete joins,
calibration restrictions, threshold selection, leakage controls, BPP
provenance, and execution completion.

Canonical artifacts are under `results/reliability_baseline_r3/`, including:

- `pair_scores/`: compressed P0--P4 and E1/E2 rows plus compact BPP matrices;
- `risk_curves/`: validation searches, locked thresholds, test curves, and
  high-preservation points;
- `calibration/`: probability-like metrics, all fixed reliability bins, and
  semantic warnings;
- `summaries/strongest_baselines.json`: both frozen comparator records;
- `integrity/`: universe, historical-score, BPP, join, metric, threshold,
  test, leakage, hash, and completion audits.
