# Phase II Dataset and Structured-Task Protocol

Status: **`PHASE2_DATASET_AND_TASK_PROTOCOL_FROZEN`**

Protocol version: **`PHASE2_DTP_V1.0`**

Date: **2026-09-09 UTC**

Git commit: **the commit containing this document**

Frozen base commit: **`27334a7a7146bb2d724b253149573edb89a8b8cb`**

Content integrity: **`docs/phase2_protocol_freeze_manifest.md`**

Implementation: **`PHASE2_IMPLEMENTATION_NOT_AUTHORIZED`**

The Git object that contains this file cannot be embedded literally in the file
without changing that object. The immutable content hash is therefore recorded
in the freeze manifest, and the containing commit is resolved from Git history.

## 1. Frozen contracts

### 1.1 DATA_ROLE_CONTRACT

- Legacy121 is `PHASE1_HISTORICAL_DIAGNOSTIC_DATA` only.
- Development-v2 is built only from the frozen sources and filters below.
- Biological clusters, not pair events, are the indivisible split units.
- TRAIN, MODEL_SELECTION, SCORE_CALIBRATION, RISK_CALIBRATION and
  DEVELOPMENT_ASSESSMENT are family/homology disjoint.
- Development assessment is used once, after model and risk-policy lock; it is
  not independent confirmation.
- external77 remains sealed as `PHASE1_BRIDGE_INDEPENDENT_ASSET`.
- A separately sealed Independent-v2 is the primary Phase II one-shot set.

### 1.2 TASK_CONTRACT

Given sequence `x`, a source prediction `S0`, permitted inference-time source
outputs, and delivered evidence `E`, predict a valid structure `S*` by
KEEP/DELETE/ADD/REPLACE edits relative to `S0`, with component-level ABSTAIN.
Candidate generation and inference cannot use ground truth, source identity,
dataset identity, family identity, or future outcomes.

### 1.3 DECODER_CONTRACT

The primary decoder is deterministic exact weighted noncrossing dynamic
programming over a prospectively fixed canonical/Wobble pair universe. It
enforces sequence bounds, minimum loop length, one nucleotide/one partner and
noncrossing validity, and contains an explicit symmetric-difference edit cost
relative to `S0`. Neural unconstrained decoding is prohibited.

### 1.4 RISK_CONTROL_CONTRACT

The sole primary route is
`FINITE_FAMILY_RISK_CONTROLLING_POLICY_SELECTION`. Six complete structured
policies are fixed before risk-calibration outcomes. Simultaneous one-sided
Hoeffding upper confidence bounds over independent biological clusters select
the highest-coverage policy with expected cluster-balanced per-RNA HarmRate
upper bound at most `alpha=0.10`, at confidence `1-delta=0.95`. This is not
called conformal risk control.

### 1.5 INDEPENDENT_TEST_CONTRACT

Neither external77 nor Independent-v2 may train, select, calibrate, repair or
rescue a method. Independent-v2 identities will be chosen and sealed only in a
separate authorized task after the applicable design is locked. Its primary
analysis is one-shot and direction-preserving; failure does not authorize
post-hoc threshold, predictor, family, seed or architecture selection.

## 2. Development-v2 source composition

The authoritative source audit is
`docs/phase2_dataset_source_audit.md`. The canonical composition is:

| Layer | Frozen source | Permitted roles | Ground-truth interpretation |
| --- | --- | --- | --- |
| Experimental core | RNA3DB-2D Figshare v1, based on RNA3DB 2024-12-04 and PDB-derived annotations | Any Development-v2 role after cluster splitting | Exact 2D reference derived from experimental 3D coordinates under a recorded annotation pipeline |
| Comparative/computational supplement | RNASSTR Zenodo 15319168; Rfam 15.1 | TRAIN and MODEL_SELECTION only | Comparative/computational consensus, never independent experimental confirmation |
| Overlap registries | bpRNA-1m, RNAStrAlign, ArchiveII, bpRNA-new | Provenance/training-overlap exclusion only | No Phase II label role |
| Temporal independent reserve | post-2024-12-04 PDB/RNA3DB records, potentially indexed through RNAsolo2 | No Development-v2 role | Candidate pool for a future sealing task only |

Dataset origin is retained for audit and stratification but prohibited from
model features and risk thresholds. No candidate sample is selected here.

## 3. Record schema and inclusion contract

Every RNA record must contain these immutable fields before role assignment:

