# Selective Refiner MLP Implementation Plan v1

Status: **FROZEN BEFORE TRAINING**. This plan defines implementation details
for `docs/selective_refiner_protocol_v1.md`; it does not train a model.

## Feature contract

The feature extractor consumes only `(sequence, immutable original predicted
canonical pair set, source variant)`. It first validates sequence length,
canonical `i < j` pairs, and the one-partner constraint. It extracts strict
stems and singleton pairs once from the original snapshot and never re-extracts
after a hypothetical edit.

For each predicted pair, emit the following deterministic fields:

| Field | Encoding |
| --- | --- |
| endpoint nucleotides | categorical `A,C,G,U,N/OTHER` for each endpoint |
| ordered pair type | categorical concatenation, e.g. `GC`, `AU`, `OTHER` |
| sequence length | numeric |
| raw separation | numeric `j-i` |
| relative separation | numeric `(j-i)/(L-1)`, with `0` only for the impossible `L=1` guard |
| singleton flag | binary |
| strict-stem length | integer, zero for singleton |
| stem pair position | integer from outer to inner, zero for singleton |
| normalized stem position | `(position)/(stem_length-1)`; zero for singleton/length-one guard |
| outer boundary flag | binary |
| inner boundary flag | binary |
| outward stacked-neighbor existence/type | binary plus categorical pair type or `NONE` |
| inward stacked-neighbor existence/type | binary plus categorical pair type or `NONE` |

The immediately outward neighbor of `(i,j)` is `(i-1,j+1)` when present in
the original prediction; the inward neighbor is `(i+1,j-1)`. Pair types use
the ordered endpoint bases. All field names and category vocabularies are
fixed before fitting.

The source-aware variant adds exactly one categorical `source_model` field with
the frozen vocabulary `rnafold`, `petfold`,
`trrosettarna2_native_ss`. The source-agnostic and LOMO variants omit it.
No GT coordinates, Phase 1 labels, family/dataset IDs, pair scores, or
confidence values appear in the primary feature matrix.

## Labels and leakage audit

For each original predicted pair, exact canonical evaluation constructs:

`KEEP = pair in ground_truth_pairs`; `DELETE = pair not in ground_truth_pairs`.

Wrong-partner FPs are ordinary `DELETE`. Missing/FN pairs are absent examples.
The label builder is run after feature construction and is never called by the
inference feature path. A leakage audit must assert that feature column names
contain none of `gt`, `truth`, `tp`, `fp`, `fn`, `wrong_partner`, `missing`,
`family`, or `dataset`, and that no GT pair coordinates occur in serialized
feature rows.

## Numeric preprocessing

Numeric features are standardized independently within each training fold:

`z = (x - mean_train) / max(std_train, 1e-8)`.

Training means and scales are serialized with the checkpoint. Categorical
features are one-hot encoded in the fixed vocabulary with an explicit unknown
bucket; no category is inferred from validation/test rows. The source-aware
source vocabulary is fixed above. Test rows never contribute to preprocessing
statistics.

## Exact MLP hyperparameters

The first implementation freezes:

- two fully connected hidden layers, width 64 each;
- ReLU after each hidden layer;
- dropout `0.10` after each hidden activation;
- one sigmoid output for `p(DELETE)`;
- AdamW optimizer;
- learning rate `1e-3`;
- weight decay `1e-4`;
- batch size `256`;
- maximum `100` epochs;
- early-stopping metric: validation DELETE F1 at the frozen default threshold
  `0.5`;
- patience `12` validation epochs;
- gradient-norm clipping at `5.0`;
- fixed seeds: `17, 29, 41, 53, 67` (five seeds);
- PyTorch default Kaiming/linear initialization with the seed set before model
  construction;
- class-weighted BCE with `pos_weight = KEEP_train / DELETE_train`, where
  DELETE is the positive class and the counts come from the training fold only.

If `DELETE_train == 0`, the fold/variant is invalid and is reported as a
training failure; no smoothing or test-derived weight is allowed.

The threshold grid is fixed before training to
`{0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95}`. The
selective threshold is chosen on validation data only among grid values with
pooled correct-pair preservation >=0.99, maximizing DELETE F1; ties choose the
higher threshold and then fewer edits. If no grid value satisfies preservation,
the fold has no deployable selective checkpoint. The `LEARNED_UNGATED` result
uses threshold `0.50` without this gate.

Checkpoint selection is the highest validation DELETE-F1 epoch tie-broken by
higher preservation, then earlier epoch. The final seed summary reports all
five seeds; no test metric selects a seed. The training schedule and values
above require a written amendment before any change.

## Frozen model variants

Implement exactly:

`MODEL_SPECIFIC_RNAFOLD`, `MODEL_SPECIFIC_PETFOLD`,
`MODEL_SPECIFIC_TRROSETTARNA2`, `POOLED_SOURCE_AWARE`,
`POOLED_SOURCE_AGNOSTIC`, `LOMO_HOLDOUT_RNAFOLD`,
`LOMO_HOLDOUT_PETFOLD`, `LOMO_HOLDOUT_TRROSETTARNA2`.

For model-specific variants, one source model supplies all three folds. Pooled
variants use all source records while preserving RNA groups. LOMO trains on two
sources and evaluates the third with source identity removed; validation and
threshold selection never use held-out-source labels.

## Future artifact layout

The training task must write, without overwriting prior runs:

```
results/selective_refiner/
  v1/
    <variant>/fold_<k>/seed_<seed>/
      config.json
      train_ids.csv
      validation_ids.csv
      test_ids.csv
      checkpoint.pt
      validation_curves.csv
      selected_threshold.json
      per_pair_scores.csv
      per_rna_edited_structures.jsonl
      pair_classification_metrics.json
      per_rna_structure_metrics.csv
      seed_summary.json
```

`config.json` includes protocol version, feature schema hash, fold assignment
hash, class-weight counts, preprocessing statistics hash, random seed, and all
hyperparameters. `test_ids.csv` is an internal development fold or locked
external IDs as appropriate; the independent external IDs are never used for
training or threshold selection.

## Required checks before first training

The implementation must fail loudly if any RNA appears in multiple folds, if an
80%-connected component crosses a fold, if any source record is separated from
its RNA, if normalization uses non-training rows, if class weights use
validation/test labels, or if threshold selection reads test outcomes. Feature
determinism and feature-column leakage audits are mandatory. No model training
is authorized by this document alone; the external test matrix and an
implementation review must be complete first.
