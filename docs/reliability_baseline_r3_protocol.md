# Pair-Reliability Baseline Suite R3 Protocol

## Status

**`FROZEN BEFORE R3 EXECUTION`**

Protocol date: 2026-09-02

This document freezes the R3 scientific and evaluation contract. It does not
report any formal R3 metric, train or retune a model, access external77, or
authorize R4.

## 1. Scientific purpose

R3 asks how much pair-error discrimination, reliability information, and
risk-control utility is already available from frozen observable signals.
It does not develop a new refinement model.

For every original predicted pair `p=(i,j)`, R3 evaluates existing signals as
comparators for the future deletion-only `KEEP / DELETE / ABSTAIN` task. Its
purpose is to freeze the strongest no-new-training reliability comparators
that a future R4 must beat.

The R3 result is scientifically valid whether the existing signals are strong
or weak. Baselines may not be adjusted to obtain a favorable narrative.

## 2. Task, labels, and primary unit

Let `S` be an immutable original source-prediction pair set and `G` the frozen
ground-truth pair set. For each `p in S`:

```text
DELETE-positive / error: p not in G
KEEP:                    p in G
```

The positive class for every discrimination metric is `DELETE`/FP.

The primary unit in Track P is one original predicted pair. In Track E it is
one original predicted pair under one frozen evidence realization. Ground-
truth pairs absent from `S` are not candidates. R3 and the future primary R4
are deletion-only and cannot act on a missing pair.

GT is used only to construct the evaluation label and outcome metrics. It is
never an input to a risk score, evidence join, threshold fit, or baseline
definition.

## 3. Two separate inference tracks

### Track P — Prediction-only reliability

Track P uses the RNA sequence and/or the three frozen source predictions as
permitted by each baseline. It receives no delivered structural evidence.

### Track E — Evidence-conditioned reliability

Track E uses the same clean delivered evidence realization as R2 and evaluates
one source pair in that evidence context. No evidence is regenerated,
resampled, weakened, or rewritten.

Track P and Track E are separate inference settings. They must have separate
score tables, summaries, strongest-baseline selections, and status fields.
They must not be pooled into one ranking. The future R4's most direct comparator
comes from Track E because R4 will also receive evidence.

## 4. Frozen Track P baselines

### R3-P0 — Training-prevalence constant baseline

For a held-out grouped rotation, the constant DELETE risk is the DELETE
prevalence estimated only from the permitted training RNAs. The pooled
baseline uses pooled training-source pairs; a source-wise reference uses that
source's pairs within the same training RNAs.

Test labels must not determine the constant. P0 explains class imbalance and
the AUPRC reference level. It supplies no meaningful ranking within a stratum
and has no invented selective-deletion operating point.

### R3-P1 — Historical v1 topology score

P1 reuses the authoritative historical v1
`POOLED_SOURCE_AGNOSTIC` raw `p_delete` score. Its features, architecture,
checkpoints, folds, seeds, preprocessing, and learned parameters are immutable.

The following are forbidden:

- retraining or fine-tuning;
- feature or architecture changes;
- hyperparameter or seed changes;
- calibration on new test labels;
- using R3 held-out labels to revise the score or historical model.

The historical `DEVELOPMENT_GATE_FAIL` remains unchanged. In R3, the raw score
is only a prediction-only pair error-risk comparator. The five frozen model
seeds are analyzed as repeated historical model runs: metrics are computed per
seed and summarized across seeds; pair rows from different seeds are never
treated as independent biological observations. No post-hoc seed ensemble is
introduced in R3 v1.

If validation scores required by the R3 high-preservation selector are not
already materialized, future R3 execution may run inference only from the
frozen historical checkpoints on the already frozen validation IDs. It must
first reproduce stored held-out scores within a frozen numerical tolerance.
It may not train, update, or recalibrate the checkpoints.

### R3-P2 — Exact cross-model agreement

For an original pair in one source prediction:

```text
support_other_count = number of the other two predictors containing
                      exactly the same canonical pair
support_other_count in {0, 1, 2}
risk_agreement = 2 - support_other_count
```

Lower exact support prospectively means higher error risk. This orientation is
frozen before R3 labels are evaluated. No alternate mapping or source-specific
remapping may be selected after results are seen. P2 is an ordinal risk
indicator, not a probability.

### R3-P3 — Historical `V3_VETO2_FIXED`

