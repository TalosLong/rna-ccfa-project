# R4 Failure Analysis and Future-Path Decision

## Status

**`R4_POSTMORTEM_COMPLETE`**

**`NEW_HYPOTHESIS_JUSTIFIED_PROTOCOL_NOT_FROZEN`**

**`R5_NOT_AUTHORIZED`**

Decision date: 2026-09-07

This postmortem uses only the frozen Legacy121 R4 candidate table and sealed
held-out ERN/B4 combined Track E outputs. It does not train or retrain a model,
change a calibrator or threshold, choose a seed or channel, add a model feature,
open external77, begin R5, use noisy or real evidence, run historical E2, or
modify any frozen R2/R3/R4 scientific result. Gate B remains
**`R4_GATE_B_FAIL`**.

Canonical derived diagnostics are in
`results/clean_learned_evidence_reconciliation_r4/postmortem/`. All counts below
are five-seed means unless stated otherwise. These are post-hoc descriptions of
already-fixed held-out decisions, not new operating-point evaluations.

## EMPIRICAL RESULT

The frozen primary combined ERN result was:

| Quantity | ERN | Matched B4 |
| --- | ---: | ---: |
| Event AUPRC | 0.811406 | 0.771726 |
| Event Brier | 0.061184 | 0.067810 |
| Event ECE | 0.018252 | 0.024127 |
| Event TP preservation | 0.989682 | 0.991886 |
| RNA-balanced TP preservation | 0.991936 | 0.993570 |
| Event FP removal | 0.475531 | 0.386622 |
| RNA-balanced FP removal | 0.660806 | 0.615236 |

Usable evidence therefore improved discrimination, calibration, and FP removal
over the matched evidence-masked model, but the event-pooled TP-preservation
requirement failed. This is the frozen R4 result; the analyses below do not
re-evaluate it.

The Gate B miss is:

```text
observed event TP preservation = 0.9896824148
frozen requirement             = 0.9900000000
gap                            = 0.0003175852  (approximately 0.000318)
```

There were 260,623 TP opportunity events per seed. ERN lost a mean 2,689.0 TP
events. A preservation of at least 0.99 corresponds to at most 2,606 lost TP
events for this fixed integer event universe, so the observed mean miss is on
the scale of approximately 82.77 excess lost-TP events per seed. This number is
descriptive only. It is not a target for moving the R4 threshold or otherwise
rescuing Gate B.

## POST-HOC DIAGNOSTIC

### Why stronger discrimination coexisted with worse preservation

AUPRC evaluates ranking over the complete held-out score distribution, whereas
TP preservation at the locked policy depends on the composition of the small
high-risk tail after validation-only calibration and threshold selection. ERN
moved many FP into that tail, improving AUPRC and FP removal, but it also moved
additional TP across the already-locked decision boundary. Thus better global
ranking did not imply a sufficiently pure deletion tail.

The scope accounting localizes this difference. Evidence behaved safely when
its meaning was explicit: ERN almost completely protected directly supported
TP and deleted local conflicts with perfect precision. The loss appeared when
the globally pooled evidence representation influenced candidates without a
direct or local-conflict relation. Calling this a learned propagation mechanism
is an interpretation of matched outputs, not a causal identification of a
specific internal neural computation.

### Scope attribution

| Scope | ERN removed FP | B4 removed FP | ERN − B4 removed FP | ERN lost TP | B4 lost TP | ERN − B4 lost TP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DIRECT | 0.0 | 0.0 | 0.0 | 1.2 | 123.2 | **−122.0** |
| LOCAL_CONFLICT | 4,862.4 | 2,361.8 | **+2,500.6** | 0.0 | 0.0 | 0.0 |
| NON_EVIDENCED | 19,016.4 | 17,052.4 | **+1,964.0** | 2,687.8 | 1,991.6 | **+696.2** |
| Total | 23,878.8 | 19,414.2 | **+4,464.6** | 2,689.0 | 2,114.8 | **+574.2** |

`LOCAL_CONFLICT` supplied 56.0% of net additional FP removal and did so with
perfect modification precision. `NON_EVIDENCED` supplied the remaining 44.0%,
which is substantial, but also supplied all material additional TP loss. The
DIRECT evidence effect protected 122.0 TP relative to B4 and partially offset
that non-evidenced harm. The evidence-attributable marginal benefit is therefore
slightly concentrated in perfectly precise local conflicts, whereas the safety
failure is specifically a non-evidenced propagation problem.

