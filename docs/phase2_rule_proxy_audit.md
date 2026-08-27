# Phase 2 Rule Proxy Audit

Status: **Frozen inference-time proxy audit; no edits or refinement evaluation
have been run**

Basis: Legacy121 v1, 121 RNAs and three historical source predictors. This
audit uses the frozen Phase 1 taxonomy to choose questions, but it does not use
ground truth or Phase 1 error labels to trigger a rule.

## Inference/evaluation boundary

The Phase 1 labels `stem_extension`, `unmatched_predicted_stem`,
`wrong_partner`, `pure_false_positive`, and `stem_missing` are evaluation-only
states. They require GT and are forbidden as deployable edit triggers. A primary
rule may inspect only:

- the RNA sequence;
- the source predictor's canonical predicted pair set;
- strict stems and singleton pairs extracted from that prediction;
- predicted stem length and boundary position;
- nucleotide identities and pair type;
- local predicted-stem context; and
- raw or relative sequence separation.

All structural features are computed from one immutable snapshot of the input
prediction. No proxy in this audit was selected by searching Legacy121 GT
correctness, Precision, Recall, or F1.

## Confidence availability

The historical RNAfold and PETfold structures retain no pair probability or
reliability. The trRosettaRNA2 native-SS records retain an `L x L` score
matrix. Consequently, the primary baseline must be confidence-free and use the
same rule semantics for all three predictors. A later source-confidence variant
may be studied only after comparable confidence contracts or reproducible
predictor reruns are frozen; it is not part of rule baseline v1.

## Read-only observable inventory

The following counts use predictions and sequences only. They are trigger-volume
diagnostics, not correctness estimates.

| Predictor | Predicted pairs | Singleton pairs | Two-pair strict stems | Pairs in two-pair stems | Non-Watson-Crick/wobble pairs | Records containing such pairs | Multiple-partner conflicts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RNAfold | 1,693 | 13 | 36 | 72 | 0 | 0 | 0 |
| PETfold | 1,704 | 10 | 34 | 68 | 15 | 11 | 0 |
| trRosettaRNA2 native SS | 1,893 | 63 | 22 | 44 | 273 | 90 | 0 |

Here “non-Watson-Crick/wobble” means a sequence pair outside
`AU, UA, GC, CG, GU, UG`; it does not mean an invalid coordinate pair under the
normalized schema. The schema's term *canonical pair* refers to normalized
coordinates `(i,j)` with `i < j`, not to a biochemical pair-class restriction.

A narrow outer-terminal diagnostic was also counted without GT. Among strict
stems of length at least three, an outer non-Watson-Crick/wobble pair immediately
followed inward by a Watson-Crick/wobble pair occurs in 0 RNAfold, 0 PETfold,
and 20 trRosettaRNA2 stems (17 records). This asymmetry must be reported when
the rule is evaluated; identical semantics do not imply identical trigger
coverage.

## Target-to-proxy audit

| Phase 1 target | Observable candidates | Decision for baseline v1 | Reason |
| --- | --- | --- | --- |
| `stem_extension` | predicted stem length; terminal pair identity; outer/inner boundary; immediate inward stack; singleton adjacency; separation | **Narrow proxy accepted** | An outer terminal pair outside the six Watson-Crick/wobble orientations, stacked immediately inside by an allowed pair and leaving a valid stem after one deletion, is a deterministic boundary heuristic. It is not an extension detector and has source-skewed coverage. |
| `unmatched_predicted_stem` | predicted stem length; minimum-length status; isolation; local pairing context | **High-risk proxy accepted** | A strict stem of exactly the frozen minimum length (two pairs) is observable. It is deliberately only a short-stem cleanup baseline and is never equated with the GT-defined unmatched state. |
| pure FP | singleton status; short-stem status; pair type; local isolation | **Singleton proxy accepted** | Singleton membership is deterministic and model-independent. A GT pair may genuinely be a singleton, so removal is an empirical cleanup test rather than a correctness assertion. |
| `wrong_partner` | predicted conflicts; alternative local partners | **No edit proxy** | In a valid one-partner prediction, the GT partner conflict is unobservable. Choosing another partner would require candidate generation and could destroy a correct pair. |
| `stem_missing` | unpaired residues; sequence complementarity; candidate pair scores | **Deferred** | A deletion-only rule cannot recover an absent GT stem. Candidate generation/addition semantics and comparable confidence are outside baseline v1. |

## Candidate-rule decisions

### R1 — singleton removal: accepted

The trigger is exact membership in the frozen predicted `singleton_pairs` set.
It is inference-safe, confidence-free, and contains no numeric threshold. Its
risk is explicit: strict-stem membership is not a correctness label, and a GT
pair can also be a singleton.

### R2 — minimum short-stem removal: accepted as a high-risk baseline

The trigger is a predicted strict stem with `n_pairs == 2`, exactly the frozen
`minimum_stem_pairs`. The value two comes from the existing representation
definition, not from a Legacy121 performance search. This proxy is called
*short-stem cleanup*, never `unmatched_predicted_stem` detection.

### R3 — conservative weak outer-terminal trimming: accepted narrowly

The trigger uses an outer terminal sequence-pair class plus its immediate
inward stacked context. It removes at most the original outer pair, never an
inner boundary and never recursively. “Weak” here is merely a rule name: the
rule is not claimed to reproduce thermodynamic stability, and AU/GU pairs are
not treated as erroneous. Exact semantics are frozen in
`docs/phase2_rule_baseline_spec.md`.

This is the only currently defensible confidence-free, GT-free boundary proxy,
and it is very narrow. It provides a practical test of whether an observable
boundary cue contains correction signal; it does **not** identify the Phase 1
`stem_extension` state. Most extension cases can use ordinary AU/UA/GC/CG/GU/UG
pairs and remain inaccessible to this rule.

### R4 — remove every non-Watson-Crick/wobble pair: rejected from v1

The trigger is observable and materially present in trRosettaRNA2, but wholesale
deletion is not justified by the normalized representation: non-Watson-Crick
and non-wobble interactions can be valid recorded base pairs. The trigger is
also strongly source-skewed (0/15/273 pairs). The much narrower R3 boundary
condition is retained; global pair-type cleanup is deferred as a separately
pre-registered sensitivity analysis, not silently folded into the primary
baseline.

### Confidence and separation rules: deferred

Confidence is unavailable for two historical predictors. Phase 1 also found no
FP/FN enrichment in the highest frozen separation bin, so separation is not a
primary cleanup trigger. Neither variable is used in baseline v1.

## Conflict detection

An incompatible-pair conflict means that a nucleotide index is assigned to
more than one distinct partner in the same predicted pair set. Duplicate pairs,
out-of-range coordinates, self-pairs, and noncanonical coordinate ordering are
also invalid inputs. All 363 current normalized predictions pass the
one-partner check.

Baseline v1 therefore treats conflict detection as a fail-fast validation and
safety invariant, not as an edit rule. A conflicting record must stop with an
explicit error; the implementation must not choose a partner, delete a pair, or
rebuild the structure implicitly.

## Audit conclusion

The accepted deployable proxy family is intentionally small: singleton
deletion, frozen-minimum two-pair-stem deletion, and one-layer outer-terminal
trimming under a fixed pair-type/context condition. The first two test simple
topological cleanup, while the third is a narrow boundary proxy. `wrong_partner`
and `stem_missing` have no safe deletion-only observable proxy, and Phase 1
extension labels remain unavailable at inference. These limitations are part
of the baseline result, not gaps to be hidden by GT-tuned thresholds.