P3 reuses the immutable `V3_VETO2_FIXED` held-out decisions. Its historical
definition is preserved: an authoritative v1 BASE deletion is vetoed when
`support_other_count == 2`; the original BASE threshold is not recalibrated.

P3 is evaluated as a deterministic binary decision/protection comparator. It
must not be presented as a probability or retuned to satisfy the R3 safety
point. Report its fixed precision, recall, fraction flagged/coverage, TP
preservation, and FP removal. The historical `V3_DEVELOPMENT_GATE_FAIL`
remains unchanged.

### R3-P4 — RNAfold thermodynamic base-pair probability

P4 is feasible in the frozen environment and is therefore included in the
future R3 execution contract.

For every original pair `(i,j)` from RNAfold, PETfold, or trRosettaRNA2, obtain
the sequence-only ViennaRNA ensemble marginal:

```text
P_RNAfold(i,j)
risk_BPP(i,j) = 1 - P_RNAfold(i,j)
```

The same sequence-derived matrix is joined to all three source predictions.
P4 must not be restricted to RNAfold source pairs.

Frozen environment and interface:

```text
executable: /usr/bin/RNAfold
version:    RNAfold 2.4.17
locale:     LC_ALL=C
command:    /usr/bin/RNAfold --noPS --partfunc=1 --bppmThreshold=0 --temp=37 --dangles=2
input:      one FASTA sequence in an isolated per-RNA working directory
```

Frozen model settings are linear RNA, the ViennaRNA default parameter set,
37 C, dangles=2, no `--noLP`, no `--noGU`, no `--noClosingGU`, no `--gquad`,
no circular mode, no constraints, and standard non-pseudoknot partition-
function dynamic programming. No Python `RNA` binding, software installation,
ViennaRNA upgrade, parameter replacement, or approximate BPP implementation is
permitted.

With `--noPS`, the MFE structure PostScript is suppressed but `<id>_dp.ps` is
still generated by `--partfunc=1`. Parse only records of the exact form:

```text
i  j  sqrt(p)  ubox
```

Indices `i,j` are ViennaRNA one-based indices and convert to project zero-based
indices by subtracting one. The stored probability is the square of the third
field. `--bppmThreshold=0` is required; the parser must require exactly
`n(n-1)/2` unique upper-triangle records, including explicit zero entries, and
must reject missing, duplicate, nonfinite, out-of-range, or misindexed values.
The `lbox` MFE records are ignored.

Toy audit on `GGGAAACCC` produced 36/36 upper-triangle entries twice with
identical parsed values; one-based pair `(3,7)` mapped to project pair `(2,6)`
with `p=0.518753349792`. This establishes interface feasibility only, not
Legacy121 performance.

Frozen feasibility state:

**`R3_BPP_BASELINE_FEASIBLE_WITH_FROZEN_CLI`**

`P_RNAfold(i,j)` is a thermodynamic ensemble probability under this model. It
is not automatically `P(the empirical pair is correct)` and must not be named
a correctness-calibrated probability.

## 5. Frozen Track E baselines

### R3-E1 — Local evidence-conflict risk

E1 strictly reuses the Stage E1 delivered-evidence definitions. For an
original predicted pair, binary risk is one exactly when the pair directly
contradicts delivered evidence or belongs to the frozen local-conflict
deletion condition; otherwise risk is zero.

The pair-level join is:

- positive-pair evidence: the exact delivered pair is consistent; any other
  original pair touching either delivered endpoint is `LOCAL_CONFLICT` and
  receives risk one;
- unpaired-nucleotide evidence: any original pair touching a delivered
  unpaired position is `LOCAL_CONFLICT` and receives risk one;
- all remaining original pairs receive risk zero.

Multiple evidence items use the union of the same frozen conditions. GT may
not redefine or expand the local scope. This baseline tests whether a future
R4 does more than learn that direct evidence conflicts should be deleted.

E1 is a binary indicator, not a probability.

### R3-E2 — B2 survival/disagreement risk

For original source pair `p` and the B2 output `R` for the same RNA and clean
evidence realization:

```text
B2_survival(p)          = 1 if p in R else 0
B2_disagreement_risk(p) = 1 if p not in R else 0
```

E2 is a mandatory strong classical baseline. It asks how well the binary
decision “global constrained refolding did not retain this original pair”
detects original FP while preserving original TP. It is not a probability.

