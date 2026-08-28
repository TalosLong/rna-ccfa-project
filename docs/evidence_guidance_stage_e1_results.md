# Evidence Guidance Stage E1 Results

**Status:** `STAGE_E1_COMPLETE`
**Progression decision:** `E2_PROTOCOL_JUSTIFIED`

## Scope and integrity

Stage E1 executed the frozen clean (`noise=0`) `simulated_evidence_v1` hard
baselines on Legacy121. It used 121 RNAs, all 363 normalized source records
(RNAfold/PETfold/trRosettaRNA2 native SS: 121 each), six frozen densities, and
five frozen evidence seeds. No neural network was trained, V3 was neither
rerun nor retuned, and external77 was not accessed.

The reconstructed 7,260-manifest suite has SHA256
`c743913d8d0b44cbccaba74b68bebaeb1551a4095d1ae51782435c12e96d11ca`.
All 9,075 zero-density identity checks and 54,450 coordinate/one-partner,
scope-partition, and non-evidenced invariance checks passed. The evaluator
preserved 54,450 per-RNA/source/configuration rows and 163,350 internal scope
rows.

## Full-structure effects

Values below are pooled over the three sources and are means across the five
evidence seeds. Evidence seeds are repeated samplings, not independent
biological samples. Complete mean/SD/min/max and source-specific values are in
the machine-readable summaries.

| Condition | Density | Macro delta F1 | Micro delta F1 | Modification precision | Correct-pair preservation |
| --- | ---: | ---: | ---: | ---: | ---: |
| PAIR_PROTECT_ONLY | 1% | +0.001022 | +0.002502 | 1.000 | 1.000 |
| PAIR_PROTECT_ONLY | 10% | +0.001286 | +0.005086 | 1.000 | 1.000 |
| PAIR_PROTECT_ONLY | 20% | +0.003024 | +0.011029 | 1.000 | 1.000 |
| PAIR_PROTECT_ONLY | 50% | +0.008516 | +0.024947 | 1.000 | 1.000 |
| PAIR_HARD_ENFORCE | 1% | +0.006020 | +0.005633 | 1.000 | 1.000 |
| PAIR_HARD_ENFORCE | 10% | +0.008649 | +0.011950 | 1.000 | 1.000 |
| PAIR_HARD_ENFORCE | 20% | +0.017095 | +0.025266 | 1.000 | 1.000 |
| PAIR_HARD_ENFORCE | 50% | +0.045045 | +0.061022 | 1.000 | 1.000 |
| UNPAIRED_HARD_DELETE | 1% | +0.007167 | +0.006006 | 1.000 | 1.000 |
| UNPAIRED_HARD_DELETE | 10% | +0.008691 | +0.009472 | 1.000 | 1.000 |
| UNPAIRED_HARD_DELETE | 20% | +0.014825 | +0.017157 | 1.000 | 1.000 |
| UNPAIRED_HARD_DELETE | 50% | +0.034332 | +0.039247 | 1.000 | 1.000 |

All clean hard-baseline edits were beneficial under exact-pair evaluation;
there were no harmful edits. This is expected from the frozen clean simulated
evidence semantics and must not be generalized to noisy or real evidence.

## Direct evidence effects

For simulated positive-pair evidence, PAIR_PROTECT_ONLY never inserts a pair:
it only removes a conflicting prediction. PAIR_HARD_ENFORCE reaches 100%
post-transformation compliance by adding supplied GT pairs that were absent.
Across source/seed summaries, direct insertion accounts for approximately
57--60% of its micro-F1 gain at nonzero densities. That fraction is explicitly
reported as tautological gain attribution, not prediction or generalization.

For simulated unpaired-nucleotide evidence, original compliance was about
78--80% across nonzero densities and UNPAIRED_HARD_DELETE reached 100% by
removing every conflicting predicted pair. No pair was added.

## Local conflict effects

Clean evidence corrected every conflicting predicted pair at an evidenced
endpoint/position. Mean pooled beneficial local removals rose with density:

| Condition | 1% | 5% | 10% | 20% | 50% |
| --- | ---: | ---: | ---: | ---: | ---: |
| PAIR_PROTECT_ONLY / PAIR_HARD_ENFORCE | 30.2 | 36.6 | 61.2 | 131.8 | 293.4 |
| UNPAIRED_HARD_DELETE | 72.2 | 80.8 | 113.4 | 203.6 | 454.2 |

These are direct local consequences of clean evidence. They demonstrate
useful local correction signal without injecting the positive pair in
PAIR_PROTECT_ONLY, but they are not evidence of non-local propagation.

## Non-evidenced effects

The `NON_EVIDENCED_EFFECT` pair set was unchanged in every one of 54,450
evaluations. Macro and micro non-evidenced delta F1 and non-evidenced modified
pair counts are exactly zero. Stage E1 therefore provides no propagation
claim; its effects are fully attributable to direct evidence and local
conflict resolution.

## Density response and actual item counts

The per-RNA minimum-one rule is material at low density. Per seed, simulated
positive-pair evidence supplies 0/121/130/180/338/875 items at
0/1/5/10/20/50%; simulated unpaired-nucleotide evidence supplies
0/121/134/185/333/873. Full-structure gains generally increase with actual
item count, while seed spread is retained as mean, population standard
deviation, minimum, and maximum in the summary tables.

## Source-specific response

All three predictors benefit under the clean hard transformations, but effect
size is source-dependent. At 50%, PAIR_HARD_ENFORCE macro/micro delta F1 is
+0.041612/+0.057416 for RNAfold, +0.043891/+0.059406 for PETfold, and
+0.049633/+0.065662 for trRosettaRNA2. UNPAIRED_HARD_DELETE is more strongly
source-dependent: +0.020051/+0.028685, +0.023779/+0.032307, and
+0.059166/+0.055246, respectively. trRosettaRNA2 benefits most from each
channel at 50%, consistent with its larger original FP opportunity set. This
does not establish model agnosticism.

## Comparison with frozen V3 context

Historical V3_VETO2_FIXED has macro/micro delta F1
+0.017160/+0.023046. PAIR_HARD_ENFORCE at 50% and
UNPAIRED_HARD_DELETE at 50% equal or exceed both values. At 20%,
PAIR_HARD_ENFORCE exceeds V3 on micro delta F1 but is lower by 0.000065 on
macro delta F1. PAIR_PROTECT_ONLY does not equal or exceed both metrics at any
frozen density. This is contextual comparison only; V3 was not rerun.

## E2 progression recommendation

The frozen decision is `E2_PROTOCOL_JUSTIFIED`. Stage E1 establishes strong,
reproducible direct and local-conflict utility across all sources, including a
positive-pair condition that does not inject the supplied pair. That is enough
to justify separately freezing an E2 learned evidence-guidance protocol.
Stage E1 does **not** show non-evidenced propagation, so E2 may test whether
such propagation can be learned but cannot assume it exists. No E2 model or
protocol is designed or trained here, and external77 remains locked.

## Artifacts

The canonical outputs are under `results/evidence_guidance/stage_e1/`:
per-RNA results, full-structure seed/summary tables, scope tables, evidence
compliance, direct/local/non-evidenced decomposition, hard-enforcement gain
attribution, density counts, source metrics, V3 context comparison, and the
machine-readable integrity report.
