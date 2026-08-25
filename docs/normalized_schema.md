# Normalized Prediction Schema v1

Status: **Confirmed infrastructure contract**

Schema version: `rna-ccfa.normalized_prediction.v1`

Frozen: 2026-08-25

## Purpose and Boundary

This schema defines the normalized record consumed by the future canonical parser, shared evaluator, error extractor, and baseline tables. It does not select the final dataset, ground-truth target, source predictor set, or refiner architecture.

The schema preserves three layers separately:

1. raw source paths and hashes for provenance;
2. human-readable structure representations when they are available and lossless;
3. canonical base-pair lists used by evaluation.

Raw data and historical predictions remain read-only. Normalization creates new records and optional score sidecars.

## Storage Contract

- Record stream: UTF-8 JSON Lines (`.jsonl`), one complete JSON object per line.
- One record represents one `(dataset, rna_id, ground_truth_label, source_model, run_id)` evaluation unit.
- Pair-score matrices are stored in sidecar NPZ files rather than embedded into JSON.
- Paths to normalized sidecars are POSIX paths relative to the JSONL file's directory.
- Raw source paths are recorded as observed; current absolute machine paths are allowed in provenance, but consumers must support configurable data-root remapping.
- Normalized outputs, logs, and per-sample metrics must not be written into any raw dataset or historical prediction directory.

## Top-Level Record

| Field | Type | Required | Contract |
| --- | --- | --- | --- |
| `schema_version` | string | Yes | Exactly `rna-ccfa.normalized_prediction.v1` |
| `record_id` | string | Yes | Unique, filesystem-safe ID for this normalized evaluation unit |
| `dataset` | string | Yes | Stable dataset namespace, not a mutable filesystem path |
| `rna_id` | string | Yes | Stable logical RNA ID from a frozen dataset manifest |
| `sequence` | string | Yes | Normalized RNA sequence in 5' to 3' order |
| `ground_truth_structure` | structure object | Yes | Explicitly labeled target structure and canonical pairs |
| `source_model` | source-model object | Yes | Model/checkpoint/run/decoder identity |
| `predicted_structure` | structure object | Yes | Source prediction and canonical pairs |
| `pair_scores` | score object or null | Yes | Normalized score sidecar descriptor; `null` when unavailable |
| `provenance` | provenance object | Yes | Raw inputs, hashes, normalizer identity, and transformations |
| `metadata` | object | Yes | Dataset/sample annotations; use `{}` when none are available |

No metric, error label, train/test assignment, or refiner output belongs in schema v1. Those are separate derived tables keyed by `record_id`.

## Record Identity

`record_id` uses the following readable layout after each component is converted to a lowercase filesystem-safe slug:

```text
<dataset>__<rna_id>__<ground_truth_label>__<source_model>__<run_id>
```

The normalized record builder must reject duplicate `record_id` values in one manifest. Filename heuristics alone must not create `rna_id`; legacy suffix removal and aliases such as PETfold's `1A9L.db` require an explicit dataset ID map.

If the same source prediction is evaluated against both `GT_ALL` and `GT_CON`, it produces two records with different `ground_truth_structure.label` values but the same prediction provenance and `source_model.run_id`. The ground-truth choice must not alter predictor input or inference.

## Sequence Contract

- `sequence` is uppercase and contains no whitespace or alignment gaps.
- The accepted v1 alphabet is the RNA IUPAC set `ACGURYSWKMBDHVN`.
- `T` is not silently accepted. A `T -> U` conversion is allowed only when recorded in `provenance.transformations` and the original sequence is hash-traceable.
- Ambiguous residues such as `N` are preserved. Predictor compatibility or sample exclusion is an evaluation-policy decision, not a schema transformation.
- `len(sequence)` is the coordinate length `L` used by every structure and score field.

## Structure Object

Both `ground_truth_structure` and `predicted_structure` use:

| Field | Type | Required | Contract |
| --- | --- | --- | --- |
| `label` | string | Yes | Target/source label such as `legacy_gt`, `GT_ALL`, `GT_CON`, `rnafold_mfe`, or `trrna2_native_ss` |
| `source_format` | enum string | Yes | `dot_bracket`, `extended_dot_bracket`, `pair_list`, `dense_matrix`, or `unknown` |
| `source_value` | string or null | Yes | Normalized textual structure when available and lossless; otherwise `null` |
| `pairs` | array of pairs | Yes | Canonical base-pair list; this is authoritative for evaluation |
| `allow_multiple_partners` | boolean | Yes | Defaults to `false`; may be `true` only for an explicitly documented annotation target that is not a matching |

### Canonical Base-Pair List

Each pair is a two-element JSON array `[i, j]` satisfying:

```text
0 <= i < j < L
```

