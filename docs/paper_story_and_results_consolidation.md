# Paper Story and Results Consolidation

Status: **`PAPER_STORY_VIABLE_WITH_CURRENT_RESULTS`**

Date: 2026-09-08

Evidence boundary: all quantitative findings below are frozen Legacy121
development results. Legacy121 is not an independent validation set for any
post-R4 method. This consolidation does not report a new experiment, select a
seed or evidence channel, move a threshold, access external77, or alter
`R4_GATE_B_FAIL` or `CONSERVATIVE_DEV_GATE_FAIL`.

## 1. SCIENTIFIC QUESTION

The paper asks a sequence of linked scientific questions rather than recounting
the project chronologically:

1. **Why not simply refold under the evidence?** Global evidence-constrained
   refolding can exploit sparse evidence strongly, but it can also replace
   correct information already present in a source prediction.
2. **Can prediction context identify residual errors safely?** Candidate
   context ranks pair errors, but good discrimination does not by itself yield
   a stable high-preservation correction policy.
3. **Does sparse evidence add learned signal?** A matched evidence-masked
   comparison can distinguish evidence-attributable information from the
   effect of candidate context and model capacity.
4. **Can conservative decision structure retain that gain without collateral
   loss?** The decisive test is not aggregate F1 alone, but whether evidence
   improves `NON_EVIDENCED` correction without additional TP harm.

The scientific object is therefore the **correction–preservation trade-off** in
predictor-output-preserving RNA secondary-structure refinement. The study does
not assume that the learned method wins; it tests where evidence is reliable,
where it propagates, and where that propagation fails.

## 2. EMPIRICAL FINDINGS

### 2.1 Global refolding is strong but occupies a different operating region

B2 global constrained refolding produced event/RNA-balanced FP removal of
`0.645883/0.775728`, but retained only `0.981767/0.975358` of original TP. It
lost 4,752 original TP, removed 32,433 original FP, added 11,042 new TP, and
added 10,823 new FP. Its full-refold action space therefore achieved strong
aggregate correction while replacing materially more source-predictor
information than the deletion-only post-hoc policies.

R4 ERN removed fewer FP (`0.475531/0.660806`) but preserved more original TP
(`0.989682/0.991936`) and had higher modification precision
(`0.898838/0.944218`) than B2 (`0.736240/0.824449`). Neither operating point
dominates the correction–preservation plane. This is the bounded basis for
`GATE_A_PASS_POSTHOC_NONDOMINATED`; it is not a superiority claim for ERN.

### 2.2 Prediction context contains signal but is not a complete safety policy

R3 P4 achieved the strongest prediction-only discrimination (event/RNA AUPRC
`0.777283/0.915326`) but failed the RNA-balanced 0.99 preservation constraint.
P3 was the strongest eligible high-preservation prediction-only comparator,
with event/RNA TP preservation `0.996771/0.997588` and FP removal
`0.347816/0.489748`, but its RNA-balanced FP removal ranged from `0.013109`
for RNAfold to `0.630129` for trRosettaRNA2. Prediction context is informative,
but source dependence and threshold-tail purity prevent a source-general safe-
correction conclusion.

### 2.3 Usable evidence adds learned reliability and correction signal

R4 ERN exceeded its matched evidence-masked B4 in event AUPRC
(`0.811406` versus `0.771726`), event FP removal (`0.475531` versus
`0.386622`), and RNA-balanced FP removal (`0.660806` versus `0.615236`), while
improving Brier and ECE. RNA-balanced FP-removal improvement over P3 was
positive for RNAfold, PETfold, and trRosettaRNA2. Thus usable clean evidence
added signal beyond candidate context and model capacity on the three current
source predictors.

That information did not produce a safe R4 policy. ERN event TP preservation
was `0.989682`, below the prospectively frozen `0.990000` Gate B requirement.
Relative to B4, 56.0% of additional FP removal occurred in perfectly precise
`LOCAL_CONFLICT`; the remaining 44.0% occurred in `NON_EVIDENCED`, which also
contained all material additional TP loss. `R4_GATE_B_FAIL` is unchanged.

