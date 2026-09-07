# Current Status

Last updated: 2026-09-07

## Current Stage

**PROJECT REBOOT v2 — `R4_POSTMORTEM_COMPLETE`**

**Future path: `NEW_HYPOTHESIS_JUSTIFIED_PROTOCOL_NOT_FROZEN`**

**Gate A: `GATE_A_PASS_POSTHOC_NONDOMINATED`**

**Gate B: `R4_GATE_B_FAIL` (unchanged)**

**Next-stage authorization: `R5_NOT_AUTHORIZED`**

**Next authorized task: `FREEZE_NEW_PROSPECTIVE_CONSERVATIVE_RECONCILIATION_PROTOCOL`**

Current working direction:

> **Post-hoc Evidence Reconciliation for RNA Secondary Structure Predictions**

R0 literature/novelty freeze and R1 task redefinition are complete. R2 protocol
v1.0.2 prospectively freezes both crossing and minimum-loop solver-capability
eligibility. The amended universe contains 7,153 eligible B2 realizations:
3,523/3,630 pair and 3,630/3,630 unpaired. All 7,153 existing fixed-command
outputs passed row-level provenance, parsing, validity, and hard-constraint
checks; no new RNAfold calls were required. Formal matched B0/B1/B2
summarization is complete. Overall Macro/Micro F1 is 0.878635/0.861068 for B0,
0.889352/0.872422 for B1, and 0.924648/0.904747 for B2. The formal R2
interpretation is frozen as `POSTHOC_HEADROOM_PLAUSIBLE`: B2 is a strong
comparator but its Macro/Micro TP preservation of 0.975358/0.981767, 4,752
lost TP, and 10,823 new FP leave a plausible high-preservation question.
Gate A is `GATE_A_DEFERRED_R4_REQUIRED`, neither PASS nor FAIL.

The R3 Pair-Reliability Baseline Suite is complete. Its prospective ECE
amendment was frozen before any Legacy121 R3 performance number. Track P used
5,290 original predicted pairs; Track E used 3,523 pair and 3,630 unpaired R2
v1.0.2 eligible manifests, yielding 310,838 pair-realizations per baseline.
The strongest Track P no-new-training comparator is historical
`R3-P3 V3_VETO2_FIXED`: RNA-balanced FP removal 0.489748 at TP preservation
0.997588, with `SOURCE_DEPENDENT_COMPARATOR`. The strongest Track E comparator
is `R3-E1 LOCAL_CONFLICT`: RNA-balanced FP removal 0.142946 at preservation
1.0. P4 BPP had the strongest Track P discrimination but failed the held-out
RNA-balanced 0.99 safety constraint; E2 B2 disagreement was strong but retained
only 0.975358 RNA-balanced TP. Full results are frozen in
`docs/reliability_baseline_r3_results.md`.

The historical `evidence_guidance_stage_e2_v1` protocol remains frozen as provenance but was superseded **before training**. It must not be executed as the current next step.

The scientific interpretation of the frozen R3 results is complete. R3 shows
usable prediction-only discrimination, but not a safe learned operating point:
P4 discriminates strongly yet misses RNA-balanced 0.99 preservation; P3 is the
frozen high-preservation prediction-only comparator but is source-dependent;
E1 is perfectly precise but coverage-limited; and E2/B2 exposes broad evidence
signal while retaining unsafe collateral TP loss. This supports a bounded,
simple R4 test without predetermining its outcome. Gate A remains
`GATE_A_DEFERRED_R4_REQUIRED`, neither PASS nor FAIL.

The clean learned R4 protocol is now prospectively frozen under working name
Evidence Reconciliation Network (ERN). R4 is deletion-only, uses RNA-grouped
train/validation/held-out roles, validation-only calibration and threshold
selection, and requires a matched evidence-masked B4. Its exact Gate B bars are
event-pooled and RNA-balanced TP preservation at least 0.99, RNA-balanced FP
removal strictly above 0.489748, event-pooled FP removal strictly above
0.347816, and improvement not driven by one predictor source. The protocol and
implementation plan were frozen without implementing or training R4.