E2 uses only the R2 v1.0.2 matched eligible universe:

- positive-pair channel: 3,523 eligible manifests;
- unpaired-nucleotide channel: 3,630 eligible manifests.

The 87 crossing-ineligible and 20 minimum-loop-ineligible pair manifests are
excluded. B0, B1, B2, R3-E, and future R4 comparisons must use identical
eligible manifest IDs.

## 6. No optional combined score in R3 v1

R3 v1 freezes no combined comparator. Logistic stacking, learned combination,
post-hoc AND/OR search, and weight searches over BPP, agreement, local conflict,
or B2 disagreement are prohibited. A combination may be introduced only by a
new prospective protocol amendment made without viewing R3 held-out results.

## 7. Evaluation universes and split semantics

### Track P universe

Track P uses frozen Legacy121 only:

- 121 RNAs;
- RNAfold, PETfold, and trRosettaRNA2 source predictions;
- original predicted pairs only;
- the existing 80%-identity grouped five-fold assignments.

For rotation `k`, test fold is `k`, validation fold is `(k+1) mod 5`, and the
other three folds are training. The split is never randomized again. All
source predictions and all pairs from one RNA remain together.

### Track E universe

Track E uses only the R2 v1.0.2 matched manifest IDs. Each RNA's fold is
inherited from the same frozen Legacy121 grouped assignment. All densities,
evidence seeds, channels, source predictions, and original pairs belonging to
one RNA remain in the same train/validation/test role.

The same original pair may occur under multiple densities and evidence seeds.
Those rows are distinct inference contexts, not independent biological
samples. Evidence contexts may not cross RNA partitions.

external77 remains locked and absent from every R3 input, audit, threshold,
metric, and artifact.

## 8. Aggregation and pseudo-replication control

Every baseline has two mandatory summary families.

### A. Event-pooled / pair-realization summary

Pool the relevant original pair events. In Track E, each eligible
pair-under-evidence-realization is an inference event. This summary describes
event-level deployment behavior and retains event, manifest, pair, and RNA
denominators.

### B. RNA-balanced summary

First aggregate eligible pair events within each RNA, then give each RNA equal
weight. Undefined per-RNA quantities remain NA; report the number of RNAs for
which each metric is defined. Evidence seeds, densities, model seeds, and
source records are repeated contexts within an RNA, not biological replicates.

Any final significance test must use RNA as the biological cluster/unit. It is
forbidden to treat pair-realizations, evidence seeds, densities, source records,
or historical model seeds as independent biological observations.

## 9. Discrimination metrics

Primary discrimination endpoint:

```text
AUPRC for positive class DELETE / FP
```

The primary numerical convention is non-interpolated average precision: group
ties at each unique risk value and sum precision weighted by the increase in
recall. Do not use trapezoidal interpolation as the primary value. Report
positive prevalence alongside every AUPRC:

```text
positive_prevalence = number_of_original_FP / number_of_original_predicted_pairs
```

The prevalence value used as the P0 score comes from the permitted training
partition; the prevalence reported for a held-out evaluation summary describes
that held-out label universe and is not used for inference or thresholding.

Secondary discrimination endpoint is AUROC with tied scores receiving average
ranks. AUPRC is undefined when no positive example exists; AUROC is undefined
unless both classes exist. Undefined values remain NA.

For binary risks, also report the immutable operating point:

- DELETE precision;
- DELETE recall;
- fraction flagged / coverage;
- TP preservation;
- FP removal.

## 10. Probability and calibration restrictions

The baselines are classified prospectively as follows.

| Baseline | Score type | Permitted calibration analysis |
| --- | --- | --- |
| P0 training prevalence | Probability-like constant reference | Brier/ECE as a constant training-prevalence reference, clearly labeled |
| P1 historical v1 `p_delete` | Historical sigmoid probability-like score | Brier, ECE, reliability diagram; label `raw / uncalibrated` unless the historical protocol proves calibration |
| P2 exact support / `2-support` | Ordinal risk indicator | None; discrimination and operating points only |
| P3 `V3_VETO2_FIXED` | Binary decision | None; fixed operating point only |
| P4 `1-P_RNAfold` | Thermodynamic probability-derived risk | Supplementary Brier/ECE/reliability relationship only; never call it empirical correctness calibration |
| E1 local conflict | Binary indicator | None; fixed operating point only |
| E2 B2 disagreement | Binary indicator | None; fixed operating point only |

