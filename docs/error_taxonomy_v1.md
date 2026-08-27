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

## Strict Stem Definition v1

This strict stacked-stem definition is frozen as a deterministic
infrastructure unit for later error analysis. It is intentionally conservative
and is not claimed to be a complete biological helix definition.

For canonical pairs `(i,j)` with `i < j`, two pairs are directly
stack-adjacent exactly when `(i+1,j-1)` exists. A strict stem is a maximal
consecutive chain:

```text
(i,     j)
(i+1, j-1)
(i+2, j-2)
...
```

No gaps are allowed. Bulges, internal loops, missing stacked pairs, and
sequence gaps are not bridged. The minimum strict stem size is exactly
`minimum_stem_pairs = 2`. A canonical pair with no strict stacked neighbor is
retained as a `singleton_pair`; singleton pairs are counted separately and are
never silently discarded.

The extraction algorithm starts each chain only at a pair whose outer
predecessor `(i-1,j+1)` is absent, then follows `(i+1,j-1)` until the chain
ends. Stem pairs are ordered outermost to innermost and stems are sorted by
their `outer_pair`. Singleton pairs are sorted lexicographically. This makes
results independent of input pair ordering.

Crossing stems are handled as ordinary independent chains. No pseudoknot
classification or special case is applied. Every canonical pair belongs to
exactly one strict stem or to the singleton set, so:

```text
sum(stem.n_pairs for stem in stems) + len(singleton_pairs)
    == total_pair_count
```

This definition does not label stems as correct, missing, shifted, truncated,
or extended, and it does not match GT stems to predicted stems. Those
decisions are defined in the matching protocol below.

### Strict-stem inventory layout

`results/error_analysis/stem_inventory_by_record.csv` contains one shared
`ground_truth` row per RNA and one `prediction` row per normalized predictor
record. The shared GT row uses a deterministic inventory-only `record_id` and
stores all three corresponding normalized record IDs in `source_record_ids`;
this preserves provenance without counting the same GT structure three times.
The summary therefore has 121 GT structures and 121 structures for each
predictor. Per-record length statistics are computed over that record's strict
stems; summary length statistics are computed over all strict stems in the
group. Inventory quantities are descriptive only.

## Stem Matching and Error Taxonomy v1

This section freezes deterministic matching semantics; implementation and
final Legacy121 stem-error counts remain a subsequent task.

### Representation and candidate diagnostics

Matching uses only strict stems from the definition above. For each GT/predicted
stem pair record exact pair overlap, GT/predicted pair counts, pair-union size,
left- and right-arm overlap, and the register `i+j` (constant across a strict
stem) with its signed difference. No family, confidence, 3D, or other metadata
is used.

An edge is a candidate when either (a) exact pair overlap is positive, or (b)
exact overlap is zero, registers differ, both arm overlaps are at least two,
and each arm overlap is at least the shorter stem's arm length minus one. Thus
at most one nucleotide on each arm of the shorter stem may be unmatched. This
is a conservative, audited shift-evidence filter.

### One-to-one assignment and ambiguity gate

Candidate edges are considered as a bipartite graph. A connected component with
more than one GT stem or more than one predicted stem is not forced into an
arbitrary match: all involved stems receive `complex_mismatch` with an
ambiguous-component annotation. This prevents merged/split stems from being
contaminated by shift or boundary labels. Isolated one-GT/one-predicted-stem
components are the eligible one-to-one matches. If a future eligible component
has multiple edges, select a maximum-weight assignment with lexicographic
objective: maximize total exact overlap, then total minimum arm overlap, then
number of matched edges, then minimize pair-union size; ties are broken by the
lexicographically smallest sorted `(gt.outer_pair, predicted.outer_pair)` list.

Within an eligible isolated match, category precedence is exact, then
truncation/extension, then shift, then complex mismatch. The component
ambiguity gate precedes this per-edge precedence.

### Primary states

* `exact`: GT pair set equals predicted pair set.
* `stem_truncation`: predicted pair set is a strict subset of GT's pair set
  on the same register. Missing pairs may be described as outer-end,
  inner-end, or both-end according to which ends of the ordered chain are
  absent; a non-contiguous subset is not rescued as truncation.
* `stem_extension`: GT pair set is a strict subset of the predicted pair set
  on the same register. Added pairs may analogously be outer-end, inner-end,
  or both-end.
* `stem_shift`: an eligible isolated match with zero exact pair overlap,
  non-zero register displacement, and the bilateral arm-overlap filter above.
  It therefore requires positive evidence of the same local helix in a changed
  pairing register, rather than being a residual “not otherwise classified”.
* `complex_mismatch`: an isolated candidate with overlap that is neither exact
  nor a strict subset/superset (for example, a shared middle run with one GT
  boundary removed and a different predicted boundary added), or any stem in
  an ambiguous candidate component.
* `stem_missing`: a GT stem with no candidate edge and not part of an ambiguous
  component. A confidently shifted candidate is therefore not called missing.
* `unmatched_predicted_stem`: a predicted stem with no candidate edge and not
  part of an ambiguous component. It is not automatically an extension.

Examples: `(10,40),(11,39),(12,38),(13,37)` versus
`(11,40),(12,39),(13,38)` is a shift (bilateral overlap and register delta
`+1`); versus `(11,41),(12,40),(13,39),(14,38)` is also a shift (delta `+2`).
The shared-register case `(11,39),(12,38),(13,37),(14,36)` is
`complex_mismatch`, not shift, because it has overlap but is neither subset nor
superset. Crossing stems are processed independently and receive no
pseudoknot-specific rule.

This protocol is provenance-preserving infrastructure, not a biological claim.
Stem-level extraction, long-range and pseudoknot-specific analysis, biological
interpretation, and refiner labels remain deferred.

## Deferred Taxonomy

This document does not define or extract:

- implementation of the frozen stem matching/error states and final counts;
- long-range pairs or sequence-separation bins;
- pseudoknot-specific errors or metrics;
- biological or causal interpretations of any error relation.