### 2.4 Conservative reconciliation improves absolute safety but fails the
matched-control causal safety test

CER achieved event/RNA TP preservation `0.991586/0.992930` and FP removal
`0.475575/0.682200`. Relative to `CER_EVIDENCE_MASKED`, evidence-attributable
FP-removal gains were `G_event=0.0889535` and `G_RNA=0.0669639`; these retained
`1.00049/1.46949` of the corresponding frozen R4 increments. CER also improved
RNA-balanced FP removal over P3 and over the matched masked control in all
three current predictor sources.

However, CER `NON_EVIDENCED` TP preservation was
`0.990864/0.992543`, below the matched masked values
`0.991702/0.993584` under event/RNA aggregation. Absolute preservation was
above 0.99 and mean `NON_EVIDENCED` lost TP fell from frozen R4's 2,687.8 to
2,192.8, but usable evidence still caused additional non-local TP harm relative
to the matched control. The conjunctive result remains
`CONSERVATIVE_DEV_GATE_FAIL`.

### 2.5 Master results table

Event-pooled and RNA-balanced values are shown as `event / RNA`. `NA` means
the metric is not defined or not appropriate for that method. B2 is a full-
refold method; all P3/R4/CER policies are deletion-only. B1 and E1 share the
local-conflict deletion fixed point, but B1 additionally retains the complete
local evidence transformation, whereas E1 is the pair-reliability projection.

| Method | TP preservation | FP removal | Modification precision | AUPRC | Delta F1 | Evidence role | Action space | Evidence/status |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| B0 Original | 1.000000 / 1.000000 | 0 / 0 | NA / NA | NA / NA | 0 / 0 | None | No edit | Frozen original comparator |
| B1 Local hard evidence | 1.000000 / 1.000000 | 0.119048 / 0.142946 | 1.000000 / 1.000000 | NA / NA | 0.011354 / 0.010717 | Explicit clean evidence | Local transform, including direct/local effects | Frozen classical comparator |
| R3-E1 `LOCAL_CONFLICT` | 1.000000 / 1.000000 | 0.119048 / 0.142946 | 1.000000 / 1.000000 | 0.261363 / 0.286350 | 0.008588 / 0.007486 | Explicit clean conflict | Deletion-only local rule | Frozen evidence-conditioned comparator |
| B2 global constrained refold | 0.981767 / 0.975358 | 0.645883 / 0.775728 | 0.736240 / 0.824449 | NA / NA | 0.043679 / 0.046012 | Clean evidence | Full refold: add, delete, replace | Frozen `FULL_REFOLD_REFERENCE` |
| R3-P3 `V3_VETO2_FIXED` | 0.996771 / 0.997588 | 0.347816 / 0.489748 | 0.956346 / 0.965504 | 0.442709 / 0.584113 | 0.024860 / 0.020751 | Prediction context only | Deletion-only | Frozen, source-dependent comparator |
| R4 B4 evidence-masked | 0.991886 / 0.993570 | 0.386622 / 0.615236 | 0.902350 / 0.947388 | 0.771726 / 0.884302 | 0.024509 / 0.024784 | Evidence exactly masked | Learned deletion-only | Frozen matched R4 control |
| R4 ERN | 0.989682 / 0.991936 | 0.475531 / 0.660806 | 0.898838 / 0.944218 | 0.811406 / 0.897194 | 0.030235 / 0.027922 | Usable clean evidence | Learned deletion-only | Frozen R4; `R4_GATE_B_FAIL` |
| CER evidence-masked | 0.991886 / 0.993570 | 0.386622 / 0.615236 | 0.902350 / 0.947388 | 0.771726 / 0.884302 | 0.024509 / 0.024784 | Evidence exactly masked | CCEG deletion/abstention control | Frozen Legacy121 development control |
| CER | 0.991586 / 0.992930 | 0.475575 / 0.682200 | 0.916103 / 0.959595 | 0.785956 / 0.887721 | 0.031188 / 0.029648 | Usable clean evidence | CCEG deletion-only with ABSTAIN | Legacy121 development; `CONSERVATIVE_DEV_GATE_FAIL` |