| Required field | Frozen semantics |
| --- | --- |
| `dataset_accession` | Source-native stable accession; never a local row number alone |
| `release_version` | Exact source release/artifact identifier |
| `sequence_sha256` | SHA256 of normalized single-strand RNA sequence |
| `structure_sha256` | SHA256 of canonical normalized pair-list serialization |
| `rna_family` | Source-backed family identifier or literal `UNKNOWN` |
| `rna_type` | Source-backed type ontology value or literal `UNKNOWN` |
| `length_nt` | Length after the frozen normalization |
| `strand_count` | Source strand count before any exclusion |
| `annotation_provenance` | Experimental/comparative/computational plus exact tool/version where derived |
| `release_or_deposition_date` | Authoritative date, otherwise `NOT_AVAILABLE` |
| pair counts | Separate canonical, Wobble and noncanonical counts |
| `crossing_status` | `NONCROSSING`, `PSEUDOKNOT_OR_CROSSING`, or `UNKNOWN` |
| `modified_base_normalization` | Complete residue-level map and policy |
| `legacy121_overlap_status` | Hash, family and 80/80 homology results; unresolved means exclude |
| `predictor_training_overlap_status` | Per frozen predictor/checkpoint: `KNOWN_OVERLAP`, `NO_KNOWN_OVERLAP`, or `UNKNOWN` |
| `license_status` | Exact license and source; `UNKNOWN` excludes the source from canonical redistribution |
| `biological_cluster_id` | Hash of the final family/homology connected component |
| `conformer_group_id` | Groups alternate conformers/annotations of the same biological molecule |
| `temporal_status` | `PRE_CUTOFF`, `POST_CUTOFF`, or `NOT_AVAILABLE` |
| `development_role` | Exactly one of the five roles, or `EXCLUDED` |

`UNKNOWN` family/type is retained literally and is never manually guessed.
Unknown family records are still clustered by sequence homology and provenance;
they cannot be split by treating each unknown label as a new family.

### 3.1 Primary-track eligibility

An eligible primary RNA must:

- be a single supported molecular strand after source-level definition;
- contain 30--600 normalized nucleotides;
- contain only resolvable A/C/G/U positions after documented modification
  mapping; records containing unresolved `N` at a paired position are excluded;
- have a traceable sequence/structure relation and annotation provenance;
- have an exact reference whose primary canonical/Wobble projection already
  satisfies the frozen decoder validity rules; and
- pass the license, Legacy121, predictor-overlap-role, family, identity and
  temporal firewalls.

The following are primary exclusions, not missing-data conveniences:

- unresolved sequence/structure mismatch;
- unsupported multi-strand structures;
- untraceable annotation;
- a structure solely generated by any source predictor in the frozen panel;
- structure incompatible with the primary decoder;
- unresolved modified-base normalization; and
- unknown provenance for which reference reliability cannot be justified.

Alternative conformers remain in one biological cluster. One conformer cannot
enter training while another enters calibration or assessment. A deterministic
pre-outcome conformer policy must be declared during manifest construction; if
no defensible choice exists, exclude the group.

## 4. Family, redundancy and Legacy121 firewall

### 4.1 Sequence normalization and orientation

Normalize to uppercase RNA alphabet, replace `T` with `U`, remove no internal
symbols, and reject unresolved modified residues rather than guessing. The
reverse complement is searched only to detect redundant/homologous records; it
does not reverse the biological orientation used for prediction. Both forward
and reverse-complement comparisons can create a cluster edge.

### 4.2 Fixed identity algorithm