Canonical pair lists must be:

- zero-based;
- lexicographically sorted by `(i, j)`;
- duplicate-free;
- free of self-pairs;
- independent of bracket-family labels;
- able to contain crossing pairs, e.g. `(i, j)` and `(k, l)` where `i < k < j < l`.

The schema does not impose Watson-Crick pairing, a minimum loop length, or a pseudoknot ban. Those properties may be annotations or later evaluation strata, but they must not silently remove pairs during parsing.

By default, each nucleotide may have at most one partner across the pair list. If an annotation such as a noncanonical all-interaction target contains multiple partners, the record must set `allow_multiple_partners: true`, use `source_format: pair_list` or `dense_matrix` when dot-bracket is not lossless, and retain the target label that explains the semantics. Predictor outputs must not enable this flag without a documented decoder specification.

### Dot-Bracket Contract

Normalized single-sequence dot-bracket may contain:

```text
unpaired: .
paired:   () [] {} <> A/a B/b ... Z/z
```

Opening and closing symbols are matched within their own family. Crossings between families are preserved by the resulting endpoints. Alignment gap `-` is not valid in normalized structure coordinates; PETfold alignment output must be projected to ungapped sequence coordinates with that transformation recorded.

`source_value` must have length `L`. If a pair list cannot be serialized losslessly as extended dot-bracket, `source_value` is `null` and `pairs` remains authoritative.

## Source-Model Object

| Field | Type | Required | Contract |
| --- | --- | --- | --- |
| `name` | string | Yes | Stable model name, e.g. `rnafold`, `petfold`, `trrosettarna2_native_ss` |
| `version` | string or null | Yes | Software release or source snapshot identifier |
| `checkpoint_id` | string or null | Yes | Checkpoint/ensemble identity when applicable |
| `checkpoint_sha256` | string or null | Yes | Hash for one checkpoint; ensemble hashes belong in `parameters` if more than one is used |
| `run_id` | string | Yes | Stable identifier for a frozen inference run/protocol |
| `input_mode` | string | Yes | For example `single_sequence`, `msa`, or `aligned_fasta` |
| `parameters` | object | Yes | All output-affecting inference and model parameters; use `{}` only when genuinely parameter-free |
| `decoder` | decoder object | Yes | Exact structure-decoding identity, including threshold/tie-breaking when applicable |

The decoder object requires `name`, `version`, and `parameters`. A historical structure-only output may use `name: historical_output`, `version: null`, and document unknown settings in `parameters`; it must not be presented as a fully reproduced run.

For trRosettaRNA2 native SS, the three checkpoint hashes are stored as a sorted list in `source_model.parameters.ensemble_checkpoint_sha256`. The current greedy DBN helper is not implicitly accepted as the project decoder; any normalized prediction derived from the NPZ must name the actual versioned decoder used.

## Pair-Score Object

`pair_scores` is `null` when no scores are available. Otherwise it contains:

| Field | Type | Required | Contract |
| --- | --- | --- | --- |
| `representation` | enum string | Yes | `dense_matrix` or `sparse_pairs` |
| `path` | string | Yes | Relative path to a normalized NPZ sidecar |
| `array_key` | string | Yes | `pair_scores` for dense data or `scored_pairs` for sparse data |
| `shape` | integer array | Yes | `[L, L]` for dense; `[N, 3]` for sparse `(i, j, score)` |
| `dtype` | string | Yes | Normalized dtype, normally `float32` |
| `semantics` | enum string | Yes | `probability`, `logit`, `energy`, `reliability`, or `model_score` |
| `symmetric` | boolean | Yes | Whether `score[i,j] == score[j,i]` is required |
| `diagonal` | string | Yes | Expected diagonal handling, normally `zero` |
| `source_path` | string | Yes | Raw score artifact from which the sidecar was normalized |
| `source_array_key` | string or null | Yes | Original NPZ key, e.g. `ss`, when applicable |

Additional requirements:

- Dense probability matrices must be finite, have shape `[L, L]`, be symmetric within a documented tolerance, have zero diagonal after normalization, and lie in `[0, 1]`.
- Missing scores must not be silently encoded as zero. A partial score set uses `sparse_pairs` or an explicitly documented mask sidecar in a later schema revision.
- Logits, energies, and generic model scores are not converted to probabilities unless the exact transformation is recorded in provenance.
- The selected `predicted_structure.pairs` may be decoded from scores, but the score object does not itself define the decoder.

## Provenance Object

| Field | Type | Required | Contract |
| --- | --- | --- | --- |
| `raw_files` | array of raw-file objects | Yes | Every raw sequence, GT, prediction, and score artifact used |
| `normalizer` | object | Yes | Normalizer name, version or Git commit, and command/config identity |
| `transformations` | array | Yes | Ordered, explicit transformations; use `[]` when none occurred |
| `created_at_utc` | string | Yes | RFC 3339 UTC timestamp |