Sources: frozen R2 overall/edit summaries, R3 strongest-baseline summaries,
R4 reliability/utility/comparator summaries, and CER reliability/utility/gate
summaries. Cross-method Delta F1 is contextual because B2 can add and replace
pairs, whereas the post-hoc policies cannot.

## 3. NEGATIVE / FAILED HYPOTHESES

The project tested the following hypotheses. Status wording is aligned with
`docs/reboot_v2_claim_evidence_map.md`.

| ID | Hypothesis | Outcome | Decisive evidence |
| --- | --- | --- | --- |
| H1 | Prediction-only context is sufficient for safe correction. | **NOT SUPPORTED** | P1/P4 missed a held-out 0.99 preservation summary, P2 selected delete-none, and P3 was source-dependent. |
| H2 | Global evidence-constrained refolding is strong. | **SUPPORTED AS STRONG CLASSICAL BASELINE** | B2 improved Macro/Micro F1 and removed substantial FP under the matched clean-evidence universe. |
| H3 | A predictor-preserving post-hoc operating region is non-dominated by full refolding. | **SUPPORTED DEVELOPMENT-LEVEL** | R4 preserved more TP and had higher edit precision, whereas B2 removed more FP; neither dominated. |
| H4 | Usable evidence adds learned pair-error signal beyond matched capacity/context. | **SUPPORTED DEVELOPMENT-LEVEL** | ERN improved AUPRC, Brier/ECE, and FP removal over B4; FP-removal gain was positive in 3/3 current sources. |
| H5 | R4 learned evidence reconciliation satisfies its frozen safety gate. | **NOT SUPPORTED** | Event TP preservation `0.989682 < 0.99`; `R4_GATE_B_FAIL`. |
| H6 | CER suppresses unsafe propagation while retaining most evidence gain. | **MIXED / GATE FAIL** | Gain retention and absolute preservation passed, but both matched-control `NON_EVIDENCED` preservation comparisons failed. |
| H7 | Evidence improves `NON_EVIDENCED` candidates without additional harm. | **NOT SUPPORTED UNDER MATCHED CONTROL** | CER `NON_EVIDENCED` preservation was lower than its matched masked control under both aggregations. |
| H8 | The approach generalizes independently across datasets. | **NOT TESTED** | Legacy121 is development-only; external77 remains locked. |
| H9 | The approach is robust to noisy or real experimental evidence. | **NOT TESTED** | R5 and SHAPE/DMS/PARS work were not run or authorized. |
| H10 | Reconciled 2D structures improve downstream 3D prediction. | **NOT TESTED** | No 3D experiment was run or authorized. |

The two central negative results are mechanistically informative rather than
incidental misses. R4 showed that strong reliability discrimination can still
produce an impure deletion tail, and CER showed that improved absolute safety
does not establish absence of evidence-attributable non-local harm.

## 4. SUPPORTED INTERPRETATION

### Central paper-level conclusion

> **Across three source predictors on Legacy121 development data, clean sparse
> structural evidence added measurable residual pair-error signal beyond
> matched candidate-context controls, but its learned use outside direct
> support or local conflict caused additional loss of correct predicted pairs.
> Post-hoc RNA secondary-structure refinement therefore faces a mechanism-
> specific correction–preservation trade-off rather than a simple shortage of
> evidence information.**

This conclusion is supported because evidence attribution, scope accounting,
and two prospectively frozen safety failures point in the same direction. It
does not claim that evidence is generally unsafe: `DIRECT` support protected
pairs and `LOCAL_CONFLICT` correction was perfectly precise under the clean
symbolic-evidence semantics. The limitation concerns learned propagation into
`NON_EVIDENCED` candidates.

