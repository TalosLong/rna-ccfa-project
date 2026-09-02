# Reboot v2 Claim–Evidence Map

Last updated: 2026-09-02

This file supplements the historical `docs/claim_evidence_map.md`. Historical claims/results remain unchanged; this map defines the claims allowed after Project Reboot v2.

| Candidate claim | Current evidence | Status | Required next evidence |
| --- | --- | --- | --- |
| Prediction-only topology/agreement is sufficient for safe source-general correction. | v1/v2/v3 development gates failed. | **NOT SUPPORTED** | Closed for current mainline; no Legacy121 v4/v5 rescue tuning. |
| Clean symbolic evidence has direct/local correction value. | Stage E1: all clean hard edits beneficial under frozen semantics; direct/local effects positive. | **SUPPORTED_DEVELOPMENT_ONLY** | Already retained as B1; not a novelty claim. |
| Clean local hard evidence propagates useful information to non-evidenced pairs. | Stage E1 non-evidenced pair set unchanged in all evaluations. | **NOT SUPPORTED / STRUCTURALLY ZERO IN B1** | R2/R4 compare useful non-local changes rather than mere propagation. |
| Global constrained refolding is a strong alternative to post-hoc reconciliation. | R2 v1.0.2 completed 7,153/7,153 amended eligible outputs at 100% constraint satisfaction. Overall B2 Macro/Micro F1 was 0.924648/0.904747 versus 0.889352/0.872422 for matched B1 and 0.878635/0.861068 for B0. | **SUPPORTED AS STRONG CLASSICAL BASELINE** | Freeze B2 as the mandatory future Gate A comparator; do not infer learned-method performance. |
| Preserving the source predictor output adds value over refolding from sequence under the same evidence. | B2 removed 32,433 original FP and added 11,042 new TP, but also lost 4,752 original TP and added 10,823 new FP; Macro/Micro TP preservation was 0.975358/0.981767. This supports a plausible high-preservation question but does not show that a post-hoc method can exploit it. | **POSTHOC_HEADROOM_PLAUSIBLE / GATE_A_DEFERRED_R4_REQUIRED** | Gate A only after a future prospectively frozen R4 is compared against B2 on the frozen correction-preservation trade-off. Do not state PASS or expected R4 superiority. |
| The frozen R3 suite prospectively defines fair reliability comparators. | Track P and Track E, original-pair labels, AUPRC, calibration restrictions, deletion-only risk–utility, RNA-balanced aggregation, validation-only `TP_preservation >= 0.99` selection, and strongest-comparator rules were frozen before execution. RNAfold 2.4.17 BPP CLI feasibility passed on a toy only. | **PROTOCOL SUPPORTED / PERFORMANCE NOT YET TESTED** | Execute the frozen R3 suite on Legacy121/R2 matched inputs without training, retuning, external77, or R4. |
| A learned post-hoc method can estimate pair-level residual error better than frozen no-new-training comparators. | Historical v1 shows source-dependent signal but failed pooled/source-general gates; R3 protocol is frozen but formal R3 baseline performance has not been run. | **NOT TESTED UNDER REBOOT** | Complete R3 and freeze both strongest comparator records, then perform a prospectively frozen R4 learned evaluation. |
| Learned evidence reconciliation improves FP removal at high TP preservation. | Historical E2 untrained. | **NOT TESTED** | R4; primary high-preservation operating point prospectively frozen. |
| Evidence can improve non-evidenced pairs without excessive collateral TP loss. | R2 B2 non-evidenced propagation was net beneficial (36,027 beneficial versus 15,575 harmful changes; Micro modification precision 0.698171), but included 4,752 lost TP and 10,823 new FP. | **MIXED DEVELOPMENT EVIDENCE** | Future R4 must improve the correction-preservation trade-off; noisy and real-evidence claims require R5/R8. |
| The method is model-agnostic / transfers to unseen predictors. | v1 LOMO did not reproduce across all three predictors. | **NOT SUPPORTED CURRENTLY** | R6 LOMO under rebooted method; claim only if supported. |
| The method generalizes across datasets. | external77 126/126 independent matrix is prepared but intentionally untested by learned methods. | **NOT TESTED** | R7 one-shot locked independent evaluation. |
| The method is robust to noisy evidence. | Corruption mechanism exists but full rebooted noisy evaluation not run. | **NOT TESTED** | R5 controlled noise with Gate C. |
| The method works with real experimental evidence. | No rebooted real-modality dataset/protocol frozen. | **NOT TESTED** | R8 provenance/mapping audit + matched classical/post-hoc comparison. |
| Refined/reconciled 2D improves downstream 3D. | None. | **NOT TESTED** | Optional frozen 2D->3D paired experiment after stable 2D method. |

## Claims explicitly excluded as novelty

The project must not claim novelty for any of the following in isolation:

- RNA canonical pairing, stem, stacking or loop heuristics;
- isolated-pair / short-stem cleanup;
- pair probability/confidence;
- thermodynamic + evolutionary evidence fusion;
- multi-predictor consensus;
- evidence-constrained global folding;
- generic post-hoc pair-level QA as an abstract ML task;
- benchmark normalization/evaluator infrastructure.

## Candidate paper-level claim if R2-R7 succeed

> A post-hoc RNA secondary-structure evidence-reconciliation framework can exploit sparse external evidence while preserving useful source-predictor information, yielding a better correction–preservation trade-off than both local evidence enforcement and matched global evidence-constrained refolding, with calibrated pair-level reliability and reproducible independent evaluation.

Every clause above is conditional and must be removed if the corresponding experiment fails.
