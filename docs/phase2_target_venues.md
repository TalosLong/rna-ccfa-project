# Phase II Target-Venue Analysis

Status: **`VENUE_CANDIDATES_ONLY_NO_SUBMISSION_DECISION`**

Assessed: 2026-09-08

Venue fit and indexing/quartile status change over time. This document uses
current official scope pages where available, but the final JCR/CAS/CCF status
must be rechecked against the institution's accepted edition immediately before
submission. No venue label is a scientific result.

## 1. Publication thesis

Phase II becomes publishable at the intended level only if it contributes more
than an RNA application with a larger model. The minimum thesis is a reusable
structured prediction framework that transports sparse evidence through an
existing prediction, makes valid minimum-cost edits, and controls a biologically
defined harmful-edit risk, supported across predictor families and data regimes.

Phase I remains independently viable as a bounded reliability/mechanistic
paper. It may later provide motivation and negative-result evidence for Phase
II, but the projects are not committed to merge.

## 2. Track A — CCF-A stretch targets

The official [CCF artificial-intelligence venue list](https://www.ccf.org.cn/Academic_Evaluation/AI/)
places AAAI, NeurIPS, ICML, and IJCAI in category A. CCF announced the seventh
edition of its [international venue directory on
2026-03-31](https://www.ccf.org.cn/Academic_Evaluation/By_category/); the live
official list, rather than an archived third-party PDF, is the authority used
here. The accepted institutional edition must still be rechecked at submission.

| Venue | Fit | Minimum additional ML contribution | Minimum empirical evidence | Primary rejection risk |
| --- | --- | --- | --- | --- |
| **AAAI** | Strongest broad-AI candidate if structured decision and safety are central | New formalization of evidence transport + valid structured editing + justified risk-control algorithm; theory or precise guarantees/limitations; generality beyond one RNA predictor | Development-v2, structured baselines, matched controls, LOPFO, noise, one-shot independent result; ideally a second structured domain or convincing task-general abstraction | Seen as a specialized bioinformatics application or a composition of known GNN/DP/conformal parts |
| **IJCAI** | Similar to AAAI; good for knowledge/constraint/risk-aware decision framing | Clear AI problem, algorithmic novelty, ablations that isolate transport, edit cost, decoder, and risk controller | Multi-family/multi-predictor development plus independent test and robustness | Biological task overwhelms general AI insight; insufficient formal novelty |
| **ICML** | Possible only with substantial learning-theoretic or optimization contribution | New risk-control result for coupled structured edits, or a broadly reusable predict-then-edit framework with nontrivial validity/risk theorem | Large, rigorous multi-domain or unusually strong RNA evaluation; exact reproducibility | Existing ICML RNA constraint post-processing and ICLR conformal work make incremental integration insufficient |
| **NeurIPS** | Possible if graph/structured uncertainty contribution is general | Method or theory advancing graph/structured risk control under dependence, not merely an RNA architecture | Strong general benchmarks plus RNA, or exceptional RNA scale/generalization and theory | “GNN + conformal” prior art; narrow application and weak guarantee |

The current design has **CCF-A potential but not CCF-A readiness**. AAAI/IJCAI
are the most plausible stretch targets. ICML/NeurIPS require a generalizable
algorithmic or theoretical result substantially beyond the present proposal.
The official [AAAI-27 review criteria](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
emphasize problem significance, literature engagement, novelty and
justification for the AI approach, evaluation quality, and follow-up value; the
Phase II plan must satisfy all of these rather than rely on benchmark gains.

## 3. Track B — strong bioinformatics / computational-biology journals

| Venue | Fit | Minimum method evidence | Biological / data evidence | Positioning |
| --- | --- | --- | --- | --- |
| **Bioinformatics** | High for a rigorous computational method | Clear algorithmic advance over constrained post-processing, refolding, and deletion-only refinement; deployable software and full reproducibility | Development-v2, independent set, multiple predictors, family-aware tests; real evidence highly beneficial | Primary realistic high-quality computational-method target |
| **PLOS Computational Biology** | High if the work yields biological insight into evidence transport and error correction | Outstanding reusable method, not an incremental enhancement | Real-world data strongly expected; independent and ideally real-probing evidence | Strong Q1-style target when method and mechanistic biology are balanced |
| **Briefings in Bioinformatics** | Plausible for substantial AI/structural-bioinformatics method | Broad benchmark and methodological novelty with open code | Multi-source, multi-family, robustness, independent test | Good fit, but editorial article mix and current category/quartile should be checked |
| **Nucleic Acids Research** | Stretch for major nucleic-acid method/resource | Substantial innovative algorithm and biologist-facing usability | Strong independent and real SHAPE/DMS/PARS validation; likely broad utility/resource value | Requires more than clean symbolic evidence |
| **Nature Communications** | High stretch | Important discipline-level advance, not only a method increment | Convincing real evidence, independent generalization, broad RNA types, possibly downstream utility | Only if Phase II produces both methodological and biological significance |
| **Communications Biology** | Conditional strong-journal option | Solid computational advance and transparent validation | Independent/real biological data expected for strongest fit | More specialized than Nature Communications; verify current partition |
| **NAR Genomics and Bioinformatics** | Useful backup, not automatically a Q1 claim | Original, useful, FAIR method; official scope expects quantifiable biological merit and large-scale suitability | Broad reproducible benchmark; independent validation | Scope fit is good, but current official category ranks do not justify assuming Q1 in every system |

Official scope evidence:

- [Bioinformatics](https://academic.oup.com/bioinformatics/pages/scope_guidelines)
  rejects straightforward applications or incremental benchmark improvements
  without substantial methodology.
- [PLOS Computational Biology](https://journals.plos.org/ploscompbiol/s/journal-information)
  expects exceptional computational significance and biological insight; its
  Methods guidance emphasizes validation and broad adoption potential.
- [NAR](https://academic.oup.com/nar/pages/Criteria_Scope) expects substantial
  innovative algorithms for nucleic-acid structure analysis.
- [NAR Genomics and Bioinformatics](https://academic.oup.com/nargab/pages/scope_and_criteria)
  emphasizes originality, usefulness, FAIR availability, and quantifiable
  biological merit.
- [Nature Communications](https://www.nature.com/ncomms/submit/guide-to-authors)
  requires an important advance within the relevant discipline.

## 4. Evidence ladder by publication track

| Evidence package | AAAI / IJCAI | ICML / NeurIPS | Bioinformatics / Briefings | PLOS Comp Bio / NAR | Nature Communications |
| --- | --- | --- | --- | --- | --- |
| Clean symbolic Development-v2 only | Insufficient | Insufficient | Usually insufficient alone | Insufficient | Insufficient |
| + exact structured baseline and ablations | Necessary | Necessary | Necessary | Necessary | Necessary |
| + formal or carefully bounded risk control | Strongly preferred | Essential | Valuable | Valuable | Valuable |
| + leave-one-predictor-family-out | Essential | Essential | Essential | Strongly preferred | Essential |
| + 5–10% noise robustness | Essential | Essential | Strongly preferred | Strongly preferred | Essential |
| + one-shot independent set | Essential | Essential | Essential | Essential | Essential |
| + real SHAPE/DMS/PARS | Helpful, possibly optional if general ML contribution is strong | Helpful; application depth otherwise weak | Strongly preferred | Usually essential for highest fit | Essential |
| + optional 2D→3D utility | Optional | Optional | Helpful | Helpful | Potentially important, not a substitute for real 2D evidence |

## 5. Go-to-venue decision rule

Do not select a venue now. After Phase II gates:

1. If the main contribution is a defensible structured-risk algorithm with a
   general theorem or cross-domain relevance, assess AAAI/IJCAI first and
   ICML/NeurIPS only if the advance exceeds application-specific integration.
2. If the main contribution is an RNA-specific method with strong independent,
   source-transfer, noise, and real-probing validation, assess Bioinformatics,
   PLOS Computational Biology, Briefings in Bioinformatics, or NAR.
3. If real evidence and biological scope are unusually broad and the method
   changes how sparse evidence is used, consider Nature Communications.
4. If Gate P0 or P2 fails, do not market architecture complexity as novelty;
   preserve Phase I's bounded paper and reassess whether Phase II supports a
   narrower methods/benchmark venue.

## 6. Current potential assessment

- **CCF-A potential:** **conditional / medium**. The problem and proposed
  structured risk formulation are credible, but CCF-A requires a general ML
  contribution and rigorous transfer/independent evidence not yet produced.
- **Strong Q1 computational-biology potential:** **conditional / medium-high**.
  The RNA question is well motivated and the Phase I failure supplies a strong
  mechanistic premise. Readiness still requires Development-v2, modern
  predictors, independent validation, robustness, and preferably real probing.

These are planning judgments. `PHASE2_IMPLEMENTATION_NOT_AUTHORIZED` remains
unchanged.