### Finding strength and manuscript placement

| Finding | Classification | Manuscript placement |
| --- | --- | --- |
| B2 and R4 occupy non-dominated correction–preservation regions. | **STRONG FINDING**, development-bounded | Abstract and main Results; state the different action spaces. |
| ERN improves discrimination/calibration/FP removal over matched B4. | **STRONG FINDING**, development-bounded | Abstract and main Results as evidence attribution, not safe-policy success. |
| FP-removal improvement occurs in 3/3 current predictor sources. | **INTERESTING BUT DEVELOPMENT-ONLY** | Main Results; mention in Abstract only with the Legacy121/three-current-source boundary. |
| `LOCAL_CONFLICT` edits are perfectly precise under clean evidence. | **STRONG MECHANISTIC FINDING**, condition-specific | Main Results and scope figure; no real/noisy-evidence generalization. |
| `NON_EVIDENCED` propagation supplies utility and all material marginal harm. | **STRONG NEGATIVE/MECHANISTIC FINDING** | Abstract, main Results, and Discussion. |
| CER restores absolute overall preservation above 0.99. | **INTERESTING BUT DEVELOPMENT-ONLY** | Main Results; not presented as a successful method endpoint. |
| CER fails both matched-control non-evidenced safety criteria. | **NEGATIVE RESULT** | Abstract and main Results because it tests the conservative hypothesis directly. |
| Independent, noisy/real-evidence, unseen-predictor, and 3D benefit. | **UNSUPPORTED / NOT TESTED** | Limitations only; never Abstract claims. |

## 5. PAPER-LEVEL CLAIM BOUNDARY

### Allowed wording

The manuscript may state that, **on Legacy121 development data under clean
symbolic evidence**:

- global evidence-constrained refolding is a strong comparator but sacrifices
  more correct source-predictor pairs than the tested post-hoc operating point;
- prediction context contains residual pair-error signal, although safe utility
  is source- and operating-point-sensitive;
- usable evidence incrementally improves pair-error discrimination,
  calibration, and FP removal over a matched evidence-masked control;
- the evidence-attributable FP-removal effect is observed for all three current
  source predictors;
- explicit `LOCAL_CONFLICT` correction is highly reliable under the frozen
  clean-evidence semantics;
- learned `NON_EVIDENCED` propagation produces both useful correction and
  collateral TP loss;
- conservative corroboration improves absolute preservation and retains the
  FP-removal gain, but fails to eliminate evidence-attributable non-local harm;
- correction–preservation and scope-resolved matched-control evaluation expose
  failure modes hidden by discrimination or aggregate F1 alone.

### Claim firewall

The current manuscript must not claim:

- model-agnostic performance or unseen-predictor generalization;
- independent dataset validation or cross-dataset generalization;
- robustness to noisy evidence;
- success with real SHAPE, DMS, PARS, or other probing evidence;
- superiority to global evidence-constrained refolding;
- safe non-local evidence propagation;
- downstream 3D improvement;
- `R4_GATE_B_PASS` or `CONSERVATIVE_DEV_GATE_PASS`;
- that CER is a validated deployment method or beats all baselines;
- that another threshold, seed, channel, feature set, or larger architecture
  would rescue either failed gate.

### Terminology ledger

| Canonical term | Meaning and usage |
| --- | --- |
| Legacy121 development data | All post-R4 train/validation/assessment uses; never “independent validation.” |
| B2 global evidence-constrained refolding | `FULL_REFOLD_REFERENCE`; may add, delete, and replace pairs. |
| Evidence Reconciliation Network (ERN) | Frozen R4 learned deletion-only model. |
| B4 evidence-masked control | Frozen R4 matched learned control with usable evidence masked. |
| Conservative Evidence Reconciliation (CER) | Development-only CCEG policy tested after the R4 postmortem. |
| Context-Corroborated Evidence Gate (CCEG) | CER action mechanism; not a third model or ensemble selection. |
| `DIRECT`, `LOCAL_CONFLICT`, `NON_EVIDENCED` | Frozen evidence-defined scopes, always in this precedence/order. |
| TP preservation / FP removal | Primary correction–preservation axes; report event-pooled and RNA-balanced forms. |

