# Phase II P3 Minimal Structured-Baseline Implementation Plan

Status: **`PHASE2_P3_IMPLEMENTATION_PLAN_FROZEN`**

Execution: **`NOT_STARTED`**

Primary-model implementation: **`NOT_AUTHORIZED`**

## 1. Purpose

The next task, if explicitly started, may implement the smallest auditable
infrastructure needed to verify the frozen structured task. It is not permission
to implement or train the primary pair-graph trust model, run Development-v2
performance experiments, generate evidence, or access independent data.

## 2. Authorized implementation scope

Only the following are in scope for P3:

1. schema validators and hash/manifest utilities;
2. family/homology connected-component and cross-role leakage checks;
3. source-output normalization interfaces using synthetic fixtures only;
4. complete legal candidate generation without labels;
5. deterministic exact noncrossing DP and validity audit;
6. KEEP/DELETE/ADD/REPLACE extraction and component ABSTAIN mechanics;
7. the frozen edit-cost objective;
8. finite-policy risk-bound calculations on synthetic fixed fixtures; and
9. non-learned baseline interfaces/tests required by the protocol.

The implementation must start with synthetic/toy structures. Acquisition or
materialization of Development-v2 records and source predictions requires a
separate, explicit data-build authorization after license/checkpoint preflight.

## 3. Prohibited scope

- GNN, Graph Transformer, trust-network or foundation-model fine-tuning code;
- any Phase II training loop or learned scoring experiment;
- architecture/hyperparameter search;
- biological performance estimates or gate decisions;
- Legacy121 optimization beyond schema/compatibility toy audits;
- E0/E1/E2 evidence generation;
- noisy, probing or 3D experiments;
- external77 or Independent-v2 access; and
- old R5/R6/R8 execution.

## 4. Mandatory test-first order

```text
schema + provenance fixtures
-> candidate universe fixtures
-> brute-force short-sequence oracle
-> exact DP equivalence
-> edit/action accounting
-> component reversion + validity
-> synthetic risk-bound selection
-> determinism and fail-closed audit
```

No step can be bypassed to obtain a biological result faster.

## 5. Baseline contracts to expose, not yet evaluate

- `S0_NO_REFINEMENT`;
- `LOCAL_EVIDENCE_CORRECTION`;
- `GLOBAL_EVIDENCE_CONSTRAINED_REFOLDING` interface;
- `DELETION_ONLY_STRUCTURED_REFINEMENT`;
- `MINIMUM_EDIT_STRUCTURED_NO_RISK`;
- `RISK_CONTROLLED_STRUCTURED_REFINEMENT` wrapper;
- `MATCHED_EVIDENCE_MASKED`;
- `TRUST_SHUFFLED` and `RELATION_ABLATED`; and
- `CALIBRATION_THRESHOLD_EMPIRICAL`.

P3 may implement only those that are non-learned and fully specified. Any
baseline needing a learned score remains an interface/stub until a later
authorization. Stubs cannot emit claimed results.

## 6. Required completion artifacts

- source files limited to protocol infrastructure/baselines;
- unit and property tests;
- synthetic fixture manifest and hashes;
- exact DP versus exhaustive-oracle report;
- candidate-label firewall audit;
- deterministic rerun report;
- validity/fail-closed report; and
- a diff confirming no model/training/evidence/independent-data code.

All reports are software correctness artifacts, not scientific results.

## 7. P3 entry and exit gates

Entry requires the current freeze manifest to match and the four primary
predictor artifacts to pass a license/version/checkpoint preflight. Failure of a
predictor preflight stops data materialization and requires a prospective
protocol amendment; it does not permit silent replacement.

P3 implementation passes only if all synthetic exactness, validity,
determinism, accounting, leakage and fail-closed tests pass. P3 does **not** pass
the scientific `P2 STRUCTURED BASELINE` gate; that later gate requires a
separately authorized Development-v2 evaluation after model/task locks.

## 8. Next-task boundary

The only proposed next task is:

```text
IMPLEMENT_PHASE2_MINIMAL_STRUCTURED_BASELINES
```

It begins only on explicit user authorization. Until then:

```text
PHASE2_IMPLEMENTATION_NOT_AUTHORIZED
EXTERNAL77_LOCKED
```