Use **MMseqs2 release `18-8cc5c`**, nucleotide search, to enumerate candidate
homology edges. The exact release and binary SHA256 must be recorded before
manifest construction. The official guide documents nucleotide operation,
identity/coverage controls and connected-component mode
([MMseqs2 user guide](https://mmseqs.com/latest/userguide.pdf)).

Each enumerated edge must be confirmed by deterministic end-to-end global
pairwise alignment of the normalized sequences with match `+1`, mismatch `0`,
gap `-1`, no free end gaps, and lexicographic traceback. Define:

- identity = identical aligned canonical bases / aligned non-gap columns;
- query coverage = aligned query residues / query length;
- target coverage = aligned target residues / target length.

Create an identity edge iff identity is at least **0.80** and both coverages are
at least **0.80**, in either forward or reverse-complement orientation. These
values are frozen before any model outcome and cannot be relaxed later.

### 4.3 Biological cluster construction

Construct an undirected graph whose vertices are all candidate Development-v2
records plus the non-sensitive Legacy121 overlap registry. Add edges for:

1. the fixed 80/80 sequence rule;
2. shared exact sequence hash;
3. shared source-backed Rfam or curated structural family, regardless of
   sequence identity;
4. alternative conformer/group membership; or
5. explicit source provenance showing the same biological molecule.

The biological cluster is the graph connected component. Family information
has higher priority than pairwise identity: sequence divergence never permits
known family relatives to cross roles. Every RNA, source prediction, evidence
realization and conformer follows its cluster.

Any component touching Legacy121 by hash, family, molecule or 80/80 edge is
excluded from Development-v2. A missing Legacy121 overlap decision is
fail-closed. Legacy121 content is not used to optimize the threshold or select
architectures.

### 4.4 Predictor-training overlap

Known checkpoint-training records and their entire biological components are
excluded from SCORE_CALIBRATION, RISK_CALIBRATION and
DEVELOPMENT_ASSESSMENT for that source realization. `UNKNOWN` overlap does not
mean clean: it is retained as an uncertainty flag and must be reported
source-wise. If a predictor's training corpus is unauditable enough that a
clean assessment direction cannot be defended, that predictor fails the
deployment audit for the primary panel before data construction.

## 5. Temporal control

The fixed Development-v2 PDB cutoff is **2024-12-04 UTC**, the release date of
the RNA3DB base used by the accepted RNA3DB-2D v1 pipeline. PDB-derived records
must have an authoritative first public release date on or before the cutoff.
Later records are prohibited from Development-v2 and reserved for possible
Independent-v2 construction.

The cutoff never overrides family/homology control: any post-cutoff record in a
Development-v2 family/component is ineligible for Independent-v2. Comparative
records without trustworthy per-structure dates receive
`temporal_status=NOT_AVAILABLE`; no date is inferred from a file timestamp or
paper year.

## 6. Development roles and leakage firewall

Assign whole biological clusters to exactly one role:

1. **TRAIN** — parameter fitting only.
2. **MODEL_SELECTION** — architecture, optimization, edit-cost `lambda_edit`,
   and other predeclared hyperparameter selection.
3. **SCORE_CALIBRATION** — probability/score calibration only, after model lock.
4. **RISK_CALIBRATION** — evaluation of the six frozen complete policies and
   risk-policy selection only.
5. **DEVELOPMENT_ASSESSMENT** — one use after model, score calibrator, decoder,
   risk policy and analysis lock.

The default and frozen contract is five disjoint cluster sets. No calibration
role is merged. A future amendment may merge roles only if it cites a method
whose theorem explicitly permits that exact adaptive reuse; otherwise the
formal-risk claim is downgraded before outcomes are seen.

The role assignment seed and algorithm, cluster manifest and hashes must be
frozen before training. Stratification may use only pre-outcome metadata (RNA
type, length bin, provenance and family size), never source-prediction error or
candidate labels. Pair events, multiple predictors and evidence realizations do
not increase the number of independent split or calibration units.

RISK_CALIBRATION requires at least **240 biological clusters** for the frozen
Hoeffding family to be able to certify `alpha=0.10` even at zero observed risk.
If it contains fewer, the formal readiness gate fails rather than combining
roles or changing the bound.

SCORE_CALIBRATION fits the single source-independent monotone Platt map defined
in `docs/phase2_risk_control_design.md`. This is ordinary calibration, not risk
control. Its optimizer and fitted parameters are sealed before RISK_CALIBRATION;
predictor-specific maps and post-hoc calibrator switching are prohibited.

## 7. Source predictor audit and panels

The panel spans algorithmic families rather than versions. Exact executable and
checkpoint SHA256 values must be recorded in a deployment manifest before any
prediction; missing, altered or legally unusable artifacts fail deployment.

| Predictor | Frozen family/version | Inputs/resources | Scores, structure and PK behavior | Training-overlap risk | License/deployability decision |
| --- | --- | --- | --- | --- | --- |
| RNAfold | `THERMODYNAMIC`; ViennaRNA **2.7.2** | Single sequence; CPU | MFE structure and base-pair probabilities; primary noncrossing model; fixed flags/temperature required | No learned training corpus; thermodynamic parameter provenance still recorded | ViennaRNA's source terms permit use/redistribution with attribution; **PRIMARY** ([release](https://github.com/ViennaRNA/ViennaRNA/releases/tag/v2.7.2), [license](https://raw.githubusercontent.com/ViennaRNA/ViennaRNA/v2.7.2/COPYING)) |
| PETfold | `COMPARATIVE_THERMODYNAMIC`; **2.2** | MSA plus ViennaRNA dependency; standardized homolog/MSA pipeline required | Pair/single reliabilities; consensus noncrossing structure | Alignment databases and input construction can leak families | Public version documented, but exact software redistribution license was not verified: **OPTIONAL, deployment audit fail until resolved** ([official site](https://rth.dk/resources/petfold/), [download](https://rth.dk/resources/petfold/download.php)) |
| MXfold2 | `LEARNED_THERMODYNAMIC_DP`; **v0.1.2**, default released checkpoint | Single sequence; CPU/GPU optional | Learned thermodynamic-compatible scores with exact DP; noncrossing | Training sets include curated/Rfam-derived corpora; exact checkpoint overlap audit mandatory | MIT; released code/checkpoint; **PRIMARY** ([repository](https://github.com/mxfold/mxfold2), [paper](https://doi.org/10.1038/s41467-021-21194-4)) |
| UFold | `END_TO_END_CONTACT_MAP`; commit **75bd9acc83826059682dfca9d3659df66b132cd1**; checkpoint **`models/ufold_train_alldata.pt`** from the repository-linked pretrained-model folder | Single sequence; GPU preferred | Internal contact score followed by constraint-aware postprocessing; the public CLI emits CT/BPSEQ, while calibrated raw pair probability is **`UNKNOWN`**; can represent pseudoknots, but normalized primary output must satisfy this protocol | Default all-data training inputs are publicly named in the repository; the exact sequence registry must be hashed and screened | MIT repository; code/output/checkpoint path is deployable subject to preflight hash; **PRIMARY** ([repository](https://github.com/uci-cbcl/UFold)) |
| RFold | `STRUCTURED_NEURAL_K_ROOK`; commit **b2952a94101eae376af16b8e1d549146db2e2ab4** | Single sequence; learned checkpoint | Structured K-rook formulation; output normalization still needed | Common structure corpora | Repository license not verified: **OPTIONAL, deployment audit fail** ([repository](https://github.com/A4Bio/RFold)) |
| DEPfold | `STRUCTURED_NEURAL_DEPENDENCY`; commit **a19cc74ff5628518970b08f166c5e7be2241bb74** | Single sequence; learned checkpoint | Dependency-parsing structured decoder; pseudoknot claims are secondary to primary normalization | Common structure corpora | Repository license not verified: **OPTIONAL, deployment audit fail** ([repository](https://github.com/Vicky-0256/DEPfold)) |
| RiNALMo SS | `FOUNDATION_MODEL`; commit **2c2c5c14a5ae609d8c560a5d9ca32e51e0288955**, checkpoint `rinalmo_giga_ss_bprna_ft.pt` in Zenodo 15043668 | Single sequence; 650M model, GPU, maximum 1,022 nt for the published setup | Pair-score head and valid postprocessing must be frozen; primary subset only | Large RNA pretraining corpus plus bpRNA fine-tuning: high and explicitly audited | Code Apache-2.0; weights CC BY 4.0; **PRIMARY** ([repository](https://github.com/lbcb-sci/RiNALMo), [paper](https://doi.org/10.1038/s41467-025-60872-5), [weights](https://doi.org/10.5281/zenodo.15043668)) |
| ERNIE-RNA SS | `FOUNDATION_MODEL`; commit **43bc06de1088ed03ffd7de918ad4b2c2a3346a43** | Single sequence; GPU; task checkpoint or zero-shot map | Pair/contact outputs require a frozen head/postprocessor | Released heads use bpRNA, RNAStrAlign, RIVAS or RNA3DB; high overlap | Code MIT; separate weight terms not verified: **OPTIONAL, deployment audit fail until resolved** ([repository](https://github.com/Bruce-ywj/ERNIE-RNA), [paper](https://doi.org/10.1038/s41467-025-64972-0)) |
| trRosettaRNA2 native SS | `MSA_3D_PIPELINE_BRIDGE`; commit **9839687f57a476df42323fe86d6effa78bf32a2e** | MSA or single-sequence mode; large databases/GPU for full pipeline | Native SS is an internal/bridge output of a 3D system, not like-for-like modern 2D scoring | Training/database overlap complex | Apache-2.0 repository; **OPTIONAL Phase I bridge only**, not primary LOPFO ([repository](https://github.com/YangLab-SDU/trRosettaRNA2)) |
| NuFold | `3D_WITH_SS_INPUT`; no primary version frozen | Uses predicted secondary structure in a 3D prediction chain | Not a like-for-like 2D source predictor | Not applicable to primary panel | **EXCLUDED from primary/optional 2D panels** |

The explicit deployment fields omitted by compact prose above are:

| Predictor | Checkpoint/parameters | MSA | GPU | Maximum length | Raw pair score / probability | Postprocessing / pseudoknot | Determinism under frozen environment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RNAfold | ViennaRNA 2.7.2 parameter set and CLI flags; no learned checkpoint | No | No | No audited hard software cap; project cap 600 | Partition-function base-pair probability available | MFE DP, primary noncrossing | Yes with frozen binary, parameters, flags, temperature and threads |
| PETfold | v2.2 package; no learned checkpoint | **Required** | No | **UNKNOWN**; project cap 600 | Pair and single-strand reliabilities available | Consensus noncrossing output | Expected with frozen MSA/dependencies; must be verified before optional admission |
| MXfold2 | v0.1.2 installed default parameters trained jointly on TrainSetA/B | No | Optional | **UNKNOWN** hard cap; project cap 600 | Internal pair/energy terms available; calibrated probability **UNKNOWN** | Exact DP, noncrossing | Yes after CPU/environment/flags freeze |
| UFold | `models/ufold_train_alldata.pt` | No | Preferred | Repository reports inference through 1,600 nt; project cap 600 | Internal contact score available; calibrated probability **UNKNOWN** | Learned map plus source postprocessor; can retain crossings, then must pass primary normalization | Must be established with frozen PyTorch/CUDA, checkpoint and postprocessor |
| RFold | Released checkpoint identifier **UNKNOWN** | No | Likely | **UNKNOWN** | Structured pair score availability **UNKNOWN** | K-rook structured output; PK status depends configuration | **UNKNOWN** |
| DEPfold | Released repository checkpoints; exact primary identifier **UNKNOWN** | No | Likely | **UNKNOWN** | Parser arc/pair score availability **UNKNOWN** | Dependency parser can express structured contacts; primary normalization required | **UNKNOWN** |
| RiNALMo SS | `rinalmo_giga_ss_bprna_ft.pt`, Zenodo 15043668 | No | Yes | Published input maximum 1,024 tokens = 1,022 nt; project cap 600 | Pair-head score available; probability calibration is separate | Published SS head/postprocessing; primary normalization required | Must be established with frozen CUDA/checkpoint/environment |
| ERNIE-RNA SS | Task-specific or zero-shot checkpoint not frozen | No | Yes | **UNKNOWN**; project cap 600 if admitted | Attention/contact score; calibrated probability **UNKNOWN** | Task-head postprocessor must be frozen | **UNKNOWN** until weight/environment audit |
| trRosettaRNA2 native SS | Repository-provided model assets; exact native-SS asset hash pending optional preflight | Optional/standard path uses MSA | Yes for full pipeline | **UNKNOWN** | Native internal SS score/probability interface **UNKNOWN** | Internal to 3D pipeline; normalized bridge output only | Must be established for optional bridge |
| NuFold | Not applicable | Its 3D chain consumes predicted SS | Yes | Not applicable | Not a primary 2D source output | 3D task | Not applicable |

`UNKNOWN` in any required primary deployment field would be a deployment-audit
failure. For the four primary entries, raw calibrated probabilities are not
required because the generic input contract permits a score plus missingness;
structure output, exact checkpoint/parameters, license and deterministic
normalization are required. Their hashes/determinism must be materialized and
verified before prediction, without using performance outcomes.

### 7.1 Frozen panels

`PRIMARY_SOURCE_PANEL`:

```text
THERMODYNAMIC          RNAfold 2.7.2
LEARNED_THERMODYNAMIC  MXfold2 v0.1.2 default released checkpoint
END_TO_END_CONTACT_MAP UFold commit 75bd9acc... models/ufold_train_alldata.pt
FOUNDATION_MODEL       RiNALMo commit 2c2c5c1... rinalmo_giga_ss_bprna_ft.pt
```

`OPTIONAL_SOURCE_PANEL`:

```text
PETfold 2.2                    only after license + MSA protocol resolution
RFold / DEPfold                only after explicit license + artifact audit
ERNIE-RNA                      only after weight license + checkpoint audit
trRosettaRNA2 native SS        Phase I bridge analysis only
```

Optional sources cannot replace a failed primary source after outcomes. A
primary source that fails pre-prediction deployment audit triggers a protocol
amendment before any performance is measured; it is not silently dropped.

### 7.2 LOPFO contract

`LEAVE_ONE_PREDICTOR_FAMILY_OUT` holds out every predictor in one algorithmic
family, not one version. The four primary families above are four indivisible
groups. The Phase II model receives no source identity, source-family identity,
dataset identity or predictor-specific embedding. Score availability is
represented by a generic value plus missingness flag. Predictor-specific
calibrators, risk thresholds and rescue policies are prohibited.

## 8. Primary structure validity

Index nucleotides from 0 to `n-1`. A valid primary pair `(i,j)` satisfies:

- `0 <= i < j < n`;
- `j-i > 3`;
- ordered bases are one of `AU, UA, GC, CG, GU, UG`;
- every nucleotide appears in at most one selected pair; and
- there are no pairs `(i,j),(k,l)` with `i < k < j < l`.

Only canonical/Wobble pairs are eligible in the primary track because this
contract is supported consistently by the accepted 2D sources and exact
noncrossing decoder. Noncanonical pairs, multi-strand contacts and pseudoknots
are retained as separate annotation fields and may support a future secondary
track. They cannot weaken or modify primary validity.

Source output must pass its official frozen postprocessor and then the above
normalization. Invalid output is a failed source-RNA realization; ad-hoc repair
is prohibited. All tie-breaking follows the deterministic decoder protocol.

## 9. Candidate generation

Candidate generation receives only `x`, `S0`, permitted inference-time
predictor outputs and delivered `E`. The primary candidate universe is the
complete set of all pairs satisfying Section 8. Therefore it includes:

- every valid original pair from `S0`;
- every valid alternative partner, including shared-nucleotide competitors;
- every directly positive-evidence-supported valid pair, including one absent
  from `S0`; and
- every other legal canonical/Wobble pair needed for exact optimization.

There is no score-based pruning, maximum sequence separation or GT-guided
neighborhood. For `n<=600`, the pre-alphabet upper bound is
`(n-4)(n-3)/2 <= 177,906` candidates. Candidate serialization and tie order are
ascending `(i,j)`. A future implementation may use sparse computation only if
it is mathematically equivalent to this universe.

Ground truth is prohibited from alternative construction, pruning, parameter
choice and recall optimization. A labeled candidate-recall calculation is
allowed only as `ORACLE_DIAGNOSTIC_ONLY`; it cannot change inference and cannot
be promoted as model performance.

## 10. Action vocabulary and accounting

- **KEEP:** an `S0` pair remains in `S*`.
- **DELETE:** an `S0` pair is absent from `S*`.
- **ADD:** a pair absent from `S0` is present in `S*`.
- **REPLACE:** one DELETE plus one ADD sharing a reassigned nucleotide, committed
  as a coupled atomic action.
- **ABSTAIN:** the risk contract declines an entire coupled edit component and
  restores that component to `S0`.

The pair symmetric difference defines edit atoms. REPLACE actions are recovered
for reporting by maximum-cardinality bipartite matching between deleted and
added atoms that share a nucleotide; each atom is used once, and ties use
lexicographically smallest `(deleted_pair, added_pair)` lists. Unmatched atoms
remain DELETE or ADD.

A correct REPLACE requires both halves to be correct. A harmful half makes the
action harmful. Reporting a beneficial ADD while hiding its harmful coupled
DELETE is prohibited.

ADD is necessary to address missing pairs and shifted stems. REPLACE is
necessary to distinguish a wrong-partner correction from an unrelated deletion
and addition. Without them, Phase II could remove FPs but could not repair FNs,
wrong partners or displaced stems.

## 11. Primary ABSTAIN level

The primary level is **component/region-level ABSTAIN**. Edit-level abstention
can break structural coupling; RNA-level abstention discards safe independent
regions and can obtain low risk through trivial zero coverage.

After a full candidate structure is decoded, create an edit-interaction graph
over DELETE/ADD atoms. Connect two atoms when they:

- form a coupled REPLACE;
- share a nucleotide;
- are stacking-adjacent;
- compete by crossing; or
- must be jointly accepted/reverted for either the decoded structure or `S0`
  restoration to remain valid.

Connected components are indivisible commitment regions. Abstaining restores
every atom in the component to `S0`. The final structure is audited again. If
component recombination is invalid or the audit cannot be completed, fail
closed to RNA-level `S0` with zero committed edits and an explicit error. Other
abstention levels are future ablations and cannot be chosen at runtime.

## 12. Minimum-edit objective

For a fixed, not-yet-implemented score function:

\[
S^*=\arg\max_{S\in\mathcal V(x)}
\left[\operatorname{score}(S\mid x,S_0,E)
-\lambda_{edit}\operatorname{EditCost}(S,S_0)\right].
\]

Freeze:

\[
\operatorname{EditCost}(S,S_0)=|S_0\setminus S|+|S\setminus S_0|.
\]

Thus KEEP cost is 0, DELETE cost 1, ADD cost 1, and coupled REPLACE cost 2.
ABSTAIN commits no edit and costs 0. There are no hidden action-specific weights.
`lambda_edit` may be selected only on MODEL_SELECTION and is locked before
score/risk calibration.

## 13. E0 clean symbolic evidence

Only E0 semantics are frozen; no evidence is generated in this task.

### 13.1 Evidence items

- `POSITIVE_PAIR_SUPPORT(i,j)`: a clean statement that valid pair `(i,j)` is
  present in the primary reference. If present in `S0`, it directly supports
  KEEP. If absent, it legally introduces an ADD candidate. If it shares a
  nucleotide with an old partner, it supports coupled REPLACE and conflicts
  with that old pair.
- `UNPAIRED_NUCLEOTIDE_SUPPORT(i)`: a clean statement that nucleotide `i` is
  unpaired in the primary reference. It directly conflicts with every incident
  candidate/S0 pair and can support DELETE. It cannot support an ADD using `i`.

An E0 realization must be mutually consistent and valid under Section 8.
Direct E0 facts are hard admissibility constraints in E0 methods: positive
pairs are selected and supported-unpaired nucleotides remain unpaired. This
makes E0 a clean symbolic intervention; learned transport affects only
non-direct candidates. An invalid or contradictory E0 package fails closed and
is not repaired.

### 13.2 Scope labels

- **DIRECT:** the exact supported pair, or a pair incident to an explicitly
  supported-unpaired nucleotide.
- **LOCAL:** a candidate linked to a direct candidate by one frozen structural
  relation.
- **PROPAGATED:** a candidate reached by an allowed two-hop typed path.

E1 (5/10/20/30% contradiction, corruption and missingness) and E2
(SHAPE/DMS/PARS) remain placeholders. They require separate freezes and are not
generated or used here. The Phase I evidence generator is not inherited
silently because deletion-only semantics do not cover ADD/REPLACE.

## 14. Evidence transport contract

The pair graph may contain these relation types:

- `STACK_ADJ`: `(i,j)` and `(i+1,j-1)` or the reverse;
- `SOURCE_STEM_ADJ`: consecutive stacked pairs both present in `S0`;
- `ALT_PARTNER`: one candidate is an `S0` pair and the two share one endpoint;
- `SHARED_NT_COMPETE`: two candidate pairs share a nucleotide; and
- `CROSSING_COMPETE`: the two pairs cross.

Only `STACK_ADJ`, `SOURCE_STEM_ADJ` and `ALT_PARTNER` can transport evidence.
`SHARED_NT_COMPETE` and `CROSSING_COMPETE` are decoder/component constraints,
not propagation highways. Generic sequence-local edges do not transport E0.

Allowed transport is evidence-to-candidate, never candidate-to-candidate
rebroadcast:

- DIRECT: exact evidence relation;
- LOCAL: one typed hop from a direct candidate;
- PROPAGATED: exactly two simple hops from a direct candidate, using the three
  allowed transport relations, with at most one `ALT_PARTNER` hop.

Maximum radius is two; repeated propagation is prohibited. There is no
outcome-tuned target budget or pruning. Contributions from one evidence item
within a scope/path type are normalized by the number of reached candidates;
DIRECT indicators remain separate.

A future trust value `T(p,e)` may see normalized sequence/local pair features,
whether `p` is in `S0`, generic source score plus a missingness flag, evidence
type/value, typed path, path length and degree normalization. It may not see GT,
source identity/family, dataset identity, RNA family identity, role identity or
assessment outcome.

The primary matched control is **trust-shuffled**: within the same RNA,
evidence type, scope, path length and degree bin, deterministically permute
evidence-to-candidate assignments while preserving counts, candidate features,
model capacity and action mechanics. The shuffle seed is frozen before
outcomes. A relation-ablated companion removes typed path identities while
preserving item counts and capacity. Neither control may alter decoder validity.

## 15. Required controls

Later work must implement these scientific roles, though this task implements
none of them:

| Control | Scientific role |
| --- | --- |
| `S0` no refinement | Source utility/preservation anchor |
| Local evidence correction | Isolate direct/local intervention benefit |
| Global evidence-constrained refolding | Compare refinement with rebuilding the whole structure |
| Deletion-only structured refinement | Test whether ADD/REPLACE adds genuine headroom |
| Minimum-edit refinement without risk control | Isolate the risk controller |
| Risk-controlled structured refinement | Primary full policy |
| Matched evidence-masked | Attribute benefit to delivered evidence rather than context/capacity |
| Trust-shuffled / relation-ablated | Attribute nonlocal effects to justified transport relations |
| Calibration/threshold-only empirical control | Separate formal finite-family selection from ordinary calibration/thresholding |

## 16. Frozen metrics; no calculation in this task

- Pair reliability: AUPRC, AUROC, Brier score, ECE.
- Structure utility: precision, recall, F1.
- Preservation: TP preservation, FP removal, modification precision.
- Structured edits: correct/harmful DELETE, ADD and coupled REPLACE; edit
  distance to `S0`.
- Risk/selectivity: per-RNA HarmRate, edit-atom coverage, RNA-level coverage,
  risk-coverage curve and abstention rate.
- Scope: DIRECT, LOCAL and PROPAGATED.
- Generalization: source-wise, family-wise and full LOPFO.

All pair/structure metrics must declare exact primary matching; any tolerant
endpoint analysis is secondary. Micro/event-pooled results cannot replace RNA-
or cluster-balanced summaries. No performance value is computed here.

## 17. Prospective Phase II gates

| Gate | Frozen decision rule |
| --- | --- |
| P0 NOVELTY | Already **PASS** as `PHASE2_PRIMARY_DIRECTION_JUSTIFIED`; isolated ingredients remain prior art and only the qualified joint gap is claimed |
| P1 DATA/PROTOCOL | PASS only when source/provenance/license, family/identity/temporal leakage, five data roles, panel/deployment, candidate/action/evidence, exact decoder, risk contract, metrics, controls and hashes are complete |
| P2 STRUCTURED BASELINE | ADD/REPLACE must show real correction headroom beyond matched deletion-only; otherwise retain a deletion-only scientific interpretation rather than complexity escalation |
| P3 SAFETY | Frozen finite-family policy must improve the primary HarmRate over the same-capacity/no-risk control at nonzero useful edit and RNA coverage; all-abstain cannot pass |
| P4 PREDICTOR TRANSFER | Effect direction must be retained for every predeclared held-out algorithmic family under LOPFO |
| P5 NOISE | At 5% and 10% frozen E1 corruption, the risk contract and useful coverage must not collapse; exact numerical utility thresholds require a pre-experiment amendment with scientific/statistical justification |
| P6 INDEPENDENT | Independent-v2 one-shot effect direction must be retained under the locked analysis |
| P7 REAL EVIDENCE | If the final venue/claim needs it, a separately frozen real-probing test must support the core mechanism |

Only the risk tolerance/confidence and minimum calibration readiness are
numerically frozen now because they define the statistical procedure. No Phase
I 0.99 threshold is copied. Other success magnitudes must be justified and
frozen before the relevant assessment, never after seeing outcomes.

## 18. Independent assets

external77 is assigned the sole Phase II role
`PHASE1_BRIDGE_INDEPENDENT_ASSET`. It is not the Phase II primary independent
set because Phase II changes the predictor panel, action space, risk controller
and family-transfer question. It remains `EXTERNAL77_LOCKED` and can later be a
sealed secondary bridge or remain exclusively with the Phase I paper.

Independent-v2 will be designed to be:

- temporally newer than 2024-12-04 where authoritative dates permit;
- family- and 80/80 sequence-component-disjoint from Development-v2 and
  Legacy121;
- diverse in RNA type and length;
- runnable by the complete primary source panel;
- supported by exact, independently traceable 2D reference annotation; and
- preferably able to define a later real-probing subset without using probing
  values in method design.

This task does not select, inspect or list Independent-v2 identities. Before
any identities are exposed to model designers, a separate authorized sealing
task must freeze the acquisition window, manifest, checksums, exclusions,
analysis and one-shot access log.

## 19. Reproducibility and change control

Before P3 execution, the minimal-baseline task must materialize only protocol
infrastructure and verify:

- exact source and record hashes;
- executable/container/checkpoint hashes and frozen predictor flags;
- cluster-edge audit and zero cross-role component overlap;
- zero Development-v2/Legacy121 component overlap;
- candidate generation without label access;
- 100% decoder validity and byte-identical reruns; and
- synthetic risk-bound/unit tests without biological performance claims.

Any semantic change to source versions, 80/80 clustering, cutoff, roles,
predictor families, candidate universe, action accounting, E0 facts, transport,
decoder, edit cost, risk procedure, metrics or gates requires a versioned
protocol amendment and a new manifest before outcomes. A failed future gate
does not itself authorize an amendment.

## 20. Freeze outcome and authorization boundary

All required contracts have a fail-closed definition; no design blocker remains.
Therefore:

```text
PHASE2_DATASET_AND_TASK_PROTOCOL_FROZEN
PHASE2_PRIMARY_DIRECTION_JUSTIFIED
PHASE2_IMPLEMENTATION_NOT_AUTHORIZED
EXTERNAL77_LOCKED
```

The next task may be `IMPLEMENT_PHASE2_MINIMAL_STRUCTURED_BASELINES`, limited by
the separate implementation plan. It does not authorize the primary GNN/Graph
Transformer, training, biological performance experiments, evidence generation,
external77 access, old R5/R6/R8, real probing or 3D validation.
