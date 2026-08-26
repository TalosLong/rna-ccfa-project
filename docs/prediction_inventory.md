# Prediction Output Inventory

Last audited: 2026-08-26

## Scope and Classification

This registry locates prediction outputs available to the RNA CCF-A project without changing the originals. It separates four asset classes:

- **Primary source 2D output**: a direct secondary-structure prediction eligible for normalization and the shared 2D evaluator.
- **Evidence-derived 2D output**: a deterministic prediction derived from structural evidence; it is not ground truth and is not automatically part of the initial source-model pool.
- **Derived/intermediate 2D output**: a transformed map, fused structure, or 3D-workflow intermediate that must not be double-counted as an independent predictor.
- **3D-only output**: a PDB/mmCIF prediction reserved for Candidate downstream analysis.

Counts below are filesystem observations, not benchmark results. No raw or historical output was modified.

## Primary Source 2D Outputs

| Dataset coverage | Source model | Primary path / pattern | Records | Stored representation | Sequence included? | Pair scores retained? | Normalization notes |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| Legacy 121 | RNAfold | `/root/autodl-tmp/data/ss/rnafold/*.db` | 121 non-empty `.db` files; one unrelated `ROSETTA_CRASH.log` is also present | One line of standard dot-bracket | No | No | Filename matches the 121 individual FASTA records after removing `.db`; the parser must join sequence by an explicit ID map |
| Legacy 121 | PETfold | `/root/autodl-tmp/data/ss/petfold/*.db` | 121 non-empty `.db` files | One line of standard dot-bracket | No | No | One filename anomaly exists: `1A9L.db` corresponds to `1A9L_38_hpbulge_nmr_A.fasta`; all other IDs match after the documented suffix normalization |
| Legacy 121 | trRosettaRNA2 native SS | `/root/autodl-tmp/models/trRosettaRNA2/data/ss_native/<rna_id>/` | 121 DBN plus 121 NPZ files, all non-empty | DBN has header + structure; NPZ key `ss` is `float32` with shape `L x L` | DBN: no; NPZ: no | Yes, in `*_ss_prob.npz` | Use this directory as the canonical local path. `/root/autodl-tmp/models/trRosettaRNA2/ss_predictions_native` is a hard-linked mirror and must not be counted again |

The 121 RNAfold IDs and the 121 trRosettaRNA2 native-SS directory IDs match the 121 individual legacy FASTA basenames under the documented normalization. PETfold has the single `1A9L` filename exception above. These mappings and the two GT-only exclusions are frozen explicitly in `manifests/legacy121_v1.csv` and `docs/legacy121_v1_protocol.md`.

### trRosettaRNA2 Related 3D/Internal Outputs

`/root/autodl-tmp/models/trRosettaRNA2/predictions/native` contains 120 completed triples of `model_1_unrelaxed.pdb`, `model_1_2D.npz`, and `plddt.csv`. The `model_1_2D.npz` files contain object-valued `distance` and `contact` dictionaries plus per-residue `plddt`; they are internal 3D-model outputs, not substitutes for the standalone SS ensemble's `L x L` pair-score NPZ files.

## Evidence-Derived 2D Predictions

| Asset | Path / pattern | Coverage | Representation | Provenance restriction |
| --- | --- | ---: | --- | --- |
| external77 `NMR_PRED` | `/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1/data/ss_dotbracket/*_NMR_PRED.dbn` and the `nmr_pred_ss_flat` field in `data/NMRFOLD_external77_fullatom_3SS_v3/NMRFOLD_external77_fullatom_3SS_v3.npz` | 77 DBN records plus matrix storage for the same manifest | Header + sequence + extended dot-bracket; binary matrices in the NPZ | Deterministic evidence-derived prediction. Never relabel as `GT_ALL` or `GT_CON` |
| Legacy V11-2 candidate topologies | `/root/autodl-tmp/data/ss/v11_2/<rna_key>/topology_*.db` and `topology_*_pairs.tsv` | 1,315 DB plus 1,315 pair tables across 121 RNA directories | Header + extended dot-bracket; explicit 1-based `i,j` TSV | Multiple candidate topologies may exist per RNA. `summary.csv` is required for rank/provenance; this is not one frozen prediction per RNA |
| Legacy flat V11-2 copy | `/root/autodl-tmp/models/trRosettaRNA2/v11_2_ss_dir_full/*.db` | 121 | One selected/copy DB per legacy RNA | Convenience input used by historical 3D experiments, not an independent predictor run or GT |

The paths embedded in `/root/autodl-tmp/data/ss/v11_2/summary.csv` still refer to an older tree. Consumers must use the current root without editing the raw summary.

## Derived and Intermediate 2D Assets

