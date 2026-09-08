# Project Reboot v2 — Research Decisions

Last updated: 2026-09-08

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

## Historical execution finding — R2 minimum-loop constraint blocker

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

**Historical consequence:** the state became
`R2_EXECUTION_PARTIAL_BLOCKED_MINIMUM_LOOP_CONSTRAINT`. Formal matched metrics
remained stopped until the prospective v1.0.2 decision below. The partial
execution and blocker artifacts remain retained rather than deleted or
rewritten.

---

## Decision — Prospective R2 minimum-loop eligibility amendment v1.0.2

**Confirmed / 已确定 (2026-08-31, before formal R2 metrics)**

R2 continues to mean standard ViennaRNA 2.4.17 global hard-constrained MFE
refolding with `/usr/bin/RNAfold --noPS -C --enforceConstraint`. A complete
positive-pair manifest is solver-capability eligible only when its delivered
pairs are noncrossing and every exact pair satisfies `j-i>3`. Crossing and
minimum-loop flags are computed independently from coordinates. Whole
ineligible manifests are excluded without deleting, weakening, replacing, or
resampling evidence and without changing ViennaRNA settings.

The deterministic audit found 3,523 eligible pair manifests, 87
crossing-ineligible manifests, and 20 minimum-loop-ineligible manifests, with
no overlap; all 3,630 unpaired manifests remain eligible. The matched B0/B1/B2
universe was refrozen by manifest ID before formal summarization.

**Consequence:** `R2_PROTOCOL_AMENDED_V1_0_2 — READY_TO_RESUME_R2_EXECUTION`.
Previously generated outputs may be reused only after complete row-level
provenance and constraint validation.

---

## Result — R2 global constrained-refolding baseline complete

**Confirmed / 已确定 (2026-08-31)**

All 7,153 v1.0.2-eligible historical PASS outputs satisfied manifest,
sequence/evidence, constraint, command/config, parser, output-hash, and hard-
constraint checks. No new RNAfold calls were required; all 107 capability-
ineligible manifests were excluded from the metric universe and their
historical provenance was preserved.

On the complete matched universe, overall Macro/Micro F1 was
0.878635/0.861068 for B0, 0.889352/0.872422 for B1, and
0.924648/0.904747 for B2. B2 had Macro/Micro TP preservation
0.975358/0.981767, FP removal 0.775728/0.645883, and modification precision
0.824449/0.736240. Non-evidenced propagation was net beneficial but included
material harm.

**Consequence:** state is `R2_GLOBAL_CONSTRAINED_REFOLDING_COMPLETE` and next
state is `READY_FOR_R2_INTERPRETATION_AND_R3_PROTOCOL`. B2 is frozen as the
future Gate A comparator. Gate A is not decided because R4 does not yet exist,
and R3 is not started automatically.

---

## Decision — Freeze R2 interpretation as plausible post-hoc headroom

**Confirmed / 已确定 (2026-09-02)**

B2 is a strong mandatory comparator: its overall Macro/Micro F1 of
0.924648/0.904747 exceeded B1 and B0 under frozen clean symbolic evidence. It
is not preservation-safe: Macro/Micro TP preservation was
0.975358/0.981767, with 4,752 lost original TP and 10,823 new FP.
NON_EVIDENCED propagation was net useful but imperfect, with 36,027 beneficial
and 15,575 harmful modifications and 0.698171 Micro modification precision.

**Interpretation:** `POSTHOC_HEADROOM_PLAUSIBLE`. B2 obtains strong correction
but causes non-negligible collateral damage. The future question is whether a
pair-selective deletion-only method can retain useful FP removal at
`TP_preservation >= 0.99`.

**Consequence:** Gate A is `GATE_A_DEFERRED_R4_REQUIRED`, neither PASS nor FAIL.
No prospective post-hoc superiority claim over B2 is permitted.

---

## Decision — Freeze separate R3 prediction-only and evidence-conditioned tracks

