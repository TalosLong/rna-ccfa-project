# MCC Definition Audit for RNA Secondary Structure

Status: **MCC deferred for the shared Phase 0 evaluator**

Audited: 2026-08-26

## Why MCC Requires True Negatives

For binary decisions, Matthews correlation coefficient is

```text
MCC = (TP * TN - FP * FN)
      / sqrt((TP + FP)(TP + FN)(TN + FP)(TN + FN))
```

Exact canonical pair lists directly determine TP, FP, and FN through set
intersection and differences. They do not determine TN. A true negative is a
candidate pair that is absent from both prediction and ground truth, so MCC
requires an explicit universe of candidate pair decisions.

## Possible Negative-Pair Universes

### All unordered residue pairs

Use every zero-based pair satisfying `0 <= i < j < L`. The universe has
`L * (L - 1) / 2` elements, and

```text
TN = L * (L - 1) / 2 - TP - FP - FN
```

This is the simplest representation-level definition and matches the schema's
lack of a minimum loop length or pairing-chemistry filter. It also creates a
very large number of negatives, especially for long RNA, so MCC can be driven
mostly by easy non-pairs.

### Minimum-separation-filtered pairs

Exclude candidates with `j - i` below a selected minimum loop or sequence
separation. Different cutoffs remove different numbers of candidates and can
also exclude pairs retained by schema v1, which intentionally imposes no
minimum loop length.

### Sequence-compatible pairs

Count only pairs allowed by a selected chemistry rule, such as Watson-Crick
pairs, optionally including G-U wobble or ambiguous IUPAC residues. TN then
depends on the sequence alphabet and the chosen compatibility table. This
would conflict with schema v1 if it silently excluded annotated noncanonical
pairs.

### Decoder- or benchmark-specific candidate masks

Use only positions considered by a predictor, decoder, score matrix, or
benchmark protocol. This may be appropriate for one model but makes TN and MCC
model-dependent unless every prediction is evaluated against exactly the same
frozen mask.

### Dense-matrix cells or nucleotide-level states

Counting ordered off-diagonal matrix cells treats `(i, j)` and `(j, i)` as two
decisions, unlike canonical pairs. Counting paired/unpaired nucleotides creates
a different classification task and does not measure exact partner identity.
Neither is interchangeable with unordered exact-pair MCC.

## Why the TN Counts Differ

Each definition changes the size and membership of the candidate universe.
Even with identical TP, FP, and FN pair sets, removing short-range candidates,
filtering by sequence chemistry, doubling symmetric matrix cells, or applying
a model mask changes TN. The resulting MCC values therefore answer different
questions and cannot be compared as if they used one metric definition.

Per-RNA MCC versus a micro-aggregated MCC introduces a second unresolved
choice: averaging per-RNA coefficients weights RNAs equally, whereas pooling
confusion counts weights longer RNAs through their much larger negative
universes.

## Decision

MCC is not implemented in the Phase 0 shared evaluator because the current
project documentation does not freeze one negative-pair universe or an
aggregation rule. Precision, Recall, and F1 require only positive pair sets and
are therefore unambiguous under the canonical schema.

If MCC becomes required later, the recommended representation-level starting
point is all unordered pairs `i < j`, because it adds no pairing chemistry,
minimum-loop, or pseudoknot restriction beyond schema v1. That choice must
still be explicitly frozen, tested for zero-denominator cases, and reported
with its per-RNA or pooled aggregation rule before MCC results are produced.