### Source and channel attribution

| Stratum | ERN − B4 removed FP | ERN − B4 lost TP | ERN TP preservation |
| --- | ---: | ---: | ---: |
| RNAfold | +1,505.4 | +222.6 | 0.989035 |
| PETfold | +1,562.0 | +166.8 | 0.990178 |
| trRosettaRNA2 | +1,397.2 | +184.8 | 0.989838 |
| Positive-pair channel | +2,066.0 | +274.4 | 0.990248 |
| Unpaired channel | +2,398.6 | +299.8 | 0.989130 |

Additional FP removal was distributed across all three sources. Additional TP
loss was also distributed: RNAfold, PETfold, and trRosettaRNA2 contributed
38.8%, 29.0%, and 32.2% of the net ERN-minus-B4 loss, respectively. In absolute
ERN loss, the corresponding means were 955.8, 850.4, and 882.8. RNAfold was the
worst source by preservation, but there was no single-source failure mechanism.

ERN's RNA-balanced FP-removal improvement over frozen P3 remained positive for
RNAfold (+0.204321), PETfold (+0.183132), and trRosettaRNA2 (+0.150813). The
learned correction signal is therefore no longer explainable as a
trRosettaRNA2-only effect. This does not establish unseen-predictor transfer.

Positive-pair event preservation exceeded unpaired preservation in four of the
five seed-level summaries, but the ordering held in only three of five
fold-level summaries pooled over seeds and 12 of 25 fold-by-seed cells. The
channel difference is not fold-stable. Moreover, within `NON_EVIDENCED` alone,
positive-pair preservation was 0.988400 versus 0.989130 for unpaired evidence;
the positive-pair overall advantage partly reflected safe DIRECT support rather
than uniformly safer propagation. Selecting the positive-pair channel would be
an invalid post-hoc rescue and is not authorized.

### NON_EVIDENCED decomposition

The full reproducible breakdown is in `diagnostic_breakdowns.csv`. The bins
below are diagnostic partitions, not proposed features, gates, or thresholds.

#### Evidence density

| Density | ERN TP preservation | ERN FP removal | ERN − B4 removed FP | ERN − B4 lost TP |
| ---: | ---: | ---: | ---: | ---: |
| 0% | 0.990630 | 0.398432 | +162.0 | +37.0 |
| 1% | 0.987824 | 0.425184 | +424.4 | +154.2 |
| 5% | 0.987453 | 0.435814 | +486.4 | +161.6 |
| 10% | 0.987900 | 0.438752 | +434.6 | +154.0 |
| 20% | 0.988828 | 0.441626 | +244.0 | +132.2 |
| 50% | 0.990514 | 0.458488 | +212.6 | +57.2 |

Non-evidenced preservation was non-monotonic in evidence density. The 0%
difference is a training-mediated ERN/B4 parameter difference when the current
test context has no items, not a direct delivered-item effect. No density level
may be selected retrospectively.

#### Sequence separation

| Separation | ERN lost TP | ERN TP preservation | ERN − B4 removed FP | ERN − B4 lost TP |
| --- | ---: | ---: | ---: | ---: |
| 4–9 | 436.0 | 0.990838 | +633.4 | +274.2 |
| 10–19 | 1,065.0 | 0.985025 | +620.8 | +179.8 |
| 20–49 | 793.8 | 0.991543 | +629.0 | +197.6 |
| 50–99 | 245.0 | 0.988951 | +65.4 | +64.2 |
| 100+ | 148.0 | 0.971911 | +15.4 | −19.6 |

The largest absolute TP loss was at separation 10–19, while the small 100+
stratum had the lowest preservation. Harm was heterogeneous rather than
described by one simple separation cutoff.

#### Stem position and boundary status

| Boundary status | ERN lost TP | ERN TP preservation | ERN − B4 lost TP |
| --- | ---: | ---: | ---: |
| Singleton | 197.8 | 0.842139 | +34.2 |
| Inner boundary | 711.8 | 0.979853 | +148.6 |
| Outer boundary | 544.0 | 0.986158 | +159.6 |
| Stem interior | 1,234.2 | 0.992480 | +353.8 |