**Confirmed / 已确定 (2026-09-02, before R3 execution)**

R3 evaluates only original predicted pairs with `DELETE`/FP as the positive
label. Track P receives no delivered evidence. Track E uses exactly the clean
R2 evidence realization and the v1.0.2 matched universe: 3,523 pair manifests
and 3,630 unpaired manifests. Missing GT pairs are excluded because the primary
task is deletion-only.

Track P freezes P0 training prevalence, P1 authoritative historical v1
source-agnostic raw score, P2 exact cross-model support with risk `2-support`,
P3 historical `V3_VETO2_FIXED`, and P4 sequence-only RNAfold thermodynamic BPP.
Track E freezes E1 Stage E1 local evidence-conflict risk and E2 B2
survival/disagreement risk. No combined score is frozen in R3 v1, and no
historical model may be retrained or retuned.

**Consequence:** Track P and Track E must produce separate strongest-comparator
records, and future R4 must compare against both.

---

## Decision — Freeze R3 risk-control and aggregation semantics

**Confirmed / 已确定 (2026-09-02, before R3 execution)**

AUPRC with `DELETE`/FP positive is the primary discrimination metric; AUROC is
secondary and positive prevalence is always reported. R3 simulates deletion
only and plots `1-TP_preservation` against `FP_removal`. Continuous/ordinal
thresholds are selected on validation data only. Eligibility requires both
event-pooled and RNA-balanced validation TP preservation at least 0.99; the
selector then maximizes RNA-balanced FP removal, followed by modification
precision and conservative tie-breaks.

Event-pooled pair-realization and RNA-balanced summaries are both mandatory.
RNA is the biological cluster/unit for any final significance test; repeated
evidence contexts, sources, densities, seeds, and model seeds are not
independent biological samples.

**Consequence:** strongest Track P and Track E comparators are selected first by
highest RNA-balanced FP removal at the frozen safety point, then modification
precision, then AUPRC. Binary baselines retain their fixed operating point and
are never altered to force 0.99 preservation.

---

## Decision — RNAfold BPP is feasible in the frozen environment

**Confirmed / 已确定 (2026-09-02, interface audit only)**

`/usr/bin/RNAfold` 2.4.17 with
`--noPS --partfunc=1 --bppmThreshold=0 --temp=37 --dangles=2` emitted a complete,
repeatable, parseable upper-triangle `ubox` matrix on a toy sequence. The third
field is `sqrt(p)`, indices are one-based, and no Python RNA binding or software
installation is required.

**Consequence:** status is `R3_BPP_BASELINE_FEASIBLE_WITH_FROZEN_CLI`. P4 will
apply the same sequence-only thermodynamic probability to original pairs from
all three sources. It is not an empirically correctness-calibrated probability.
Formal Legacy121 BPP metrics remain unexecuted.

---

## Decision — R3 protocol is frozen before execution

**Confirmed / 已确定 (2026-09-02)**

`docs/reliability_baseline_r3_protocol.md` and
`docs/reliability_baseline_r3_implementation_plan.md` freeze the scientific
question, labels, units, baselines, universes, splits, metrics, calibration
restrictions, risk–utility analysis, high-preservation selector, leakage
controls, artifacts, and completion criteria.

**Consequence:** state is `R3_PROTOCOL_FROZEN` and
`READY_FOR_R3_EXECUTION`. This does not mean R3 is complete and does not
authorize R4 or learned training.

---

## Decision — Prospective R3 ECE calibration amendment

**Confirmed / 已确定 (2026-09-03, before any Legacy121 R3 performance number)**

R3 ECE uses ten immutable equal-width bins `[0,.1),...,[.9,1]` on DELETE-risk
scores. Empty bins remain explicit with zero contribution and NA empirical
statistics. Event-pooled ECE bins all events directly; RNA-balanced ECE first
computes ECE within each RNA and then gives defined RNAs equal weight. Only P0,
P1, and P4 are calibration-eligible.

