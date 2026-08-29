# Reboot v2 Claim–Evidence Map

Last updated: 2026-08-29

This file supplements the historical `docs/claim_evidence_map.md`. Historical claims/results remain unchanged; this map defines the claims allowed after Project Reboot v2.

| Candidate claim | Current evidence | Status | Required next evidence |
| --- | --- | --- | --- |
| Prediction-only topology/agreement is sufficient for safe source-general correction. | v1/v2/v3 development gates failed. | **NOT SUPPORTED** | Closed for current mainline; no Legacy121 v4/v5 rescue tuning. |
| Clean symbolic evidence has direct/local correction value. | Stage E1: all clean hard edits beneficial under frozen semantics; direct/local effects positive. | **SUPPORTED_DEVELOPMENT_ONLY** | Already retained as B1; not a novelty claim. |
| Clean local hard evidence propagates useful information to non-evidenced pairs. | Stage E1 non-evidenced pair set unchanged in all evaluations. | **NOT SUPPORTED / STRUCTURALLY ZERO IN B1** | R2/R4 compare useful non-local changes rather than mere propagation. |
| Global constrained refolding is a strong alternative to post-hoc reconciliation. | `/usr/bin/RNAfold` 2.4.17 hard-constraint CLI and noncrossing semantics were audited; 87/3,630 frozen pair manifests contain crossing evidence that standard ViennaRNA cannot represent. | **MANDATORY BASELINE BLOCKED BEFORE TESTING** | Resolve crossing-evidence semantics prospectively without dropping or rewriting delivered items, then run matched R2. |
| Preserving the source predictor output adds value over refolding from sequence under the same evidence. | No matched B2 comparison; formal R2 execution was not started because of the hard-constraint semantic blocker. | **PRIMARY CLAIM NOT TESTED** | Gate A after an unblocked R2/R3 comparison; use TP-preservation/FP-removal risk–utility trade-off. |
| A learned post-hoc method can estimate pair-level residual error better than non-learned baselines. | Historical v1 shows source-dependent signal but failed pooled/source-general gates; no rebooted B2/B3 comparison. | **NOT TESTED UNDER REBOOT** | R3 frozen baselines + R4 learned evaluation; AUPRC/Brier/ECE/risk–utility. |
| Learned evidence reconciliation improves FP removal at high TP preservation. | Historical E2 untrained. | **NOT TESTED** | R4; primary high-preservation operating point prospectively frozen. |
| Evidence can improve non-evidenced pairs without excessive collateral TP loss. | B1 cannot test propagation; R2 is blocked before any B2 structure is generated. | **NOT TESTED** | Unblocked R2 and later R4 non-evidenced modification precision, FP removal and TP loss. |
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