Singletons and boundaries had the highest loss rates, but stem interiors had
the largest absolute additional loss because they contained most TP
opportunities. Normalized stem-position bins showed the same mixed pattern:
the `[0,0.25)` and `[0.75,1]` bins had preservation 0.987417 and 0.987372,
whereas the two middle bins preserved 0.991827 and 0.992966. Unsafe propagation
was not confined to a single boundary class.

#### Pair type

The lost canonical TP events were distributed across AU (909.0), GC (767.2),
CG (351.2), GU (246.8), UA (233.6), and UG (180.0). AU and GC accounted for
62.4% of absolute non-evidenced TP loss, largely because they were common.
Noncanonical pair-type strata contained FP but no TP under the frozen GT
matching semantics. Pair type therefore describes where losses were observed;
it does not define a valid post-hoc deletion rule.

#### P2 agreement and P4 BPP risk

| P2 support by other sources | TP opportunities | ERN lost TP | ERN TP preservation | ERN − B4 removed FP | ERN − B4 lost TP |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0/2 | 4,305 | 775.6 | 0.819837 | +987.6 | +242.8 |
| 1/2 | 11,230 | 1,591.8 | 0.858255 | +959.6 | +433.6 |
| 2/2 | 224,478 | 320.4 | 0.998573 | +16.8 | +19.8 |

Low and partial P2 agreement contained nearly all correction opportunity and
89% of TP loss. Full agreement was strongly protective but not perfectly so.

| P4 DELETE-risk (`1−BPP`) | ERN lost TP | ERN TP preservation | ERN − B4 removed FP | ERN − B4 lost TP |
| --- | ---: | ---: | ---: | ---: | ---: |
| [0.00, 0.10) | 1,088.8 | 0.994628 | +364.2 | +366.8 |
| [0.10, 0.25) | 344.6 | 0.981200 | +357.6 | +106.4 |
| [0.25, 0.50) | 412.0 | 0.965812 | +339.8 | −35.4 |
| [0.50, 0.75) | 297.8 | 0.916184 | +214.2 | +64.2 |
| [0.75, 1.00] | 544.6 | 0.839351 | +688.2 | +194.2 |

High P4 risk was associated with poor preservation, but the large low-risk
population still contributed 1,088.8 lost TP and 366.8 additional ERN-minus-B4
loss. P2/P4 strata cannot be converted into a retrospective rescue gate.

#### Calibrated ERN risk and ERN–B4 risk shift

Within `NON_EVIDENCED`, 2,236.6 of 2,687.8 lost TP events (83.2%) occurred in
the calibrated ERN `[0.6,0.8)` risk bins. Their modification precision was
0.761 in `[0.6,0.7)` and 0.819 in `[0.7,0.8)`, compared with 0.949 in
`[0.8,0.9)` and 0.989 in `[0.9,1.0]`. This identifies an impure decision-tail
region under the already-locked fold-specific policies; it does not authorize
moving those policies.

For rows where ERN risk exceeded B4 risk by 0.02–0.10, the net changes were
+1,154.0 removed FP and +668.6 lost TP. A shift of 0.10–0.25 yielded +1,644.8
removed FP and +478.2 lost TP. Positive evidence-associated risk shifts thus
carried both much of the marginal benefit and much of the marginal harm. Risk
difference is a post-hoc diagnostic involving two fitted models and is not an
allowed inference feature for any current method.

## INTERPRETATION

R4 failed because it did not translate a real, source-broad evidence signal
into the prospectively required purity of the deletion tail. The failure is not
explained by absent discrimination, failed calibration in aggregate, one bad
predictor, or one evidence channel. It is localized scientifically to unsafe
`NON_EVIDENCED` propagation: the same extension beyond explicit evidence that
adds useful FP removal also adds enough TP loss to cross the frozen safety bar.

The postmortem supports a narrower mechanism-level observation. A slight
majority of net evidence-attributable FP-removal gain was already available in
perfectly precise `LOCAL_CONFLICT`, and DIRECT evidence protected TP. The
remaining non-evidenced gain was real and too large to dismiss, but was not
selective enough. This creates a plausible future question about whether useful
correction can be retained while making propagation conditional on prospective
trust/locality semantics. It does not show that such a method will pass.

### What R4 established

Supported on Legacy121 development data:

1. Source-agnostic candidate context contains substantial error signal.
2. Usable clean evidence contributes incremental discrimination and
   calibration beyond matched B4.