The frozen R4 execution is now complete: all 100 ERN/B4 channel x fold x seed
runs, 100 validation-only calibrations/threshold locks, and 100 one-shot
held-out evaluations completed. Primary combined ERN achieved event/RNA TP
preservation 0.989682/0.991936 and FP removal 0.475531/0.660806. It exceeded
both FP-removal bars and improved over P3 in all three sources, but failed the
conjunctive event `TP_preservation >= 0.99` condition. The decision is
`R4_GATE_B_FAIL`; no rescue tuning was performed. B2 removes more FP, while R4
preserves more TP and has higher modification precision, so Gate A is boundedly
`GATE_A_PASS_POSTHOC_NONDOMINATED`. R5 is not authorized.

The frozen-output R4 postmortem is complete. Relative to B4, ERN gained a mean
4,464.6 removed FP and lost a net additional 574.2 TP per seed. Perfectly
precise `LOCAL_CONFLICT` supplied 2,500.6 (56.0%) of the marginal FP removal;
`NON_EVIDENCED` supplied 1,964.0 (44.0%) and all material additional harm
(+696.2 lost TP), partly offset by protection of 122.0 DIRECT TP. Loss was
distributed across all sources and both channels. The positive-pair preservation
advantage was not fold-stable, so no channel rescue is permitted.

This supports only a new hypothesis that most evidence-attributable correction
may be recoverable while suppressing unsafe non-evidenced propagation. Status
is `NEW_HYPOTHESIS_JUSTIFIED_PROTOCOL_NOT_FROZEN`; the only next task is to
freeze a new conservative trust-gated/locality-aware protocol. No implementation
or training is authorized.

## Rebooted Scientific Question

> Given an RNA sequence, an already-computed secondary-structure prediction from an existing predictor, and sparse external structural evidence, can a post-hoc method identify and selectively correct residual pair errors while preserving predictor information that is already correct?

Mandatory comparison:

```text
B0 Original predictor
vs
B1 local hard evidence enforcement
vs
B2 global evidence-constrained refolding
vs
future B4/R4 post-hoc learned evidence reconciliation
```

The project must explicitly answer:

> **Why not simply refold the RNA under the same evidence?**

## Novelty Boundary

Do not claim novelty for these components by themselves:

- basic RNA pairing/stem/stacking rules;
- isolated-pair or short-stem cleanup;
- pair probability/confidence;
- thermodynamic + evolutionary evidence fusion;
- predictor consensus;
- evidence-constrained global folding;
- generic pair-level post-hoc QA as an abstract ML task;
- benchmark normalization/evaluator infrastructure.

Current candidate contribution:

> **Predictor-output-preserving evidence reconciliation for RNA secondary-structure predictions.**

`Model-agnostic`, `unseen-predictor`, `real-evidence robust`, and `3D benefit` remain candidate claims only.

## Preserved Historical Results

No prior result is deleted or reinterpreted.

### Infrastructure and error analysis

- Legacy121 v1: 121 RNAs, 363 normalized source predictions.
- RNAfold / PETfold / trRosettaRNA2 native SS each have 121 valid records.
- shared exact canonical-pair evaluator complete.
- pair-level missing/FP/wrong-partner analysis complete.
- strict stem extraction/matching taxonomy complete.
- sequence-separation analysis complete.

### Legacy121 infrastructure baseline

| Predictor | Macro F1 | Micro F1 | TP | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| RNAfold | 0.905818 | 0.874443 | 1473 | 220 | 203 |
| PETfold | 0.896849 | 0.865680 | 1463 | 241 | 213 |
| trRosettaRNA2 native SS | 0.842871 | 0.818717 | 1461 | 432 | 215 |

These are infrastructure baselines, not refinement claims.

### Prediction-only refinement development

- Rule baseline: complete.
- selective-refiner v1: `DEVELOPMENT_GATE_FAIL`.
- selective-refiner v2: `V2_DEVELOPMENT_GATE_FAIL`.
- selective-refiner v3 primary: `V3_DEVELOPMENT_GATE_FAIL`.
- prediction-only cross-model mainline: **CLOSED FOR CURRENT MAINLINE**.
- no Legacy121 v4/v5 rescue tuning is authorized.

### Simulated evidence development

