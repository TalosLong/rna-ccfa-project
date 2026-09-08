# Phase II Risk-Control Design

Status: **`PHASE2_RISK_CONTROL_PROTOCOL_FROZEN`**

Protocol: **`FINITE_FAMILY_RISK_CONTROLLING_POLICY_SELECTION`**

Implementation: **`NOT_AUTHORIZED`**

## 1. Objective

Phase I used calibrated pair-error scores and validation-selected thresholds,
then evaluated TP preservation. That is careful empirical operating-point
selection, but it is not conformal risk control and does not provide a
finite-sample safety guarantee.

Phase II should ask a sharper question:

> Among edits that preserve RNA validity, which edits can be committed while
> controlling collateral damage to an existing prediction at a declared
> biological unit and coverage?

The risk controller is downstream of model scoring and structured decoding. It
must not hide unsafe edits by excluding ABSTAIN cases from denominators.

## 2. Four concepts that must not be conflated

| Concept | Purpose | What it can support | What it cannot support alone |
| --- | --- | --- | --- |
| Probability calibration | Align predicted probabilities with empirical frequencies | Brier/ECE/reliability claims on an allowed partition | A guaranteed safe edit rate or choice of action |
| Thresholding | Convert a score into KEEP/edit decisions | A fixed empirical operating point | Distribution-free control, unless embedded in a valid risk procedure |
| Selective prediction | Permit ABSTAIN and study risk versus coverage | Risk–coverage trade-offs and reject-option utility | Finite-sample guarantees by default |
| Formal risk control | Use held-out calibration and stated assumptions to select a policy with a finite-sample bound | Only the exact risk and sampling unit proved by the method | Conditional, per-family, or per-RNA guarantees not present in the theorem |

Platt scaling plus a threshold must never be described as conformal. A
conformal prediction set is also not automatically a safe edit policy: coverage
of the true label and harmful-edit loss are different quantities.

## 3. Edit and harm accounting

### 3.1 Atomic actions

Let `S0` be the source prediction and `S*` the committed refinement. Evaluation
uses atomic pair changes:

- DELETE atom: pair in `S0` but absent from `S*`;
- ADD atom: pair absent from `S0` but present in `S*`;
- REPLACE action: one linked DELETE atom plus one linked ADD atom sharing the
  reassigned nucleotide;
- KEEP and ABSTAIN: no committed atom.

A correct REPLACE requires both removal of the wrong original partner and
addition of an accepted new partner under the frozen exact/tolerant scoring
policy. Reporting only the beneficial half is prohibited.

### 3.2 Harmful edit

Against reference structure `Y`, a committed atom is harmful when:

- DELETE removes a pair accepted in `Y`;
- ADD introduces a pair not accepted in `Y`; or
- either half of a REPLACE is harmful.

The protocol may also report action-level REPLACE harm, where any harmful atom
makes the coupled action harmful. Atom-level and action-level summaries must not
be mixed.

### 3.3 Primary safety quantity

For RNA `R`, the proposed primary reporting quantity is:

\[
\operatorname{HarmRate}_R=
\frac{H_R}{\max(1,A_R)},
\]

where `H_R` is harmful committed edit atoms and `A_R` is all committed edit
atoms. RNAs with no committed edits have HarmRate zero **and coverage zero**;
both must always be reported. The primary aggregate is the mean across RNAs or
predeclared biological clusters, not the micro-average across millions of
dependent pair candidates.

Mandatory companions are:

- TP preservation, so deletion of correct source information remains visible;
- modification precision `1 - HarmRate` under exactly matching atom semantics;
- committed-edit coverage and RNA-level non-abstention coverage;
- harmful edit count per RNA;
- beneficial DELETE/ADD/REPLACE counts; and
- DIRECT, LOCAL, and PROPAGATED harm decomposition.

## 4. Why the intuitive probability statement is not automatic

The statement

\[
P(\operatorname{HarmRate}_R\leq\alpha)\geq1-\delta
\]

