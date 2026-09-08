# Phase II Dataset Source Audit

Status: **`PHASE2_DATASET_SOURCE_AUDIT_COMPLETE`**

Audit date: **2026-09-09 UTC**

Scope: public source metadata only. No candidate sample was selected, no
sequence or structure was downloaded for model development, and external77 was
not accessed.

`UNKNOWN` means that the cited public source did not establish the field
reliably enough for this protocol. It is a fail-closed value, not an inference.

## 1. Audit criteria

A source can enter a canonical Development-v2 role only when its exact frozen
release, annotation provenance, lawful-use terms, and normalization path are
auditable. A public download link alone does not prove redistribution
permission. A benchmark's popularity does not establish independence from
predictor training.

The source-level decision does not admit records automatically. Every admitted
record must still pass the per-RNA inclusion, family/homology, temporal,
predictor-overlap, and primary-validity contracts in
`docs/phase2_dataset_and_task_protocol.md`.

## 2. Dataset audit

| Dataset | Exact release/version | URL/DOI | License / redistribution | Sequence and annotation origin | Family/date metadata | Pseudoknots, modified bases, strands | Predictor-training and Legacy121 risk | Phase II decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bpRNA-1m | Exact downloadable release identifier: **`UNKNOWN`**; paper used Rfam 12.2 and six additional archives | [bpRNA repository](https://github.com/hendrixlab/bpRNA); [paper](https://doi.org/10.1093/nar/gky285) | Dataset license and explicit redistribution permission: **`UNKNOWN`** | 102,318 structures compiled from CRW, tmRNA, tRNAdb, SRP, RNase P, PDB and Rfam 12.2; mixed experimental, comparative and computational provenance | 2,588 families reported; per-record deposition date not established by the audited source | bpRNA notation represents pseudoknots and loop types; normalization of modified bases and multi-strand policy for this project: **`UNKNOWN`** | High: a common training/evaluation source, and its heterogeneous inputs create nontrivial Legacy121 overlap risk | **DEFER**. Provenance/training-overlap reference only until exact artifact and license are resolved |
| RNAStrAlign | Original exact release/version and canonical checksum: **`UNKNOWN`** | Described and re-hosted by [MXfold2](https://github.com/mxfold/mxfold2) | Original dataset license and redistribution permission: **`UNKNOWN`** | Curated benchmark with accepted secondary structures; exact record-level source provenance differs across distributions and is not frozen here | Eight-family usage is common; record dates: **`UNKNOWN`** | Distribution-specific; modified-base and strand policy: **`UNKNOWN`** | Very high: directly used by multiple neural RNA-SS predictors | **DEFER / overlap registry only** |
| ArchiveII | Exact canonical release is **`UNKNOWN`**; processed publications report non-identical record counts | Described and re-hosted by [MXfold2](https://github.com/mxfold/mxfold2) | Original license and redistribution permission: **`UNKNOWN`** | Literature/accepted-structure benchmark; exact annotation lineage must be resolved per artifact | Family labels are available in common processed copies; trustworthy record dates: **`UNKNOWN`** | Distribution-specific; modified-base and strand policy: **`UNKNOWN`** | Very high: established predictor benchmark/training-adjacent corpus | **DEFER / overlap registry only** |
| RNASSTR | Fixed Zenodo record **15319168**, deposited 2025-05-01; internal semantic version field: **`UNKNOWN`** | [Zenodo record](https://doi.org/10.5281/zenodo.15319168); [paper](https://doi.org/10.1093/nar/gkaf579) | **CC BY 4.0**, including redistribution with attribution | Sequences derived using NCBI RefSeq release 229 and GTDB release 214; family/fold assignments and structures inferred with Infernal 1.1.5 and Rfam 14.10 consensus models | 4,028 folds reported; source-level release dates are known, but record-level experimental deposition dates are not applicable | Pseudoknots are not represented by the Rfam consensus workflow used; modified-base and multi-strand experimental semantics are not applicable in the same sense as PDB records | Moderate-to-high predictor pretraining overlap risk; exact Legacy121 identity/family overlap must be removed | **ADMIT only to TRAIN/MODEL_SELECTION candidate pools**. Computational consensus annotations are prohibited from score/risk calibration and assessment GT |
| bpRNA-new | Rfam **14.2** families absent from Rfam 12.2; exact standalone artifact checksum: **`UNKNOWN`** | [MXfold2 paper](https://doi.org/10.1038/s41467-021-21194-4); [distribution](https://github.com/mxfold/mxfold2) | Standalone dataset license and redistribution permission: **`UNKNOWN`** | Rfam comparative consensus structures; constructed as a family-new test relative to bpRNA/Rfam 12.2 and filtered with CD-HIT-EST | Family provenance is available through Rfam; sequence-specific deposition dates are not the intended metadata | Consensus secondary structures; pseudoknot and modified-base semantics are limited by the source representation | Very high evaluation-overlap risk because it is an established family-wise test set | **DEFER / overlap registry only**; must not be repurposed as pristine assessment data |
| Rfam | **15.1**, January 2026 | [release notes](https://rfam.org/release-notes); [Rfam](https://rfam.org/) | Rfam states that its data are **CC0** | Family seed/full alignments, consensus secondary structures and covariance models; comparative/computational, not an experimental structure collection | 4,227 families in 15.1; family-level release history available, sequence-specific experimental dates generally not the relevant unit | Consensus representation; pseudoknot/noncanonical and modified-base handling are not equivalent to exact 3D-derived pair annotations | High pretraining overlap risk for modern language/structure models; family labels are valuable for leakage control | **ADMIT as family authority and TRAIN supplement only**. Never use a consensus record as experimental confirmation |
| RNAsolo2 | Live snapshot audited: **BGSU 4.53 / Rfam 15.1**, updated **2026-08-20** | [about](https://rnasolo.cs.put.poznan.pl/about); [help](https://rnasolo.cs.put.poznan.pl/help); [paper](https://doi.org/10.1016/j.jmb.2025.169570) | Site is open access; explicit derived-dataset redistribution license: **`UNKNOWN`** | PDB-derived experimentally determined RNA structures curated into nonredundant representatives | PDB deposition/release metadata and Rfam annotations can be traced; live resource changes weekly | BPSEQ/DBN and coordinate exports available; server treats multi-chain structures as separate chains; exact modified-residue normalization must be recorded per record | PDB-based model training overlap is plausible; Legacy121 overlap must be tested | **RESERVE, not Development-v2**. Preserve as a candidate discovery/indexing route for a future temporally newer Independent-v2; resolve license before redistribution |
| wwPDB / PDB-derived RNA | Archive releases are record-specific; every admitted PDB accession and first public release date must be frozen | [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies) | PDB archive data are **CC0 1.0** | Experimentally determined 3D structures; 2D pair annotation is derived and must name the exact annotation tool/version | Record deposition/release date is authoritative; family labels require an audited external mapping | May contain modified residues, multiple strands, alternate conformers and crossing/noncanonical contacts | High but auditable overlap risk for structure/foundation-model training; exact accession/hash and family filtering required | **ADMIT through the fixed RNA3DB-2D path below**, not by ad-hoc PDB parsing |
| RNA3DB-2D | Figshare **v1**, DOI **10.6084/m9.figshare.30144502.v1**; based on RNA3DB release **2024-12-04** | [Figshare artifact](https://doi.org/10.6084/m9.figshare.30144502.v1); [pipeline](https://github.com/ZYZhang17/RNA3DB-2D-Structures); [RNA3DB](https://github.com/marcellszi/rna3db) | Artifact/pipeline report **MIT**; underlying PDB records are CC0 | RNA3DB sequence/structure clusters over PDB-derived RNA; rnapolis-py produces BPSEQ 2D annotations from coordinates | PDB dates are traceable; RNA3DB supplies sequence/structure clustering, while this project independently reapplies its frozen family/homology rule | Pipeline standardizes modified residues to A/C/G/U/N; conformer, strand, noncanonical and pseudoknot fields must still be retained explicitly | PDB/foundation-model overlap must be audited per accession and cluster; exact Legacy121 overlap is removed | **PRIMARY experimental candidate pool** for all Development-v2 roles after filtering; no role assignment may cross a biological cluster |
| Current RNA3DB | Observed listed release **2025-10-01-incremental** | [RNA3DB repository](https://github.com/marcellszi/rna3db); [preprint](https://doi.org/10.1101/2024.01.30.578025) | Repository: **MIT**; PDB records: CC0 | PDB-derived sequence/structure clusters | Record dates traceable | Same caveats as RNA3DB-2D | Must remain unseen during model design if used for temporal independence | **RESERVE** as a possible Independent-v2 source; no identities are selected in this task |

## 3. Canonical source decision

Development-v2 is a role-partitioned resource, not a single homogeneous
benchmark:

1. **Experimental core:** RNA3DB-2D Figshare v1, based on RNA3DB 2024-12-04,
   after the frozen per-record filters.
2. **Training/model-selection supplement:** RNASSTR Zenodo 15319168 and Rfam
   15.1 consensus records, with computational/comparative provenance retained.
3. **Leakage registries only:** bpRNA-1m, RNAStrAlign, ArchiveII and bpRNA-new.
   They cannot supply pristine calibration or assessment labels.
4. **Future independent reserve:** post-cutoff PDB/RNA3DB/RNAsolo2 records.
   No identity was viewed or selected here.

This design prevents millions of easy comparative records from overpowering
the smaller experimentally grounded units. Dataset origin must be available to
auditors and stratified reports, but it is prohibited as a model or risk-policy
input.

## 4. Unresolved items and fail-closed handling

The following remain `UNKNOWN` and therefore cannot be silently waived:

- original license and canonical version for bpRNA-1m, RNAStrAlign, ArchiveII
  and bpRNA-new;
- explicit RNAsolo2 derived-data redistribution terms;
- exact predictor-training membership for individual records in most public
  model checkpoints; and
- reliable structure-level dates for comparative consensus records.

Before any source is promoted, a new protocol amendment must cite the exact
artifact and license, record its checksum, and pass the same family/identity
firewall. Convenience is not an amendment criterion.

## 5. Non-actions

This audit created no Development-v2 manifest, downloaded no biological
records or checkpoints, generated no evidence, ran no predictor, trained no
model, and did not access external77.
