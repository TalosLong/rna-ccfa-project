# Phase 2 Minimal Rule-Based Refinement Baseline v1

Status: **Frozen specification; implementation and evaluation have not started**

## Purpose and scope

This pilot asks whether simple features observable from a sequence and its
predicted secondary structure contain any useful deletion signal. It is not an
attempt to maximize Legacy121 F1. Rule baseline v1 is deterministic,
confidence-free, and identically available to RNAfold, PETfold, and
trRosettaRNA2 native SS.

This specification permits pair deletion only. It forbids pair addition,
partner reassignment, global reconstruction, learned parameters, GT-dependent
triggers, source-specific primary rules, and recursive edits. The frozen Phase
1 pair/stem taxonomy and long-range protocol are inputs to evaluation only and
are not changed here.

Legacy121 has already been used for Phase 1 characterization and target-family
selection. Any Legacy121 rule result is therefore a **pilot/feasibility
evaluation**, not independent evidence of cross-dataset generalization.

## Representation and inference contract

The deployable input is:

1. the RNA sequence;
2. the normalized predicted canonical pair set; and
3. strict stems and singleton pairs extracted once with Strict Stem Definition
   v1 and `minimum_stem_pairs = 2`.

“Canonical” describes 0-based coordinate ordering `(i,j)`, `i < j`. The allowed
sequence-pair orientations used by R3 are separately named the
Watson-Crick/wobble set:

```text
AU, UA, GC, CG, GU, UG
```

Before any trigger is computed, the implementation must validate coordinates,
uniqueness, sequence bounds, no self-pairs, and the one-partner constraint. An
incompatible-pair conflict is any nucleotide assigned to more than one distinct
partner. A validation failure aborts that record and condition; v1 never repairs
it.

All triggers are evaluated against one immutable **original prediction
snapshot**. Candidate deletions are collected, deduplicated, sorted by canonical
pair coordinates, and applied simultaneously. The edited pair set is validated
again. Deleted pairs are not reconsidered, strict stems are not re-extracted to
create new triggers, and no rule cascades.

## Frozen atomic rules

### R1_SINGLETON_DELETE — singleton cleanup

- **Observable inputs:** original predicted pair set and frozen strict-stem
  extraction.
- **Trigger:** a predicted pair belongs to the original
  `singleton_pairs` set; equivalently, it is not part of any predicted strict
  stem.
- **Edit:** delete that pair.
- **Maximum edits per stem:** not applicable; singleton pairs are outside
  strict stems. Every triggered original singleton may be deleted once.
- **Cascade:** none.
- **Stopping condition:** one snapshot pass has completed.

This rule does not assert that singleton pairs are false positives.

### R2_TWO_PAIR_STEM_DELETE — short-stem cleanup baseline

- **Observable inputs:** original predicted strict stems.
- **Trigger:** a predicted strict stem has exactly
  `n_pairs == minimum_stem_pairs == 2`.
- **Edit:** delete both pairs of that original stem.
- **Maximum edits per stem:** two; there is no additional per-record cap.
- **Cascade:** none. A longer stem cannot become eligible after another edit.
- **Stopping condition:** one snapshot pass has completed.

This is a deliberately high-risk minimum-length baseline. It is not an
`unmatched_predicted_stem` detector and must not be named or interpreted as one.

### R3_OUTER_NONCANONICAL_TRIM — conservative outer-boundary proxy

- **Observable inputs:** sequence, original predicted strict stems, original
  outer pair, and the immediately inward stacked pair.
- **Trigger:** all of the following hold for an original strict stem:
  1. `n_pairs >= 3`, so one deletion leaves at least the frozen minimum of two
     pairs;
  2. the outer pair's oriented sequence identity is **not** one of
     `AU, UA, GC, CG, GU, UG`; and
  3. the immediately inward pair's oriented sequence identity **is** one of
     those six types.
- **Edit:** delete the original `outer_pair` only.
- **Boundary:** outer only; the inner boundary is never inspected as a trigger
  in v1.
- **Maximum edits per stem:** one pair.
- **Cascade:** none. The new outer pair cannot trigger another deletion.
- **Stopping condition:** one snapshot pass has completed.

