# Project Reboot v2 — Research Decisions

Last updated: 2026-08-31

This file supplements the historical `docs/decisions.md`. Earlier decisions remain part of project history; the decisions below govern the rebooted mainline when they conflict with older planning.

## Decision — Reframe the mainline around post-hoc evidence reconciliation

**Confirmed / 已确定**

Working direction:

> **Post-hoc Evidence Reconciliation for RNA Secondary Structure Predictions**

### Reason

The historical prediction-only selective-refiner sequence did not satisfy preregistered development gates, and the literature review showed that generic pair rules, pair confidence, consensus, constrained folding and generic post-hoc QA cannot support novelty claims by themselves.

### Consequence

The main problem is now whether sparse external evidence can be reconciled with an existing predictor output while preserving already-correct source information.

---

## Decision — Global constrained refolding is a mandatory baseline

**Confirmed / 已确定**

Before any new learned evidence model is trained, the project must implement a matched global evidence-constrained refolding baseline using the same sequence and delivered evidence.

### Reason

A post-hoc method has no scientific necessity unless it can show value beyond simply refolding from sequence under the same evidence.

### Consequence

R2 precedes R4. The initial baseline should use a prospectively frozen, reproducible ViennaRNA/RNAfold hard-constraint protocol.

---

## Decision — Historical Stage E2 is superseded before training

**Confirmed / 已确定**

`evidence_guidance_stage_e2_v1` remains an immutable historical protocol/design artifact but must not be executed as the next experiment.

### Reason

Its frozen comparator set did not include the newly mandatory global constrained-refolding baseline, so its original success criteria no longer answer the strongest scientific question.

### Consequence

The architecture may be reused as a candidate starting point later, but a new R4 protocol must be frozen after R2 and R3.

---

## Decision — Pair reliability is primary output; structure correction is an application

**Confirmed / 已确定 at task level**

For each original predicted pair, the rebooted learned task estimates an error/correctness probability. The first edit policy is `KEEP / DELETE / ABSTAIN`.

### Reason

This cleanly separates quality estimation from full RNA re-prediction and supports calibrated risk control.

### Consequence

Primary rebooted evaluation includes AUPRC/Brier/ECE plus TP-preservation/FP-removal risk–utility analysis. Aggregate F1 remains important but is not the sole primary endpoint.

---

## Decision — Preserve deletion-only primary edit space

**Confirmed / 已确定**

The first rebooted mainline does not add absent pairs, reassign partners, rebuild stems, or use a decoder that creates new pairs.

### Reason

Those operations would confound post-hoc quality control with secondary-structure prediction and make the comparison to constrained refolding less interpretable.

### Consequence

Missing-pair recovery is deferred until the post-hoc reliability/correction question is established.

---

## Decision — Separate evidence into clean, noisy and real levels

**Confirmed / 已确定**

Evidence progression:

```text
E0 clean symbolic
-> E1 controlled noisy symbolic
-> E2 real experimental evidence
```

### Reason

Clean GT-derived simulated evidence tests mechanism/upper bound but cannot support claims about noisy or real experiments.

### Consequence

Real probing data are not introduced until controlled-noise robustness is established and a dedicated provenance/mapping protocol is frozen.

---

## Decision — external77 is a locked one-shot independent test

**Confirmed / 已确定**

The 42-RNA x three-source normalized external matrix remains inaccessible to development until R7.

### Reason

The project needs a genuinely independent evaluation after repeated Legacy121 development.

### Consequence

No feature, architecture, calibration, threshold or rescue decision may use external77 before the final development protocol is frozen.

---

## Decision — Do not pre-claim model agnosticism

**Confirmed / 已确定**

`Model-agnostic` and `unseen-predictor transfer` are candidate outcomes, not project assumptions.

### Reason

Historical v1-v3 evidence does not support a reliable source-general claim.

### Consequence

R6 LOMO determines whether these terms are permitted in the paper. Failure is reported as source dependence rather than repeatedly retuned on Legacy121.

---

## Decision — Use explicit Go / No-Go gates

**Confirmed / 已确定**

- **Gate A:** stop the post-hoc mainline if matched global constrained refolding dominates the relevant correction-preservation trade-off.
- **Gate B:** do not escalate learned architecture unless the simple R4 method improves FP removal over the strongest frozen non-learned baseline at a prospectively frozen high-preservation operating point and is not single-source driven.
- **Gate C:** do not claim real-evidence readiness if low controlled noise destroys safety/utility without a prospectively frozen trust mechanism.
- **Gate D:** do not claim cross-dataset generalization if the one-shot external77 result does not preserve the development effect direction.

