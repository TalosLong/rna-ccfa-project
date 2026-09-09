# Phase II Roadmap Revision — 2026-09-09

Status: **`PHASE2_ROADMAP_REVISED`**

Current milestone: **`M0_FEASIBILITY_AUDIT_COMPLETE_WITH_BLOCKERS`**

Next proposed task: **`RESOLVE_PHASE2_E0_ABSTENTION_PROTOCOL_CONFLICT`**

This document adopts the revised M0--M6 sequence from
`RNA_Research_Plan_Revised_2026-09-09.md`. It changes project ordering, not
scientific outcomes. `PHASE2_DTP_V1.0`, `PHASE2_DECODER_V1.0`, the freeze
manifest, `alpha=0.10`, `delta=0.05`, the Phase I failures, and every data lock
remain unchanged.

## 1. Why the sequence changes

The previous roadmap placed P3 minimal software immediately before primary
model work. The revised roadmap inserts two distinct decisions:

1. software and mathematical correctness of the frozen structured machinery;
2. biological usefulness of ADD/REPLACE under a separately frozen development
   comparison.

Passing the first is not evidence for the second. A learned propagation model
is justified only if the structured action space shows useful headroom and the
data, source, evidence, and risk-control routes are operational.

## 2. M0--M6 execution roadmap

The windows are planning estimates for one primary researcher and are not
deadlines or success promises. Later milestones require explicit authorization.

| Milestone | Window | Goal and allowed input roles | Required output | Continue condition | Failure or blocker handling |
| --- | --- | --- | --- | --- | --- |
| **M0 feasibility and protocol audit** | Week 1 | Documents, formulas, synthetic counterexamples, public source metadata; no biological values | Synchronized roadmap, risk-budget audit, E0/ABSTAIN conflict record, DP/statistical applicability audit, one real-evidence source route | Every M1 entry requirement is either executable or explicitly blocked | Draft a prospective amendment before implementation; never reinterpret the old freeze |
| **M1 data and minimal software foundation** | Weeks 2--3 | Synthetic fixtures for software; biological metadata only after separate authorization; five roles remain disjoint | Development-v2 manifest and hashes, leakage audit, four-predictor deployment manifests, exact candidate/decoder/edit/ABSTAIN/risk infrastructure | Reproducible sources, role isolation, exact software correctness, and resolved E0/fallback semantics | Fix protocol/data/tool blockers; do not silently delete a failed source or merge roles |
| **M2 structured-baseline scientific validation** | Weeks 4--5 | Only prospectively allowed Development-v2 roles; no independent set | Matched S0, local evidence, constrained refolding, deletion-only and full minimum-edit comparisons; prespecified uncertainty and utility/coverage gates | ADD/REPLACE provides additional net correction value at comparable harm and useful coverage | Narrow the project to deletion/local correction; do not automatically escalate architecture |
| **M3 simple learned propagation** | Weeks 6--8 | TRAIN for fitting; MODEL_SELECTION for architecture/hyperparameters; no calibration/assessment reuse | One simple scorer plus evidence-masked, trust-shuffled, relation-ablated, local and threshold/no-risk controls | Beats the strongest matched simple baseline and attributes non-local gain to allowed evidence paths | Preserve a negative result and revisit the task; do not rescue by stacking modules |
| **M4 development robustness and policy lock** | Weeks 9--10 | TRAIN/MODEL_SELECTION only, under their frozen roles | Controlled-noise and source-transfer development audits, risk/coverage readiness decision, frozen model/policy family/evidence processing/analysis plan | Prespecified utility, harm, coverage and transfer conditions are met; formal assumptions remain defensible | Restrict claims or prospectively select an empirical route; do not change bounds after outcomes |
| **M5 one-shot confirmation** | Weeks 11--12 | After the M4 lock: SCORE_CALIBRATION, then RISK_CALIBRATION, then one-use DEVELOPMENT_ASSESSMENT, followed by sealed Independent-v2/real-evidence confirmation | Locked calibration, one-shot development assessment and independent confirmation package | Prespecified conclusions hold under the locked policy | Report unsupported claims and stop; never tune on confirmation data |
| **M6 writing and optional downstream validation** | Weeks 13--16 | Completed, claim-eligible artifacts only; optional 3D requires a separate freeze and budget | Manuscript/reproduction package and, only if justified, limited paired 2D-to-3D study | Every claim maps to eligible evidence and limitations are explicit | Narrow scope/venue; omit unsupported 3D or generalization claims |

## 3. Mapping from the older P roadmap

The older P0--P2 work remains historical completed design work. Its labels are
not erased. The forward mapping is:

| Existing item | Revised placement | State |
| --- | --- | --- |
| P0 literature/novelty audit | prerequisite to M0 | complete |
| P1/P2 dataset/task design freeze | audited input to M0/M1 | frozen v1.0; a conflict now requires prospective resolution |
| P3 minimal structured baselines | M1 software-correctness work | not started; no longer the immediate task |
| P2 structured-baseline performance gate in older prose | M2 biological/scientific validation | not run and not authorized |
| P4 learned primary model | M3, conditional on M2 | not authorized |
| noise, transfer, risk lock | M4 | not authorized |
| independent and real-evidence confirmation | M5 | not authorized |
| manuscript/optional 3D | M6 | not authorized |

In particular:

```text
P3 software pass != M2 scientific value pass
M2 scientific value pass != M3 learned-model success
M4 development readiness != M5 independent confirmation
```

## 4. Current M0 outcome

The detailed evidence is in `docs/phase2_feasibility_audit.md`.

- The frozen Hoeffding calculation is internally consistent, but 240 clusters
  is useful only near zero empirical HarmRate. Exact post-filter, post-component
  role counts are **`UNKNOWN`** until an authorized data build.
- Exact interval DP is applicable only to fixed additive pair scores, additive
  symmetric-difference edit cost, and the frozen noncrossing constraints. It
  does not make an arbitrary higher-order neural objective exactly solvable.
- A valid E0 pair absent from `S0` yields a direct contradiction between
  mandatory-E0 satisfaction and unconditional component/RNA fallback to `S0`.
  This is a protocol blocker, not an implementation choice.
- RMDB-to-SHAPE is a plausible metadata route, but no eligible cohort or exact
  snapshot is frozen. Entry-level conditions, sequence/reference concordance,
  missingness, replicates and role assignment require a later pre-value audit.
- A limited local artifact observation found RNAfold 2.4.17 rather than frozen
  2.7.2 and did not find the three learned primary packages in the active
  Python environment. This is not the formal M1 source-panel preflight.

## 5. Authorization and immediate dependency

No Phase II implementation is authorized by this planning revision. Before M1
P3 work begins, a prospective versioned amendment must resolve the E0/ABSTAIN
and fallback semantics, update every affected contract together, and publish a
new manifest. It must be decided without biological performance results.

The single next proposed task is therefore:

```text
RESOLVE_PHASE2_E0_ABSTENTION_PROTOCOL_CONFLICT
```

Its scope is protocol reasoning and a prospective amendment only. It does not
authorize source prediction, Development-v2 materialization, P3 code, a primary
model, training, E0/E1/E2 generation, real evidence, Independent-v2,
external77, or 3D.