## 6. PROPOSED PAPER STORY

### Framing options

| Framing | Novelty and evidence fit | Main weakness | Reviewer-rejection risk | Current support |
| --- | --- | --- | --- | --- |
| **A. Method paper — “CER as a new refinement method”** | CCEG is interpretable and overall metrics are competitive. | Both frozen learned-method gates failed; no independent/noisy/real-evidence validation. | **High**: reviewers can reject the central method-success premise directly. | Insufficient for the primary framing. |
| **B. Reliability/mechanistic study — “Why better evidence does not automatically yield safer correction”** | Matched evidence attribution, prospective gates, scope decomposition, and two informative failures support a mechanistic insight. | Restricted to clean symbolic evidence and Legacy121 development data. | **Moderate**: novelty depends on presenting the evaluation logic and mechanism, not a winning model. | **Best supported primary framing.** |
| **C. Benchmark/evaluation framework — “Correction–preservation evaluation of evidence-guided refinement”** | Strong comparator breadth, action-space accounting, source/scope metrics, and reproducibility. | One development dataset and simulated clean evidence limit a broad benchmark/resource claim. | Moderate-to-high if sold as comprehensive benchmark; lower as a secondary contribution. | Supported as a secondary framing. |

### Selected primary framing

**B. RELIABILITY / MECHANISTIC STUDY**, with the correction–preservation
evaluation framework from option C as a secondary contribution.

The proposed narrative is:

1. Sparse evidence is commonly treated as a reason to globally revise a
   structure, but correction and preservation are distinct objectives.
2. A matched classical comparison shows that global refolding is powerful yet
   replaces correct predictor information, motivating a post-hoc operating
   space without implying superiority.
3. Prediction-only baselines show that residual-error signal exists but cannot
   guarantee a safe high-risk tail.
4. Matched ERN/B4 experiments establish that evidence adds information across
   all three current sources, while a frozen safety gate reveals collateral
   loss.
5. Scope accounting localizes reliable benefit to explicit/local effects and
   the unresolved trade-off to `NON_EVIDENCED` propagation.
6. CER prospectively tests the natural conservative hypothesis. It restores
   absolute preservation and retains evidence gain, yet still fails the
   matched-control non-local safety criterion.
7. The broader conclusion is methodological and mechanistic: evidence quality,
   model discrimination, and aggregate utility are insufficient proxies for
   safe post-hoc correction; preservation and causal evidence attribution must
   be evaluated explicitly.

## 7. FIGURE PLAN

### Figure 1 — Problem formulation and competing action spaces (main)

| Panel | Display / axes | Frozen data source | Core message |
| --- | --- | --- | --- |
| 1a | Schematic: original prediction + sparse evidence | Protocol definitions only | The task starts from an existing predictor output rather than sequence alone. |
| 1b | Schematic branches: local enforcement, global refold, post-hoc deletion | R2/R4/CER action contracts | The methods do not share the same action space. |
| 1c | Conceptual x=`1−TP preservation`, y=`FP removal` plane | Metric definitions only | Correction and preservation must be assessed jointly. |
| 1d | Scope map: `DIRECT > LOCAL_CONFLICT > NON_EVIDENCED` | Frozen scope semantics | Explicit/local effects and learned propagation are scientifically distinct. |

### Figure 2 — Baseline correction–preservation landscape (main)

