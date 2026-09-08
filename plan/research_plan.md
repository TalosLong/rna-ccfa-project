# Research Plan — Reboot v2

Last updated: 2026-09-08

## 1. Phase I Working Direction — Complete and Frozen

> **Post-hoc Evidence Reconciliation for RNA Secondary Structure Predictions**

The project studies whether an already-computed RNA secondary-structure prediction can be selectively quality-controlled using sparse external structural evidence, while preserving useful information already captured by the source predictor.

The primary scientific comparison is:

```text
Original predictor
vs
local evidence enforcement
vs
global evidence-constrained refolding
vs
post-hoc evidence reconciliation
```

Phase I did not assume that post-hoc reconciliation was useful; its completed
R2--R4/CER sequence established a bounded mechanistic paper story while failing
both learned safety gates. Phase II is separately defined in Section 14 and
does not alter these results.

## 2. Core Research Questions

### RQ1 — Post-hoc necessity

Does the original predictor output retain correct information that can be damaged or overwritten by global evidence-constrained refolding?

### RQ2 — Safe correction

Can sparse evidence improve false-positive removal while maintaining high correct-pair preservation?

### RQ3 — Useful non-local effect

Can a method make beneficial corrections outside the directly evidenced/local-conflict region, rather than merely causing global collateral changes?

### RQ4 — Generalization

Does the signal hold across predictors, RNA groups, and a locked independent dataset?

### RQ5 — Robustness and real evidence

How does performance degrade under controlled evidence noise, and does any effect survive real probing evidence?

### Candidate downstream question

Does a validated 2D improvement improve downstream RNA 3D prediction under an identical frozen 3D pipeline?

## 3. Task Definition

For sequence `x`, original predicted pair set `S`, delivered evidence `E`, and an original predicted pair `p=(i,j) in S`, estimate:

```text
q_ij = P(p is incorrect | x, S, E)
```

Primary decisions:

```text
KEEP / DELETE / ABSTAIN
```

The first rebooted mainline is deletion-only. It does not add absent pairs, reassign partners, rebuild stems, or generate a new full structure from scratch.

## 4. Prior-Art Boundary

The following are treated as prior art/baselines rather than contributions:

- RNA canonical-pair/stem/stacking rules;
- isolated-pair and short-stem cleanup;
- thermodynamic base-pair probability/confidence;
- thermodynamic + evolutionary evidence fusion;
- predictor consensus/ensemble confidence;
- evidence-constrained global folding;
- generic post-hoc pair-level quality assessment as an abstract ML problem.

The candidate contribution is narrower:

> **Predictor-output-preserving evidence reconciliation for RNA secondary-structure predictions.**

`Model-agnostic`, `unseen-predictor`, `real-evidence robust`, and `3D benefit` are candidate claims only.

## 5. Historical Evidence Preserved

- Phase 0 normalization/evaluator: complete.
- Phase 1 error taxonomy and descriptive analysis: complete.
- Rule baseline: complete.
- Selective-refiner v1: `DEVELOPMENT_GATE_FAIL`.
- Selective-refiner v2: `V2_DEVELOPMENT_GATE_FAIL`.
- Selective-refiner v3 primary: `V3_DEVELOPMENT_GATE_FAIL`.
- Prediction-only cross-model mainline: closed for the current mainline; no Legacy121 v4/v5 rescue tuning.
- Simulated evidence Stage E1: complete; direct/local utility positive, non-evidenced effect exactly zero.
- Historical Stage E2: frozen but untrained; superseded by Reboot v2 before training.
- external77-derived independent matrix: 42 RNAs x 3 predictors = 126/126 valid; remains locked.

## 6. Data Strategy

### Legacy121 v1

Development-only dataset for:

- baseline design;
- model/feature selection;
- calibration and threshold selection;
- ablation;
- simulated evidence;
- Go/No-Go decisions.

