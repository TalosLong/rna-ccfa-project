# Selective Refiner Experimental Protocol v1

Status: **FROZEN BEFORE MODEL IMPLEMENTATION OR TRAINING**

This document preregisters the first learned selective-refinement experiment.
It does not report learned-model results. The protocol preserves the frozen
canonical pair representation, exact-pair evaluator, Phase 1 taxonomy, and
Phase 2 rule baseline.

## Research question and scope

The first experiment asks whether inference-time observable sequence and
predicted-topology features can identify a useful subset of predicted pairs to
delete. It is a precision-oriented cleanup task, not complete RNA secondary
structure prediction.

The learned model must answer:

> Should this original predicted pair be kept or deleted?

Version 1 permits pair deletion only. It does not generate pairs, reassign a
partner, reconstruct a structure globally, use pseudoknot-specific logic, or
recover false-negative pairs. Pseudoknot-aware refinement remains a separate
side track.

## Prediction-unit audit

| Candidate unit | Training label | Observable deployable context | Supported edit | Main limitation / leakage risk |
| --- | --- | --- | --- | --- |
| Original predicted pair | `KEEP` for exact TP; `DELETE` for exact FP | Endpoint sequence, pair identity, separation, predicted stem/singleton position and local predicted topology | Pair deletion | GT pair membership must be confined to label construction; missing or alternative GT partners must not enter features |
| Original predicted strict stem | Stem-level correctness or edit state derived from constituent pair labels or frozen GT-stem matching | Predicted stem length, boundaries, sequence and topology | Whole-stem deletion or coarse stem edit | A stem may contain both TP and FP pairs, so one label can force destructive edits; using Phase 1 GT-stem states as inputs would leak evaluation information |
| Original predicted boundary pair | Exact TP/FP label restricted to predicted stem boundaries | Pair-level features plus outer/inner boundary context | Boundary deletion | Omits singleton and interior errors; the R3 pilot has severe source-dependent coverage, so it is not a complete primary unit |

### Frozen primary unit

The primary unit is **one pair in the immutable original predicted canonical
pair set**. Every pair is represented exactly once. All pairs from the same
RNA and source prediction remain in the same data split.

This unit was chosen because it has an exact non-ambiguous label, directly
supports selective deletion, covers every deployable prediction, and permits
the shared evaluator to account for each edit. Strict-stem and boundary status
remain observable features and analysis slices; neither becomes the label.

The unit does not support pair addition or partner reassignment. Those tasks
need candidate-generation and constrained-decoding protocols and are deferred.

## First learned task and labels

For an original predicted pair `p` and ground-truth pair set `G`:

- `KEEP` iff `p in G` (the pair is an exact TP);
- `DELETE` iff `p not in G` (the pair is an exact FP).

GT is used only to construct training labels and to perform evaluation. It is
not an inference input. The labels are generated from the frozen normalized
records using exact canonical-pair equality and the existing shared evaluator.

A wrong-partner FP receives the ordinary `DELETE` label. Its linked missing GT
pair, conflicting endpoint, GT partner identity, and `wrong_partner` annotation
must not be used as features. False-negative/missing pairs are not examples in
v1 because they are absent from the predicted-pair universe. Consequently, v1
tests precision-oriented cleanup and cannot recover recall by adding a pair.

## Frozen Legacy121 label inventory

Legacy121 has already informed Phase 1 characterization and rule selection.
The following counts describe development data; they are not independent test
evidence.

| Source model | RNAs | Predicted pairs | KEEP | DELETE | DELETE fraction | RNAs with DELETE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RNAfold | 121 | 1,693 | 1,473 | 220 | 0.129947 | 51 (42.15%) |
| PETfold | 121 | 1,704 | 1,463 | 241 | 0.141432 | 58 (47.93%) |
| trRosettaRNA2 native SS | 121 | 1,893 | 1,461 | 432 | 0.228209 | 106 (87.60%) |
| Pooled | 121 unique RNAs / 363 source records | 5,290 | 4,397 | 893 | 0.168809 | 109 unique RNAs (90.08%) |

The pooled DELETE:KEEP ratio is 0.2031. Source imbalance is material and must
be reported rather than hidden by pooling.