The rule name is shorthand, not a thermodynamic claim. It does not declare AU,
GU, or any other allowed pair erroneous. It is a narrow observable boundary
heuristic, not an inference-time detector of the GT-defined `stem_extension`
label. The proxy audit found 0/0/20 triggers for RNAfold/PETfold/trRosettaRNA2,
so source-skewed coverage must accompany any result.

## Rule precedence and overlap

Execution order is fixed:

1. validate the original record;
2. extract original strict stems and singleton pairs once;
3. independently collect each selected rule's candidate deletions;
4. take the set union and retain every triggering rule ID per pair;
5. apply every unique deletion once in lexicographic pair order; and
6. validate the resulting pair set.

There is no biological precedence among R1–R3 because they only delete and
operate on the same snapshot. Under the frozen extraction, R1 pairs, R2 stem
pairs, and R3 stem pairs are disjoint. The union/deduplication rule remains a
safety contract: if future implementation detects an overlap, one edit is
logged with all triggering rule IDs and is never double-counted.

## Pre-registered conditions

The Legacy121 pilot may run only these deployable conditions:

| Condition ID | Rules | Purpose |
| --- | --- | --- |
| `ORIGINAL` | none | Frozen source-prediction reference. |
| `R1` | R1 | Test isolated singleton cleanup alone. |
| `R2` | R2 | Test the deliberately high-risk two-pair-stem baseline alone. |
| `R3` | R3 | Test the narrow boundary proxy alone. |
| `R1_R2` | R1 + R2 | Test topology-only removal of the two smallest frozen structural units. |
| `R1_R3` | R1 + R3 | Test conservative isolated-pair plus boundary cleanup. |

`R2_R3` and `R1_R2_R3` are not pre-registered: R2 and R3 address disjoint stem
lengths, and an all-rules condition would confound the conservative boundary
test with the intentionally high-risk R2 baseline. No data-dependent subset or
additional `2^N` combination may be added after results are inspected.

## Rejected or deferred primary rules

- **Wholesale non-Watson-Crick/wobble cleanup:** rejected because biochemical
  pair identity is not a normalized-schema validity rule and such interactions
  can be genuine. It is highly source-skewed in the current outputs.
- **Generic AU/GU terminal trimming:** rejected because no GT-free fixed
  semantic makes those valid pair classes erroneous.
- **Inner-terminal or recursive trimming:** deferred to avoid arbitrary
  boundary precedence and cascade behavior.
- **Wrong-partner repair:** deferred because the alternative GT partner is
  unobservable and reassignment is outside deletion-only v1.
- **Missing-stem recovery:** deferred because it requires candidate generation
  and addition.
- **Pair-confidence filtering:** deferred because comparable historical
  confidence is unavailable for RNAfold and PETfold. A later
  source-confidence variant must be reported separately from this primary
  cross-model baseline.
- **Sequence-separation filtering:** rejected from v1 because Phase 1 showed no
  shared error enrichment in the highest frozen separation bin.

## Non-deployable oracle diagnostics

Two optional evaluation-only conditions may later quantify available deletion
signal. They are not rule-baseline conditions and must be displayed in a
separate oracle table:

- `ORACLE_EXTENSION_DELETE`: for an isolated GT-defined
  `stem_extension`, delete the predicted boundary pairs not present in its
  matched GT stem.
- `ORACLE_UNMATCHED_FP_DELETE`: within GT-defined
  `unmatched_predicted_stem` instances, delete only pairs that belong to the
  exact FP partition.

Both use GT and Phase 1 labels. They are diagnostic upper bounds only, cannot
trigger inference-time edits, and must never be described as a practical
refiner, rule baseline, or deployable result. Running them is optional in the
later implementation task and does not alter the frozen deployable conditions.

## Evaluation protocol and endpoints

Later evaluation must compare `ORIGINAL` with each pre-registered condition
using only `rna_ccfa.metrics.evaluate_pairs`. It must report per sample and per
source model:

- Precision, Recall, and F1;
- `delta_precision`, `delta_recall`, and `delta_f1` relative to the same
  record's original prediction;
- `modified_pair_count`, the number of unique deleted pairs;
- `beneficial_edit_count`, deleted pairs that were FP before editing;
- `harmful_edit_count`, deleted pairs that were TP before editing;
- `beneficial_edit_fraction = beneficial_edit_count / modified_pair_count`;
- `harmful_edit_fraction = harmful_edit_count / modified_pair_count`; and
- `correct_pair_preservation_rate = TP_after / TP_before`.

