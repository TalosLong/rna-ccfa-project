# Evidence Guidance Stage E1 Protocol

Status: **FROZEN BEFORE E1 EVALUATION**

E1 is a Legacy121-only clean simulated-evidence hard-baseline experiment. It
uses `simulated_evidence_v1` manifests with noise level zero. It does not train
a model, evaluate noise robustness, map to a real modality, or access
external77.

## Frozen conditions

- `ORIGINAL`: unchanged source prediction.
- `V3_VETO2_FIXED`: reuse its exact historical fold/score-seed decisions as a
  development-only internal-prediction comparator; do not retune or call it a
  successful method.
- `PAIR_PROTECT_ONLY`: positive-pair channel only, frozen protocol semantics.
- `PAIR_HARD_ENFORCE`: positive-pair channel only, frozen direct-injection
  upper/reference semantics.
- `UNPAIRED_HARD_DELETE`: unpaired-nucleotide channel only, frozen deletion
  semantics.

The evidence conditions use all 121 Legacy121 RNAs, the three immutable
source predictions, six densities, and five evidence seeds. The existing
five grouped folds are retained as reporting strata; they do not select or
tune a hard rule. ORIGINAL is paired to every evidence realization for exact
delta calculations. `V3_VETO2_FIXED` is reported from its existing 25 frozen
fold×score-seed outcomes and compared descriptively as internal-information
context, not replicated as five new independent observations.

## Frozen evaluation

Every result is stratified by condition, channel, density, evidence seed,
source, and frozen fold where applicable. It reports all full-structure and
anti-tautology endpoints frozen in `docs/evidence_guidance_protocol_v1.md`.
The `DIRECT_EVIDENCE_EFFECT`, `LOCAL_CONFLICT_EFFECT`, and
`NON_EVIDENCED_EFFECT` scopes must be disjoint and exhaust the evaluated pair
union. Directly supplied pairs cannot contribute to non-evidenced gain.

For hard-enforce, inserted evidence pairs and the fraction of total F1 gain
attributable to them are mandatory. Evidence-seed variability is reported;
seed replicas are not treated as independent biological RNAs.

## Scientific questions

1. Does sparse evidence improve full structure metrics?
2. How much gain comes from direct enforcement versus local conflict
   resolution?
3. Is `NON_EVIDENCED_EFFECT` positive?
4. At what frozen density does useful effect become measurable?
5. Do effects differ across RNAfold, PETfold, and trRosettaRNA2 native SS?
6. Does simulated external evidence provide information beyond the frozen
   cross-model consensus comparator?

E1 is descriptive development evidence and has no independent-evaluation
pass/fail gate. It cannot unlock external77. After E1, any learned E2 protocol
and its progression criteria must be separately frozen before training; E1
results may justify that new hypothesis but cannot alter E1 conditions or
metrics.
