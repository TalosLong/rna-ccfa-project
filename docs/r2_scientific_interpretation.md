# R2 Scientific Interpretation

Status: **FROZEN — `R2_INTERPRETATION_COMPLETE`**

Date: 2026-09-02

Authoritative result basis:

- `docs/global_constrained_refolding_r2_results.md`;
- `results/global_constrained_refolding_r2/summaries/overall_summary.csv`;
- `results/global_constrained_refolding_r2/summaries/source_wise_summary.csv`;
- `results/global_constrained_refolding_r2/summaries/evidence_efficiency_summary.csv`;
- `results/global_constrained_refolding_r2/integrity/formal_summary_integrity_v1_0_2.json`.

This interpretation is restricted to the frozen R2 v1.0.2 matched eligible
universe and clean symbolic evidence. It does not use a learned model, noisy or
real evidence, external77, a pseudoknot-capable branch, or R4 results.

## Interpretation contract

The statements below use three non-interchangeable labels:

- **EMPIRICAL RESULT**: directly reported by the frozen R2 artifacts.
- **INTERPRETATION**: a bounded scientific reading of those results.
- **FUTURE HYPOTHESIS**: an unverified question reserved for R3/R4.

An interpretation must not be promoted to an empirical result, and a future
hypothesis must not be written as an expected outcome.

## A. B2 is a strong mandatory comparator

### EMPIRICAL RESULT

On the complete matched v1.0.2 universe, aggregate structure quality was:

| Method | Macro F1 | Micro F1 |
| --- | ---: | ---: |
| B0 Original | 0.878635 | 0.861068 |
| B1 Local hard | 0.889352 | 0.872422 |
| B2 Global constrained refolding | **0.924648** | **0.904747** |

B2 exceeded both B0 and B1 in aggregate Macro and Micro F1 under the frozen
clean-evidence comparison.

### INTERPRETATION

B2 is a strong classical baseline and a mandatory comparator for future R4.
The scientific case for post-hoc reconciliation cannot rest on improvement
over B0 or B1 alone.

### FUTURE HYPOTHESIS

None is needed to establish B2's comparator status. Whether a post-hoc method
can achieve a better correction-preservation trade-off remains untested.

## B. B2 is not preservation-safe

### EMPIRICAL RESULT

| Quantity | Frozen R2 value |
| --- | ---: |
| Macro TP preservation | 0.975358 |
| Micro TP preservation | 0.981767 |
| Lost original TP | 4,752 |
| New FP | 10,823 |

B2 also removed 32,433 original FP and added 11,042 new TP, but those benefits
co-occurred with the losses above.

### INTERPRETATION

**B2 obtains strong correction but causes non-negligible collateral damage.**

No safety claim for evidence-constrained refolding is supported. Aggregate F1
improvement does not establish safe preservation of correct source-predictor
pairs.

### FUTURE HYPOTHESIS

A deletion-only post-hoc method may be able to retain useful FP removal while
reducing collateral TP loss, but R2 does not test that hypothesis.

## C. NON_EVIDENCED propagation is net useful but imperfect

### EMPIRICAL RESULT

Within the frozen `NON_EVIDENCED_EFFECT` pair scope, B2 produced:

| Quantity | Frozen R2 value |
| --- | ---: |
| Beneficial modifications | 36,027 |
| Harmful modifications | 15,575 |
| Micro modification precision | 0.698171 |

All R2 collateral harm occurred in the non-evidenced pair scope under the
frozen decomposition.

### INTERPRETATION

Global constraint propagation has net positive utility, but a substantial
fraction of non-local edits are harmful. The result supports useful
propagation in aggregate; it does not support uniformly reliable propagation.

### FUTURE HYPOTHESIS

A pair-selective method may identify a safer subset of non-evidenced changes.
This is a prospective R3/R4 question, not an R2 result.

## D. Source dependence

### EMPIRICAL RESULT

trRosettaRNA2 received the largest relative B2 correction, including the
largest Macro F1 gains and FP removal, and had the lowest Macro TP preservation
among the three source predictors. RNAfold and PETfold had smaller relative
gains, while their original frozen Legacy121 structure quality was higher.

### INTERPRETATION

**The value of preserving source-predictor output is source-dependent.**

The pooled result must therefore be accompanied by RNAfold-, PETfold-, and
trRosettaRNA2-specific analysis.

### FUTURE HYPOTHESIS

No cause of the source dependence is inferred. Any explanation involving model
family, thermodynamic similarity, training data, confidence, or error type
requires separate evidence.

## E. Evidence efficiency and density

### EMPIRICAL RESULT

Absolute B2 structure quality generally improved as clean evidence density
increased. In contrast, FP removed per delivered evidence item declined
substantially at higher density. Event-pooled FP removal per evidence item fell
from 1.422590 at pair 1% to 0.181835 at pair 50%, and from 1.392287 at unpaired
1% to 0.303475 at unpaired 50%.

The pair channel retained 121 eligible RNAs through 10% density but only 118 at
20% and 113 at 50% because of prospectively frozen solver-capability
eligibility. The unpaired channel retained all 121 RNAs at every density.

### INTERPRETATION

More evidence is associated with higher absolute structure quality but
diminishing correction efficiency per evidence item. Absolute pair-channel
comparisons across 20% and 50% density are composition-sensitive because the
eligible RNA set changes.

Within-density matched B0/B1/B2 comparisons are therefore primary. Cross-
density absolute comparisons, especially for pair 20% and 50%, are contextual
and must retain eligible-RNA denominators.

### FUTURE HYPOTHESIS

R2 does not establish why evidence efficiency declines, and no mechanism is
inferred.

## Gate A interpretation

### Question

> Does source-prediction preservation have plausible headroom versus B2?

### Frozen answer

**`POSTHOC_HEADROOM_PLAUSIBLE`**

B2's future safety reference is:

| Quantity | Macro | Micro |
| --- | ---: | ---: |
| TP preservation | 0.975358 | 0.981767 |
| FP removal | 0.775728 | 0.645883 |

The future R4 candidate safety point is `TP_preservation >= 0.99`. B2 lies
below that preservation level in both aggregate summaries and produced 4,752
lost TP and 10,823 new FP. This leaves a scientifically reasonable but
unverified question:

> Can a pair-selective post-hoc method retain useful FP removal at TP
> preservation >= 0.99?

### Gate status

**`GATE_A_DEFERRED_R4_REQUIRED`**

Gate A is neither PASS nor FAIL because no future R4 result exists. The only
permitted conclusion is:

> Headroom is scientifically plausible and requires R3/R4 testing.

The following claim forms are prohibited:

- assigning a PASS status to Gate A before R4 exists;
- stating present post-hoc superiority over B2 without an R4 result;
- predicting future post-hoc superiority over B2;
- any claim that R2 demonstrates safe evidence-constrained refolding.

## Frozen R2 interpretation state

```text
R2_INTERPRETATION_COMPLETE
POSTHOC_HEADROOM_PLAUSIBLE
GATE_A_DEFERRED_R4_REQUIRED
```