**Consequence:** `R3_CALIBRATION_AMENDMENT_FROZEN` and
`READY_TO_RESUME_R3_EXECUTION`. No baseline, score, threshold, split,
universe, or other metric changed.

---

## Result — R3 Pair-Reliability Baseline Suite complete

**Confirmed / 已确定 (2026-09-03)**

All frozen P0--P4 and E1/E2 baselines completed. Track P contained 5,290
original predicted pairs across 121 RNAs and three sources. Track E contained
3,523 pair and 3,630 unpaired eligible manifests and 310,838 original
pair-realizations per baseline. Integrity, BPP, historical-score, manifest,
threshold, calibration, and leakage gates passed.

P3 `V3_VETO2_FIXED` is
`STRONGEST_R3_PREDICTION_ONLY_BASELINE`: RNA-balanced FP removal was 0.489748
at TP preservation 0.997588, modification precision 0.965504, and coverage
0.055930. It is flagged `SOURCE_DEPENDENT_COMPARATOR`. E1 local conflict is
`STRONGEST_R3_EVIDENCE_CONDITIONED_BASELINE`: RNA-balanced FP removal was
0.142946 at TP preservation 1.0, modification precision 1.0, and coverage
0.018623.

P4 BPP had the highest prediction-only AUPRC but failed held-out RNA-balanced
preservation; E2 B2 disagreement was strong but reproduced B2's below-0.99
preservation. Historical v1/v3 decisions remain failures under their original
gates.

**Consequence:** state is `R3_RELIABILITY_BASELINE_SUITE_COMPLETE` and
`READY_FOR_R3_INTERPRETATION_AND_R4_PROTOCOL_DECISION`. Gate A remains
`GATE_A_DEFERRED_R4_REQUIRED`; R4 has not started.

---

## Interpretation — R3 supports a bounded R4 test, not a safety claim

**Confirmed / 已确定 (2026-09-07, frozen R3 results only)**

R3 establishes that prediction-only context contains residual-error signal,
but P4's strong discrimination did not produce a safe held-out operating point.
P3 `V3_VETO2_FIXED` is the frozen high-preservation prediction-only comparator
and is materially source-dependent. E1 local conflict is perfectly precise but
coverage-limited. E2/B2 demonstrates broad evidence-related correction signal
while retaining below-0.99 preservation and full-refold collateral edits.

**Consequence:** simple learned evidence reconciliation has reasonable but
untested headroom. State is `R3_INTERPRETATION_COMPLETE`; Gate A remains
`GATE_A_DEFERRED_R4_REQUIRED`, neither PASS nor FAIL.

---

## Decision — Freeze the simple ERN R4 protocol before execution

**Confirmed / 已确定 (2026-09-07, before R4 implementation or training)**

`docs/clean_learned_evidence_reconciliation_r4_protocol.md` freezes original
predicted pairs as candidates, DELETE/FP as the positive label, deletion-only
edits, inference-time prediction/evidence features, separate permutation-
invariant evidence encoders, a simple DeepSets-style ERN, matched
evidence-masked B4, RNA-grouped splits, validation-only calibration and
threshold selection, KEEP/DELETE/ABSTAIN, mandatory baselines/metrics, and full
provenance and leakage controls.

Gate B requires all of: event-pooled and RNA-balanced TP preservation at least
0.99, RNA-balanced FP removal strictly above 0.489748, event-pooled FP removal
strictly above 0.347816, and improvement over P3 in at least two sources
including RNAfold or PETfold. E1 at RNA-balanced FP removal 0.142946 and TP
preservation 1.0 remains a mandatory comparison. Paired B4 is a mandatory
separate evidence-attribution analysis, not an additional numerical Gate B
bar. A failure cannot be rescued automatically with a larger architecture.

**Consequence:** state is `R4_PROTOCOL_FROZEN` and `R4_NOT_EXECUTED`. The next
task is `IMPLEMENT_AND_EXECUTE_FROZEN_R4`. Historical E2 is not executed;
external77, noisy evidence, and real SHAPE/DMS/PARS remain out of scope.