is a quantile/per-RNA statement. Standard calibration, selective prediction,
and expected-risk conformal control do not imply it. [Conformal Risk
Control](https://research.google/pubs/conformal-risk-control/) controls the
expected value of a suitable monotone loss; [risk-controlling prediction
sets](https://www.gsb.stanford.edu/faculty-research/publications/distribution-free-risk-controlling-prediction-sets)
likewise require the claimed loss and calibration scheme to match the theorem.

The project should initially target the more defensible population statement:

\[
\mathbb E_R[\operatorname{HarmRate}_R(\hat\lambda)]\leq\alpha,
\]

with a separately declared confidence level over calibration sampling. This is
still not automatically valid because HarmRate has a changing denominator and
structured decoding can make policy outputs non-nested.

If the project later wants the per-RNA probability statement, it must freeze a
quantile-risk or conformal construction designed for it, demonstrate adequate
calibration clusters, and state whether validity is marginal or conditional.

## 5. Candidate control mechanisms

### 5.1 Conformal risk control over a nested policy family

Candidate: define policies `pi_lambda` so that increasing conservatism removes
committed edits without altering remaining edits, and choose `lambda` using an
RNA-cluster calibration split.

Advantages:

- finite-sample, distribution-free expected-loss control may be possible under
  exchangeability and the exact monotonicity conditions;
- directly yields a risk–coverage curve; and
- makes ABSTAIN operational rather than decorative.

Critical problem: exact structured decoding may replace one edit with another
when a score threshold changes. HarmRate may also rise or fall as its denominator
changes. Neither the policy family nor this loss is automatically monotone.
Therefore CRC is the preferred research candidate, not a pre-approved theorem.

### 5.2 Finite-family risk-controlling policy selection

Candidate fallback: freeze a finite collection of complete valid edit policies,
evaluate each once on independent calibration RNA clusters, construct
simultaneous upper confidence bounds for mean HarmRate, and select the
highest-coverage policy whose upper bound is at most `alpha`.

Advantages:

- does not require pretending a non-nested decoder family is nested;
- policy selection and multiplicity can be audited; and
- can certify the exact end-to-end structured action engine.

Limitations:

- the bound and multiplicity method must be prospectively chosen;
- cluster count may make it conservative; and
- it is “risk-controlling policy selection,” not necessarily conformal risk
  control.

### 5.3 FDR-style edit selection

Conformal p-values plus an FDR procedure are attractive because the scientific
quantity resembles the fraction of harmful selected edits. [Selection by
Prediction with Conformal p-values](https://jmlr.org/papers/v24/22-1176.html)
is relevant prior art.

However, RNA edits are coupled through one-partner and noncrossing constraints,
multiple edits share an RNA, and REPLACE has linked atoms. Classical BH
conditions cannot be assumed. FDR control is a companion research option only
after dependence and selection effects are resolved; it is not the primary
current design.

### 5.4 Per-RNA or cluster-conditional control

Family/Mondrian-style calibration might expose heterogeneity, but subgroup
validity requires enough calibration units and predeclared groups. Using
source-, length-, or family-specific thresholds after observing failures would
repeat Phase I's forbidden rescue pattern. Primary guarantees should therefore
be marginal across independent RNA/family clusters, with source/family results
as audits unless a valid simultaneous group-control procedure is frozen.

## 6. Frozen primary design

The protocol audit applied the following hierarchy:

1. **Safety loss:** RNA-balanced HarmRate with full edit-atom accounting.
2. **Safety guard:** RNA-balanced and event-pooled TP preservation.
3. **Policy family:** predeclared complete structured component-commitment
   policies with ABSTAIN.
4. **Calibration unit:** family/identity-disjoint RNA clusters from
   Development-v2, never candidate pairs.
5. **Formal-route audit:** standard conformal risk control is rejected because
   the end-to-end policy and HarmRate loss are not nested/monotone.
6. **Selected route:** finite-family simultaneous risk upper bounds selected on
   an isolated calibration split.
7. **Fail-closed route:** if the frozen finite-family assumptions/readiness do
   not hold, return all-abstain and make no formal useful-policy claim.

The exact target, bound, policy family and tie handling are frozen in Section
13 and the canonical dataset/task protocol.

## 7. Data partition contract

A defensible future split needs at least:

- model-training families/clusters;
- model-selection/early-stopping families/clusters;
- score-calibration families/clusters, if probability calibration is used;
- risk-control calibration families/clusters not used to choose the model or
  design the policy family; and
- Development-v2 assessment families/clusters used once after policy lock.

If sample size forces score calibration and risk calibration to share data,
the protocol must use a method whose validity covers that reuse or explicitly
downgrade the claim. Pair events from one RNA do not increase the number of
exchangeable calibration units.

external77 and any future Independent-v2 set cannot calibrate risk. They only
test whether the locked direction and empirical risk behavior transfer.

## 8. Selective action semantics

ABSTAIN was compared at three levels:

- **edit-level:** do not commit a particular otherwise valid edit;
- **region-level:** preserve a coupled stem/competition component when actions
  cannot be made safely in isolation;
- **RNA-level:** return `S0` unchanged when no policy meets the risk contract.

The frozen primary level is component/region-level abstention because RNA
validity couples competing pairs. Every abstained item remains in reliability
and coverage accounting. An RNA returned unchanged is not a successful edit and
must contribute zero edit coverage.

## 9. Required controls

The risk-control experiment must compare:

- no refinement (`S0`);
- Phase I local evidence correction;
- full evidence-constrained refolding;
- deletion-only structured refinement;
- minimum-edit structured refinement without risk control;
- risk-controlled structured refinement;
- matched evidence-masked control;
- trust-shuffled or relation-ablated control with matched capacity; and
- calibration/threshold-only empirical control.

These separate benefits from architecture, evidence, structured validity,
minimal editing, and risk selection. Source/family-specific outcomes are always
reported, never cherry-picked.

## 10. Metrics and diagnostic plots

Required risk reporting includes:

- mean HarmRate across RNAs and clusters with uncertainty intervals;
- micro HarmRate as a secondary descriptive statistic;
- risk upper bound and nominal `alpha`, if a formal procedure is valid;
- risk–coverage and TP-preservation–coverage curves;
- harmful edits per RNA and tail quantiles;
- fraction of RNAs with any harmful edit;
- DELETE/ADD/REPLACE atom- and action-level harm;
- DIRECT/LOCAL/PROPAGATED risk and coverage;
- evidence-attributable risk versus the matched evidence-masked control;
- source/predictor-family, RNA-family, length, and evidence-level audits; and
- abstention rates at all enabled levels.

A lower average HarmRate caused solely by near-zero coverage is not success.
Utility and coverage gates must be conjunctive with safety.

## 11. Validity checklist before any formal claim

- The risk and denominator were frozen before assessment.
- The complete structured policy, not isolated pair scores, is calibrated.
- Calibration units are RNA/family clusters and role-disjoint.
- The policy family is fixed before risk calibration.
- Required monotonicity/nesting is proved or exhaustively verified where
  finite.
- Exchangeability assumptions and known violations are documented.
- Model selection did not reuse the risk-calibration labels improperly.
- Multiple candidate policies/groups are handled by the declared correction.
- Zero-edit and all-abstain behavior is explicit.
- Independent data are never used for calibration or rescue.
- The written claim matches expected, quantile, marginal, or group-conditional
  validity exactly.

Failure of any necessary item blocks the word “conformal” or “guaranteed.”

## 12. Theorem audit conclusion

Standard conformal risk control requires a suitable monotone loss along a
nested/conservative policy parameter; this is explicit in the ICLR 2024
[Conformal Risk Control](https://research.google/pubs/conformal-risk-control/)
result. The proposed structured decoder does not meet that contract:

- changing an edit penalty or threshold can replace one valid structured edit
  with another instead of returning a subset of the former edit set;
- component recombination couples decisions; and
- HarmRate has a policy-dependent denominator, so deleting a committed edit can
  increase or decrease the realized ratio.

Consequently, neither policy nestedness nor loss monotonicity can be proved.
The selected primary route is therefore **not**
`FORMAL_CONFORMAL_RISK_CONTROL`. It is the discrete, complete-policy alternative
below, aligned with risk-controlling prediction-set/Learn-then-Test reasoning
for bounded loss ([Bates et al.](https://arxiv.org/abs/2101.02703)).

## 13. Frozen finite-family risk-controlling policy selection

### 13.1 Target and calibration unit

For RNA `R`, freeze

\[
L_R=\operatorname{HarmRate}_R=H_R/\max(1,A_R)\in[0,1].
\]

For biological component `C`, define `L_C` as the unweighted mean `L_R` over
RNA records in that component. Independent/exchangeable Development-v2
biological components are the calibration observations. The controlled
population quantity is the expected cluster-balanced per-RNA loss
`E_C[L_C]`, not a conditional family guarantee and not
`P(HarmRate_R <= alpha)`.

No-edit RNAs have HarmRate 0 and edit coverage 0. They remain in the loss mean,
RNA coverage denominator and all-abstain report. Pair events, predictors and
evidence realizations within a cluster are not extra calibration samples.

### 13.2 Score calibration is separate from risk control

The future scorer must emit one real-valued harmfulness logit `z_a` for every
proposed edit atom. On SCORE_CALIBRATION only, fit one source-independent
monotone Platt map

\[
\hat p_a=\operatorname{sigmoid}(a z_a+b),\qquad a\ge0,
\]

by minimizing RNA-balanced binary log loss plus
`1e-6*(a^2+b^2)`: every RNA has total weight one, divided equally over its
proposed atoms. Fit one map across all predictor families; source-specific maps
are prohibited. Exact optimizer/tolerance and fitted parameters must be sealed
before RISK_CALIBRATION. Degenerate one-class or nonfinite calibration fails
closed to all-abstain rather than switching calibrators.

This Platt map is ordinary probability calibration. It supplies the fixed score
used to define complete policies but contributes no formal guarantee. The
simultaneous bounded-loss risk calibration below is the control mechanism.

### 13.3 Fixed policy family

After model, score calibration, decoder and `lambda_edit` are locked, define a
component harm score as the maximum calibrated harmful-atom probability among
the atoms in the component. The six complete policies are:

```text
K = 6
tau in {0.010, 0.025, 0.050, 0.100, 0.200, 1.000}
pi_tau commits a component iff its maximum harm score <= tau;
otherwise it restores that complete component to S0.
```

Each `pi_tau` includes exact decoding, component construction, reversion and
validity audit. The family is frozen before RISK_CALIBRATION labels are used.
An all-abstain sentinel is a failure fallback and not one of the six candidates.
Direct, mutually consistent E0 hard facts remain feasibility constraints.

The six thresholds are a prospectively logarithmic/coarse resolution grid over
the calibrated harmfulness scale, including the declared 0.10 risk target and a
no-score-rejection endpoint. They are policy definitions, not observed-result
gates, and cannot be densified after risk outcomes.

### 13.4 Simultaneous upper bounds and selection

Freeze `alpha=0.10` and `delta=0.05`. For `n` independent risk-calibration
components and policy `k`, compute mean bounded loss `bar_L_k` and

\[
U_k=\min\left(1,\bar L_k+
\sqrt{\frac{\log(K/\delta)}{2n}}\right).
\]

Hoeffding's inequality with a union bound makes all six upper bounds
simultaneous at confidence at least `1-delta`, under the stated sampling
assumptions. Choose among policies with `U_k <= alpha` by:

1. highest committed edit-atom coverage;
2. highest RNA-level coverage;
3. smallest `U_k`;
4. fewest committed atoms; then
5. smallest `tau`.

All comparisons use exact unrounded sufficient statistics; reported values may
be rounded only after selection. If no policy qualifies, return all-abstain and
declare that no nontrivial risk-controlled policy was found. Zero coverage can
never pass the Phase II safety gate.

The values have a prospective interpretation: `alpha=0.10` targets at least
90% modification precision under matching atom accounting, while `delta=0.05`
is the confidence budget over risk-calibration sampling. They are not inherited
from Phase I's 0.99 TP-preservation gate.

### 13.5 Readiness and assumptions

At zero empirical loss, the frozen bound can satisfy `U_k<=0.10` only when

\[
n\ge \left\lceil\log(6/0.05)/(2\times0.10^2)\right\rceil=240.
\]

Thus RISK_CALIBRATION must contain at least 240 disjoint biological components.
Fewer components fail formal readiness; roles cannot be merged and the bound
cannot be changed after outcomes.

The confidence statement is conditional on: the six policies being fixed
before risk outcomes; independent/exchangeable biological components from the
target Development-v2 population; bounded correctly labeled loss; no use of
risk-calibration data in training/model/score-calibrator/policy-family design;
and complete inclusion of no-edit/abstained RNAs. Family/source shift is audited
and tested by LOPFO and Independent-v2; it is not covered by the marginal bound.

### 13.6 Frozen claim language

If assumptions and readiness pass, the allowed statement is:

> With probability at least 0.95 over the risk-calibration components, the
> selected member of the six predeclared complete structured policies has
> expected cluster-balanced per-RNA HarmRate at most 0.10 for an exchangeable
> new component from the same target population.

Do not call this conformal, per-RNA, family-conditional, predictor-conditional,
distribution-shift robust, or an FDR guarantee. If any assumption fails, report
`EMPIRICAL_SELECTIVE_RISK_CONTROL` for that analysis and remove formal claim
language.
