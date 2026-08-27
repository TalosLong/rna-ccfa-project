# RNA Pair-Level Error Taxonomy v1

Status: **Frozen for pair-level extraction only**

Frozen: 2026-08-27

## Scope

This version freezes three pair-level terms for canonical RNA secondary
structures:

- `missing_pair`;
- `false_positive_pair`;
- `wrong_partner`.

All coordinates are canonical zero-based pairs `[i,j]` satisfying `i < j`.
Inputs must already satisfy the normalized schema's matching constraint: each
nucleotide has at most one partner in GT and at most one partner in the
prediction. Pair extraction reuses `rna_ccfa.metrics.evaluate_pairs`; it does
not introduce another structure parser or metric definition.

Stem-level errors, sequence-separation/long-range bins, and
pseudoknot-specific definitions remain explicitly deferred. Crossing pairs are
ordinary canonical pairs in this pair-level taxonomy.

## Exact Pair Partitions

For canonical prediction set `P` and ground-truth set `G`, the shared evaluator
defines:

```text
TP = P intersection G
FP = P - G
FN = G - P
```

### `missing_pair`

Every exact false-negative GT pair is one `missing_pair`:

```text
missing_pair = GT pair not present in prediction = FN
```

This label neither merges nor relaxes pairs. Its count must remain identical
to the shared evaluator's FN count.

### `false_positive_pair`

Every exact false-positive predicted pair is one `false_positive_pair`:

```text
false_positive_pair = predicted pair not present in GT = FP
```

Its count must remain identical to the shared evaluator's FP count.

## `wrong_partner` Relation

`wrong_partner` is an annotation on a `false_positive_pair`, not a third
mutually exclusive metric partition.

For each FP pair `p = (i,j)`, construct the GT partner map. Inspect both
endpoints independently:

- endpoint `i` conflicts when GT pairs `i` with `k`, where `k != j`;
- endpoint `j` conflicts when GT pairs `j` with `l`, where `l != i`.

Define:

```text
wrong_partner_degree = number of conflicting endpoints
```

For an FP pair its possible values and meanings are:

| Degree | Meaning |
| ---: | --- |
| 0 | Pure false positive; neither endpoint has a different GT partner. |
| 1 | Wrong-partner conflict at one endpoint. |
| 2 | Wrong-partner conflicts at both endpoints. |

An FP pair is a `wrong_partner` event exactly when
`wrong_partner_degree >= 1`. Every conflicting endpoint contributes its unique
GT pair to `linked_missing_pairs`. Because GT is a matching, a degree-1 event
links to one FN and a degree-2 event links to two distinct FNs.

The event representation contains:

```text
predicted_pair
wrong_partner_degree
conflicting_endpoints
linked_missing_pairs
```

Each `conflicting_endpoints` item records the endpoint, its predicted partner,
and its GT partner. Event and linked pairs must belong to the same normalized
record.

### One-endpoint example

```text
GT:         (10,40)
Prediction: (10,35)

FP: (10,35)
FN: (10,40)
wrong_partner_degree: 1
linked_missing_pairs: [(10,40)]
```

### Two-endpoint example

```text
GT:         (10,40), (20,35)
Prediction: (10,35)

FP: (10,35)
FN: (10,40), (20,35)
wrong_partner_degree: 2
linked_missing_pairs: [(10,40), (20,35)]
```

One wrong predicted pair can therefore link to two missing GT pairs.
`wrong_partner` event counts must not be forced to equal FP or FN counts.

## Reverse Missing-Pair Annotation

Each `missing_pair` also receives a reverse annotation. For missing GT pair
`(i,j)`, inspect whether prediction assigns either endpoint to a different
partner:

- `wrong_partner = true` when at least one endpoint has another predicted
  partner;
- `wrong_partner_degree` is the number of such endpoints (`0`, `1`, or `2`);
- `linked_false_positive_pairs` are the unique FP pairs using those endpoints.

This reverse relation does not redefine or subdivide FN for evaluation.
`missing_pairs_linked_to_wrong_partner` counts unique annotated FN pairs;
`pure_missing_pair_count` is the remaining FN count.

## Determinism and Required Identities

Pairs, events, endpoint conflicts, and links are emitted in canonical sorted
order. Input ordering must not change extraction output. For each record:

```text
wrong_partner_event_count + pure_false_positive_count
    == false_positive_pair_count
```

Every event's `predicted_pair` must be in FP, and every
`linked_missing_pair` must be in FN. No equality is required between the
number of wrong-partner events and the number of missing pairs.

## Deferred Taxonomy

This document does not define or extract:

- stems or `stem_missing`, `stem_truncation`, `stem_extension`, `stem_shift`;
- long-range pairs or sequence-separation bins;
- pseudoknot-specific errors or metrics;
- biological or causal interpretations of any error relation.