| Asset | Current paths | Observed coverage / shape | Why it is not an independent source output |
| --- | --- | --- | --- |
| DRfold ViennaRNA/PETfold intermediates for external77 | `/root/autodl-tmp/results/DRfold_external77_missing/<EXTSEQ*>/seq_ss_vie_ViennaRNASS.txt`, `seq_ss_pet_PETfoldSS.txt`, and `seq_ss.npy` | 44 non-empty records of each type; text files hold one structure; sampled `seq_ss.npy` is `L x L x 4` floating point | Generated inside a 3D pipeline, covers only a subset, and lacks a frozen channel/confidence contract |
| DRfold ViennaRNA/PETfold intermediates for TS85/CASP working trees | `/root/autodl-tmp/data/TS85_DRfold_holdout/**/seq_ss_*` and `/root/autodl-tmp/data/TS85_DRfold_CASP_output/**/seq_ss_*` | 88 non-empty Vienna text files, 88 PETfold text files, and 88 `seq_ss.npy` files | Working-tree intermediates with nested paths and potential target duplication; must be mapped through a frozen sample manifest before reuse |
| RNAbpFlow RNAfold maps | `/root/autodl-tmp/RNAbpFlow/Inputs_rnafold_maps/<target>/map{1,2,3}.npy` | 87 target directories and 261 binary maps; sampled map is `L x L float32` | Three-channel downstream inputs derived from RNAfold, not three predictions and not a new source model |
| trRosettaRNA2 fused/ablation structures | `/root/autodl-tmp/models/trRosettaRNA2/fused_ss/` and historical `predictions/{gt,v11_2,scrambled,complementary,alldot,...}` conditions | `fused_ss` contains 119 DB, 239 probability files, and 121 text files across several conditions | Experimental mixtures, controls, GT-conditioned inputs, or destructive ablations; exclude from source baseline normalization unless a later experiment explicitly specifies them |
| Historical GT convenience copy | `/root/autodl-tmp/models/trRosettaRNA2/gt_ss_dir_full/*.dbn` | 121 | Copy of legacy GT for 3D input experiments, not a prediction |

## Consolidated 3D Prediction Registry

The canonical 3D consolidation root is `/root/autodl-tmp/RNA_benchmark_predictions`. These files do not enter the Phase 0 2D evaluator.

### Main external77 + TS85 Manifest

`consolidation_manifest.csv` contains 972 data rows, all marked `FOUND`:

| Dataset | Methods | Records per method | Total |
| --- | --- | ---: | ---: |
| external77 | AF3, DRfold, FARFAR2, RNAbpFlow, RhoFold+, trRosettaRNA2 | 77 | 462 |
| TS85 working set | AF3, DRfold, FARFAR2, RNAbpFlow, RhoFold+, trRosettaRNA2 | 85 | 510 |

The manifest preserves both `source_path` and `copied_path`; it is the preferred registry for tracing these 3D outputs back to model-specific trees.

### Full Historical Consolidation Manifest

`consolidation_manifest_full.csv` contains 6,684 data rows, all marked `FOUND`:

| Dataset class | Method | Rows |
| --- | --- | ---: |
| singlechain | trRosettaRNA2 | 3,995 |
| singlechain | FARFAR2 | 442 |
| RNA-ligand | AF3 | 366 |
| RNA-ligand | trRosettaRNA2 / FARFAR2 / RhoFold+ | 61 each |
| RNA-protein | AF3 | 1,116 |
| RNA-protein | trRosettaRNA2 / FARFAR2 / RhoFold+ | 194 each |

The large row counts include multiple conditions, samples, or copied historical outputs. They must not be interpreted as unique RNA counts.

### Older external77 Collection

`/root/autodl-tmp/external77_predictions` contains an earlier partial/heterogeneous 3D collection: 77 trRosettaRNA2 files, 77 RNAbpFlow files, and 72 each for AF3, DRfold, FARFAR2, and RhoFold+. Use the complete 77-per-method consolidated external77 tree for downstream bookkeeping; retain the older tree only as source/provenance material.

## Coverage Gaps and Required Handling

1. The legacy 121 collection is currently the only dataset with complete historical outputs from all three verified runnable 2D candidates: RNAfold, PETfold, and trRosettaRNA2 native SS.
2. external77 does not currently have a complete three-source 2D prediction matrix. Its 3D six-method predictions cannot substitute for source secondary structures.
3. external77 predictor reruns must wait for a frozen `GT_ALL`/`GT_CON` evaluation target and an explicit policy for the four sequences containing `N`; the target choice must not affect predictor inputs.
4. Historical RNAfold/PETfold structures do not retain pair probabilities. Confidence-aware experiments require reproducible reruns or must use a confidence-free shared setting.
5. All normalizers must write new artifacts outside these raw/historical roots and preserve `raw_prediction_path` plus provenance metadata.
6. Duplicate copies, hard links, fused conditions, and downstream input maps must be linked to their parent prediction rather than counted as independent source-model observations.

## Reproducibility Record

Counts, sample formats, manifest status, array keys/shapes, and legacy ID-set comparisons were checked read-only on 2026-08-25. This inventory locates assets; it does not assert that historical outputs can already reproduce published or previously reported metrics.