The frozen R4 held-out folds have now been observed and used for post-hoc
diagnosis. Any method designed after R4 must treat all Legacy121 folds as
development/hypothesis-generation data; a new Legacy121-only result is not
independent confirmation.

### external77-derived 42-RNA set

Locked independent test only. No feature redesign, model selection, threshold tuning, or rescue analysis may use it before R7.

## 7. Evidence Ladder

### Level E0 — Clean symbolic evidence

- positive base-pair evidence;
- unpaired-nucleotide evidence.

Purpose: mechanism/upper-bound development.

### Level E1 — Controlled noisy symbolic evidence

Frozen corruption mechanisms and candidate noise levels are used to study robustness and the need for learned trust.

### Level E2 — Real experimental evidence

Candidate modalities: SHAPE, DMS, PARS and related probing data after a separate provenance/data audit. Real probing is evidence, not GT.

## 8. Required Baselines

### B0 — Original Predictor

No modification.

### B1 — Local Hard Evidence

Completed Stage E1 local hard transformations.

### B2 — Global Evidence-Constrained Refolding

**Mandatory new baseline before learned training.**

Use the same sequence and the same delivered sparse evidence, but allow a classical folding algorithm to re-optimize the complete structure. The first frozen implementation should use a reproducible ViennaRNA/RNAfold hard-constraint protocol.

This baseline answers:

> Why not simply refold from sequence under the evidence?

### B3 — Prediction-Only Reliability Baselines

Retain as mechanistic comparators:

- rule-based conditions;
- historical v1 topology-only score;
- historical v3 fixed consensus veto;
- compatible pair-confidence/BPP baseline;
- simple cross-model agreement where semantically valid.

### B4 — Evidence-Masked Learned Control

Matched learned condition without usable evidence, required to attribute any gain to evidence rather than model capacity.

## 9. Candidate Learned Method

Internal working name: **Evidence Reconciliation Network (ERN)**.

The historical E2 DeepSets-style architecture may be reused as an implementation starting point because it already supports a source-agnostic candidate branch and permutation-invariant evidence-set encoding.

The historical E2 success criteria are superseded. The new R4 protocol is now
frozen after R2/R3 and requires comparisons against B0/B1/B2, R3-P3, R3-E1,
and B4.

No Transformer/GNN/foundation-model escalation is authorized unless a simple architecture first establishes signal beyond the strongest frozen non-learned baseline.

After R4 Gate B failure, the prospectively frozen successor is **Conservative
Evidence Reconciliation (CER)** with one Context-Corroborated Evidence Gate
(CCEG). CER retains the exact R4 features and simple branch architecture. It
changes action structure only: DIRECT support protects a pair, LOCAL_CONFLICT
retains the explicit E1 deletion, and NON_EVIDENCED deletion requires
agreement between usable-evidence and evidence-masked candidate-context risk.
Branch disagreement is ABSTAIN. This is a new hypothesis, not an R4 rescue.

## 10. Metrics

### Pair reliability

Primary candidates:

- AUPRC for `DELETE`/FP;
- Brier score;
- ECE;
- reliability diagrams;
- precision among highest-risk pairs.

AUROC is secondary.

### Refinement utility

Mandatory:

```text
TP_preservation = TP_after / TP_before
FP_removal = (FP_before - FP_after) / FP_before
modification_precision = beneficial_edits / modified_pairs
```

Also report Precision, Recall, macro/micro F1, edit counts, beneficial/harmful decomposition.

### Risk–utility

Primary comparison should use curves/operating points such as:

```text
x-axis: TP loss or 1 - TP preservation
y-axis: FP removal
```

The main question is whether post-hoc reconciliation gives a better correction-preservation trade-off than B2, not whether it achieves a small isolated F1 gain.

### Non-evidenced effects

Report separately:

- non-evidenced modification precision;
- non-evidenced FP removal;
- non-evidenced TP loss.

### Evidence efficiency

Report benefit per delivered evidence item, including `FP_removed / evidence_items` and optionally `Delta_F1 / evidence_items`.

