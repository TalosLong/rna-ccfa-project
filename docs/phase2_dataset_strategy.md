# Phase II Dataset and Predictor Strategy

Status: **`PHASE2_P1_DATASET_STRATEGY_DRAFT`**

Execution: **`NOT_AUTHORIZED`**

external77: **`ONE_SHOT_LOCKED_NOT_ACCESSED`**

This document defines design requirements. It does not select records, inspect
external77, download data, run predictors, generate evidence, or freeze the
final dataset protocol.

## 1. Why the data strategy must change

Legacy121 was repeatedly used in Phase I, and its R4/CER assessment outputs were
observed during hypothesis formation. It is now permanently:

```text
PHASE1_HISTORICAL_DIAGNOSTIC_DATA
```

It may be used to reproduce Phase I, illustrate failure modes, specify unit
tests, and check backward compatibility. It must not be the main dataset for
Phase II architecture selection, risk calibration, a confirmatory development
claim, or independent validation.

Phase II needs a larger, provenance-rich, family-aware corpus because it adds
new pair actions, evaluates unseen predictor families, and may calibrate risk at
the RNA-cluster level.

## 2. Three data roles

| Role | Name | Permitted use | Prohibited use |
| --- | --- | --- | --- |
| Historical | Legacy121 | Phase I reproduction, diagnostic examples, schema/unit tests, hypothesis provenance | Primary Phase II model selection, calibration, gate decisions, independent claims |
| New development | Development-v2 | Candidate/feature design after freeze, training, validation, calibration, internal family/predictor transfer | Final independent confirmation; tuning after independent results |
| Final independent | Independent-v2, with external77 retained as a locked bridge candidate | One-shot direction and safety confirmation after complete freeze | Training, threshold selection, feature changes, rescue, method redesign |

## 3. Candidate source pools for Development-v2

Candidate pools must be audited rather than concatenated blindly:

- [bpRNA-1m](https://pubmed.ncbi.nlm.nih.gov/29746666/): broad integrated
  sequence/structure annotations and thousands of families; valuable for scale,
  but source duplication, annotation provenance, and train-overlap risk require
  explicit control.
- RNAStrAlign / ArchiveII: widely used curated family datasets; useful for
  benchmark continuity but limited family diversity and heavily reused in
  modern predictor training/evaluation.
- [RNASSTR](https://pmc.ncbi.nlm.nih.gov/articles/PMC12247784/): a recent,
  family-expanded resource with structure-aware split work; candidate for scale
  and diversity, but its release/version and annotation-generation pipeline
  must be frozen and independently audited.
- bpRNA-new and current Rfam releases: candidates for new-family development,
  subject to temporal/version provenance and covariance-model annotation
  caveats.
- [RNAsolo2](https://rnasolo.cs.put.poznan.pl/) or another PDB-derived curated
  source: candidate high-confidence structures and temporal splits; mapping 3D
  structures to a canonical 2D reference, alternate conformers, modified bases,
  complexes, and noncanonical contacts must be prospectively defined.

No pool is accepted merely because a prior paper called it a test set. Phase II
must reconstruct overlap, family, annotation, and predictor-training risks.

## 4. Development-v2 inclusion contract to freeze next

Each candidate RNA must have:

- stable dataset/source accession and exact release/version;
- sequence and secondary-structure hashes;
- annotation origin: comparative, experimentally derived, database consensus,
  or computationally inferred;
- RNA family and type, with an explicit `UNKNOWN` state rather than imputation;
- length, alphabet/modification normalization, strand count, and circularity;
- pair alphabet, minimum-loop violations, and pseudoknot/crossing annotation;
- date metadata when available (deposition, release, family-release inclusion);
- a record of overlap with Legacy121 and known training corpora of candidate
  source predictors;
- license and redistribution status.

Likely exclusions include unresolved sequence/structure mismatches, ambiguous
chain mapping, structures generated solely by one of the source predictors,
untraceable consensus annotations, unsupported multi-strand complexes in the
primary track, and RNAs whose structure cannot be represented under the frozen
primary action/decoder policy. The next protocol must make these exact.

## 5. Redundancy, family, and temporal control

### 5.1 Biological grouping hierarchy

The split unit is never a predictor record or evidence realization. A proposed
hierarchy is:

```text
sequence/construct
  -> near-duplicate cluster
    -> Rfam or curated structural family
      -> broad RNA-type stratum
```

All source-predictor outputs, evidence realizations, conformers, and assay
conditions belonging to the same RNA/construct follow the same role. Where
homolog clusters cross named families, the connected component must stay in one
role or be removed.

### 5.2 Sequence identity

The final identity threshold is not frozen here. The next audit should compare
candidate cutoffs and alignment coverage using a reproducible sequence-cluster
tool, then freeze one rule *before* model evaluation. The rule must specify:

- global versus local identity;
- minimum aligned coverage on both sequences;
- handling of reverse/complement or modified alphabets;
- transitive connected-component grouping; and
- exclusion against every Legacy121 sequence.

Reported performance must include family-held-out results even if pairwise
identity filtering has already been applied; low identity does not guarantee
structural independence.

### 5.3 Family-aware split

At minimum, all members of a declared RNA family must be assigned together for
the strongest transfer assessment. If Development-v2 size permits, reserve:

- family-disjoint model-selection folds;
- a calibration partition with disjoint family clusters; and
- an untouched Development-v2 assessment partition used once per frozen
  candidate family, still labeled internal development rather than independent.

Risk calibration at RNA level must not treat thousands of pair edits from one
RNA as independent calibration samples.

### 5.4 Temporal split

For PDB/RNAsolo-derived structures, prefer a fixed release-date cutoff:
pre-cutoff records for development and later records for a prospective temporal
assessment. The cutoff must predate retrieval, and homolog/family leakage across
the cutoff must still be removed. For database-consensus records without
meaningful experimental release dates, temporal status must be recorded as not
available rather than fabricated.

## 6. Diversity and balance

Development-v2 should prospectively stratify and report:

- RNA type/family;
- length bins chosen before outcome analysis;
- number of stems, junction complexity, and pair density;
- canonical/wobble/noncanonical content;
- nested versus pseudoknotted annotation;
- source-annotation type and experimental confidence;
- predictor family and prediction quality distribution; and
- clean-evidence eligibility/coverage.

Sampling should cap dominant families and near duplicates. Macro RNA-family and
RNA-level metrics must accompany micro/event metrics. Rare long RNAs and
pseudoknots should be preserved as explicit strata rather than allowed to
distort a single aggregate.

## 7. Source-predictor panel

### 7.1 Selection principles

Choose predictors for methodological diversity, deployability, reproducible
versions, and access to pair scores—not raw count. Every selected predictor
requires a container/environment lock, exact command, checkpoint hash, license,
training-data disclosure audit, failure policy, and deterministic output parser.

### 7.2 Proposed initial panel

| Family | Candidate | Priority | Required audit |
| --- | --- | --- | --- |
| Thermodynamic | RNAfold | Required anchor | ViennaRNA version, parameters, MFE/BPP semantics |
| Comparative/thermodynamic | PETfold | Required if alignment inputs can be standardized | Homolog source, alignment leakage, single-sequence failure semantics |
| Learned thermodynamic | MXfold2 | High | Checkpoint/training-set overlap, pair/energy outputs, version |
| End-to-end contact map | UFold | High | Length policy, post-processing, canonical/noncanonical behavior, score export |
| Structured neural | RFold **or** DEPfold | Conditional, choose at most one initially | Code/checkpoint maturity, score export, training overlap, pseudoknot and pair-alphabet semantics |
| Foundation-model 2D | RiNALMo **or** ERNIE-RNA | Conditional, choose one first | Compute, license, checkpoint, fine-tuning/training overlap, score extraction |
| Historical deep source | trRosettaRNA2 secondary output | Bridge comparator | Reproducible deployment and distinction from its 3D pipeline |
| 3D | NuFold | Not a primary 2D source | Reserve for optional downstream 2D→3D; it consumes a predicted secondary structure |

The minimal Phase II source matrix should cover at least four distinct families,
not necessarily all listed tools. A source with unavailable code/checkpoint,
intractable compute, or opaque post-processing should fail deployment audit
rather than be approximated.

### 7.3 Leave-one-predictor-family-out

The future LOMO/LOPFO design must hold out an entire algorithmic family, not one
version while a close relative remains in training. Example groups are:

- thermodynamic;
- comparative/thermodynamic;
- learned-thermodynamic DP;
- end-to-end contact-map neural; and
- structured matching/parsing neural, if one candidate passes deployment; and
- RNA foundation-model-based.

Source identity is an evaluation variable and default-excluded from model
features. Thresholds and risk controllers are not source-specific. A predictor
family must have enough RNAs and successful outputs to support RNA-level
uncertainty intervals; otherwise its result is exploratory.

## 8. Candidate and label construction

Development-v2 must support all structured actions without hidden GT leakage.
Before implementation, freeze:

- original pair candidates from `S0`;
- alternative partners from inference-time sequence/predictor/evidence rules;
- whether canonical/wobble candidates only are allowed in the primary track;
- maximum candidate inventory and deterministic pruning;
- ground-truth action labels used only for training/evaluation;
- atomic accounting of REPLACE as DELETE-old + ADD-new plus one coupled action;
- shifted-pair tolerance, if any, separately from exact-pair scoring; and
- cases with multiple acceptable conformations or uncertain reference pairs.

Candidate generation must not use the reference structure except when a
separate oracle-recall diagnostic is explicitly labeled and firewalled from
inference.

## 9. Evidence generation and modalities

### E0 — clean symbolic

The generator/version, channel, density, seeds, eligibility, and mapping from
reference to delivered evidence must be frozen. The old Phase I generator may
serve as a comparator, but Phase II must not silently copy it if ADD/REPLACE
requires new evidence semantics.

### E1 — controlled noisy symbolic

The design includes 5%, 10%, 20%, and 30% corruption. Freeze separate axes for:

- false pair support / contradictions;
- false unpaired evidence;
- dropped true evidence;
- random missingness versus structure-dependent missingness; and
- mixed channel noise.

Do not tune corruption definitions after performance is seen. Results must show
each axis and level, not only a favorable combined noise score.

### E2 — real probing

Candidate resources include [RMDB](https://rmdb.stanford.edu/), the SHAPE
benchmark represented by Hajdin et al., the six-RNA quantitative DMS benchmark,
and other datasets with both assay provenance and an independently accepted
pair structure. PARS is useful for transcriptome-scale pairedness signal but
should not be treated as pair-resolved ground truth; its reference-structure
coverage must be audited.

Required metadata include reagent/assay, in vitro/in vivo state, ionic and
ligand conditions, replicate/SNR, normalization, missing positions, sequence
mapping, and compatibility between probed state and accepted structure. The
reactivity-to-evidence mapping must be frozen on non-test data.

No real-evidence work is authorized by this document.

## 10. Independent-test strategy

external77 remains sealed and uninspected. It was designed around the Phase I
question and may not cover Phase II's modern source panel, ADD/REPLACE labels,
family transfer, or real-evidence requirements. Therefore:

1. retain external77 as an untouched **Phase I bridge independent asset**;
2. do not automatically designate it as the sole Phase II final test;
3. design an `Independent-v2` set aligned with the final Phase II task,
   preferably temporally newer and family-disjoint from Development-v2; and
4. before any access, freeze whether external77 is a secondary bridge test,
   part of a sealed multi-cohort plan, or held for the Phase I paper.

If overlap checks against external77 would reveal its identities, those checks
must wait for a formally authorized data custodian/sealing step. An alternative
is to use precomputed blinded hashes or retire external77 from Phase II and lock
a separate Independent-v2. This proposal did neither.

The final one-shot contract must precede opening any independent set and cover:

- exact data/version/exclusions;
- final predictor matrix and failure handling;
- evidence generation or real-evidence preprocessing;
- model/checkpoint, features, decoder, edit costs, calibration, risk level, and
  abstention policy;
- all metrics, aggregation, source/family/noise analyses, and multiplicity;
- numerical success/failure gates; and
- a no-retrain/no-rescue/no-redesign rule.

## 11. Planned split artifacts and audits

The next frozen protocol should require:

```text
data/phase2/manifests/source_inventory.*
data/phase2/manifests/rna_identity_inventory.*
data/phase2/manifests/family_cluster_manifest.*
data/phase2/manifests/predictor_output_manifest.*
data/phase2/manifests/evidence_manifest.*
data/phase2/splits/development_v2_roles.*
data/phase2/splits/calibration_clusters.*
data/phase2/integrity/input_hash_inventory.json
data/phase2/integrity/legacy121_overlap_audit.json
data/phase2/integrity/family_leakage_audit.json
data/phase2/integrity/predictor_training_overlap_audit.json
data/phase2/integrity/temporal_split_audit.json
```

Paths are illustrative until the dataset protocol is frozen. No artifact above
was created in this planning task.

## 12. Dataset readiness gates

Before implementation authorization, all of these must pass:

- every Development-v2 record has traceable reference provenance and license;
- exact and near-duplicate overlap with Legacy121 is removed or isolated;
- family/identity connected components are role-disjoint;
- source-predictor training overlap is measured and reported;
- predictor execution succeeds at a prospectively required coverage level;
- candidate-generation oracle recall is measured only as a firewalled
  diagnostic and meets a frozen floor;
- calibration contains enough independent RNA/family-cluster units for the
  chosen risk statement;
- pseudoknot and noncanonical cases have explicit track assignment;
- the independent-test role and seal procedure are decided without opening
  external77; and
- all manifests and hashes are locked before model selection.

## 13. Decision boundary

This design supports proceeding to `FREEZE_PHASE2_DATASET_AND_TASK_PROTOCOL`.
It does not certify that Development-v2 exists, that any predictor is deployable,
that a formal risk guarantee is feasible, or that external77 is suitable for
Phase II. Those are fail-closed questions for the next task.
