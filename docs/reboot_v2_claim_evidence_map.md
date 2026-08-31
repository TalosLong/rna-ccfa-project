# Reboot v2 Claim–Evidence Map

Last updated: 2026-08-31

This file supplements the historical `docs/claim_evidence_map.md`. Historical claims/results remain unchanged; this map defines the claims allowed after Project Reboot v2.

| Candidate claim | Current evidence | Status | Required next evidence |
| --- | --- | --- | --- |
| Prediction-only topology/agreement is sufficient for safe source-general correction. | v1/v2/v3 development gates failed. | **NOT SUPPORTED** | Closed for current mainline; no Legacy121 v4/v5 rescue tuning. |
| Clean symbolic evidence has direct/local correction value. | Stage E1: all clean hard edits beneficial under frozen semantics; direct/local effects positive. | **SUPPORTED_DEVELOPMENT_ONLY** | Already retained as B1; not a novelty claim. |
| Clean local hard evidence propagates useful information to non-evidenced pairs. | Stage E1 non-evidenced pair set unchanged in all evaluations. | **NOT SUPPORTED / STRUCTURALLY ZERO IN B1** | R2/R4 compare useful non-local changes rather than mere propagation. |
| Global constrained refolding is a strong alternative to post-hoc reconciliation. | The fixed command handled all 7,173 frozen eligible realizations: 7,153 passed and 20 failed because ViennaRNA omitted forced pairs that violate its minimum loop size; 87 crossing manifests were skipped as frozen. No performance summary was computed. | **MANDATORY BASELINE PARTIAL / BLOCKED** | Prospectively resolve the minimum-loop representability blocker, restore complete matched constraint-compliant coverage, then run the frozen analysis. |
| Preserving the source predictor output adds value over refolding from sequence under the same evidence. | B2 structures are incomplete for 20 frozen eligible manifests and formal matched B0/B1/B2 analysis was intentionally not started. | **PRIMARY CLAIM NOT TESTED** | Gate A only after an authorized blocker resolution and complete matched analysis; use the frozen TP-preservation/FP-removal trade-off. |
| A learned post-hoc method can estimate pair-level residual error better than non-learned baselines. | Historical v1 shows source-dependent signal but failed pooled/source-general gates; no rebooted B2/B3 comparison. | **NOT TESTED UNDER REBOOT** | R3 frozen baselines + R4 learned evaluation; AUPRC/Brier/ECE/risk–utility. |
| Learned evidence reconciliation improves FP removal at high TP preservation. | Historical E2 untrained. | **NOT TESTED** | R4; primary high-preservation operating point prospectively frozen. |
| Evidence can improve non-evidenced pairs without excessive collateral TP loss. | B1 cannot test propagation; partial R2 outputs were not analyzed because 20 eligible realizations failed hard-constraint satisfaction. | **NOT TESTED** | Complete R2 after prospective blocker resolution, then report frozen non-evidenced modification precision, FP removal and TP loss. |
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