### Matching robustness

Exact canonical-pair matching remains primary. Add +/-1-endpoint flexible matching only as a separate final robustness analysis; never rewrite historical exact results.

## 11. Experimental Stages

### R0 — Literature & novelty freeze

**Status: COMPLETE FOR REBOOT.**

### R1 — Task/protocol redefinition

**Status: COMPLETE.**

Freeze project documents and supersede historical E2 training before any learned run.

### R2 — Global constrained-refolding baseline

**Status: COMPLETE.**

Freeze and implement a clean hard-constraint global-refolding protocol on Legacy121 using the same clean evidence manifestations as B1 wherever semantics match.

Protocol v1.0.2 prospectively froze crossing and minimum-loop capability
eligibility before formal metrics. The amended universe contains 7,153
eligible folds (3,523 pair; 3,630 unpaired), all validated at 100% constraint
satisfaction. Formal matched B0/B1/B2 metrics, full-refold edits, scope
decomposition, density/source summaries, and evidence efficiency are complete.
B2 overall Macro/Micro F1 was 0.924648/0.904747 versus 0.889352/0.872422 for
B1 and 0.878635/0.861068 for B0.

Required outputs:

- full-structure metrics;
- TP preservation;
- FP removal;
- modification precision;
- direct/local/non-evidenced decomposition;
- evidence efficiency;
- source-wise summaries;
- exact identity/constraint compliance checks.

### R3 — Reliability baseline suite

**Status: COMPLETE.**

The frozen suite separates prediction-only Track P from evidence-conditioned
Track E. It evaluates original predicted pairs with DELETE/FP positive, AUPRC
primary, deletion-only risk–utility, event-pooled and RNA-balanced summaries,
and validation-only selection at `TP_preservation >= 0.99`. RNAfold 2.4.17 BPP
was generated through the frozen CLI without software installation. P3
`V3_VETO2_FIXED` and E1 local conflict are the frozen strongest Track P and
Track E comparators, respectively. Full results and source-dependence limits
are recorded in `docs/reliability_baseline_r3_results.md`.

### R4 — Clean learned evidence reconciliation

**Status: `R4_COMPLETE` — `R4_GATE_B_FAIL`.**

The frozen experiment uses original predicted pairs as candidates, DELETE/FP
as the positive label, the historical source-agnostic candidate encoding plus
frozen P2/P4 inference-time context, and separate permutation-invariant
positive-pair/unpaired evidence encoders. The starting model is a simple
DeepSets-style ERN; primary R4 remains deletion-only. Predictor identity is
evaluation metadata, not a shortcut feature.

RNA is the split unit. Preprocessing is training-only; checkpoint selection,
monotone Platt calibration, and the operating point use validation only. B4 is
a separately trained paired control with identical rows, architecture,
capacity, optimization, splits, seeds, calibration, and threshold procedure;
only usable evidence is exactly masked.

Frozen Gate B requires held-out event-pooled and RNA-balanced TP preservation
at least 0.99, RNA-balanced FP removal strictly above 0.489748, event-pooled FP
removal strictly above 0.347816, and positive improvement over P3 in at least
two sources including RNAfold or PETfold. E1 at RNA-balanced FP removal
0.142946 and preservation 1.0 remains a mandatory comparison. Matched B4 is a
separate required evidence-attribution analysis, not an added numerical Gate B
bar. Failure does not authorize automatic architecture escalation.

The frozen execution completed 100/100 ERN/B4 runs. Primary combined ERN
event/RNA preservation was 0.989682/0.991936 and FP removal was
0.475531/0.660806. Source improvement over P3 was positive in all three
predictors, but the event preservation requirement failed. Gate A is
`GATE_A_PASS_POSTHOC_NONDOMINATED`; Gate B is `R4_GATE_B_FAIL`. No rescue was
performed and R5 is not authorized.

### R4 postmortem — conservative future hypothesis