Each raw-file object requires:

```text
role
path
sha256
```

Recommended roles include `sequence`, `ground_truth`, `prediction`, `pair_scores`, `dataset_manifest`, and `id_map`. Paths alone are insufficient because historical files may be moved or hard-linked.

Transformation records require `name`, `version`, `parameters`, and `input_roles`. Examples include suffix-to-ID mapping, `T -> U`, alignment-gap projection, 1-based-to-0-based conversion, matrix symmetrization, and score dtype conversion.

## Metadata Object

`metadata` stores annotations that do not change coordinate or evaluation semantics, for example:

```text
sequence_length
contains_ambiguous_bases
structure_source_method
pseudoknot_encoded
experimental_method
family
split
```

`sequence_length` is required inside metadata and must equal `len(sequence)`. Other keys are optional. Split/family fields remain null or absent until a leakage-safe manifest is frozen; normalization must not infer them from filenames.

## Illustrative Synthetic Record

The following is a schema example only, not a project sample or experimental result:

```json
{
  "schema_version": "rna-ccfa.normalized_prediction.v1",
  "record_id": "synthetic__example_rna__synthetic_gt__rnafold__smoke_v1",
  "dataset": "synthetic",
  "rna_id": "example_rna",
  "sequence": "GCGCUUCGCC",
  "ground_truth_structure": {
    "label": "synthetic_gt",
    "source_format": "dot_bracket",
    "source_value": "(((...))).",
    "pairs": [[0, 8], [1, 7], [2, 6]],
    "allow_multiple_partners": false
  },
  "source_model": {
    "name": "rnafold",
    "version": "2.4.17",
    "checkpoint_id": null,
    "checkpoint_sha256": null,
    "run_id": "smoke_v1",
    "input_mode": "single_sequence",
    "parameters": {"noPS": true},
    "decoder": {"name": "rnafold_mfe", "version": "2.4.17", "parameters": {}}
  },
  "predicted_structure": {
    "label": "rnafold_mfe",
    "source_format": "dot_bracket",
    "source_value": "(((...))).",
    "pairs": [[0, 8], [1, 7], [2, 6]],
    "allow_multiple_partners": false
  },
  "pair_scores": null,
  "provenance": {
    "raw_files": [
      {"role": "sequence", "path": "/tmp/synthetic/example.fa", "sha256": "0000000000000000000000000000000000000000000000000000000000000000"},
      {"role": "ground_truth", "path": "/tmp/synthetic/example.db", "sha256": "0000000000000000000000000000000000000000000000000000000000000000"},
      {"role": "prediction", "path": "/tmp/synthetic/rnafold.out", "sha256": "0000000000000000000000000000000000000000000000000000000000000000"}
    ],
    "normalizer": {"name": "rna_ccfa_normalizer", "version": "illustrative", "config": "illustrative"},
    "transformations": [],
    "created_at_utc": "2026-08-25T00:00:00Z"
  },
  "metadata": {
    "sequence_length": 10,
    "contains_ambiguous_bases": false,
    "pseudoknot_encoded": false
  }
}
```

## Validation Levels Required by the Future Implementation

### Fatal record errors

- missing required field or wrong schema version;
- duplicate `record_id`;
- empty/invalid normalized sequence;
- structure length mismatch;
- unmatched or illegal dot-bracket symbol;
- out-of-range, reversed, duplicate, or self pair;
- multiple partners when `allow_multiple_partners` is false;
- score shape inconsistent with `L`;
- non-finite probability, probability outside `[0, 1]`, or a nonzero dense-score diagonal after normalization;
- missing raw-file hash or normalized score sidecar.

### Warnings that require explicit reporting

- ambiguous sequence symbols;
- `allow_multiple_partners: true`;
- historical output with unknown decoder settings;
- source representation that cannot be serialized losslessly as dot-bracket;
- asymmetric raw score matrix that was symmetrized by a recorded transformation;
- optional metadata such as family/split unavailable.

No invalid record may be silently dropped. The normalizer must emit a machine-readable validation report keyed by the attempted `record_id`.

## Deferred Decisions

The following remain outside schema v1 and are not fixed by this document:

- legacy 121/123 GT reconciliation;
- external77 `GT_ALL` versus `GT_CON` selection and scoring semantics;
- handling of the four external77 sequences containing `N` for each predictor;
- final initial 3-5 source predictors;
- the project decoder for probability matrices;
- MCC definition;
- pseudoknot-specific metrics and stem taxonomy;
- train/validation/test splits and all Refiner records.