| Panel | Display / axes | Frozen data source | Core message |
| --- | --- | --- | --- |
| 2a | Event x=`1−TP preservation`, y=`FP removal`; B0/E1/P3/B2 | R2 overall summary; R3 strongest baselines | B2 removes more FP but sacrifices more original TP; E1 and P3 occupy conservative regions. |
| 2b | RNA-balanced version of 2a | Same sources | The non-dominance conclusion holds under RNA-balanced aggregation. |
| 2c | x=method, y=modification precision, event/RNA paired markers | R2/R3 summaries | Aggregate F1 obscures edit quality and action-space differences. |
| 2d | Source-wise P3 FP removal | R3 source-wise summary | Prediction-only utility is source-dependent. |

### Figure 3 — R4 matched evidence attribution (main)

| Panel | Display / axes | Frozen data source | Core message |
| --- | --- | --- | --- |
| 3a | ERN vs B4 AUPRC, Brier, ECE | `results/clean_learned_evidence_reconciliation_r4/summaries/reliability_summary.csv` | Usable evidence improves discrimination and calibration. |
| 3b | x=`1−TP preservation`, y=`FP removal`, ERN/B4/P3 | R4 utility and R3 comparator summaries | Evidence gains correction but crosses the frozen event-safety line. |
| 3c | Source on x, y=`ERN−P3` RNA FP removal | R4 source-wise summary | Positive improvement occurs in 3/3 current sources. |
| 3d | Seed on x, paired `ERN−B4` metric differences | R4 ERN-vs-B4 summary | Report all seeds; no best-seed selection. |

### Figure 4 — Scope-resolved mechanism of benefit and harm (main)

| Panel | Display / axes | Frozen data source | Core message |
| --- | --- | --- | --- |
| 4a | Scope on x, y=ERN-minus-B4 additional FP removed | R4 postmortem scope attribution | `LOCAL_CONFLICT` supplies 56.0% and `NON_EVIDENCED` 44.0% of marginal FP removal. |
| 4b | Scope on x, y=ERN-minus-B4 additional TP lost | Same source | All material marginal harm occurs in `NON_EVIDENCED`; DIRECT protects TP. |
| 4c | Source/channel grouped bars for added FP removal and TP loss | R4 postmortem source/channel attribution | Benefit and harm are not explained by one source or one channel. |
| 4d | Risk-bin purity or risk–utility curve, descriptive only | R4 frozen postmortem diagnostics | Better ranking does not guarantee a sufficiently pure locked deletion tail. |

### Figure 5 — Prospective conservative test and decisive failure (main)

| Panel | Display / axes | Frozen data source | Core message |
| --- | --- | --- | --- |
| 5a | CCEG schematic: DIRECT KEEP, LOCAL_CONFLICT DELETE, corroborated NON_EVIDENCED actions | Frozen CER protocol | CER tests decision structure rather than larger capacity or added features. |
| 5b | Event/RNA correction–preservation points for R4, CER, CER masked, P3, B2 | CER frozen comparator and utility summaries | CER improves absolute safety while retaining correction. |
| 5c | Paired CER-minus-masked `G_event/G_RNA` with R4-gain-retention reference | CER evidence-attribution summary | Evidence-attributable correction remains substantial. |
| 5d | `NON_EVIDENCED` TP preservation: CER vs matched masked; event and RNA bars with 0.99 line | CER non-evidenced safety summary | Absolute safety passes, but both no-additional-harm criteria fail. |

Supplementary figures should contain channel-wise, seed-wise, density-wise,
source-wise preservation, calibration diagrams, complete risk curves, evidence
efficiency, and integrity/reproducibility summaries. No panel may select a
favorable channel, source, or seed.

## 8. TABLE PLAN