- clean simulated evidence generator: complete/reproducible.
- Stage E1 local hard baseline: complete.
- direct/local utility: positive under clean evidence semantics.
- `NON_EVIDENCED_EFFECT == 0` because B1 is local by construction.
- historical E2 architecture remains a candidate implementation asset only.

## Independent Test

external77-derived 42-RNA set is ready and locked:

- RNAfold: 42/42 valid;
- PETfold: 42/42 valid under reproduced historical single-sequence condition;
- trRosettaRNA2 native SS: 42/42 valid under recovered query-only condition;
- normalized matrix: **126/126 PASS**.

Role: **R7 one-shot independent evaluation only**. No development/tuning access.

## Evidence Ladder

- **E0 clean symbolic**: positive pair / unpaired nucleotide; mechanism and upper-bound development.
- **E1 controlled noisy symbolic**: robustness/trust testing.
- **E2 real experimental evidence**: candidate SHAPE/DMS/PARS after dedicated audit.

Real probing signals are evidence, not GT.

## Reboot Evaluation

### Pair reliability

Planned primary metrics:

- AUPRC for DELETE/FP;
- Brier score;
- ECE / reliability diagrams;
- high-risk-pair precision;
- AUROC as secondary.

### Refinement utility

Mandatory:

```text
TP_preservation = TP_after / TP_before
FP_removal = (FP_before - FP_after) / FP_before
modification_precision = beneficial_edits / modified_pairs
```

Also retain Precision, Recall, macro/micro F1 and complete edit accounting.

### Risk–utility

Primary method comparison emphasizes TP loss versus FP removal rather than only aggregate `Delta F1`.

### Non-evidenced effect

Report non-evidenced modification precision, FP removal and TP loss. The question is whether propagation is useful rather than merely present.

### Evidence efficiency

Report correction benefit per delivered evidence item.

### Matching

Exact canonical-pair equality remains primary. Final paper-level robustness may separately add +/-1 endpoint flexible matching without rewriting historical exact results.

## Roadmap

```text
R0 Literature & novelty freeze              COMPLETE
R1 Task/protocol redefinition               COMPLETE
R2 Global constrained-refolding baseline    COMPLETE
R3 Reliability baseline suite               COMPLETE
R4 Clean learned evidence reconciliation       COMPLETE / GATE B FAIL
R4 postmortem / future-path decision            COMPLETE / NEW HYPOTHESIS ONLY
New conservative reconciliation protocol       NOT FROZEN / PLANNING ONLY
R5 Controlled noise robustness                 NOT AUTHORIZED
R6 Cross-predictor transfer / LOMO
R7 Locked external77 independent test
R8 Real experimental evidence
R9 Final calibrated KEEP/DELETE/ABSTAIN
Optional 2D -> 3D validation
```

## Go / No-Go Gates

### Gate A — Post-hoc necessity

If matched global constrained refolding dominates the relevant TP-preservation / FP-removal trade-off, stop the post-hoc mainline.

### Gate B — Learned utility

Learned R4 must satisfy all frozen held-out criteria: event-pooled and
RNA-balanced `TP_preservation >= 0.99`, RNA-balanced
`FP_removal > 0.489748`, event-pooled `FP_removal > 0.347816`, and improvement
not driven by one source. Matched B4 is a mandatory evidence-attribution
comparison, not an extra numerical Gate B bar. Failure does not authorize
automatic architecture escalation.

### Gate C — Noise robustness

If 5-10% controlled evidence noise causes negative structure utility or unsafe TP loss, do not advance to a real-evidence claim without a prospectively frozen trust mechanism.

### Gate D — Independent generalization

Open external77 once. If the development effect does not preserve direction, no cross-dataset generalization claim and no external77 rescue tuning.

## Completed Task — R2 Global Constrained Refolding

- Protocol v1.0.2 was frozen before formal metrics. It adds a whole-manifest
  minimum-loop capability rule (`j-i>3`) to the historical v1.0.1 crossing
  rule without changing the solver or delivered evidence.
- The coordinate-only audit found 3,523 eligible, 87 crossing-ineligible, and
  20 minimum-loop-ineligible pair manifests, with no overlap; all 3,630
  unpaired manifests remain eligible.