---

## Result — Frozen R4 ERN/B4 experiment complete

**Confirmed / 已确定 (2026-09-07)**

All 100 frozen condition x channel x fold x seed runs completed, followed by
100 validation-only monotone Platt calibrations and threshold locks and 100
one-shot held-out evaluations. The primary combined ERN five-seed mean had
event/RNA TP preservation 0.989682/0.991936, FP removal 0.475531/0.660806,
and modification precision 0.898838/0.944218. RNA-balanced FP-removal
improvement over P3 was positive in all three predictor sources.

Matched B4 had event/RNA TP preservation 0.991886/0.993570 and FP removal
0.386622/0.615236. ERN improved AUPRC, Brier, ECE, FP removal, and delta F1
over B4, but reduced both preservation summaries. Evidence therefore supplies
incremental learned signal without satisfying the frozen safe-policy gate.

**Consequence:** Gate B is `R4_GATE_B_FAIL` because event TP preservation was
strictly below 0.99; its other numerical and source-consistency conditions
passed. No seed/channel selection, threshold rescue, retraining, feature
change, or architecture escalation is authorized.

---

## Decision — Gate A passes bounded non-dominance; R5 is not authorized

**Confirmed / 已确定 (2026-09-07, after complete frozen R4)**

B2 remains the `FULL_REFOLD_REFERENCE`. B2 removes more FP than ERN
(event/RNA 0.645883/0.775728 versus 0.475531/0.660806), while ERN preserves
more original TP (0.989682/0.991936 versus 0.981767/0.975358), has higher
modification precision, and adds no pairs. Neither method dominates the
correction-preservation plane; delta F1 is not used alone.

**Consequence:** Gate A is `GATE_A_PASS_POSTHOC_NONDOMINATED`, a bounded
statement that the post-hoc operating region remains distinct. It does not
override `R4_GATE_B_FAIL`. Project state is `R4_COMPLETE`, and R5, external77,
and real-evidence execution are not authorized. Any continuation requires a
new prospective decision and cannot be a rescue of the observed R4 result.

---

## Decision — R4 failure localizes to unsafe non-evidenced propagation

**Confirmed / 已确定 (2026-09-07, post-hoc diagnostic only)**

The frozen ERN-versus-B4 held-out decisions were decomposed without retraining,
recalibration, threshold changes, or seed/channel selection. Of the mean
4,464.6 additional FP removals attributable to usable evidence, 2,500.6
(56.0%) occurred in perfectly precise `LOCAL_CONFLICT` and 1,964.0 (44.0%) in
`NON_EVIDENCED`. `NON_EVIDENCED` also contributed all material additional TP
loss (+696.2 per seed); DIRECT evidence protected 122.0 TP relative to B4,
leaving a net +574.2 lost TP. Source-level benefit and loss were distributed
across RNAfold, PETfold, and trRosettaRNA2.

The observed event TP preservation was 0.9896824148 against the frozen
0.990000 requirement, a gap of approximately 0.000318 or a descriptive scale
of 82.77 excess lost-TP events per seed in the fixed universe. Positive-pair
preservation exceeded unpaired preservation in four of five seed summaries,
but only three of five fold summaries and 12/25 fold-by-seed cells.

**Consequence:** Gate B remains `R4_GATE_B_FAIL`. The diagnostic strata and
channel difference cannot be used for threshold rescue, channel selection, or
retrospective policy construction.

---

## Decision — A new conservative hypothesis is justified, but no protocol exists

**Confirmed / 已确定 (2026-09-07)**

The selected future-path status is:

```text
NEW_HYPOTHESIS_JUSTIFIED_PROTOCOL_NOT_FROZEN
```

The sole justified conceptual hypothesis is:

> Most evidence-attributable useful correction may be recoverable while
> suppressing unsafe NON_EVIDENCED propagation.

