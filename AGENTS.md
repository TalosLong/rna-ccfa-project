# Codex Collaboration Rules

These instructions apply to the entire repository.

## Authoritative State

Before substantial work, read:

- `CONTEXT.md`;
- `STATUS.md`;
- `docs/project_reboot_v2.md`;
- `docs/reboot_v2_decisions.md`;
- `docs/reboot_v2_claim_evidence_map.md`;
- `docs/conservative_reconciliation_protocol.md`;
- `docs/conservative_reconciliation_implementation_plan.md`;
- `plan/research_plan.md`;
- `plan/timeline.md`;
- `tasks/TODO.md`;
- historical `docs/decisions.md` when older decisions/provenance are relevant.

Treat Confirmed/Frozen content as a constraint. Treat Candidate content as unconfirmed and do not present it as a fixed method, result, or paper claim.

When a Reboot v2 decision conflicts with older planning, the Reboot v2 documents govern the current mainline; historical files remain provenance and must not be rewritten to erase prior decisions.

Do not invent experimental results, alter raw historical data, or reinterpret failed gates as successes.

## Reboot v2 Execution Rule

The current mainline is:

> **Post-hoc Evidence Reconciliation for RNA Secondary Structure Predictions**

The historical `evidence_guidance_stage_e2_v1` protocol is **frozen but superseded before training**.

**Do not implement or run historical Stage E2 training.**

Current authorized sequence:

```text
R1 documentation freeze
-> R2 global evidence-constrained refolding baseline
-> R3 reliability baseline suite
-> R3 scientific interpretation
-> freeze new R4 protocol
-> implement and execute frozen R4 learned clean evidence reconciliation
-> R4 postmortem and future-path decision
-> freeze a new prospective conservative-reconciliation protocol
-> implement and execute frozen conservative-reconciliation development only
-> consolidate the bounded paper story after the conservative development gate failure
```

R2/R3 and the frozen R4 ERN/B4 execution are complete. R4 is
`R4_GATE_B_FAIL` because event-pooled TP preservation was below 0.99. Gate A is
`GATE_A_PASS_POSTHOC_NONDOMINATED`, but it does not override Gate B. No R5,
external77, real-evidence, or rescue execution is currently authorized.

The frozen-output R4 postmortem and exact Conservative Evidence Reconciliation
(CER) Legacy121 development experiment are complete. Current status is
`CONSERVATIVE_RECONCILIATION_DEVELOPMENT_COMPLETE` and
`CONSERVATIVE_DEV_GATE_FAIL`. The only authorized next task is
`PAPER_STORY_AND_RESULTS_CONSOLIDATION`. R5 and external evaluation remain
unauthorized.

## R4 Constraints

The frozen R2/R3 inputs, universes, comparators, thresholds, metrics, and
results are read-only. R4 must:

- use original predicted pairs as the primary unit and remain deletion-only;
- keep RNA as the biological split unit with no source-record leakage;
- use only the frozen feature allowlist and source-independent simple ERN;
- run the exactly matched evidence-masked B4 control;
- fit preprocessing on training data and select checkpoint, calibration, and
  threshold on validation data only;
- apply one locked held-out policy without rescue thresholds;
- report every channel/fold/seed and all mandatory reliability, utility,
  decomposition, efficiency, and source-wise outputs.

Frozen Gate B is conjunctive:

```text
event-pooled TP_preservation       >= 0.99
RNA-balanced TP_preservation       >= 0.99
RNA-balanced FP_removal            >  0.489748
event-pooled FP_removal            >  0.347816
```

Success also requires improvement not driven by one predictor source. Paired
B4 is a mandatory separate evidence-attribution control, not an additional
numerical Gate B bar. Do not change these criteria or automatically escalate
architecture after held-out results. Completed R4 established
`GATE_A_PASS_POSTHOC_NONDOMINATED` and `R4_GATE_B_FAIL`.

Do not begin R5 noise, real SHAPE/DMS/PARS work, or R7 external evaluation.
Do not rescue R4 by moving thresholds, choosing seeds/channels, adding
features, or increasing model complexity.

## Post-R4 Development Boundary

Legacy121 R4 held-out outcomes have been observed and used for post-hoc
diagnosis. Any future method designed from those findings must treat Legacy121
as development/hypothesis-generation data, not pristine confirmation. No
Legacy121-only result may be promoted as independent validation.

external77 remains unopened and one-shot. Before any future access, the full
method, feature/action contract, calibration, thresholds, gates, and analysis
plan must be prospectively frozen. external77 may never be used for rescue.

## Conservative Reconciliation Constraints