---

## Decision — Keep historical negative results

**Confirmed / 已确定**

v1/v2/v3 failures, E1 results and historical protocol artifacts remain part of the project record.

### Reason

They constrain the next hypothesis and provide mechanistic/negative evidence.

### Consequence

Do not erase, relabel, or post-hoc retune them as successes.

---

## Decision — Keep pseudoknot and 2D->3D outside the rebooted core

**Confirmed / 已确定**

Pseudoknot-aware refinement remains a separate side track. 2D->3D validation remains an optional strengthening experiment after the 2D post-hoc task is stable.

### Consequence

Neither branch may block R2-R7 or be used to rescue a failed core claim.

## Decision — Prospective R2 crossing-evidence eligibility amendment

**Confirmed / 已确定 (2026-08-29)**

R2 remains the standard pseudoknot-free ViennaRNA baseline. The complete
delivered pair set is the sole eligibility input: noncrossing manifests are
`R2_ELIGIBLE`; any crossing relation makes the entire manifest
`R2_INELIGIBLE_CROSSING_EVIDENCE`. No crossing item is deleted, rewritten,
resampled, sequentially refolded, or replaced by a pseudoknot solver.

The deterministic audit found 3,543 eligible and 87 ineligible pair manifests
out of 3,630. Primary B0/B1/B2 comparisons use the identical eligible manifest
IDs; the existing B1 full-universe results remain immutable and a filtered
matched B1 view is generated by manifest ID only. RNA-balanced macro and
event-pooled micro aggregation, including explicit zero-coverage missing
strata, are frozen before execution.

**Consequence:** `R2_PROTOCOL_AMENDED — READY_FOR_R2_EXECUTION`. Only the
eligible matched R2 universe may now be executed; external77, learned models,
and pseudoknot branches remain locked.

---

## Decision — R2 hard-constraint environment is blocked by crossing evidence

**Confirmed / 已确定 (2026-08-29)**

The audited R2 candidate is `/usr/bin/RNAfold` 2.4.17. Its CLI expresses an
exact forced partner with matching round brackets plus `--enforceConstraint`,
and forced unpaired positions with `x`; project coordinates convert uniquely
from zero-based to ViennaRNA one-based positions by adding one. Python
ViennaRNA bindings are absent in the probed environments.

The frozen clean Legacy121 suite contains 87 of 3,630 positive-pair manifests
with mutually crossing delivered evidence pairs across 11 RNAs. Standard
ViennaRNA non-pseudoknot dynamic programming cannot express those pair sets
simultaneously. Dropping, rewriting, sequentially folding, or replacing those
constraints would change the frozen evidence semantics.

**Consequence:** R2 is `R2_PROTOCOL_BLOCKED`; no formal Legacy121 R2 benchmark,
learned training, noisy/real evidence, or external77 access is authorized until
a separate prospective decision resolves the crossing-evidence semantics.

---

## Execution finding — R2 minimum-loop constraint blocker remains unresolved

**Confirmed observation / no resolution decision selected (2026-08-31)**

The frozen R2 command was invoked for all 7,173 `R2_ELIGIBLE` realizations.
It produced 7,153 constraint-compliant PASS records. In 20 positive-pair
realizations across four RNAs, ViennaRNA 2.4.17 emitted an explicit warning
that a forced pair encloses only two nucleotides, violates the model's minimum
loop size of three nucleotides, and is therefore omitted. The output failed the
post-fold hard-constraint check exactly as required. All 87 crossing manifests
were skipped according to v1.0.1 and were not involved in this failure.

This is not a transient subprocess failure and cannot be corrected by rerunning
the same command. Excluding the 20 manifests would change the frozen comparison
universe; deleting or rewriting their evidence would change evidence semantics;
and changing the ViennaRNA minimum-loop setting would change the frozen folding
model. None of those choices is made retrospectively here.

**Consequence:** current state is
`R2_EXECUTION_PARTIAL_BLOCKED_MINIMUM_LOOP_CONSTRAINT`. Formal matched metrics,
edit/scope decompositions, interpretation, Gate A, and R3/R4 progression remain
stopped pending a separate prospective resolution. The partial execution and
blocker artifacts are retained rather than deleting or imputing failed rows.