The working concept may be called Trust-Gated / Locality-Aware Evidence
Reconciliation. This is not a moved R4 threshold, positive-pair-only rescue,
held-out-error tuning exercise, feature authorization, or larger-model
authorization. It is an untested future hypothesis.

**Consequence:** R5 remains unauthorized. The only next authorized task is
`FREEZE_NEW_PROSPECTIVE_CONSERVATIVE_RECONCILIATION_PROTOCOL`; implementation
or training remains prohibited.

---

## Decision — Legacy121 is no longer a pristine confirmatory test for future methods

**Confirmed / 已确定 (2026-09-07)**

Legacy121 R4 held-out outcomes have now been observed and used for scientific
interpretation and hypothesis generation. Any method designed afterward may
use Legacy121 only as development/hypothesis-generation data under a newly
frozen protocol; a Legacy121-only result cannot be described as independent
validation.

**Consequence:** external77 remains unopened and reserved as a one-shot
independent test. Before it can be accessed, the complete future method,
features, calibration, thresholds, gates, and analysis plan must be frozen.
external77 may not be used for rescue.

---

## Decision — Freeze Conservative Evidence Reconciliation with one corroboration gate

**Confirmed / 已确定 (2026-09-08, before implementation or training)**

The new method name is **Conservative Evidence Reconciliation (CER)**. Its sole
primary mechanism is Context-Corroborated Evidence Gate (CCEG). DIRECT
positive-pair support is protected, LOCAL_CONFLICT retains the explicit E1
deletion, and NON_EVIDENCED deletion requires both a usable-evidence risk branch
and an exactly evidence-masked candidate-context branch to meet one newly
validation-locked threshold. Branch disagreement is a normal ABSTAIN state and
leaves the original pair unchanged.

CER reuses the exact R4 80/17/8/4 feature contract and simple ERN branch
architecture. It does not use source identity, GT-derived inference features,
B2 disagreement, R4 decisions/thresholds, postmortem bins, attention,
Transformer, GNN, RNA language model, or foundation model. The scientific
rationale is independent corroboration for a non-local action whose relation to
evidence is not explicit; the rule is not fitted from a favorable held-out
stratum.

**Consequence:** status is
`CONSERVATIVE_RECONCILIATION_PROTOCOL_FROZEN` and
`CONSERVATIVE_RECONCILIATION_NOT_EXECUTED`. R4 remains
`R4_GATE_B_FAIL`. The only next authorized task is
`IMPLEMENT_AND_EXECUTE_CONSERVATIVE_RECONCILIATION_DEVELOPMENT`.

---

## Decision — Freeze a new development-only safety and attribution gate

**Confirmed / 已确定 (2026-09-08, prospectively)**

`CONSERVATIVE_DEV_GATE` retains event-pooled and RNA-balanced TP preservation
at least 0.99, event FP removal strictly above 0.347816, RNA-balanced FP
removal strictly above 0.489748, and improvement over P3 in at least two
sources including RNAfold or PETfold. It additionally requires both
NON_EVIDENCED preservation summaries at least 0.99, no evidence-attributable
reduction in NON_EVIDENCED preservation relative to the matched masked
control, and retention of strictly more than 50% of the frozen R4 ERN-minus-B4
FP-removal increment under both aggregations.

This is a Legacy121 development Go/No-Go gate, not R4 Gate B and not paper-level
confirmation. The complete 200 condition x branch x channel x fold x seed
matrix must be retained; no seed, channel, density, source, or protocol variant
may be selected.

**Consequence:** failure stops the conservative mainline and leads to
`PAPER_STORY_AND_RESULTS_CONSOLIDATION`. A development PASS can authorize only
a separate prospective final-policy/validation freeze. Neither outcome
automatically authorizes R5 or external77.

---

## Decision — Freeze CER data roles and external77 one-shot prerequisites

**Confirmed / 已确定 (2026-09-08)**

Legacy121 rotations are now named development train, development validation,
and development assessment. RNA remains the grouping unit, but no fold is
pristine confirmation. external77 remains `ONE_SHOT_INDEPENDENT_TEST` and
`EXTERNAL77_LOCKED`.

