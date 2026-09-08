# Phase II Literature and Novelty Audit

Status: **`PHASE2_P0_LITERATURE_AUDIT_COMPLETE`**

Cut-off: **2026-09-08**

Scope: design evidence only; no model, dataset, or scientific experiment was
executed.

Subsequent state: P1/P2 is frozen in `docs/phase2_dataset_and_task_protocol.md`;
any `PROTOCOL_NOT_FROZEN` wording below records the P0 audit checkpoint.

## 1. Audit question and method

This audit asks whether the proposed Phase II direction—risk-controlled,
structured post-hoc refinement of an existing RNA secondary-structure
prediction using sparse external evidence—has a defensible methodological gap.
It does **not** ask whether a larger RNA predictor would improve F1.

Searches covered 2023--2026 work plus classical anchors in:

- RNA secondary-structure correction, post-processing, and constrained folding;
- chemical-probing-guided folding (SHAPE, DMS, PARS);
- pair/contact representations, graph models, structured decoders, and learned
  thermodynamic energies;
- pair confidence and structure-quality estimation;
- selective prediction, abstention, conformal prediction, conformal risk
  control, structured conformal prediction, and FDR-style selection;
- RNA foundation models and post-hoc structural bioinformatics.

Public publisher pages, proceedings, PubMed/PMC, arXiv, bioRxiv, OpenAlex, and
official project/data pages were searched. The academic MCP endpoints were
unavailable, so the academic-search workflow was completed with public web and
OpenAlex fallbacks. Targeted follow-up searches explicitly tested the terms
`fixing`, `post-processing`, `pair evidence`, `minimum edit`, `assignment`,
`dependency parsing`, `selective prediction`, and `conformal risk control`.
Network literature audit was therefore **not blocked**.
Absence statements below mean “not located by this bounded audit,” never a
proof that no such work exists.

## 2. Evidence table

Abbreviations: `Y/N` = explicit yes/no in the reported method; `Partial` = only
some aspect; `NA` = not the method's task; `Pred` = a newly predicted structure,
not preservation-aware refinement of an input prediction. “Independent” uses
the paper's own evaluation design and does not certify freedom from all forms
of homology leakage.