The frozen CER protocol uses only one primary mechanism: Context-Corroborated
Evidence Gate (CCEG). Preserve its contract exactly:

- original predicted pair is the unit and edits are deletion-only;
- DIRECT positive-pair support is KEEP;
- LOCAL_CONFLICT is the explicit E1-compatible DELETE;
- NON_EVIDENCED DELETE requires both calibrated usable-evidence and exactly
  evidence-masked candidate-context risks at or above the same locked threshold;
- branch disagreement is ABSTAIN and leaves the original pair unchanged;
- the exact R4 80/17/8/4 feature allowlist and simple ERN branch architecture
  are reused without additions or capacity escalation;
- `CER_EVIDENCE_MASKED` matches branches, capacity, optimization, splits,
  calibration, and action mechanics except usable evidence;
- all 200 condition x branch x channel x fold x seed runs are required;
- Legacy121 roles are development train/validation/assessment, never
  independent confirmation;
- apply `CONSERVATIVE_DEV_GATE` exactly once after the complete sealed matrix.

Do not convert postmortem separation, P2/P4, risk, risk-difference, boundary,
density, source, or channel strata into a hard-coded rule. Do not reuse an R4
threshold/calibrator/checkpoint as a fitted CER artifact. A failed development
gate cannot be rescued through another threshold, seed/channel selection,
feature, or larger architecture.

CER failed the conjunctive development gate because NON_EVIDENCED TP
preservation was lower than the matched masked control in both aggregations.
Do not rescue with an alternate CCEG, threshold movement, seed/channel
selection, new feature, or larger architecture. The only authorized next task
is `PAPER_STORY_AND_RESULTS_CONSOLIDATION`; R5, R6, R7, external77, noisy
evidence, and real evidence remain unauthorized.

## Locked Independent Data

The external77-derived 42-RNA x three-source normalized matrix is complete and is a **locked independent test**.

Do not access external77 for:

- feature selection;
- architecture selection;
- calibration;
- threshold tuning;
- rescue analysis;
- intermediate Go/No-Go decisions.

It is opened only at R7 after the development protocol is frozen.

## Historical Results

Preserve all historical outputs and decisions, including:

- v1 `DEVELOPMENT_GATE_FAIL`;
- v2 `V2_DEVELOPMENT_GATE_FAIL`;
- v3 `V3_DEVELOPMENT_GATE_FAIL`;
- Stage E1 direct/local utility and zero non-evidenced effect.

Do not retune Legacy121 v4/v5 rules or thresholds to rescue the closed prediction-only cross-model mainline.

## Model Escalation Rule

Do not introduce a Transformer, GNN, foundation model, new large predictor, or substantially more complex architecture merely to rescue a failed simple baseline.

A simple learned method must first demonstrate value beyond the strongest frozen non-learned baselines at the prospectively defined risk/preservation operating point.

## Progress Tracking

- Update `tasks/TODO.md` whenever a listed task is completed.
- Update `STATUS.md` when project stage, blocker, finding, gate, or immediate next action changes.
- Record new reboot-level durable decisions in `docs/reboot_v2_decisions.md`; keep `docs/decisions.md` as historical decision provenance.
- Update `docs/reboot_v2_claim_evidence_map.md` when a reboot claim's evidence state changes; keep the historical claim map unchanged as provenance unless a correction is necessary.
- Report results before changing a frozen research protocol unless the protocol itself specifies the gate response.
- Preserve raw, normalized, per-sample and aggregate artifacts separately.

## Reproducibility and Leakage

- Use frozen manifests and explicit IDs; do not infer benchmark membership from directory contents.
- Keep train/validation/test or development/independent roles explicit.
- Compute preprocessing/calibration parameters from allowed development partitions only.
- Preserve exact command/version/configuration provenance for external tools.
- Do not use GT-derived information at inference except explicitly delivered simulated evidence in a frozen evidence experiment.
- Do not convert real probing evidence into GT labels without a prospectively frozen mapping.

## Git Synchronization

After completing and verifying each coherent task:

1. inspect `git diff` and `git status`;
2. run relevant tests/checks;
3. create a descriptive commit;
4. push to `origin/main` in the same Codex task.

Do not commit incomplete work merely to show activity. For long work, commit only independently useful and internally consistent milestones.

Never commit secrets, private keys, credentials, local environments, caches, large generated artifacts, or unrelated user changes.

Do not rewrite published history or force-push unless explicitly requested.

If push is blocked, preserve the local commit and report the exact blocker.

## Commit Messages

Use concise imperative subjects that describe the completed result. Group documentation, implementation, tests, and generated outputs only when they form one coherent milestone.