Before any external77 path is opened, a separate final-policy seal must contain
the final architecture/checkpoints, unchanged feature contract, CCEG action
rule, fitted calibration artifacts, exact numeric threshold, clean-evidence
generation and eligibility semantics, metrics, source analyses, success rule,
code/environment hashes, and commands. The clean-evidence contract is already
fixed to both channels, densities `0,1,5,10,20,50`, evidence seeds
`101,103,107,109,113`, `simulated_evidence_v1`, and R2 v1.0.2 pair
eligibility.

**Consequence:** external77 cannot be used for development, retraining,
recalibration, threshold rescue, feature/method redesign, subset selection, or
a second attempt. R5, noisy evidence, and real SHAPE/DMS/PARS remain
unauthorized.

---

## Decision — Stop the conservative mainline after the frozen development gate

**Confirmed / 已确定 (2026-09-08, after the sealed Legacy121 development assessment)**

The exact CER/CCEG experiment completed 200/200 training runs, 200 branch
calibrations, 100 policy calibrations and threshold seals, and 100 sealed
development-assessment evaluations. Primary combined five-seed event/RNA TP
preservation was 0.991586/0.992930 and FP removal was 0.475575/0.682200.
Evidence-attributable gains were G_event=0.0889535 and G_RNA=0.0669639, with
positive source-wise gain in all three current predictors and more than 50%
retention of the frozen R4 increment under both aggregations.

The prospectively frozen `CONSERVATIVE_DEV_GATE` nevertheless failed. CER
NON_EVIDENCED TP preservation was 0.990864 event-pooled and 0.992543
RNA-balanced, but both values were lower than the matched evidence-masked
control (0.991702 and 0.993584, respectively). The two no-evidence-attributable-
harm criteria therefore failed. All other gate conditions passed. The lower
mean NON_EVIDENCED lost-TP count (2,192.8 versus frozen R4 2,687.8) is
descriptive support only and does not override the matched-control failures.

**Consequence:** status is `CONSERVATIVE_RECONCILIATION_DEVELOPMENT_COMPLETE`
and `CONSERVATIVE_DEV_GATE_FAIL`. No alternate CCEG, larger model, threshold
rescue, seed/channel selection, R5, or external77 access is authorized. The
only next task is `PAPER_STORY_AND_RESULTS_CONSOLIDATION`. Legacy121 remains
development-only; `R4_GATE_B_FAIL` and `GATE_A_PASS_POSTHOC_NONDOMINATED`
remain unchanged.

---

## Decision — Freeze a bounded reliability/mechanistic paper story

**Confirmed / 已确定 (2026-09-08, after result consolidation only)**

The current results support a standalone paper only under a bounded
reliability/mechanistic framing: clean sparse structural evidence adds
residual pair-error signal beyond matched candidate-context controls, while
learned use outside direct support or local conflict creates a persistent
correction–preservation trade-off. The correction–preservation evaluation
framework is a secondary contribution.

The project is not framed as a successful CER method paper. B2/R4
non-dominance, ERN-versus-B4 evidence attribution, 3/3 current-source FP-
removal direction, perfect-precision clean `LOCAL_CONFLICT`, scope-localized
`NON_EVIDENCED` harm, and the prospective CER matched-control failure form the
evidence chain. All claims remain restricted to Legacy121 development data and
clean symbolic evidence.

**Consequence:** status is
`PAPER_STORY_AND_RESULTS_CONSOLIDATION_COMPLETE` and
`PAPER_STORY_VIABLE_WITH_CURRENT_RESULTS`. The only next authorized task is
`DRAFT_MANUSCRIPT_OUTLINE_AND_ASSEMBLE_FIGURE_DATA`, using already frozen
artifacts only. This decision does not alter `R4_GATE_B_FAIL` or
`CONSERVATIVE_DEV_GATE_FAIL`, authorize a new experiment, open external77,
start R5/R6, or support independent, unseen-predictor, noisy/real-evidence,
safe-non-local-propagation, global-superiority, or 3D claims.