For a deletion-only condition, these identities are mandatory:

```text
beneficial_edit_count + harmful_edit_count == modified_pair_count
TP_after == TP_before - harmful_edit_count
FP_after == FP_before - beneficial_edit_count
FN_after == FN_before + harmful_edit_count
```

Edit fractions are explicit `null` when `modified_pair_count == 0` rather than
zero. Correct-pair preservation is explicit `null` when `TP_before == 0`.
Model-level edit fractions use summed numerators and denominators; undefined
per-sample values are not silently replaced in macro summaries.

Macro P/R/F1 remain arithmetic means of the 121 per-sample shared-evaluator
values. Micro P/R/F1 are recomputed from summed TP/FP/FN. Both macro and micro
deltas must be named explicitly. Raw paired per-sample deltas are preserved;
statistical testing is deferred until final independent evaluation sets are
frozen.

## Edit log contract

The future `results/rule_baseline/edit_log.jsonl` must contain one row per
unique deletion with at least:

```text
record_id
rna_id
source_model
condition_id
rule_id                 # or triggering_rule_ids for a deduplicated overlap
deleted_pair            # canonical zero-based [i,j]
observable_trigger_features
stem_id                 # null for singleton edits
```

The observable feature payload must be sufficient to recompute the trigger
without GT. Post-hoc fields `was_tp_before`, `was_fp_before`, and
`beneficial_or_harmful` may be appended only after triggering and must never be
read by the rule executor.

## Pre-registered pilot interpretation

Outcome labels are assigned per condition from aggregate edit counts and both
macro/micro shared metrics. No significance threshold is introduced.

1. **USEFUL SIGNAL:** at least one edit occurs; beneficial edits exceed harmful
   edits; and both macro and micro F1 deltas are positive. Precision, Recall,
   and the numerical preservation rate must still be reported, and this label
   is not a safety or generalization claim.
2. **NO USEFUL SIGNAL:** no edit occurs, or beneficial edits do not exceed
   harmful edits. Neutral/negative metric changes are reported rather than
   hidden.
3. **TRADE-OFF:** every other edited outcome, particularly a Precision gain
   accompanied by enough Recall/preservation loss that macro and micro F1 do
   not both improve.

This precedence is fixed as `NO USEFUL SIGNAL`, then `USEFUL SIGNAL`, otherwise
`TRADE-OFF`. Magnitudes, per-model heterogeneity, correct-pair preservation,
and raw paired deltas remain mandatory; the qualitative label alone is not a
paper-level conclusion.

## Frozen rule-testable hypotheses

### H1 — observable boundary proxy

R3 tests whether the frozen outer-terminal/context cue has a beneficial edit
count greater than its harmful edit count and positive macro/micro F1 deltas.
Endpoints: all edit counts/fractions, correct-pair preservation, and
Precision/Recall/F1 deltas. This tests the proxy, not detection of all
`stem_extension` instances.

### H2 — minimal structural cleanup trade-off

R1 and the deliberately high-risk R2 test whether singleton or two-pair-stem
removal trades Precision against Recall. Their atomic conditions and `R1_R2`
combination are evaluated by the same endpoints; neither trigger is treated as
a GT error label.

### H3 — source-dependent response

The same inference-safe rule semantics can yield different trigger coverage
and edit-quality profiles for RNAfold, PETfold, and trRosettaRNA2. Endpoints are
modified/beneficial/harmful counts, edit fractions, preservation, and metric
deltas reported separately by source model. No expected numeric direction is
pre-specified.

## Known limitations

- The narrow R3 proxy does not make extension broadly observable; most Phase 1
  extensions remain targets for later selective or confidence-aware methods.
- R1 and R2 deliberately risk deleting valid GT pairs and cannot be assumed to
  represent pure FP or unmatched stems.
- Identical rule semantics do not guarantee equal trigger coverage across
  source predictors.
- Legacy121 pilot results cannot establish cross-dataset, model-agnostic,
  learned-correctability, evidence-guided, or downstream-3D claims.
- Pseudoknot-aware refinement remains a separate side track and is not part of
  this nested/currently supported mainline baseline.