3. Usable evidence increases FP removal beyond matched B4.
4. The observed post-hoc operating region is non-dominated by full refolding.
5. RNA-balanced FP-removal improvement over P3 occurs across all three current
   predictor sources.

Not supported:

1. Safe learned correction under frozen Gate B.
2. Independent generalization.
3. An unseen-predictor or model-agnostic claim.
4. Noisy-evidence robustness.
5. Real experimental-evidence utility.
6. Any 3D benefit.
7. A claim that a different R4 threshold would pass.
8. A claim that a larger model would rescue R4.

## FUTURE HYPOTHESIS

The only justified new conceptual hypothesis is:

> **Most evidence-attributable useful correction may be recoverable while
> suppressing unsafe NON_EVIDENCED propagation.**

A possible working name is **Trust-Gated / Locality-Aware Evidence
Reconciliation**. This is an untested future hypothesis, not a method, protocol,
result, or authorization to implement. It must not be represented as moving the
R4 threshold, selecting positive-pair evidence, tuning to held-out errors,
adding a larger architecture, or encoding the diagnostic strata above as new
features.

Any future protocol would need to define trust and locality prospectively,
freeze all permitted inputs and actions, specify a matched control and safety
gate, and state exactly how Legacy121 is used for development before code or
training. Nothing in this document decides those design details.

## Future-path assessment

### Path 1 — Stop and consolidate a bounded negative/near-miss study

This remains scientifically defensible. R4 is a rigorous near miss with strong
evidence attribution, a preserved negative gate, and a non-dominated comparison
to full refolding. It is the default fallback if a new protocol cannot be made
genuinely prospective and falsifiable.

### Path 2 — New prospective conservative reconciliation hypothesis

This path is scientifically justified at the hypothesis level because 56.0%
of net marginal FP removal was perfectly precise `LOCAL_CONFLICT`, DIRECT
evidence protected TP, and all material marginal TP loss was
`NON_EVIDENCED`. The remaining 44.0% non-evidenced FP gain shows that the open
question is not identical to E1: a useful but unsafe propagation signal exists.
The next experiment, if eventually frozen, would ask whether most benefit can
be retained without permitting the observed broad collateral tail.

This justification authorizes protocol design only. It does not authorize
implementation, training, threshold selection, or R5.

### Path 3 — Retain only direct/local evidence correction

This is the safest operational fallback but has limited novelty. Frozen E1
already achieved TP preservation and modification precision of 1.0 with
RNA-balanced FP removal 0.142946 and structurally zero non-evidenced effect.
Abandoning learned propagation would largely retain an established baseline,
not explain how to obtain the additional broad correction that motivated R4.
It may remain a recommended conservative baseline or deployment fallback, but
it is not a strong new mainline contribution by itself.

## Data-independence consequence

Legacy121 R4 held-out outcomes have now been observed, decomposed, and used for
scientific interpretation. Consequently, a method designed after this
postmortem cannot treat the same Legacy121 held-out folds as a pristine
confirmatory test.

If a new method is later authorized:

- Legacy121 may be used only as development and hypothesis-generation data
  under a newly frozen protocol;
- no new Legacy121-only result may be promoted as independent validation;
- external77 must remain unopened until the complete future method, permitted
  inputs, calibration, thresholds, gates, and analysis plan are prospectively
  frozen;
- external77 remains a one-shot independent test and cannot be used for rescue.

external77 was not opened in this task.

## FUTURE-PATH DECISION

**`NEW_HYPOTHESIS_JUSTIFIED_PROTOCOL_NOT_FROZEN`**

This is selected instead of mainline stop because the matched scope accounting
provides a specific, falsifiable scientific rationale for a conservative new
hypothesis: most marginal benefit lies in safe local evidence handling, while
the Gate B miss arises from unsafe non-evidenced propagation rather than lack of
signal. The 44.0% non-evidenced marginal FP gain also makes the question more
substantive than simply reinstating E1.

The decision does not erase or alter `R4_GATE_B_FAIL`, does not promote ERN, and
does not authorize R5. The only next authorized task is:

```text
FREEZE_NEW_PROSPECTIVE_CONSERVATIVE_RECONCILIATION_PROTOCOL
```

No implementation or training is authorized until that separate protocol task
is completed and explicitly approved.