**Status: `R4_POSTMORTEM_COMPLETE`.**

Frozen-output diagnostics found that 56.0% of ERN's net added FP removal over
B4 came from perfectly precise `LOCAL_CONFLICT`; `NON_EVIDENCED` contributed
44.0% and all material additional TP loss, while DIRECT evidence protected TP.
The loss was distributed across sources and channels, and the positive-pair
preservation advantage was not fold-stable.

**Decision at that checkpoint: `NEW_HYPOTHESIS_JUSTIFIED_PROTOCOL_NOT_FROZEN`.**
The next task at that checkpoint was to freeze a new prospective conservative
trust-gated/locality-aware reconciliation protocol. This is not R4 threshold
movement, channel selection, held-out rescue, feature addition, or architecture
escalation. No implementation or training was authorized at that checkpoint.

### Conservative reconciliation development

**Status: `CONSERVATIVE_RECONCILIATION_DEVELOPMENT_COMPLETE` /
`CONSERVATIVE_DEV_GATE_FAIL`.**

The protocol freezes CER/CCEG, the unchanged R4 feature contract and simple
branch architecture, paired `CER_EVIDENCE_MASKED` control, grouped Legacy121
development CV, validation-only calibration and thresholding, complete
KEEP/DELETE/ABSTAIN accounting, and a new `CONSERVATIVE_DEV_GATE`.

The development gate is not R4 Gate B. It retains event-pooled and RNA-balanced
TP preservation at least 0.99, event/RNA FP removal strictly above the frozen
P3 bars, and source consistency. It additionally requires both
NON_EVIDENCED preservation summaries at least 0.99, no evidence-attributable
reduction of NON_EVIDENCED preservation relative to the matched control, and
strictly more than 50% retention of the frozen R4 evidence-attributable FP-
removal increment under both aggregations.

Legacy121 assessment folds provide internal development evidence only. A gate
PASS could authorize only a separate final-policy/validation protocol freeze;
it would not constitute paper confirmation or automatically authorize R5,
R6, or external77.

The frozen execution completed 200/200 runs and all calibration/threshold
seals. CER met both 0.99 overall preservation bars, both FP-removal bars,
source consistency, positive matched evidence attribution, and majority R4
gain retention. It failed because NON_EVIDENCED TP preservation was lower than
the matched evidence-masked control in both event and RNA aggregation. The
development gate is final `CONSERVATIVE_DEV_GATE_FAIL`; no rescue variant is
authorized.

### Paper-story consolidation

**Status: `PAPER_STORY_AND_RESULTS_CONSOLIDATION_COMPLETE` /
`PAPER_STORY_VIABLE_WITH_CURRENT_RESULTS`.**

The primary paper framing is a bounded reliability/mechanistic study of why
better evidence information does not automatically yield safer non-local RNA
secondary-structure correction. The correction–preservation evaluation
framework is a secondary contribution. The viable claim is limited to clean
symbolic evidence on Legacy121 development data: usable evidence adds
residual-error signal beyond matched controls, while learned
`NON_EVIDENCED` propagation contributes both FP correction and collateral TP
loss.

The paper is not framed as a successful CER method paper. It does not claim
independent validation, unseen-predictor transfer, noisy/real-evidence utility,
safe non-local propagation, global-refolding superiority, or 3D benefit.
Canonical story, master table, hypothesis outcomes, figure/table plan, and
claim firewall are in `docs/paper_story_and_results_consolidation.md`.

### R5 — Noise robustness

**Not authorized after `R4_GATE_B_FAIL`.** Do not freeze or execute controlled
noise work without a new prospective project decision.

### R6 — Cross-predictor transfer

Run source-wise and LOMO analyses. Promote `model-agnostic` only if supported.

### R7 — Locked independent external test

Open external77 once after model, features, calibration, thresholds, and analysis are frozen.

### R8 — Real evidence

Audit and evaluate real probing modalities only if R4-R7 justify continuation.

