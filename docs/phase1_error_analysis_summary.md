# Phase 1 Error Analysis Summary

## Scope

This is descriptive analysis of Legacy121 v1: 121 RNAs and three historical
source predictors (RNAfold, PETfold, and trRosettaRNA2 native SS), totaling 363
normalized records. Pair equality, stem extraction/matching, and separation
bins use the frozen protocols. No predictor inference, refinement, biological
causal analysis, or cross-dataset comparison is included.

## Baseline

| Model | Macro F1 | Micro F1 | TP / FP / FN |
| --- | ---: | ---: | ---: |
| RNAfold | 0.905818 | 0.874443 | 1473 / 220 / 203 |
| PETfold | 0.896849 | 0.865680 | 1463 / 241 / 213 |
| trRosettaRNA2 native SS | 0.842871 | 0.818717 | 1461 / 432 / 215 |

## Pair-Level Findings

RNAfold and PETfold have similar pair error partitions. Their FP rates among
predicted pairs are 12.99% and 14.14%; 59.09% and 56.43% of FPs are
wrong-partner events. trRosettaRNA2 has a higher FP rate (22.82%) and its FP
partition is instead majority pure FP (263/432, 60.88%). FN rates are close
across models (12.11%, 12.71%, 12.83%). Missing pairs linked to a wrong-partner
event comprise 64.53%, 64.32%, and 73.49% of FNs.

Pair-error rankings use the mutually exclusive pair-event partition
`missing_pair`, wrong-partner FP, and pure FP with denominator `FP+FN`; they do
not mix pair and stem counts. Missing pairs rank first for RNAfold/PETfold;
pure FP ranks first for trRosettaRNA2.

## Stem-Level Findings

GT-side rates use 335 GT stem instances per model. Predicted residual rates use
each model's predicted-stem count.

| Model | Exact | Extension | Missing | Ambiguous GT | Unmatched predicted |
| --- | ---: | ---: | ---: | ---: | ---: |
| RNAfold | 67.76% | 13.13% | 13.73% | 2.99% | 12.88% |
| PETfold | 60.60% | 12.54% | 14.33% | 10.45% | 14.10% |
| trRosettaRNA2 | 33.43% | 30.75% | 11.94% | 20.30% | 12.20% |

RNAfold/PETfold have similar extension, missing, and unmatched rates, although
PETfold has more ambiguous GT stems and a lower exact rate. trRosettaRNA2 is
extension- and ambiguity-skewed. Its 295 predicted stems are fewer than the 335
GT stems, while its 1,893 predicted pairs exceed 1,676 GT pairs because its
predicted strict stems are longer on average (6.20 versus 4.88 pairs), it has
103 extension relations, and ambiguous components often consolidate multiple
GT stems into fewer predicted stems.

The trRosettaRNA2 FP excess is not primarily an unmatched-stem count effect:
its unmatched rate (12.20%) is comparable to the other models. Exact pair
mapping attributes 146 FP pairs to extension stems and 125 to unmatched
predicted stems, with another 83 in ambiguous predicted stems and 49 outside
predicted strict stems. Thus boundary excess/extension is at least as important
as unmatched predicted stems in the observed FP structure.

Truncation (5/4/1), shift (2/2/6), and isolated complex mismatch (1/1/5) are
too sparse to be dominant first targets. Ambiguous states remain residuals,
not forced matches.

## Sequence-Separation Findings

The GT-derived highest-separation bin contains 167 GT pairs and covers 100
RNAs. RNAfold/PETfold/trRosettaRNA2 place only 6/5/15 FPs and 0/0/0 FNs there,
corresponding to 2.73%, 2.07%, and 3.47% of model FPs. Errors are therefore not
enriched in the frozen highest-separation bin on Legacy121. This negative
result means sequence separation is a useful descriptor but not a major shared
error signal for the first refinement baseline.

## Shared Patterns

Stem extension, stem missing, unmatched predicted stems, wrong-partner events,
pure FP, truncation, and shift are observed in all three predictors. Shared
presence is not shared dominance: stem extension is strongly trRosettaRNA2-
skewed, while stem missing and unmatched predicted-stem rates are comparatively
similar across models. Wrong-partner events dominate the FP partition only for
RNAfold/PETfold.

## Model-Specific Patterns

RNAfold and PETfold form the closest descriptive pair, with similar extension,
missing, unmatched, FN, and FP-subtype profiles. PETfold has intermediate stem
ambiguity. trRosettaRNA2 is distinguished by higher FP rate, pure-FP dominance,
more extension and ambiguous GT-stem dispositions, fewer but longer predicted
stems, and a lower exact-stem rate.

## What Phase 1 Supports

On Legacy121 and these three predictors, errors exhibit repeatable structured
partitions and stem-boundary/residual patterns rather than an undifferentiated
count of mismatched pairs. This supports the descriptive claim that structured
error patterns exist and motivates testing narrowly scoped rules.

## What Phase 1 Does NOT Support

- no evidence yet that error patterns are learnable or correctable;
- no evidence that any rule improves Precision, Recall, or F1;
- no model-agnostic refinement claim;
- no evidence-guided refinement claim;
- no downstream 3D benefit claim;
- no cross-dataset claim;
- no pseudoknot-aware comparison or mechanism claim.

## Implications for Phase 2

The first rule specification should prioritize conservative extension-boundary
trimming and a clearly labeled high-risk unmatched-stem removal baseline. Pure
FP, wrong partner, and missing stems remain important Priority B targets but
require observable proxies or candidate generation. Shift, truncation, complex
mismatch, ambiguity, and PK-aware edits are deferred. Phase 2 must freeze edit
triggers and preservation measurements before implementation.