| Paper | Year / venue | Task | Representation | Evidence type | Model | Action space | Structured decoder? | Risk / uncertainty control? | Abstention? | External evidence propagation? | Preserves original prediction? | Independent validation? | Real probing evidence? | Overlap with Phase II |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Deigan et al., *Accurate SHAPE-directed RNA structure determination*](https://pubmed.ncbi.nlm.nih.gov/19109441/) | 2009, PNAS | Evidence-guided folding | Nucleotide reactivities + nearest-neighbor states | SHAPE | Pseudo-free-energy MFE folding | Global refold | Y, DP | N | N | Global energy coupling | N | Small accepted-structure benchmark | Y | Canonical real-evidence baseline; no learned trust or edit preservation |
| [Kertesz et al., *Genome-wide measurement of RNA secondary structure in yeast*](https://www.nature.com/articles/nature09322) | 2010, Nature | Structure profiling | Per-nucleotide enzymatic cleavage profile | PARS | Experimental scoring and analysis | Pairedness profile | N | N | N | NA | NA | Known-structure checks | Y | Establishes PARS evidence modality, not a refinement policy |
| [Washietl et al., *RNA folding with soft constraints*](https://academic.oup.com/nar/article/40/10/4261/2411101) | 2012, NAR | Reconcile probing and thermodynamics | Reactivity-derived perturbation vector | SHAPE / generic probing | Iterative pseudo-energy adjustment | Global refold | Y, thermodynamic DP | Explicit noise weighting, not selective risk control | N | Global ensemble effect | N, though energy is changed only when needed | Benchmark RNAs; no locked external test | Y | Closest classical “minimal intervention” idea, but modifies folding energy rather than an existing prediction |
| [Cordero et al., *Quantitative DMS mapping for automated RNA secondary structure inference*](https://pmc.ncbi.nlm.nih.gov/articles/PMC3448840/) | 2012, Biochemistry | DMS-guided folding | A/C reactivity | DMS | Pseudo-energy MFE inference | Global refold | Y | N | N | Global energy coupling | N | Six ncRNAs | Y | Real-evidence comparator and mapping reference |
| [Hajdin et al., *Accurate SHAPE-directed RNA secondary structure modeling, including pseudoknots*](https://pmc.ncbi.nlm.nih.gov/articles/PMC3619282/) | 2013, PNAS | Evidence-guided folding including PKs | Reactivity + thermodynamic states | SHAPE | RNAstructure / ShapeKnots | Global refold | Y; PK extension | N | N | Global | N | Accepted structures | Y | Shows real evidence and PK feasibility; not preservation-aware editing |
| [Lorenz et al., *RNA folding with hard and soft constraints*](https://pubmed.ncbi.nlm.nih.gov/27110276/) | 2016, Algorithms Mol. Biol. | General constrained folding API | Hard/soft nucleotide and pair constraints | Generic experimental/computational constraints | ViennaRNA thermodynamic algorithms | Global refold | Y, DP | N | N | Constraint contribution can affect global fold | N | Software demonstrations | Supports real inputs | Mandatory classical baseline; direct prior art for constraint injection |
| [ShapeSorter](https://academic.oup.com/nar/article/50/15/e85/6596092) | 2022, NAR | Detect conserved structure features supported by probing | Evolutionary structure model + per-nucleotide SHAPE probabilities | SHAPE + alignment | Fully probabilistic evidence integration | Predict supported pairs/features | Y, probabilistic grammar | Probabilistic evidence/P-values, not harmful-edit control | Thresholded non-selection, not an edit ABSTAIN policy | Converts nucleotide evidence into pair/feature support | N | Multiple established test collections | Y | Direct collision for pair-specific evidence interpretation; lacks arbitrary-source preservation and selective edit-risk control |
| [SPOT-RNA](https://www.nature.com/articles/s41467-019-13395-9) | 2019, Nature Communications | De novo secondary-structure prediction | Pairwise sequence features | Sequence + evolutionary features | Ensemble CNN / 2D-BLSTM | Predict pairs | Pair-rule post-processing, not an exact primary noncrossing decoder | N | N | N | NA (no input prediction) | Multiple held-out sets; family leakage concerns remain field-wide | N | Modern source predictor; no external evidence trust or edit-cost objective |
| [E2Efold](https://arxiv.org/abs/2002.05810) | 2020, ICLR | De novo secondary-structure prediction | Pair score matrix | Sequence | Transformer/CNN + unrolled optimization | Predict pairs | Y, differentiable constrained program | N | N | N | NA | ArchiveII/RNAStrAlign evaluation | N | Strong prior art against claiming differentiable constrained RNA decoding itself |
| [MXfold2](https://www.nature.com/articles/s41467-021-21194-4) | 2021, Nature Communications | De novo secondary-structure prediction | Learned loop/pair scores + Turner energy | Sequence | CNN/BiLSTM, structured max-margin training | Predict full non-PK structure | Y, exact Zuker-style DP | N | N | N | NA | Sequence- and family-wise CV | N | Prior art for neural scoring + exact DP and biological energy regularization |
| [UFold](https://academic.oup.com/nar/article/50/3/e14/6430845) | 2022, NAR | De novo secondary-structure prediction | Image-like pair map | Sequence + base-pair rules | U-Net | Predict pairs | Constrained post-processing | N | N | N | NA | Cross-family-style benchmarks reported | N | Prior art for pair-map neural prediction and valid-structure post-processing |
| [CDPfold / CNN+DP](https://pmc.ncbi.nlm.nih.gov/articles/PMC8812003/) | 2022, Bioinformatics | De novo secondary-structure prediction | Pair score map | Sequence / pair features | CNN | Predict pairs | Y, DP or weighted matching variants | N | N | N | NA | Standard benchmarks | N | Prior art for neural pair scoring + DP/matching; no input-preservation objective |
| [GCNfold](https://pmc.ncbi.nlm.nih.gov/articles/PMC10925402/) | 2023, Computers in Biology and Medicine | De novo prediction | Sequence graph + RNAfold BPP | Sequence + predicted thermodynamic context | GCN/BiLSTM/CNN | Predict pairs | Pair-rule post-processing | N | N | N | NA | Standard datasets | N | “RNA + GNN” and BPP fusion are already occupied; pair graph alone is weak novelty |
| [RNADiffFold](https://pmc.ncbi.nlm.nih.gov/articles/PMC11586127/) | 2024, Briefings in Bioinformatics | Generative de novo prediction | Discrete contact map | Sequence | Multinomial diffusion | Generate pairs | Validity post-processing, not minimal-edit decoding | N | N | N | NA | Within- and cross-family datasets | N | More evidence that architecture novelty alone is crowded |
| [Hong et al., *Improving transformer secondary structure predictions with secondary structure “fixing” task*](https://proceedings.mlr.press/v240/hong24a.html) | 2024, MLCB / PMLR | Improve a prediction using an input structure as scaffold | Sequence + dynamic-programming prediction | Existing predicted structure, no external probing | LSTM / Transformer | Re-predict/fix base pairs | Learned bracket/pair output; no exact minimum-edit contract reported | N | N | N | Uses and can change an input prediction | Benchmark evaluation | N | Direct prior art for prediction-as-scaffold refinement; no sparse external evidence transport, preservation penalty, or formal edit safety |
| [Suh et al., *Enforcing Constraints in RNA Secondary Structure Predictions*](https://proceedings.mlr.press/v235/suh24a.html) | 2024, ICML | Post-process ML RNA predictions to enforce validity | Predicted pairing matrix / assignment graph | Predictor output | Assignment-inspired algorithm | Reassign/select pairs | Y, theoretical validity guarantee | N | N | N | Changes input to satisfy constraints; not explicit preservation-risk control | Multiple predictors/datasets | N | Closest structured post-processing prior art; rules out claiming generic RNA post-processing or assignment decoding |
| [RFold](https://proceedings.mlr.press/v235/tan24a.html) | 2024, ICML | De novo secondary-structure prediction | Probabilistic K-rook matching matrix | Sequence | Neural pair scoring + bi-dimensional optimization | Predict/select pairs | Y, valid matching output | N | N | N | NA | Multiple datasets/generalization tests | N | Strong collision for matching-based RNA decoding and output-validity claims; no evidence-guided editing of `S0` |
| [DEPfold](https://proceedings.iclr.cc/paper_files/paper/2025/hash/1ad84bf5a6711cb9541c8976617cc00f-Abstract-Conference.html) | 2025, ICLR | De novo secondary-structure prediction as dependency parsing | Labeled dependency tree | Sequence + pretrained embeddings | Biaffine parser + optimal tree decoder | Predict pairs and pair types | Y, optimal tree decoding including PK representation | N | N | N | NA | Within- and cross-family tests | N | Strong collision for learned structured RNA decoding and cross-family framing; no source-preserving evidence refinement |
| [MoEFold2D](https://pubmed.ncbi.nlm.nih.gov/39811444/) | 2025, Biology Methods and Protocols | Robust OOD RNA secondary prediction | Ensemble agreement and RNA-type clusters | Predictor consensus | Deep/physics mixture of experts | Choose consensus DL or physics prediction | Decoder depends on expert | OOD heuristic/consensus, not harmful-edit guarantee | Defers to a physics expert rather than leaving `S0` unchanged | N | NA | Filtered external-style benchmarks | N | Important RNA precedent for safety-aware routing and cluster audits; does not selectively control structured edits |
| [RiNALMo](https://doi.org/10.1038/s41467-025-60872-5) | 2025, Nature Communications | RNA representation + secondary-structure prediction | LM nucleotide embeddings, outer pair representation | Sequence pretraining | 650M Transformer + pair head | Predict pairs | Greedy clash removal | N | N | N | NA | Leave-one-family-style evaluation | N | Modern predictor/source family; using an RNA LM is not the Phase II novelty |
| [BPfold](https://www.nature.com/articles/s41467-025-60048-1) | 2025, Nature Communications | De novo prediction and confidence index | Local base-pair motifs / energy map | Sequence + modeled motif energies | Deep motif-energy model | Predict pairs | Structural refinement step | Heuristic confidence index, no harmful-edit control | N | N | NA | Cross-family evaluations | N | Pair reliability is occupied; confidence is not selective edit-risk control |
| [ERNIE-RNA](https://www.nature.com/articles/s41467-025-64972-0) | 2025, Nature Communications | Structure-aware RNA LM and secondary prediction | Sequence/structure-enhanced LM representation | Sequence pretraining | Transformer | Predict pairs | Pair output processing | N | N | N | NA | bpRNA-new/RNA3DB-2D-style tests | N | Modern predictor/source family; reinforces need for family-aware evaluation |
| [RNASSTR](https://pmc.ncbi.nlm.nih.gov/articles/PMC12247784/) | 2025/2026, preprint/data resource | Expanded RNA secondary-structure training resource | Family/structure-aware sequence-structure pairs | Curated annotations | Dataset pipeline + retraining studies | NA | NA | N | N | N | NA | Structure-aware splits | N | Useful Development-v2 candidate and warning about memorization; not method prior art |
| [NTFold](https://pmc.ncbi.nlm.nih.gov/articles/PMC12845834/) | 2026, Sensors | De novo secondary-structure prediction with interaction-map refinement | Attention-derived nucleotide interaction map | Sequence | Attention + structural refinement module | Predict/refine contact map | Constraint post-processing | N | N | N | NA | Standard held-out benchmarks | N | Recent direct collision for calling a neural contact-map module “structural refinement”; no `S0`, external evidence, edit cost, or risk control |
| [FoldARE](https://www.biorxiv.org/content/10.64898/2026.03.04.709501v2) | 2026, bioRxiv preprint | Ensemble analysis and pseudo-SHAPE-guided folding | In-silico ensemble-derived pseudo-reactivity | Generated pseudo-SHAPE | Generative pseudo-SHAPE + SHAPE-aware folding | Global guided refold / ensemble | Uses downstream folding engine | Ensemble variability, not selective risk control | N | Pseudo-SHAPE affects downstream fold globally | N | Tool comparisons; preprint | Pseudo rather than real probing | Recent evidence that evidence-generation/fusion and ensemble analysis remain active; not source-preserving edit refinement |
| [El-Yaniv & Wiener, *On the Foundations of Noise-free Selective Classification*](https://jmlr.csail.mit.edu/papers/v11/el-yaniv10a.html) | 2010, JMLR | Selective classification | Generic examples | Labels | Risk/coverage theory | Predict or reject | N | Selective-risk analysis | Y | NA | NA | Theory | NA | Foundation for ABSTAIN and risk–coverage; not RNA or structured editing |
| [Geifman & El-Yaniv, *Selective Classification for Deep Neural Networks*](https://proceedings.neurips.cc/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html) | 2017, NeurIPS | Selective deep prediction | Generic features | Labels | Confidence-based selection | Predict or reject | N | High-probability selective-risk bound | Y | NA | NA | Image benchmarks | NA | Prior art for confidence-threshold abstention |
| [SelectiveNet](https://proceedings.mlr.press/v97/geifman19a.html) | 2019, ICML | Learn prediction and selection jointly | Generic features | Labels | Multi-head selective network | Predict or reject | N | Coverage-constrained selective risk | Y | NA | NA | Vision benchmarks | NA | Gating/abstention alone is not novel |
| [Bates et al., *Distribution-Free, Risk-Controlling Prediction Sets*](https://www.gsb.stanford.edu/faculty-research/publications/distribution-free-risk-controlling-prediction-sets) | 2021, JACM | General finite-sample risk control | Black-box scores | Calibration labels | RCPS | Set-valued prediction | Loss-dependent | Expected-loss control | Set output, not edit abstention | NA | NA | Held-out calibration; protein example | NA | Direct foundation for loss-aware control; no RNA edit transport |
| [Huang et al., *Conformalized Graph Neural Networks*](https://papers.nips.cc/paper_files/paper/2023/hash/54a1495b06c4ee2f07184afb9a37abda-Abstract-Conference.html) | 2023, NeurIPS | Graph-node uncertainty | Graph nodes/edges | Labels | GNN + conformal layer | Prediction sets | N | Marginal coverage under graph conditions | Set output | Generic graph propagation | NA | Multiple graph datasets | NA | “GNN + conformal” is prior art; Phase II must control structured edits, not merely node coverage |
| [Jin & Candès, *Selection by Prediction with Conformal p-values*](https://jmlr.org/papers/v24/22-1176.html) | 2023, JMLR | Select candidates with FDR control | Generic examples | Calibration labels | Conformal p-values + BH-style selection | Select / do not select | N | FDR control | Implicit non-selection | NA | NA | Theory + applications | NA | Candidate foundation for edit-level FDR; structured edit dependence needs new treatment |
| [Angelopoulos et al., *Conformal Risk Control*](https://research.google/pubs/conformal-risk-control/) | 2024, ICLR | Control expected monotone losses | Nested black-box decisions | Calibration labels | Conformal calibration | Tunable prediction/action family | Task-dependent | Expected monotone-loss control | Possible through action family | NA | NA | Multiple tasks | NA | Strong foundation; ordinary Platt scaling or thresholding must not be called conformal |
| [Zhang et al., *Conformal Structured Prediction*](https://proceedings.iclr.cc/paper_files/paper/2025/hash/1868a3c73d0d2a44c42458575fa8514c-Abstract-Conference.html) | 2025, ICLR | Prediction sets for structured labels | Implicit structured label sets / DAGs | Calibration labels | General conformal framework | Structured prediction sets | Y in representation | Coverage guarantee | Set-valued uncertainty | NA | NA | Multiple structured domains | NA | Structured conformal prediction is occupied; harmful-edit control for RNA refinement remains distinct |
| [ModFOLD9](https://doi.org/10.1016/j.jmb.2024.168531) | 2024, Journal of Molecular Biology | Protein-model quality estimation/refinement support | 3D model quality features | Predicted protein models | Ensemble quality assessment | Flag/refine protein regions | External refinement pipeline | Confidence estimation, not conformal edit control | User can defer | No RNA evidence transport | Attempts local correction | Independent CASP-style targets | N | Cross-domain precedent that local quality estimation and refinement are distinct; not a direct RNA method |

## 3. Four-component novelty test

### A. Candidate Pair Graph

**Finding: not novel in isolation.** Pair/contact matrices, nucleotide graphs,
RNA base-pair edges, GCNs, and graph/matching post-processing are established.
GCNfold, E2Efold, CDPfold, UFold, RFold, DEPfold, NTFold, and the ICML
assignment framework occupy much of this space. The proposed graph is useful as
an inductive bias because a pair node can explicitly encode stacking, same-stem,
shared-nucleotide competition, alternative partners, sequence locality, and
evidence relations. Its novelty can only come from the role it plays in a
preservation-aware edit and risk system, not from the words “pair graph,”
“interaction-map refinement,” or “GNN.”

### B. Evidence Trust / Transport

**Finding: qualified gap located.** Classical hard/soft-constraint folding and
learned sequence/evolutionary fusion transport information globally through an
energy model or network. Washietl et al. formalize changing the energy model
when prediction and evidence disagree, and ShapeSorter explicitly converts
SHAPE evidence into probabilistic support for conserved structure features.
Thus neither “pair-specific evidence” nor “probabilistic evidence fusion” is a
novelty claim. However, this audit did not locate an RNA method that estimates
whether a sparse evidence item is *eligible to cause an edit of a particular
candidate pair relative to an arbitrary source prediction*, while separately
penalizing loss of correct source information.

The defensible gap is therefore not “evidence fusion.” It is:

> preservation-aware, relation-explicit evidence-to-edit transport, with a
> falsifiable distinction between DIRECT/LOCAL and PROPAGATED effects.

This remains a hypothesis until a full protocol and appropriate controls are
frozen.

### C. Structured Edit Decoder

**Finding: decoder machinery is prior art; the objective may be distinctive.**
DP, constrained optimization, maximum-weight matching, K-rook matching,
dependency parsing, and assignment-based post-processing all exist for RNA.
Hong et al. also use an input prediction as scaffolding for a learned “fixing”
task. No located method jointly used sparse external evidence and an explicit
distance from an arbitrary starting prediction to choose atomic
KEEP/DELETE/ADD/REPLACE/ABSTAIN actions under RNA validity constraints. The
proposed distinction is a *minimum-edit evidence-guided refinement objective*,
not exact decoding or prediction fixing by itself:

\[
S^*=\arg\max_{S'\in\mathcal{V}(x)}
\left[f_\theta(S'\mid x,S_0,E)-\lambda_{edit}C(S',S_0)\right].
\]

Hong et al. 2024 and Suh et al. 2024 are mandatory nearest comparators; RFold
and DEPfold are mandatory decoder collisions. Phase II must show that
evidence-conditioned, risk-controlled minimal edits add value beyond either
re-predicting from a scaffold or merely repairing invalid predictor outputs.

### D. Risk-Controlled Selective Refinement

**Finding: strongest qualified novelty opportunity.** Selective prediction,
FDR-controlled selection, RCPS/CRC, conformal GNNs, and conformal structured
prediction are mature general foundations. This audit did not locate their use
to control harmful structured edits in evidence-guided RNA secondary-structure
refinement, especially at the RNA/family-cluster biological unit.

The novelty claim must be narrow: define a nested family of valid edit policies,
calibrate at the RNA or predeclared RNA-cluster unit, and control a prospectively
defined harmful-edit loss. A calibrated probability plus a threshold is not a
formal guarantee. If exchangeability, monotonicity, cluster sample size, or
dependence requirements cannot be established, the method must be described as
**empirical selective risk control**, not conformal risk control.

## 4. Joint gap and collision map

| Proposed element | Existing collision | What remains potentially new | Required falsification |
| --- | --- | --- | --- |
| Pair graph | GCNfold, NTFold and graph/contact-map predictors | Typed graph of *candidate edits relative to* `S0` | Non-graph/equivalent-capacity ablation |
| Evidence transport | SHAPE/DMS pseudo-energies; ShapeSorter; generic fusion/attention | Eligibility of external evidence to *cause a specific edit relative to `S0`* | Matched evidence-masked and trust-shuffled controls; DIRECT/LOCAL/PROPAGATED accounting |
| Exact validity | DP, matching, RFold, DEPfold, E2Efold, UFold, Suh et al. | Evidence-guided minimal-edit objective over `S0` with atomic replacement semantics | Hong fixing-task, deletion-only and refolding comparators; illegal-output audit |
| Abstention | Selective classification / SelectiveNet | Structured abstention over edits/regions/RNAs | Risk–coverage and abstention accounting |
| Risk control | RCPS, CRC, graph conformal, structured conformal | RNA-cluster harmful-edit control for a structured refinement policy | Prospective loss, nested policy, calibration-unit and exchangeability audits |
| Foundation-model context | RNA-FM, RNAErnie, RiNALMo, ERNIE-RNA | At most an optional input/source predictor | Must not be the central novelty; frozen lightweight and non-LM baselines required |

## 5. Novelty decision

**`PHASE2_PRIMARY_DIRECTION_JUSTIFIED`**

The decision is conditional and design-level. Individual components are not
novel, and the field is crowded. A defensible Phase II direction exists only as
the joint problem of:

1. preserving useful information in an existing source prediction;
2. learning *where* sparse evidence is structurally entitled to act;
3. making valid minimum-cost structured edits including missing/wrong-partner
   repairs; and
4. prospectively controlling harmful edit risk at a biological grouping unit.

This audit does **not** freeze a final architecture, theorem, dataset, method
name, success threshold, or publication claim. `PROTOCOL_NOT_FROZEN` and
`IMPLEMENTATION_NOT_AUTHORIZED` remain in force.

## 6. Claims prohibited by this audit

Phase II may not claim novelty for any of the following alone:

- applying a GNN/Graph Transformer to RNA;
- representing RNA as a graph or pair/contact matrix;
- neural pair scoring followed by DP, matching, ILP, or assignment;
- adding SHAPE/DMS/PARS constraints or pseudo-energies to folding;
- converting probing reactivity into pair/feature-level probabilities;
- using an existing predicted structure as neural scaffolding for re-prediction;
- post-processing a predicted contact map to make it valid;
- confidence calibration, thresholding, abstention, conformal prediction, or
  FDR control in generic form;
- using an RNA foundation model;
- outperforming a baseline on Legacy121.

Any later novelty claim must be re-audited immediately before protocol freeze
and again before submission because 2025--2026 RNA and conformal literatures are
moving quickly.