---

## Decision — Initiate Phase II without reopening Phase I

**Confirmed / 已确定 (2026-09-08, design and literature audit only)**

The user authorized a separate Phase II research direction aimed at a CCF-A
capable contribution or an equivalently strong Q1 journal. Phase I remains
research-complete and retains its bounded reliability/mechanistic paper story.
`R4_GATE_B_FAIL` and `CONSERVATIVE_DEV_GATE_FAIL` are immutable and are not
converted into Phase II baselines to be rescued by threshold, seed, channel,
source, feature, or capacity selection.

Phase II's provisional title is **Risk-Controlled Structured Evidence
Refinement for RNA Secondary Structure Prediction**. Its central question is
whether sparse structural evidence can be transported through an existing
prediction only along structurally justified paths and under statistically
defensible harmful-edit control, while supporting valid edits beyond deletion.

**Consequence:** state is `PHASE1_RESEARCH_COMPLETE`,
`PHASE1_PAPER_STORY_VIABLE`, `PHASE2_INITIATED`, and
`PHASE2_NOVELTY_AND_METHOD_DESIGN`. No Phase II implementation or training is
authorized.

## Decision — Select a qualified risk-controlled structured-refinement direction

**Confirmed / 已确定 (2026-09-08, after fresh prior-art audit)**

The audit found strong prior art for every isolated ingredient: graph/contact
representations, GNNs, pair-specific probing-evidence probabilities,
evidence-guided hard/soft folding, input-prediction “fixing,” learned scores plus
DP/matching/parsing, validity-enforcing post-processing, selective prediction,
conformal risk control, conformal structured prediction, and RNA foundation
models. In particular, Hong et al.'s 2024 fixing task, ICML 2024
assignment/K-rook work, ICLR 2025 DEPfold, and ShapeSorter prevent generic
claims around source scaffolding, structured post-processing/decoding, or
pair-specific evidence. ICLR 2024/2025 risk work likewise prevents relabeling
calibration or graph conformal prediction as a new risk method.

The remaining qualified gap is the *joint* problem of preserving an arbitrary
source prediction, estimating evidence-to-edit transport eligibility, making
valid minimum-cost KEEP/DELETE/ADD/REPLACE/ABSTAIN decisions, and controlling a
prospectively defined harmful-edit loss at an RNA/family-cluster unit.

Three model families were compared: Pair-Graph Trust Refinement, Energy-Based
Minimal-Edit Refinement, and Risk-Controlled Structured Refinement. The third is
selected as the primary concept, with the energy-based family as the required
simple baseline.

**Consequence:** `PHASE2_PRIMARY_DIRECTION_JUSTIFIED`, but
`PROTOCOL_NOT_FROZEN` and `PHASE2_IMPLEMENTATION_NOT_AUTHORIZED`. The direction
must be rejected or downgraded if a refreshed audit closes the joint gap or the
risk-control assumptions cannot be satisfied. No GNN, Transformer, foundation
model, or decoder is authorized by this decision.

## Decision — Replace Legacy121 with Development-v2 for Phase II design

**Confirmed / 已确定 (2026-09-08, prospective data-role decision)**

Legacy121 outputs were observed and used to construct the Phase II hypothesis.
It is therefore renamed `PHASE1_HISTORICAL_DIAGNOSTIC_DATA`. It may support
Phase I reproduction, diagnostic examples, and compatibility tests, but cannot
be the primary basis for Phase II architecture selection, risk calibration, or
independent validation.

Phase II requires Development-v2: new structures with exact provenance,
sequence-identity filtering, family-aware grouping, type/length diversity,
predictor-training-overlap audits, and a temporal split where feasible. The
predictor panel must support leave-one-predictor-family-out evaluation and
should prioritize a small deployable set spanning thermodynamic, comparative,
learned-thermodynamic, end-to-end neural, and optionally one foundation-model
family. NuFold is a 3D predictor and is not treated as a like-for-like 2D source.