Ordinal and binary indicators must not be assigned arbitrary pseudo-
probabilities such as `0 -> 0.0`, `1 -> 0.5`, `2 -> 1.0` for Brier/ECE.
No empirical calibrator may be fitted after viewing R3 held-out results.

## 11. Deletion-only risk–utility framework

For a sortable risk score, begin with the immutable original structure and
delete original predicted pairs from highest risk to lowest risk. Equal-score
pairs enter together. R3 never adds a pair, reassigns a partner, or refolds the
remaining structure.

For each threshold:

```text
lost_TP       = number of deleted original TP
removed_FP    = number of deleted original FP
TP_after      = TP_before - lost_TP
FP_after      = FP_before - removed_FP
FN_after      = FN_before + lost_TP
TP_preservation = TP_after / TP_before
FP_removal      = removed_FP / FP_before
modification_precision = removed_FP / (removed_FP + lost_TP)
```

The primary curve is:

```text
x-axis: 1 - TP_preservation
y-axis: FP_removal
```

Also retain resulting structure Precision, Recall, F1, modification precision,
flagged count, and coverage. Zero denominators are NA. Binary baselines appear
as their one frozen operating point on this plane and are not modified to trace
an artificial curve.

## 12. High-preservation operating point

The primary safety point is:

```text
TP_preservation >= 0.99
```

For a continuous or ordinal score, candidate thresholds are the unique
validation risk values plus a delete-none threshold. The decision is
`DELETE iff risk >= threshold`; tied scores are never split using labels.

Threshold selection uses validation labels only. A threshold is eligible only
when both validation event-pooled TP preservation and validation RNA-balanced
TP preservation are at least 0.99. Among eligible thresholds:

1. maximize RNA-balanced FP removal;
2. if tied, maximize RNA-balanced modification precision;
3. if still tied, choose the more conservative threshold, meaning fewer
   deleted pairs;
4. if still tied, choose the numerically higher risk threshold.

The selected threshold is then locked and applied unchanged to the held-out
test fold. No test label may select, move, or rescue a threshold.

The canonical frozen output is:

```text
RNA_balanced_FP_removal_at_TP_preservation_ge_0.99
```

The event-pooled companion
`FP_removal_at_micro_TP_preservation_ge_0.99` is mandatory. Both must retain
their achieved preservation values and denominators.

P0 has no useful ranking and is not assigned an artificial threshold. P3, E1,
and E2 keep their fixed binary operating points. If a binary point has TP
preservation below 0.99 in either primary aggregation, it is not adjusted and
is ineligible for the high-preservation comparison. If it naturally satisfies
both constraints, it may enter that comparison directly.

## 13. R2 headroom reference

R2/B2 remains contextual rather than a deletion-only R3 score curve:

| R2 B2 endpoint | Macro | Micro |
| --- | ---: | ---: |
| TP preservation | 0.975358 | 0.981767 |
| FP removal | 0.775728 | 0.645883 |

Future R4 is not judged only by whether F1 exceeds 0.924648. The primary
question is how much FP can be removed under the prospectively frozen
`TP_preservation >= 0.99` risk constraint.

## 14. Source-wise analysis

Every feasible baseline must report RNAfold, PETfold, and trRosettaRNA2
separately as well as pooled. Mandatory questions are:

- whether the v1 topology score remains source-dependent;
- whether exact cross-model support is asymmetric across sources;
- whether RNAfold BPP has a natural advantage on RNAfold source pairs;
- whether B2 disagreement is driven mainly by trRosettaRNA2;
- whether the high-preservation operating point holds across sources or only
  because of one source.

The global validation threshold is not retuned separately on held-out source
test labels. Report per-source achieved TP preservation and FP removal at the
same locked threshold. Any pooled winner with materially inconsistent source
behavior receives the flag `SOURCE_DEPENDENT_COMPARATOR`; it cannot support a
source-general claim.

## 15. Strongest frozen comparator selection

Track P and Track E are selected separately after the frozen evaluation is
complete. The eligible pool contains the prespecified R3 baselines only. The
phrase “no-new-training comparator” is used operationally: P1 and P3 retain
their historical learned-score provenance and must not be mislabeled as
intrinsically non-learned methods.