Observable subgroup counts further show that labels are not distributed
uniformly. Across all source records, singleton pairs contain 63 DELETE out of
86 pairs (73.26%); two-pair stems contain 92/184 (50.00%); outer boundaries
211/933 (22.62%); inner boundaries 285/933 (30.55%); and stem interiors
334/3,338 (10.01%). These are retrospective label-balance diagnostics, not
prevalidated decision rules. In particular, they must not be converted into
new hand-tuned thresholds.

The complete frozen summaries are:

- `results/selective_refiner_protocol/label_balance_by_model.csv`;
- `results/selective_refiner_protocol/label_balance_by_feature_group.csv`.

## Inference-time inputs

All features are computed from the sequence and the immutable original source
prediction. Stem/singleton extraction uses Strict Stem Definition v1. Feature
preprocessing, category vocabularies, and normalization statistics are fit on
the training partition only.

### Mandatory cross-model features

- nucleotide identities at endpoints `i` and `j`, with an explicit unknown
  category;
- ordered pair type;
- sequence length;
- raw separation `j - i` and relative separation
  `(j - i) / (sequence_length - 1)`;
- singleton flag;
- strict-stem length, using zero for a singleton;
- outer-to-inner pair position and normalized position within a stem;
- outer-boundary and inner-boundary flags;
- existence and pair type of the immediately outward and inward stacked
  predicted neighbors, using an explicit `NONE` value;
- local predicted topology only as represented by the fields above.

No numeric separation bin is a learned-label proxy. Raw and relative values
are supplied directly; the frozen Phase 1 bins may be used only for reporting.

### Source variants

- **Variant A — pooled source-aware:** add source-model identity as a
  categorical feature.
- **Variant B — pooled source-agnostic:** exclude source-model identity and all
  source-specific confidence. This variant must not be called model-agnostic
  unless it passes the leave-one-model-out protocol below.
- **Model-specific:** train an otherwise identical model separately for each
  source predictor.

Historical RNAfold and PETfold records do not retain comparable pair
confidence, while trRosettaRNA2 records do. Pair scores are therefore excluded
from all primary v1 variants. A source-confidence variant is deferred until a
comparable confidence protocol exists for every evaluated source.

### Prohibited inputs and leakage paths

The following are prohibited at training-feature construction, model
selection, threshold selection, and inference as applicable:

- GT pairs or dot-bracket structure;
- TP/FP/FN, wrong-partner, missing-pair, or stem-error labels as features;
- the identity or coordinates of an alternative GT partner;
- features computed after an edit or from recursively re-extracted stems;
- Phase 1 error frequencies attached to individual records;
- RNA family or dataset identity as a shortcut feature;
- source confidence available for only one source in a supposedly common
  variant;
- preprocessing statistics, class weights, feature vocabularies, early
  stopping, hyperparameters, or decision thresholds estimated from validation
  or test partitions outside the current training/validation fold;
- duplicated or sequence-redundant RNAs appearing across partitions;
- selecting a final configuration after inspecting the independent test set.

## Dataset and split protocol

### Redundancy definition

Sequences are compared by deterministic global alignment with match score 1,
mismatch score 0, gap-open -1, and gap-extension -1. Identity is:

`identities / (identities + mismatches + gaps)`.

Terminal gaps count. Any pair of sequences with identity **at least 0.80** is
connected, and connected components of this graph are the indivisible split
groups. The 80% threshold is frozen before learned-model training; it is a
conservative redundancy-control choice, not a value optimized for Legacy121
performance.

The same `rna_id`, all records from that RNA, and all members of a redundancy
component must remain in one partition. Source-model records may never be
randomly split at the pair or record level.

Reliable RNA-family labels are absent from the current frozen manifests, so a
family-level split cannot currently be audited. Family membership must not be
inferred from filenames or topology. If curated family labels are obtained,
the entire family becomes an indivisible group and the union of family and
80%-identity connections is assigned together.

### Legacy121 development use

Legacy121 may be used for feature-pipeline debugging, training, hyperparameter
selection, and **grouped internal development estimates only**. It must never
be relabeled as the final independent test set.

Use deterministic grouped five-fold cross-validation over the 80%-identity
components. In rotation `k`:

- internal test/development-report fold = `k`;
- validation fold = `(k + 1) mod 5`;
- training folds = the remaining three folds.

Fold construction must be deterministic, balance RNA counts and source-model
coverage as far as group constraints allow, and be saved before labels are
used for fitting. Each RNA brings all three source records, so primary splits
retain the complete three-model matrix. Metrics are reported per source and
pooled; pooled values never replace source-specific results. These internal
test folds remain exploratory because the dataset already informed protocol
design.