- Every one of 7,153 amended eligible outputs was validated and reused; no new
  RNAfold call was needed and eligible constraint satisfaction was 100%.
- B2 achieved overall Macro/Micro F1 0.924648/0.904747 versus
  0.889352/0.872422 for B1 and 0.878635/0.861068 for B0.
- B2 preserved 0.975358 Macro / 0.981767 Micro of original TP and removed
  0.775728 Macro / 0.645883 Micro of original FP. It made 43,475 beneficial
  and 15,575 harmful changes.
- NON_EVIDENCED propagation was net beneficial (36,027 beneficial versus
  15,575 harmful) but not uniformly safe (Micro modification precision
  0.698171).
- Full results and the retained historical blocker record are in
  `docs/global_constrained_refolding_r2_results.md`.
- R2 supplies the frozen future Gate A comparator; it does not decide Gate A
  without a future R4 result.

## Completed Task — R2 Interpretation and R3 Protocol Freeze

- `docs/r2_scientific_interpretation.md` strictly separates empirical result,
  interpretation, and future hypothesis.
- R2 interpretation status is `POSTHOC_HEADROOM_PLAUSIBLE`.
- Gate A status is `GATE_A_DEFERRED_R4_REQUIRED`; no PASS/FAIL is assigned
  before a future R4 comparison.
- `docs/reliability_baseline_r3_protocol.md` freezes separate prediction-only
  and evidence-conditioned tracks, original-pair labels, R2 matched-universe
  joins, dual aggregation, calibration restrictions, deletion-only risk curves,
  validation-only threshold selection, and strongest-comparator rules.
- `docs/reliability_baseline_r3_implementation_plan.md` records the future
  scripts, reusable assets, artifact layout, integrity checks, and execution
  gate without implementing or running the formal suite.
- BPP feasibility is `R3_BPP_BASELINE_FEASIBLE_WITH_FROZEN_CLI` using
  `/usr/bin/RNAfold` 2.4.17 and the frozen partition-function interface.

## Completed Task — R3 Pair-Reliability Baseline Suite

- The ECE amendment was frozen prospectively with fixed ten-bin event-pooled
  and per-RNA-then-equal-weight RNA-balanced semantics.
- Track P completed P0--P4 on 121 RNAs, 363 source records, and 5,290 original
  pairs; Track E completed E1/E2 on 7,153 eligible manifests and 310,838
  pair-realizations per baseline.
- P3 is `STRONGEST_R3_PREDICTION_ONLY_BASELINE`; its RNA-balanced preservation,
  FP removal, modification precision, and coverage are 0.997588, 0.489748,
  0.965504, and 0.055930. Its utility is source-dependent.
- E1 is `STRONGEST_R3_EVIDENCE_CONDITIONED_BASELINE`; corresponding values are
  1.0, 0.142946, 1.0, and 0.018623.
- P4 was the strongest prediction-only discriminator (event/RNA AUPRC
  0.777283/0.915326) but was high-preservation-ineligible; E2 reproduced B2's
  original-pair preservation/FP-removal point and was likewise ineligible.
- All joins and leakage gates passed; targeted tests passed 33/33 and the full
  suite passed 201 tests plus 29 subtests. No new training, retuning,
  external77 access, or R4 execution occurred.

## Completed Task — R3 Interpretation and R4 Protocol Freeze

- `docs/r3_scientific_interpretation.md` separates frozen empirical results,
  bounded interpretation, and untested R4 requirements.
- Status is `R3_INTERPRETATION_COMPLETE`; R4 headroom is scientifically
  reasonable but untested, and Gate A remains `GATE_A_DEFERRED_R4_REQUIRED`.
- `docs/clean_learned_evidence_reconciliation_r4_protocol.md` freezes the
  simple ERN inputs, evidence encodings, architecture, B4 control, grouped
  splits, calibration, threshold selection, actions, metrics, comparisons,
  source-consistency rule, and exact Gate B.
- `docs/clean_learned_evidence_reconciliation_r4_implementation_plan.md`
  defines planned code and artifact contracts, historical E2 reuse boundaries,
  provenance, leakage/hash checks, and tests without implementing or executing
  R4.