For each track, a baseline first must have a valid held-out operating point
satisfying both primary `TP_preservation >= 0.99` summaries. Selection then
uses:

1. highest RNA-balanced FP removal at the high-preservation point;
2. higher RNA-balanced modification precision;
3. higher RNA-balanced AUPRC;
4. if still tied, fewer deleted pair events.

Calibration quality is supplementary and, even for probability-like scores,
cannot override risk-control utility.

Save exactly one status record for each track:

```text
STRONGEST_R3_PREDICTION_ONLY_BASELINE
STRONGEST_R3_EVIDENCE_CONDITIONED_BASELINE
```

The record must include the baseline ID, threshold or fixed-point semantics,
both aggregation summaries, all three source summaries, and any
`SOURCE_DEPENDENT_COMPARATOR` flag. Future R4 must compare against both saved
baselines; the Track E winner is its most direct evidence-conditioned bar.

## 16. Leakage controls

- Use GT only for labels and outcome metrics.
- Use no missing GT pair as a candidate or feature.
- Use no test label for prevalence, score construction, calibration, threshold
  selection, tie-breaking, or combined-rule design.
- Preserve the frozen grouped folds; never split pairs, sources, evidence
  contexts, or model seeds independently of RNA.
- Use the identical clean evidence realization and R2 v1.0.2 manifest ID for
  Track E joins.
- Do not include crossing/minimum-loop-ineligible manifests in E2.
- Do not retrain or retune v1/v3.
- Do not fit a new score combination.
- Do not access external77.
- Do not use noisy evidence, real evidence, a pseudoknot branch, or R4 data.

Each future score artifact must retain `rna_id`, source, original pair,
fold/partition, track, baseline, label provenance, and—where applicable—channel,
density, evidence seed, manifest ID, historical seed, score type, and threshold
provenance. Integrity checks must prove one GT-derived field did not enter
inference features.

## 17. Prospective interpretation rules

- If E2 B2 disagreement is strong, the future R4 bar is high.
- If P4 BPP is strong, a future learned method must demonstrate value beyond
  classical thermodynamic evidence.
- If prediction-only baselines are weak, that supports the prior finding that
  prediction-only correction is insufficient under this development setting.
- If E1 local conflict is precise but low-coverage, future R4 value must come
  primarily from safe `NON_EVIDENCED` inference.

These are interpretation branches, not targets. No baseline may be tuned to
produce a “promising” conclusion.

## 18. Required artifacts

Future R3 execution must write separate raw, normalized, and aggregate
artifacts under:

```text
results/reliability_baseline_r3/
    integrity/
    pair_scores/
    risk_curves/
    calibration/
    summaries/
```

At minimum retain:

- input file hashes and exact manifest/fold inventories;
- the environment and BPP CLI audit;
- one normalized pair-score/decision table per track;
- event-pooled and RNA-balanced discrimination summaries;
- fixed binary operating points;
- validation threshold-search tables and locked thresholds;
- deletion-only risk–utility curves;
- probability-like calibration diagnostics with score-type warnings;
- pooled and source-wise high-preservation summaries;
- the two strongest-baseline selection records;
- leakage, accounting, duplicate-key, and completion audits;
- an explicit record that no training, external77 access, R4, noise, real
  evidence, pseudoknot branch, or 2D-to-3D work occurred.

## 19. Completion criteria

R3 is complete only when:

1. Track P and Track E are evaluated separately on their exact frozen
   universes;
2. every mandatory baseline is present, or P4 alone carries an explicit
   frozen-environment unavailable status after a failed interface audit;
3. every score is classified as probability-like, ordinal, or binary and the
   calibration restrictions are enforced;
4. event-pooled and RNA-balanced summaries, prevalence, AUPRC, AUROC, fixed
   binary points, and source-wise results are complete;
5. all sortable scores have validation-only high-preservation selection and
   held-out risk–utility artifacts;
6. `RNA_balanced_FP_removal_at_TP_preservation_ge_0.99` and its event-pooled
   companion are saved with achieved preservation;
7. the two strongest comparator records are frozen by the prespecified rule;
8. all integrity and leakage checks pass with RNA as the biological unit;
9. no formal result was produced from external77 and no learned model was
   trained or retuned.

Until those criteria are met, the state is `R3_PROTOCOL_FROZEN` and
`READY_FOR_R3_EXECUTION`, not `R3_COMPLETE`.
