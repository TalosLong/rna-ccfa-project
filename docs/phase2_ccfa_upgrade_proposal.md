# Phase II CCF-A Upgrade Proposal

Status:

```text
PHASE2_INITIATED
PHASE2_NOVELTY_AND_METHOD_DESIGN
PHASE2_PRIMARY_DIRECTION_JUSTIFIED
PHASE2_DATASET_AND_TASK_PROTOCOL_FROZEN
IMPLEMENTATION_NOT_AUTHORIZED
```

Provisional research title:

> **Risk-Controlled Structured Evidence Refinement for RNA Secondary
> Structure Prediction**

This remains the research-direction document. The canonical dataset/task,
decoder and risk contracts are now frozen separately in
`docs/phase2_dataset_and_task_protocol.md`. The final method name and learned
architecture remain undecided, and no implementation or training is authorized.

## 1. Phase boundary

Phase I remains frozen:

```text
R4_COMPLETE
R4_GATE_B_FAIL
CONSERVATIVE_RECONCILIATION_DEVELOPMENT_COMPLETE
CONSERVATIVE_DEV_GATE_FAIL
PAPER_STORY_AND_RESULTS_CONSOLIDATION_COMPLETE
PAPER_STORY_VIABLE_WITH_CURRENT_RESULTS
```

Phase II does not reinterpret either failure. It does not move a threshold,
select a seed/channel/source, or replace the failed simple classifier with a
larger one on the same development loop.

Data roles change prospectively:

- Legacy121: **`PHASE1_HISTORICAL_DIAGNOSTIC_DATA`**. It can motivate and
  audit hypotheses, but it cannot be the main confirmatory basis for Phase II
  architecture selection or an independent validation claim.
- external77: **`ONE_SHOT_LOCKED`**. It was not accessed for this proposal and
  is not automatically assumed to match the revised Phase II task.
- Development-v2: required before model selection; see
  `docs/phase2_dataset_strategy.md`.

## 2. Central scientific question

Phase I established five bounded observations on clean symbolic evidence and
Legacy121 development data:

1. source-prediction context contains residual-error signal;
2. usable clean sparse evidence adds incremental signal;
3. DIRECT support and LOCAL_CONFLICT correction are highly reliable;
4. NON_EVIDENCED propagation creates both useful correction and collateral TP
   harm; and
5. simple context corroboration improves absolute preservation but does not
   remove evidence-attributable non-local harm relative to its matched control.

Therefore Phase II does not ask whether a larger classifier raises aggregate
metrics. It asks:

> **How can sparse structural evidence be transported through an existing RNA
> secondary-structure prediction only when its effect is structurally justified
> and statistically safe, while allowing the structure to be edited beyond
> deletion-only correction?**

The new scientific objects are transport eligibility, structured edit cost,
and harmful-edit risk—not network size.

## 3. Candidate structured task

### 3.1 Inputs and output

Candidate inputs are RNA sequence `x`, an existing source prediction `S0`,
sparse evidence `E`, and inference-time source outputs whose eligibility will be
frozen later. The output is either a valid refined structure `S*` or an explicit
decision to leave some or all of `S0` unchanged.

### 3.2 Candidate-pair graph

Graph nodes represent:

- original pairs in `S0`; and
- plausible alternative pairs permitted by the prospective base-pair and loop
  policy.

Typed relations may represent:

- stacking adjacency;
- same-stem membership;
- shared-nucleotide competition;
- alternative-partner competition;
- sequence-local proximity; and
- direct evidence support or evidence conflict.

This graph is a representation choice, **not a standalone novelty claim**.
Message passing must not turn every evidence item into unrestricted global
influence. A later protocol must define and test an explicit transport gate.

### 3.3 Structured action space

The proposed Phase II action vocabulary is:

- `KEEP`: retain an original pair;
- `DELETE`: remove an original pair;
- `ADD`: commit a candidate pair absent from `S0`;
- `REPLACE`: atomically remove an original partner and add a new partner;
- `ABSTAIN`: preserve the affected original region or full RNA because the
  policy cannot commit within its safety contract.

`ADD` and `REPLACE` are scientifically necessary because deletion-only Phase I
cannot repair false negatives, wrong partners, or shifted stems. `REPLACE` must
be an atomic coupled edit for evaluation and decoding, rather than a favorable
ADD reported separately from its necessary harmful DELETE.

### 3.4 Validity contract to be frozen later

The primary track should enforce:

- at most one partner per nucleotide;
- a prospectively fixed canonical/wobble alphabet (candidate default:
  AU/UA, GC/CG, GU/UG);
- a prospectively fixed minimum hairpin-loop length;
- a noncrossing primary structure; and
- deterministic tie-breaking.

An unconstrained neural decoder is prohibited. Pseudoknots should be annotated
and scored separately. They are an optional secondary track, not a reason to
weaken the primary validity contract.

## 4. Evidence-scope semantics

The Phase I taxonomy remains useful but its actions are no longer hard-coded:

- **DIRECT:** evidence refers to the candidate pair itself. The model should
  generally protect supported original pairs and may consider directly
  supported alternative pairs, subject to evidence reliability and structure
  validity.
- **LOCAL:** an evidence item has an explicit structural relation to the edit,
  such as shared-nucleotide conflict, adjacent stack continuation, or a
  predefined local stem relation.
- **PROPAGATED / NON_EVIDENCED:** evidence reaches a candidate only through a
  declared sequence of graph relations. Its influence must be gated by learned
  or rule-defined transport eligibility and audited by path length/type.

Candidate trust is conceptually:

\[
T(p,e)\in[0,1],
\]

where `T` measures whether evidence item `e` has a structurally justified path
to affect candidate pair `p`. This is not generic attention: the path types,
normalization, maximum transport radius or budget, and supervision/control must
be prospectively specified. A matched trust-shuffled or relation-ablated control
is required to show that gains arise from justified paths rather than extra
capacity.

## 5. Three candidate model families

### Candidate A — Pair-Graph Trust Refinement

Components: typed candidate-pair graph, modest relational GNN or Graph
Transformer, explicit evidence-to-pair trust transport, and exact structured
decoder.

Strength: directly models stacking, competition, alternative partners, and
evidence paths. Weakness: high risk of being reviewed as “RNA + GNN,” with
capacity and trust intertwined.

### Candidate B — Energy-Based Minimal-Edit Refinement

Components: learned candidate/edit energy, explicit evidence-conditioned energy
terms, edit cost relative to `S0`, ABSTAIN, and exact optimization:

\[
S^*=\arg\max_{S'\in\mathcal V(x)}
\bigl[f_\theta(S'\mid x,S_0,E)-\lambda_{edit}C(S',S_0)\bigr].
\]

Strength: interpretable and sharply distinct from unconstrained global
refolding. Weakness: decoder and learned energy precedents are strong; without
new risk/transport machinery, ML novelty is limited.

### Candidate C — Risk-Controlled Structured Refinement

Components: typed pair graph or equivalent relational representation;
separated source-context, evidence, and transport-eligibility terms; a
minimum-edit exact decoder; and a selective controller calibrated on held-out
RNA clusters to limit a prospectively defined harmful-edit loss.

Strength: directly answers Phase I's failure mechanism and could contribute a
general predict-then-edit risk-control formulation. Weakness: formal guarantees
depend on a nested policy family, exchangeable calibration units, adequate
cluster sample size, and a monotone loss. If these fail, the contribution must
be empirical rather than conformal.

### 5.1 Comparative scorecard

Each score is 1 (weak/unfavorable) to 5 (strong/favorable). For compute and data,
a higher score means lower resource burden. Scores are design judgments, not
experimental results.

| Criterion | A: Pair-Graph Trust | B: Minimal-Edit Energy | C: Risk-Controlled Structured |
| --- | ---: | ---: | ---: |
| Scientific rationale | 4 | 4 | 5 |
| ML novelty | 3 | 3 | 5 |
| RNA novelty | 3 | 4 | 5 |
| Answers Phase I failure | 4 | 4 | 5 |
| Interpretability | 3 | 5 | 4 |
| Risk-control rigor | 2 | 3 | 5 |
| Structured validity | 4 | 5 | 5 |
| Implementation feasibility | 3 | 5 | 3 |
| Compute requirement | 2 | 5 | 3 |
| Data requirement | 3 | 4 | 3 |
| CCF-A potential | 3 | 3 | 5 |
| Q1 journal potential | 4 | 4 | 5 |
| **Total / 60** | **38** | **49** | **53** |

Score rationale:

- **Scientific rationale / Phase I fit:** C receives 5 because harmful-edit
  control is the missing scientific object exposed by R4/CER; A and B receive 4
  because transport structure and minimal editing address only parts of that
  failure.
- **ML and RNA novelty:** graph encoders, pair maps, energy objectives, and
  exact decoding are crowded prior art, limiting A/B to 3--4. C receives a
  conditional 5 only for the joint formulation of preservation-aware evidence
  transport, valid editing, and biological-unit risk control—not for any
  component alone.
- **Interpretability:** B's explicit edit energies and cost earn 5. C retains
  those terms but adds a controller and calibration assumptions (4); A's
  message passing is harder to attribute without path-level audits (3).
- **Risk rigor / validity:** A has no intrinsic risk mechanism (2), while B can
  abstain empirically but does not itself provide formal control (3). C makes
  the safety loss and controller primary (5). B/C both pair learned scores with
  exact decoding (5); A depends more heavily on the later decoder choice (4).
- **Feasibility, compute, and data:** B is the lightest and most reproducible
  option (all 5). A has heavier graph construction/training (3 feasibility, 2
  compute), while C needs isolated calibration roles and enough independent
  RNA/family clusters (3 across these criteria).
- **Publication potential:** A and B are credible Q1 method directions but weak
  CCF-A claims in isolation. C has the highest potential only if it produces a
  generalizable risk-control result plus transfer and independent evidence; a
  routine GNN-plus-threshold implementation would score substantially lower.

## 6. Primary direction decision

Decision: **`PHASE2_PRIMARY_DIRECTION_JUSTIFIED`**.

Primary architecture concept: **Candidate C, a preservation-aware,
risk-controlled structured refinement system**, provisionally composed of:

1. a modest typed candidate-pair graph encoder;
2. explicitly separated context, evidence, and transport-eligibility scores;
3. learned edit energies plus a transparent cost for departing from `S0`;
4. a deterministic exact noncrossing decoder for KEEP/DELETE/ADD/REPLACE;
5. ABSTAIN as a first-class action; and
6. an RNA-cluster-calibrated harmful-edit risk controller.

Candidate B is the required strong simpler baseline and a fallback if formal
risk control proves impossible. Candidate A provides representation ablations,
not the primary claim.

This direction is more than replacing an MLP with a GNN because its testable
contribution is the *decision system*: evidence can act only through auditable
relations; valid changes optimize a cost relative to an existing prediction;
and committed edits are selected under a predeclared risk objective. A GNN that
raises F1 without those components would fail the Phase II question.

The decision is conditional on Gate P0 being rechecked before protocol freeze.
No architecture, feature, or hyperparameter is frozen here.

## 7. Decoder options

| Decoder | Noncrossing | Pseudoknots | Differentiability | Complexity / speed | Reproducibility | Phase II role |
| --- | --- | --- | --- | --- | --- | --- |
| Dynamic programming | Exact for declared nested grammar | No in standard form; restricted classes can be expensive | Usually no; structured losses can train scores without differentiating through argmax | Typically cubic for rich secondary-structure recurrences; practical variants exist | High with fixed tie-breaks | **Primary recommendation** |
| Integer linear programming | Yes with crossing-exclusion constraints | Yes if crossing variables/classes are allowed | No by default | Potentially slow and solver-dependent | High only with version/options/tolerances frozen | **Optional pseudoknot extension** |
| Maximum-weight / K-rook matching | Enforces one partner | Can permit crossings | No | Polynomial and often fast | High | RFold/Suh-style comparator; insufficient alone for primary noncrossing constraint |
| Differentiable structured optimization | Depends on relaxation | Depends on formulation | Yes/approximate | Training and numerical complexity are high | More fragile | Research ablation only, not default |
| Neural scoring + exact decoder | Determined by chosen exact solver | Determined by chosen solver | Score model differentiable; decoder need not be | Moderate | High | **Recommended composition**; compare RFold/DEPfold-style structured decoding |

Primary recommendation: neural edit scoring followed by an exact,
deterministic, noncrossing DP decoder with an explicit edit-cost term. Optional
pseudoknot track: frozen ILP with one-partner, pair-alphabet, minimum-loop, and
declared crossing-class constraints. The two tracks must never be pooled without
separate reporting.

## 8. Predictor strategy

Phase II needs structural diversity among source predictors, not a long list.
Candidate deployability audit:

| Predictor | Family / useful output | Phase II role | Caveat |
| --- | --- | --- | --- |
| RNAfold | Thermodynamic; MFE/BPP available | Historical anchor and probabilistic context | Same thermodynamic family as several comparators |
| PETfold | Comparative/thermodynamic | Historical comparative anchor | Requires usable homologous alignment semantics |
| trRosettaRNA2 | Deep 3D pipeline with secondary output | Historical deep-source bridge | Installation/runtime and output provenance must be audited |
| MXfold2 | Learned + thermodynamic DP | **Priority modern 2D source** | Training-data overlap must be audited |
| UFold | End-to-end contact-map DL | **Priority modern 2D source** | Output validity/post-processing and length limits must be frozen |
| RFold or DEPfold | Structured neural matching/parsing | Conditional modern source; choose at most one initially | Code/checkpoint maturity, score export, training overlap, and pair/pseudoknot semantics must be audited |
| RiNALMo or ERNIE-RNA | Foundation-model 2D predictor | Conditional modern family source | Heavy compute/licensing/checkpoint reproducibility; choose at most one initially |
| NuFold | End-to-end RNA **3D** predictor using predicted 2D as input | Optional later 2D→3D evaluation only | Not a like-for-like Phase II secondary-structure source predictor |

Minimum useful family panel for Development-v2 is four deployable families:
thermodynamic, comparative, learned-thermodynamic, and end-to-end neural. Add a
foundation-model source only if checkpoints, inference, pair scores, licensing,
and compute are reproducible.

Future evaluation must perform leave-one-predictor-family-out rather than only
record-wise source stratification. Predictor identity should not be a model
input by default; it is an evaluation/grouping variable. A source-specific
threshold is prohibited unless a later protocol provides an independent
scientific rationale and equally strong held-out calibration.

## 9. Evidence ladder

Phase II retains three levels but defines them independently of old R5--R8
numbering:

- **E0 clean symbolic evidence:** exactly interpretable pair and unpaired
  statements; used first to test task mechanics, transport, and edit accounting.
- **E1 controlled noisy symbolic evidence:** prospectively generated 5%, 10%,
  20%, and 30% corruption levels, with contradiction, false-positive evidence,
  false-negative/missing evidence, and coverage missingness separated rather
  than collapsed into one number.
- **E2 real probing evidence:** SHAPE, DMS, and PARS candidates. Dataset
  eligibility requires raw/processed provenance, condition matching, mapping
  from reactivity to model input frozen without GT tuning, and an accepted
  paired reference structure. RMDB is a candidate source; the Hajdin SHAPE and
  Cordero DMS benchmarks are small anchors, while PARS provides scale but often
  lacks a single molecule-specific paired ground truth.

No evidence was downloaded or regenerated in this task.

## 10. Risk-control concept

The future primary safety quantity is a per-RNA harmful-edit loss, with atomic
accounting for correct and harmful DELETE/ADD/REPLACE actions. A candidate is:

\[
H_R(\lambda)=
\frac{\#\text{ harmful committed edit atoms on RNA }R}
     {\max(1,\#\text{ committed edit atoms on RNA }R)}.
\]

TP preservation remains a non-negotiable companion metric because HarmRate can
look favorable when coverage is tiny or when an accounting convention hides
deleted TPs. The policy should expose a nested coverage/risk family indexed by
`lambda`, and calibration must occur on RNA or predeclared family-cluster units.

The intended formal target is initially:

\[
\mathbb E_R[H_R(\hat\lambda)]\leq\alpha
\]

under stated exchangeability and monotonicity assumptions, using a method such
as conformal risk control. This is **not** equivalent to
`P(H_R <= alpha) >= 1-delta`, and Phase II must not claim the latter without a
separate quantile/high-probability construction. If the assumptions or sample
size are inadequate, the locked fallback label is empirical selective risk
control. Details are in `docs/phase2_risk_control_design.md`.

## 11. Evaluation design

All future reports must include:

1. **Pair reliability:** AUPRC, AUROC, Brier, ECE, and reliability diagrams.
2. **Structure utility:** precision, recall, F1, and per-RNA distributions.
3. **Preservation:** TP preservation, FP removal, modification precision, and
   full beneficial/harmful edit accounting.
4. **Structured editing:** correct/harmful DELETE, ADD, and atomic REPLACE;
   edit distance to `S0`; validity-violation count.
5. **Selective risk:** coverage, harmful-edit risk, risk–coverage curve, and
   ABSTAIN at pair/region/RNA levels as applicable.
6. **Scope:** DIRECT, LOCAL, and PROPAGATED/NON_EVIDENCED contributions.
7. **Source generalization:** leave-one-predictor-family-out, not only pooled
   or source-stratified reporting.
8. **Evidence robustness:** separately reported corruption and missingness
   levels.
9. **Independent test:** one-shot evaluation only after complete policy lock.
10. **Optional 3D:** paired downstream evaluation with one frozen 3D pipeline;
    never inferred from 2D F1 alone.

Primary aggregation units and the finite-family risk procedure are now frozen
in `PHASE2_DTP_V1.0`. RNA and family-cluster summaries accompany event pooling.

## 12. Prospective Phase II gates

Gate definitions are frozen in the canonical protocol:

- **P0 NOVELTY:** PASS remains `PHASE2_PRIMARY_DIRECTION_JUSTIFIED`.
- **P1 DATA/PROTOCOL:** provenance, leakage, source panel, decoder, risk,
  metrics, controls and hashes must be complete.
- **P2 STRUCTURED BASELINE:** ADD/REPLACE must add correction headroom over
  deletion-only or the interpretation reverts to deletion-only.
- **P3 SAFETY:** finite-family risk control must improve HarmRate over the
  same-capacity no-risk control at nonzero useful coverage.
- **P4 PREDICTOR TRANSFER:** direction survives every held-out family.
- **P5 NOISE:** the risk contract/useful coverage survive 5% and 10% corruption.
- **P6 INDEPENDENT:** Independent-v2 one-shot direction is retained.
- **P7 REAL EVIDENCE:** required when the final venue/claim depends on probing.

Only `alpha=0.10`, `delta=0.05`, and the 240-cluster risk readiness minimum are
numerical now. Other thresholds require prospective scientific/statistical
justification and are not copied from Phase I.

A failed gate freezes that claim and triggers review; it does not automatically
authorize a larger architecture, alternate split, or threshold rescue.

## 13. Phase II roadmap

```text
P0  literature / novelty audit                         COMPLETE (design only)
P1  dataset and predictor audit                        COMPLETE / FROZEN
P2  structured task and protocol freeze                COMPLETE / FROZEN
P3  minimal structured baselines                       NEXT PROPOSED / NOT STARTED
P4  primary model implementation                       NOT AUTHORIZED
P5  clean-evidence Development-v2                      NOT AUTHORIZED
P6  controlled-noise robustness                        NOT AUTHORIZED
P7  cross-predictor-family transfer                     NOT AUTHORIZED
P8  real probing evidence                              NOT AUTHORIZED
P9  one-shot independent test                          LOCKED / NOT AUTHORIZED
P10 optional 2D -> 3D                                  NOT AUTHORIZED
P11 manuscript / submission                            NOT AUTHORIZED
```

P1/P2 are complete. P3 begins only on explicit authorization under the frozen
minimal-baseline implementation plan; primary-model implementation remains
unauthorized.

## 14. Publication potential

### CCF-A stretch assessment

**Potential: conditional / high risk.** AAAI, IJCAI, ICML, or NeurIPS would
require a transferable ML contribution: a formal or rigorously validated
structured harmful-edit controller, a nontrivial relation between evidence
transport and valid edit decoding, multiple biological/predictor families,
strong generic baselines, and evidence that the method is not RNA-specific
feature engineering plus a standard GNN. RNA accuracy alone is insufficient.

### Strong Q1 computational-biology assessment

**Potential: realistic if fully validated.** A strong journal path can rest on
the biological refinement problem, transparent structured decoder, modern
predictors, family-aware Development-v2, real probing evidence, and one-shot
independent validation. It still requires a substantial method or biological
insight rather than incremental benchmark improvement. Venue-specific analysis
is in `docs/phase2_target_venues.md`.

## 15. Claim firewall

This proposal does not establish:

- a final method or method name;
- model-agnostic or unseen-predictor transfer;
- safe evidence transport;
- a conformal or high-probability guarantee;
- noisy- or real-evidence robustness;
- independent validation;
- benefit over all global refolding methods;
- pseudoknot performance;
- 3D benefit; or
- CCF-A / Q1 acceptance likelihood.

## 16. Next proposed task

Because the qualified joint novelty gap is defensible and P1/P2 are frozen, the
next proposed task, requiring explicit authorization, is:

```text
IMPLEMENT_PHASE2_MINIMAL_STRUCTURED_BASELINES
```

That task is limited to synthetic-fixture schema, candidate, exact-DP,
action/component and risk-bound infrastructure in
`docs/phase2_p3_minimal_baseline_implementation_plan.md`. It does not authorize
the primary model, training, evidence generation, biological performance or
independent-data access.