- Historical E2 runtime source is not available as auditable source code; its
  documented feature/architecture contracts remain sufficient implementation
  provenance and this is not a scientific blocker.
- At the protocol-freeze checkpoint, state was `R4_PROTOCOL_FROZEN` and
  `R4_NOT_EXECUTED`, and the next task was `IMPLEMENT_AND_EXECUTE_FROZEN_R4`.

## Completed Task — Frozen R4 ERN/B4 Execution

- The exact 121-RNA, 363-source-record, 7,153-manifest, 310,838-event feature
  universe passed all preflight, split, hash, and feature-firewall audits.
- All 100 expected training runs completed under the frozen architecture and
  optimization contract. All calibrators and thresholds were selected using
  validation only and sealed before 100 one-shot held-out evaluations.
- ERN primary combined five-seed event/RNA AUPRC was 0.811406/0.897194.
  Event/RNA TP preservation was 0.989682/0.991936; FP removal was
  0.475531/0.660806; modification precision was 0.898838/0.944218.
- Matched B4 had event AUPRC 0.771726, event/RNA preservation
  0.991886/0.993570, and event/RNA FP removal 0.386622/0.615236. Evidence
  improved reliability and removal but reduced preservation.
- Source-wise RNA FP-removal improvements over P3 were positive for RNAfold,
  PETfold, and trRosettaRNA2. Source consistency passed.
- Gate B is `R4_GATE_B_FAIL` solely because five-seed mean event TP
  preservation was below 0.99. Gate A is
  `GATE_A_PASS_POSTHOC_NONDOMINATED`; R5 is not authorized.
- Full results are in
  `docs/clean_learned_evidence_reconciliation_r4_results.md`.

## Completed Task — R4 Postmortem and Future-Path Decision

- The analysis read only sealed R4 held-out scores and immutable candidate
  metadata; all frozen input hashes matched.
- The Gate B gap is 0.000317585 in event TP preservation, corresponding
  descriptively to about 82.77 excess mean lost-TP events on the fixed 260,623
  TP-event universe. This is not a threshold-rescue target.
- `LOCAL_CONFLICT` contributed 56.0% of ERN's net added FP removal over B4 at
  perfect precision. `NON_EVIDENCED` contributed 44.0% and all material added
  TP loss; DIRECT evidence protected TP.
- TP loss was distributed across RNAfold, PETfold, trRosettaRNA2 and both
  evidence channels. Positive-pair preservation was not fold-stable.
- The selected branch is
  `NEW_HYPOTHESIS_JUSTIFIED_PROTOCOL_NOT_FROZEN`. R4 Gate B remains FAIL and R5
  remains unauthorized.
- Full diagnostic interpretation is in
  `docs/r4_failure_analysis_and_future_decision.md`.

## Current Restrictions

- **Do not train historical Stage E2.**
- **Do not access external77.**
- **Do not rescue the failed R4 Gate B with threshold changes, seed/channel
  selection, new features, or a Transformer/GNN/foundation model.**
- **Do not retune v1/v2/v3 on Legacy121 to rescue old claims.**
- **Do not alter or expand the frozen R2 v1.0.2 comparison universe.**
- **Do not change the frozen R3 score definitions, threshold rule, or
  aggregation semantics after viewing held-out results.**
- **Do not change frozen R4 features, calibration, threshold rules, Gate B, or
  source-consistency requirement after held-out results.**
- **Do not begin R5, R7 external77, or real-evidence work: no next scientific
  execution stage is authorized after `R4_GATE_B_FAIL`.**
- **The only authorized next task is protocol freeze for the new prospective
  conservative-reconciliation hypothesis; do not implement or train it.**
- **Legacy121 held-out folds are no longer pristine confirmation for any method
  designed after the R4 postmortem. Keep external77 unopened until a complete
  future protocol and analysis plan are frozen.**

Detailed current-mainline documents:

- `docs/project_reboot_v2.md`
- `docs/reboot_v2_decisions.md`
- `docs/reboot_v2_claim_evidence_map.md`
- `plan/research_plan.md`
- `plan/timeline.md`
- `tasks/TODO.md`