external77 remains `ONE_SHOT_LOCKED` and was not accessed. Because the Phase II
task adds ADD/REPLACE, modern predictors, and structured risk control,
external77 is retained as a Phase I bridge candidate rather than automatically
declared the sole Phase II final test. A separately locked Independent-v2 may be
required.

**Consequence:** the only next authorized task is
`FREEZE_PHASE2_DATASET_AND_TASK_PROTOCOL`. It may freeze data/task/risk
semantics but may not implement or train models, generate evidence, run new
scientific evaluations, access external77, or begin old R5/R6/R8 work.

## Decision — Freeze Phase II Development-v2 and structured-task protocol

**Confirmed / 已确定 (2026-09-09, prospective protocol only)**

The P1 source audit accepts RNA3DB-2D v1 as the Development-v2 experimental
core and restricts RNASSTR/Rfam comparative annotations to TRAIN and
MODEL_SELECTION. bpRNA-1m, RNAStrAlign, ArchiveII and bpRNA-new remain overlap
registries because exact artifact/license or predictor-use independence is not
sufficiently established. No records were selected or downloaded.

Biological connected components are formed by fixed 80% sequence identity at
80% bilateral global-alignment coverage, exact identity/provenance/conformer
edges, and higher-priority source-backed family edges. Components are disjoint
across TRAIN, MODEL_SELECTION, SCORE_CALIBRATION, RISK_CALIBRATION and one-use
DEVELOPMENT_ASSESSMENT. The PDB temporal cutoff is 2024-12-04; missing dates are
`NOT_AVAILABLE`, never inferred.

The primary source panel freezes four algorithmic families: RNAfold 2.7.2,
MXfold2 v0.1.2, UFold commit `75bd9acc...`, and RiNALMo commit `2c2c5c1...`
with its named bpRNA-SS checkpoint. Every artifact must pass a pre-prediction
license/version/hash/training-overlap audit. LOPFO holds out a full family;
source identity and predictor-specific risk thresholds are prohibited.

The structured task uses the complete legal AU/UA/GC/CG/GU/UG, `j-i>3`,
single-partner, noncrossing candidate universe for 30--600 nt RNAs. It freezes
KEEP/DELETE/ADD/coupled-REPLACE/component-ABSTAIN, symmetric-difference edit
costs 0/1/1/2, clean E0 pair/unpaired facts, radius-two typed evidence
transport, and deterministic exact weighted interval DP. Pseudoknots remain a
separate future ILP track.

The theorem audit rejects standard conformal risk control because structured
policy changes can substitute edits and per-RNA HarmRate is non-monotone. The
sole primary route is `FINITE_FAMILY_RISK_CONTROLLING_POLICY_SELECTION`: six
complete component policies, simultaneous Hoeffding upper bounds over
biological calibration components, `alpha=0.10`, `delta=0.05`, and a minimum
readiness count of 240 risk-calibration components. The permitted guarantee is
only the stated marginal expected cluster-balanced HarmRate claim under its
assumptions; it is not conformal, conditional, FDR or per-RNA control.

external77 was not accessed and is assigned
`PHASE1_BRIDGE_INDEPENDENT_ASSET`. A separately sealed, temporally newer,
family/sequence-disjoint Independent-v2 is the Phase II primary one-shot set.

**Consequence:** state is `PHASE2_DATASET_AND_TASK_PROTOCOL_FROZEN` and
`PHASE2_IMPLEMENTATION_NOT_AUTHORIZED`. The next proposed task is
`IMPLEMENT_PHASE2_MINIMAL_STRUCTURED_BASELINES`, beginning only on explicit
authorization and limited to synthetic/non-learned protocol infrastructure.
Primary-model implementation, training, evidence generation, Development-v2
performance, external77, old R5/R6/R8, real probing and 3D remain unauthorized.
Phase I results and both failed gates are unchanged.