### Independent test requirement and local inventory audit

No adequate independent normalized test dataset is currently ready.

| Candidate | Read-only audit | Current role |
| --- | --- | --- |
| Legacy121 v1 | 121 RNAs; complete 363-record matrix; already used for Phase 1/rule pilot | Development/grouped CV only |
| external77 full inventory | 77 sequences; 4 contain `N`; 30 exact Legacy matches; among 73 ACGU sequences, 31 have identity >=0.80 to Legacy121 | Source pool only |
| external77 GT_CON nonredundant candidate | 42 ACGU sequences below 0.80 identity to every Legacy RNA | Preferred independent test candidate, not test-ready |
| TS85/CASP18 | 18 GT targets; only 15 manifest-level entity sequences currently resolved; those 15 have no >=0.80 Legacy matches | Secondary future candidate |
| TS85 holdout67 | 67 sequences, 31 exact Legacy matches, no frozen authoritative 2D GT manifest | Ineligible now |
| CASP16 working set | Partial/provisional files without a frozen sample/sequence/GT manifest | Ineligible now |

Before any independent learned-refiner evaluation, prepare
`external77_GT_CON_v1_nonredundant` as follows:

1. freeze GT_CON as the target semantics and freeze the 42 eligible rows from
   the per-sequence audit in
   `results/selective_refiner_protocol/external77_gt_con_candidate_ids.csv`;
2. preserve sequence, structure, source path, and hash provenance;
3. run the same frozen RNAfold, PETfold, and trRosettaRNA2-native-SS source
   protocols for all 42 RNAs without inspecting refiner outcomes;
4. normalize the resulting 126 source records under the existing schema;
5. validate the complete three-source matrix and canonical GT/prediction pairs;
6. keep the dataset test-only after the model configuration and decision
   threshold are locked using Legacy121 development data.

The 42-row set is a candidate until those steps pass. It is not permissible to
drop difficult or failed samples after inference without a frozen failure
policy. The inventory and per-sequence identity audit are machine-readable in
`dataset_split_inventory.csv` and `external77_gt_con_candidate_ids.csv`.

## Cross-model experiments

The following experiments are preregistered on identical RNA partitions:

1. model-specific training and evaluation for each source;
2. pooled source-aware Variant A;
3. pooled source-agnostic Variant B;
4. leave-one-model-out (LOMO) Variant B for each of the three source models.

For LOMO, source-model identity and source-specific confidence are excluded.
Training uses two source predictors, and validation threshold selection uses
only those training sources. The third source is held out in its entirety.
Within development CV, the held-out-source evaluation RNA groups must also be
sequence-cluster-disjoint from training RNAs. The strongest LOMO test applies
the configuration frozen on Legacy121 to the independent external set, again
holding out one source at a time.

Observed shared error types are not transfer evidence. Any later
“model-agnostic” claim requires successful LOMO results on all held-out sources
under the independent protocol; otherwise that claim is dropped.

## Baselines and model variants

All variants use identical partitions and the existing shared pair evaluator.
Preregistered baselines are:

- `ORIGINAL`;
- frozen `R1` singleton deletion;
- frozen `R3` outer noncanonical trim where applicable;
- frozen `R1_R3`;
- `LEARNED_UNGATED`;
- `LEARNED_SELECTIVE`.

Frozen R2 may be retained as a labeled high-risk negative-control result, but
it is not used to select a learned model. Frozen rule semantics cannot be
retuned.

`LEARNED_UNGATED` and `LEARNED_SELECTIVE` share the same trained backbone and
features. Ungated inference deletes whenever `p(DELETE) >= 0.5` and receives no
selective mask. Selective inference deletes only above a high-confidence
threshold selected on the validation fold; all other pairs are kept. This
ensures the non-selective baseline does not receive the selective model's
abstention mechanism.

For each fold, select the selective threshold using validation data only: among
thresholds that achieve pooled correct-pair preservation at least 0.99, choose
the threshold with the highest DELETE F1; break ties by the higher threshold
and then fewer edits. If no threshold satisfies the preservation constraint,
the fold emits no deployable selective configuration and is a no-go. The
threshold is locked before internal-test or external-test application.

## Conservative first architecture