| Table | Contents | Placement | Source |
| --- | --- | --- | --- |
| Table 1 | Legacy121 RNA/source counts, evidence channels/densities/seeds, grouped roles, candidate universe, action spaces | Main | R2/R3/R4/CER protocols and universe audits |
| Table 2 | Master correction–preservation comparison from Section 2.5 | Main | Frozen R2/R3/R4/CER summaries |
| Table 3 | H1–H10 hypothesis and gate outcomes | Main | Frozen decisions and claim–evidence map |
| Supplementary Table S1 | Source-wise reliability and utility | Supplement | R3/R4/CER source-wise summaries |
| Supplementary Table S2 | Channel-wise and five-seed mean/SD/min/max | Supplement | R4/CER channel and per-seed summaries |
| Supplementary Table S3 | Calibration, reliability bins, Brier, ECE | Supplement | R3/R4/CER calibration artifacts |
| Supplementary Table S4 | `DIRECT`/`LOCAL_CONFLICT`/`NON_EVIDENCED` complete edit accounting | Supplement | R2/R4/CER scope summaries |
| Supplementary Table S5 | Protocol gates, leakage/hash checks, matrix completion, deterministic reruns | Supplement | Integrity artifacts |

## 9. LIMITATIONS

1. All learned-method conclusions use Legacy121 as development and hypothesis-
   generation data. The dataset cannot provide independent confirmation for
   CER because R4 outputs informed the conservative hypothesis.
2. Evidence is clean, symbolic, sparse, and GT-derived. The study does not test
   measurement noise, missingness, assay bias, or real SHAPE/DMS/PARS mapping.
3. The three source predictors are evaluated, but no predictor is held out as
   an unseen model family; 3/3 source consistency is not model agnosticism.
4. B2 and the deletion-only policies have different action spaces. Their
   non-dominance is informative, but no single scalar establishes superiority.
5. The exact canonical-pair metric is primary. Flexible endpoint matching was
   not added retrospectively and cannot be inferred from current results.
6. CER's overall 0.99 preservation does not validate safe non-local evidence
   propagation because the matched-control `NON_EVIDENCED` criteria failed.
7. No noisy-evidence, real-evidence, independent external, cross-predictor, or
   3D experiment is available to broaden the claim.

The lack of external77 is not a logical blocker to writing the bounded
development-level mechanistic result. It is a major boundary and likely review
risk for a venue expecting independent method validation.

## 10. PAPER VIABILITY DECISION

**`PAPER_STORY_VIABLE_WITH_CURRENT_RESULTS`**

The paper is viable now as a bounded **reliability/mechanistic study**, not as a
validated-method or broad benchmark paper. The scientific question is clear;
the classical and learned controls are strong; two prospectively frozen
failures generate a coherent mechanism-level insight; evidence attribution is
matched; and the negative result explains why discrimination and aggregate
utility do not imply safe correction. These elements provide new knowledge
even without claiming a winning method.

The decision is conditional on preserving the claim firewall. A manuscript
that leads with CER performance, independent generalization, or practical
evidence readiness would not be viable with current evidence. Review risk
remains substantial because the evidence is simulated and the data are
development-only, so venue selection should favor reliability, evaluation, or
negative-results contributions rather than method-leaderboard novelty.

## 11. NEXT AUTHORIZED TASK

The only next authorized task is:

```text
DRAFT_MANUSCRIPT_OUTLINE_AND_ASSEMBLE_FIGURE_DATA
```

That task may draft the manuscript outline and assemble plotting tables from
already frozen artifacts. It may not run a new scientific experiment, retrain
or re-evaluate R4/CER, select a seed/channel, move a threshold, access
external77, start R5/R6, use noisy or real evidence, or perform 3D analysis.

Authoritative state after consolidation:

```text
R4_COMPLETE
R4_GATE_B_FAIL
GATE_A_PASS_POSTHOC_NONDOMINATED
R4_POSTMORTEM_COMPLETE
CONSERVATIVE_RECONCILIATION_PROTOCOL_FROZEN
CONSERVATIVE_RECONCILIATION_DEVELOPMENT_COMPLETE
CONSERVATIVE_DEV_GATE_FAIL
PAPER_STORY_AND_RESULTS_CONSOLIDATION_COMPLETE
PAPER_STORY_VIABLE_WITH_CURRENT_RESULTS
R5_NOT_AUTHORIZED
EXTERNAL77_LOCKED
```
