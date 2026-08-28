# Claim–Evidence Map

Status labels describe current project evidence, not intended future results.

| Candidate claim | Evidence | Status | Qualification |
| --- | --- | --- | --- |
| Prediction errors exhibit structured patterns. | Legacy121 Phase 1 exact pair partitions, wrong-partner relations, strict-stem dispositions, and GT-derived separation strata across three predictors. | PARTIALLY_SUPPORTED | Demonstrated descriptively on one dataset and three historical predictors only. |
| Errors are correctable. | Legacy121 Phase 2 pilot applies frozen GT-free deletion proxies and records exact beneficial/harmful edits. | PARTIALLY_SUPPORTED | Some PETfold/trRosettaRNA2 conditions have more beneficial than harmful edits and positive macro/micro F1, but RNAfold does not; this is one reused pilot dataset, not independent evidence. |
| Observable sequence/structure heuristics contain correction signal. | Legacy121 R1/R3/R1_R3 pilot conditions evaluated with immutable GT-free triggers and post-hoc edit accounting. | PARTIALLY_SUPPORTED | Supported for selected model-condition pairs only. R3 has 20/20 beneficial edits on trRosettaRNA2 but zero RNAfold/PETfold coverage; no universal or model-agnostic claim. |
| Observable pair/topology features support a learned selective refiner. | 200 frozen Legacy121 grouped-CV runs completed; selected sources show learnable FP signal, but the pooled development gate failed. | PARTIALLY_SUPPORTED | Legacy121 development evidence only; no external learned-model evaluation. |
| Claim A: selective refinement can identify high-risk predicted pairs. | v1 selective gating raises pooled modification precision to 0.875/0.857, but preservation and two-source structure-effect gates fail. | PARTIALLY_SUPPORTED | Supported only as source-dependent Legacy121 development evidence, predominantly trRosettaRNA2-driven. |
| Claim B: cross-model agreement provides transferable correction evidence. | Prediction-only Legacy121 audit: correct fraction rises from 0.1587 to 0.3686 to 0.9764 for 0/1/2 other-model supports, monotonically for all three sources. | PROMISING_HYPOTHESIS | Retrospective label enrichment justifies frozen v2 testing; no trained cross-model refiner or independent evidence yet. |
| Claim C: the refiner generalizes to unseen source predictors. | v1 LOMO passes only for held-out trRosettaRNA2; RNAfold and PETfold fail. | NOT_SUPPORTED_V1 | Do not claim model agnosticism; a fixed three-model agreement feature is not evidence for an unseen fourth predictor. |
| Learned refinement generalizes across datasets. | external77 GT_CON candidate membership, all three 42/42 source conditions, and the 126-record normalized matrix are frozen and validated. | NOT_TESTED | The learned Legacy121 development gate failed; external77 was deliberately not evaluated. |
| Sparse evidence improves refinement. | None. | NOT_TESTED | Requires controlled evidence-density and noise experiments. |
| Refinement improves downstream 3D structure. | None. | NOT_TESTED | Requires a frozen 2D→3D protocol and paired downstream evaluation. |
| Highest-separation interactions are a dominant shared error source. | Legacy121 GT-derived relative-separation bins. | NOT_SUPPORTED_ON_LEGACY121 | Highest bin contains 0 FNs and only 2.07–3.47% of each model's FPs; no universal conclusion beyond Legacy121. |

Pseudoknot-aware claims are outside the current mainline and remain a separate
side track requiring predictors with explicit crossing-pair output capability.