The primary architecture is a pair-feature multilayer perceptron:

- categorical embeddings/one-hot encodings plus standardized numeric inputs;
- two hidden layers of width 64;
- ReLU activations;
- dropout 0.10;
- one sigmoid output giving `p(DELETE)`;
- class-weighted binary cross-entropy, with the DELETE weight computed from
  the training fold only.

Optimization duration, learning rate, batch size, random seeds, and early
stopping patience must be frozen in the implementation plan before the first
training run. At least five fixed seeds must be reported; validation, not test,
selects epochs and thresholds.

A lightweight pair/sequence-context Transformer is a deferred alternative: at
most two layers, hidden width 64, four attention heads, and the same pair-level
output. It is introduced only after the MLP experiment is completed and
documented as insufficient, not selected retrospectively because it performs
better on test data. The MLP is the smallest architecture capable of testing
whether the frozen observable features contain learnable selective signal.

## Evaluation endpoints

### Pair-classification endpoints

Treat `DELETE` as the positive class and report per source and pooled:

- DELETE precision, recall, and F1;
- AUPRC from continuous scores when both classes occur;
- AUROC as secondary context when both classes occur.

Undefined metrics remain null. Accuracy is not a primary endpoint because KEEP
dominates the label inventory.

### Structure and edit endpoints

After applying predicted deletions, evaluate exact canonical pairs with the
existing shared evaluator. Report:

- macro and micro Precision, Recall, and F1;
- macro and micro delta F1 from ORIGINAL;
- beneficial and harmful edit counts and fractions;
- **modification precision = beneficial edits / total edits**;
- beneficial-to-harmful edit ratio, with explicit infinity/null handling;
- correct-pair preservation = `TP_after / TP_before`;
- modified pair count and number/fraction of modified RNAs.

All deletion-only accounting identities from the rule baseline remain
mandatory. Paired per-RNA deltas and seed variability are retained. No
significance test is preregistered until the independent dataset is frozen.

R3 zero coverage must be reported as zero coverage, not zero accuracy. Macro
and micro effects remain separately labeled.

## Go/no-go criteria frozen before training

These thresholds govern the first learned experiment and may not be changed
after observing learned results.

### Development go gate

Advance the MLP configuration from grouped Legacy121 development to the
independent test only if the cross-validated `LEARNED_SELECTIVE` result meets
all of the following, aggregated strictly from held-out development rotations:

1. pooled modification precision is at least **0.80**;
2. pooled DELETE recall is at least **0.10**, preventing a near-zero-coverage
   classifier from passing on precision alone;
3. pooled correct-pair preservation is at least **0.99**, and preservation is
   at least **0.98 for each source predictor**;
4. both macro and micro delta F1 are positive for at least **two of three**
   source predictors;
5. at least 10% of RNAs are modified for each source on which a useful-effect
   statement is made;
6. selective modification precision and correct-pair preservation both exceed
   those of its matched `LEARNED_UNGATED` backbone.

The 0.80 modification-precision gate is above the pooled R1_R3 pilot value
(83/106 = 0.7830) and was frozen before learned training. It does not imply
statistical significance.

### Independent-evidence and transfer gates

An effectiveness claim additionally requires the locked model to reproduce:

- modification precision >=0.80;
- DELETE recall >=0.10;
- pooled preservation >=0.99 and per-source preservation >=0.98;
- positive macro and micro delta F1 on at least two sources;

on the independently prepared external test, with no retuning. Failure is
reported as a no-go, not repaired by changing thresholds or subsets.

A model-agnostic claim has the stricter requirement that all three independent
LOMO evaluations individually have modification precision >=0.80, positive
macro and micro delta F1, and per-source preservation >=0.98. If any held-out
source fails, the model-agnostic claim is dropped. Source-aware success cannot
substitute for this gate.

If the development gate fails, stop before adding a larger architecture and
report that the minimal observable-feature hypothesis was not supported. A
Transformer requires a new preregistered protocol amendment and cannot be used
to overwrite the MLP result.

## Interpretation limits

Legacy121 training or grouped CV is development evidence only because the same
dataset shaped the error taxonomy, target selection, and rule baseline. No
current result establishes that error labels are learnable, that learned
deletion improves structure, that transfer is model-agnostic, or that results
generalize across datasets. Those claims remain untested until the protocol is
implemented and an independent dataset is frozen and evaluated.