### R9 — Final calibrated selective correction

Freeze KEEP/DELETE/ABSTAIN policy, final ablations, statistics, and claims.

### Optional — 2D -> 3D validation

Only after the 2D task is stable.

## 12. Go / No-Go Gates

### Gate A — Post-hoc necessity

If global constrained refolding dominates the post-hoc approach across the relevant TP-preservation / FP-removal trade-off, stop the post-hoc mainline.

Current status is `GATE_A_PASS_POSTHOC_NONDOMINATED`. B2 is a
`FULL_REFOLD_REFERENCE`: it removes more FP, whereas completed R4 preserves
more TP and has higher modification precision. This bounded non-dominance
decision does not override the failed Gate B.

### Gate B — Learned reconciliation utility

At the prospectively frozen operating point, learned R4 must satisfy all of:

```text
event-pooled TP_preservation       >= 0.99
RNA-balanced TP_preservation       >= 0.99
RNA-balanced FP_removal            >  0.489748
event-pooled FP_removal            >  0.347816
```

Improvement over P3 must occur in at least two sources including RNAfold or
PETfold; no single source may drive the success claim. Matched B4 remains a
mandatory, separately interpreted evidence-attribution control.

### Gate C — Noise robustness

If 5-10% controlled evidence noise causes negative structure utility or unsafe TP loss, do not make a real-evidence claim without first freezing a new trust mechanism.

### Gate D — Independent generalization

external77 is opened once. If the development effect does not preserve direction, do not claim cross-dataset generalization and do not tune on external77 to rescue the result.

## 13. Frozen Paper Story

```text
global constrained refolding is strong but sacrifices more source-predictor TP
-> prediction context ranks residual errors but does not guarantee a safe tail
-> matched ERN/B4 establishes incremental evidence signal across current sources
-> explicit/local evidence behavior is highly reliable
-> NON_EVIDENCED propagation creates both correction and collateral loss
-> CER restores absolute preservation but fails matched-control non-local safety
-> safe post-hoc correction requires correction–preservation and scope-resolved
   evidence-attribution evaluation, not discrimination or aggregate F1 alone
```

This is a reliability/mechanistic story, not a claim that CER passes its gate.

## 14. Phase II — Risk-Controlled Structured Evidence Refinement

Phase I is research-complete and retains its bounded paper story. Phase II is a
new research direction, not R4/CER rescue. Its central question is how sparse
evidence can be transported only through structurally justified paths, used to
make valid edits beyond deletion-only correction, and subjected to explicit
harmful-edit risk control.

The primary design direction is a modest typed candidate-pair representation
with separated prediction-context, evidence, and transport-eligibility terms;
learned edit energies; explicit cost relative to the source prediction; an exact
primary noncrossing decoder for KEEP/DELETE/ADD/REPLACE; ABSTAIN; and RNA-cluster
risk calibration. This design is justified by the novelty audit but is not
implemented. Its dataset/task/decoder/risk contracts are now frozen in
`PHASE2_DTP_V1.0`; the final learned architecture and method name remain open.

### Phase II data roles

- Legacy121: `PHASE1_HISTORICAL_DIAGNOSTIC_DATA` only.
- Development-v2: RNA3DB-2D experimental core plus RNASSTR/Rfam training-only
  supplements, with 80/80 identity and higher-priority family connected
  components, five disjoint roles and a 2024-12-04 PDB temporal cutoff.
- Final independent: a separately sealed Independent-v2 is the primary Phase II
  one-shot set. external77 remains unopened as a Phase I bridge asset.

### Phase II evidence ladder

- E0: clean symbolic evidence.
- E1: controlled contradiction/noise/missingness at 5%, 10%, 20%, and 30%.
- E2: SHAPE/DMS/PARS with paired accepted structures and frozen preprocessing.

No noisy or real evidence is authorized yet.

### Phase II roadmap

```text
P0  literature / novelty audit                         COMPLETE (design only)
P1  dataset and predictor audit                        COMPLETE / FROZEN
P2  structured task / dataset protocol freeze          COMPLETE / FROZEN
P3  minimal structured baseline                        NEXT PROPOSED / NOT STARTED
P4  primary model implementation                       NOT AUTHORIZED
P5  clean-evidence Development-v2                      NOT AUTHORIZED
P6  controlled-noise robustness                        NOT AUTHORIZED
P7  cross-predictor-family transfer                     NOT AUTHORIZED
P8  real probing evidence                              NOT AUTHORIZED
P9  independent one-shot test                          NOT AUTHORIZED
P10 optional 2D -> 3D                                  NOT AUTHORIZED
P11 manuscript / submission                            NOT AUTHORIZED
```

### Phase II frozen prospective gates

- P0 NOVELTY: PASS remains `PHASE2_PRIMARY_DIRECTION_JUSTIFIED`.
- P1 DATA/PROTOCOL: provenance, leakage, source panel, decoder, risk, metrics,
  controls and hashes are complete.
- P2 STRUCTURED BASELINE: ADD/REPLACE must add real correction headroom beyond
  deletion-only or the interpretation reverts to deletion-only.
- P3 SAFETY: finite-family control must improve HarmRate versus same-capacity
  no-risk control at nonzero useful coverage; all-abstain cannot pass.
- P4 PREDICTOR TRANSFER: direction survives every held-out predictor family.
- P5 NOISE: risk contract and useful coverage survive 5--10% corruption.
- P6 INDEPENDENT: sealed Independent-v2 one-shot direction is retained.
- P7 REAL EVIDENCE: required if the final venue/claim depends on probing.

The risk procedure freezes `alpha=0.10`, `delta=0.05` and at least 240
risk-calibration biological clusters. Other numerical gates remain unset until
scientifically/statistically justified prospectively. Failed gates do not
authorize architecture, split, seed or threshold rescue.

## 15. Current Execution State

**Do not train historical Stage E2.**

Phase I paper-story consolidation and Phase II P0--P2 protocol design are
complete. The next proposed task, requiring explicit authorization, is:

> **`IMPLEMENT_PHASE2_MINIMAL_STRUCTURED_BASELINES`**

That task is limited to synthetic-fixture schema, candidate, exact-DP,
action/component and risk-bound infrastructure under the frozen P3 plan. It
does not authorize the primary model, training, Development-v2 performance,
evidence generation, external77 or real-evidence work.

The completed execution state is:

```text
R4_COMPLETE
R4_GATE_B_FAIL
GATE_A_PASS_POSTHOC_NONDOMINATED
R5_NOT_AUTHORIZED
R4_POSTMORTEM_COMPLETE
CONSERVATIVE_RECONCILIATION_PROTOCOL_FROZEN
CONSERVATIVE_RECONCILIATION_DEVELOPMENT_COMPLETE
CONSERVATIVE_DEV_GATE_FAIL
PAPER_STORY_AND_RESULTS_CONSOLIDATION_COMPLETE
PAPER_STORY_VIABLE_WITH_CURRENT_RESULTS
PHASE1_RESEARCH_COMPLETE
PHASE1_PAPER_STORY_VIABLE
PHASE2_INITIATED
PHASE2_NOVELTY_AND_METHOD_DESIGN
PHASE2_PRIMARY_DIRECTION_JUSTIFIED
PHASE2_DATASET_AND_TASK_PROTOCOL_FROZEN
PHASE2_IMPLEMENTATION_NOT_AUTHORIZED
EXTERNAL77_LOCKED
```

Legacy121 is `PHASE1_HISTORICAL_DIAGNOSTIC_DATA`. external77 remains an
unopened one-shot asset and may be accessed only after the complete applicable
future method, calibration/risk policy, thresholds, evidence semantics, gates,
and analysis plan are frozen.

Detailed rationale and reboot contract: `docs/project_reboot_v2.md`.
