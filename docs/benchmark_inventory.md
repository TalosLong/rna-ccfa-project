# Benchmark and Ground-Truth Inventory

Last audited: 2026-08-25

## Scope and Status Labels

This inventory records every dataset or dataset-like working set referenced by the current local benchmark index. It does not freeze the final refinement training/evaluation dataset list.

- **Primary candidate**: sufficiently organized to enter Phase 0 normalization after the listed decisions are resolved.
- **Supporting / incomplete**: useful records exist, but the directory is not yet a frozen 2D benchmark.
- **Downstream only**: currently relevant to optional 2D -> 3D validation, not source-model 2D evaluation.
- **UNKNOWN**: the requested fact is not established by existing local documentation or a direct, unambiguous file count.

No data were downloaded and no raw-data file was modified during this audit.

## Repository and Workspace Inspection

- This Git repository currently contains project-state Markdown only. It has no repository-local dataset directory, README, executable script, or YAML/JSON/TOML/INI/CFG configuration file.
- The existing local data index is `/root/autodl-tmp/benchmark_workspace/README.md`, with source-path mappings in `/root/autodl-tmp/benchmark_workspace/LINK_MANIFEST.tsv`. The index uses symlinks and states that source data were not moved or copied.
- Standard external77 documentation and reproducible evaluation/build scripts are under `/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1/README.md` and `/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1/scripts`.
- General consolidation/verification scripts are under `/root/autodl-tmp/scripts`. No single configuration file currently freezes dataset roots, sample IDs, 2D target choice, or split membership for this research project.

## Dataset Inventory

| Dataset name | Local path | Source documented locally | Number of samples directly obtainable | Sequence format | Secondary-structure format | Pseudoknots represented? | Ground-truth 3D available? | Current use in benchmark |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Legacy NMR collection | `/root/autodl-tmp/data/sequences`; `/root/autodl-tmp/data/ss/gt`; `/root/autodl-tmp/data/structures` | **UNKNOWN** — these roots have no README or manifest. Filenames contain PDB-like IDs and experimental-modality labels, but those names are not a source document. | 121 primary one-record FASTAs; 123 GT `.db`; 147 CIF in the structure pool. All 121 sequence IDs and all 123 GT ID prefixes have a same-prefix CIF. | One-record FASTA; `all.fasta` is a 121-record aggregate. The ligand/protein aggregate FASTAs are separate complex assets. | One-line extended dot-bracket in `ss/gt`; filenames end in `_matrix.db`. | **YES** — 13/123 GT files encode crossing bracket families. | **YES, mapping not frozen** — matching CIFs exist by ID prefix, but explicit chain/model mapping is not documented. | Primary Phase 0 2D candidate after resolving the 121-sequence/123-GT discrepancy. |
| TS85 benchmark working tree | `/root/autodl-tmp/data/TS87`; consolidated predictions at `/root/autodl-tmp/RNA_benchmark_predictions` | **PARTIAL** — the 18-target CASP package README identifies corrected CASP RNA targets and an AutoDL CASP staging source; source documentation for the 67-target holdout was not found. | 85 benchmark targets: 67 holdout + 18 CASP package manifest rows. The 9 RNAbpFlow Fig. 3 and 6 CASP15 FASTAs are filename-confirmed subsets of those 18, not additional targets. | One-record FASTA in `Fasta/holdout`; per-target plus aggregate FASTA in the corrected CASP package. | Holdout: **UNKNOWN** as frozen GT 2D. CASP18: canonical `L x L` `.npy`/`.csv` matrices plus 1-based pair-list `.tsv`. | **PARTIAL** — 10/18 CASP pair lists contain crossing pairs; status for the 67 holdout targets is **UNKNOWN**. | **YES** — all 67 rows in `predictions/evaluation_comparison.csv` point to existing GT CIFs, and the CASP manifest has 18 selected-chain full-atom CIFs. | Current six-method 3D benchmark: 510 consolidated prediction rows = 85 targets x 6 methods. Not yet a unified 2D baseline dataset. |
| NMRFold external77 full-atom standard v3 | `/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1` | Audited v7 external split, according to the package README. Row-level `source_record`, `pdb_id`, `source_cif`, and selected-CIF provenance are in `NMRFOLD_external77_fullatom_3SS_manifest.csv`. | 77 manifest rows, length 14-219; 4 sequences contain `N`; 77 selected full-atom GT CIFs. | Sequence in CSV manifest and NPZ; readable DBN exports also repeat the sequence. | NPZ `L x L` matrices for `GT_ALL`, `GT_CON`, and `NMR_PRED`; 77 three-line extended-DBN exports per target type. | **YES** — crossing pairs occur in 31/77 `GT_ALL`, 25/77 `GT_CON`, and 17/77 `NMR_PRED` exports. | **YES** — the README and manifest define one deterministic full-atom GT conformer per sequence. | Current six-method 3D benchmark: 462 consolidated prediction rows = 77 targets x 6 methods. Primary 2D candidate after target semantics are frozen. |
| CASP16 working set | `/root/autodl-tmp/data/casp16` | **UNKNOWN** — no README or manifest exists in this root. The directory name alone is not treated as sufficient provenance. | Frozen sample count **UNKNOWN**. Directly observed: 18 target-named `.txt` files (14 non-empty), 8 target CIFs, and 10 FASTAs (8 test FASTAs plus 2 chain-specific FASTAs for 8UO6). | FASTA; a test FASTA may be multi-chain, and 8UO6 also has chain-specific FASTAs. | Non-empty `.txt` files contain repeated three-line `>strand`, sequence, extended-dot-bracket records. | **YES** in observed non-empty files. | **PARTIAL** — CIFs exist for 8 of the 18 target-named structure files. | Supporting source/staging records only; not a frozen benchmark split. |
| RNA complex structure collection | `/root/autodl-tmp/data/complexes`; aggregate sequences at `/root/autodl-tmp/data/sequences/rna_{ligand,protein}_sequences.fasta` | **UNKNOWN** — no README or manifest exists for the collection. | 248 CIFs: 54 ligand and 194 protein complexes. Aggregate FASTAs contain 61 ligand and 194 protein records, so a one-to-one sample mapping is not assumed. | RNA sequence is present in mmCIF polymer records; separate multi-record FASTA aggregates exist. | **UNKNOWN** — no frozen 2D GT files or coordinate-to-pair annotation protocol were found. | **UNKNOWN** — directory category names are not accepted as a 2D structure representation. | **YES** at the coordinate-asset level: 248 CIFs; sequence/chain-to-CIF mapping still requires a manifest. | Downstream-only candidate; excluded from current Phase 0 2D baseline evaluation. |

The six methods in the consolidated TS85 + external77 3D manifest are AF3, DRfold, FARFAR2, RNAbpFlow, RhoFold+, and trRosettaRNA2. Their presence there does not by itself make them runnable 2D source predictors.

## Derived and Non-Dataset Benchmark Assets

| Asset | Local path | Records observed | Structure representation | Ground-truth 3D linkage | Current use |
| --- | --- | ---: | --- | --- | --- |
| Legacy V11-2 topology candidates | `/root/autodl-tmp/data/ss/v11_2` | 121 RNA IDs; 1,315 `.db` plus 1,315 pair-list `.tsv` | Header + extended dot-bracket and explicit pair lists; multiple candidate topologies per RNA; crossing metadata in `summary.csv` | Inherits legacy RNA IDs, but an explicit topology-to-CIF manifest is absent | Candidate/evidence-generation audit material; not one GT per RNA |
| external exact V11-2 candidate set | `/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1/data/nmr_pred_v11_2_exact_v3` | 78 rows in `summary.csv` | Candidate matrices/topologies from deterministic inversion | **UNKNOWN** for the complete 78-row set; it contains one record outside final external77 | Candidate-generation audit material, not GT |
| Consolidated TS85 + external77 3D predictions | `/root/autodl-tmp/RNA_benchmark_predictions/consolidation_manifest.csv` | 972 rows, all `FOUND`: 510 TS85 + 462 external77 | Predicted PDB/mmCIF plus CSV provenance | Uses the GT coordinate assets described above; it does not contain common 2D GT | Optional downstream 3D validation asset, not a dataset |

## Ground-Truth Location Registry

| Ground-truth asset | Path / pattern | Representation and interpretation |
| --- | --- | --- |
| Legacy NMR GT | `/root/autodl-tmp/data/ss/gt/*.db` | One-line extended dot-bracket. Treat as unnormalized until the 121-sequence/123-GT ID discrepancy is resolved. |
| Legacy coordinate pool | `/root/autodl-tmp/data/structures/*.cif` | 147 mmCIF files. Same-prefix CIFs exist for every current primary sequence and GT filename, but the chain/model mapping is not yet frozen. |
| Historical trRosettaRNA2 copy of legacy GT | `/root/autodl-tmp/models/trRosettaRNA2/gt_ss_dir_full/*.dbn` | 121 copied DBN files. This is a convenience copy, not an independent source of truth. |
| Historical trRosettaRNA2 V11-2 copy | `/root/autodl-tmp/models/trRosettaRNA2/v11_2_ss_dir_full/*.db` | 121 V11-2 structures. Candidate/evidence-derived structures, not automatically GT. |
| Legacy V11-2 explicit pairs | `/root/autodl-tmp/data/ss/v11_2/*_topology_*.tsv` | Explicit base-pair tables, with multiple candidate topologies possible for one RNA. |
| TS85 holdout GT 3D registry | `/root/autodl-tmp/data/TS87/predictions/evaluation_comparison.csv` | 67 rows with existing `gt_cif` paths. This is a 3D evaluation registry, not a 2D GT manifest. |
| TS85 CASP18 canonical 2D GT | `/root/autodl-tmp/data/TS87/GT-CIF/casp_fullatom_v2/casp_fullatom_v2_CODEX/ss_canonical_matrix_manifest.csv` | 18 targets with canonical matrix and 1-based explicit-pair paths. |
| TS85 CASP18 GT 3D | `/root/autodl-tmp/data/TS87/GT-CIF/casp_fullatom_v2/casp_fullatom_v2_CODEX/casp_fullatom_v2_manifest.csv` | 18 targets with selected chain, sequence, missing-position metadata, and full-atom CIF/PDB/NPZ paths. |
| external77 primary matrices | `/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1/data/NMRFOLD_external77_fullatom_3SS_v3/NMRFOLD_external77_fullatom_3SS_v3.npz` | Per-record `L x L` matrices for `GT_ALL` and `GT_CON`; also contains `NMR_PRED`, which is a deterministic evidence-derived prediction and must not be relabeled as GT. |
| external77 readable DBN exports | `/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1/data/ss_dotbracket/*_{GT_ALL,GT_CON}.dbn` | Three non-empty lines: header, sequence, extended dot-bracket. |
| external77 manifest | `/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1/data/NMRFOLD_external77_fullatom_3SS_v3/NMRFOLD_external77_fullatom_3SS_manifest.csv` | Stable `sequence_id`, sequence, pair counts, source mapping, and GT status metadata. |
| external77 GT 3D | `/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1/data/NMRFOLD_external77_fullatom_3SS_v3/selected_fullatom_cif/*.cif` | 77 deterministic selected full-atom GT conformers, mapped by the external77 manifest. |
| CASP16 provisional structures | `/root/autodl-tmp/data/casp16/dot/*.txt` | Multi-record extended dot-bracket for 14 non-empty files; 4 files are empty. Provisional only until sequence/chain mapping is frozen. |
| CASP16 provisional GT 3D | `/root/autodl-tmp/data/casp16/CIF/*.cif` | 8 target coordinate files; no local manifest establishes a complete 18-target mapping. |
| RNA complex coordinates | `/root/autodl-tmp/data/complexes/{ligand,protein}/**/*.cif` | 248 coordinate files. These are not converted to 2D GT and currently lack a frozen sequence/chain manifest. |

3D CIF/PDB coordinates are not silently converted into 2D GT in Phase 0. Any future coordinate-to-pair annotation procedure must be specified, versioned, and validated first.

## Representation Notes

- Extended dot-bracket must preserve distinct bracket families such as `()`, `[]`, `{}`, and `<>`; flattening everything to `()` would erase crossing pairs.
- The legacy GT files contain structure only, while external77 DBN exports contain header, sequence, and structure. A parser must distinguish these layouts instead of returning the first non-header line unconditionally.
- `GT_ALL` is the union of all RNApolis base-pair rows with `GT_CON` and may contain noncanonical pairs. `GT_CON` is the constrained/canonical target. Selecting one is a research/evaluation decision, not a file-format decision.
- `NMR_PRED` and V11-2 solutions are evidence-derived candidate predictions. They are not interchangeable with experimentally annotated GT.

## Integrity Issues and Blockers

1. The legacy tree has 121 primary individual FASTA files and 121 RNAfold outputs, but 123 GT files. The two GT-only records are `8Q4O_23_g4_nmr_matrix.db` and `8TNS_24_g4_nmr_matrix.db`; filename suffix conventions also differ across directories and require an explicit ID mapper.
2. external77 requires a frozen choice between `GT_ALL` and `GT_CON`, including how noncanonical pairs are scored.
3. Four external77 sequences contain ambiguous `N`; predictor compatibility and exclusion/imputation policy must be recorded before batch execution.
4. Paths stored inside legacy `ss/v11_2/summary.csv` point to an older `/root/autodl-tmp/Bench/...` location. Consumers must resolve current files under `/root/autodl-tmp/data/ss/v11_2` without editing the original summary.
5. TS87/TS85 and CASP16 do not yet have a single authoritative 2D sample manifest with validated sequence, chain, GT, and split fields.

## Reproducibility Record

Counts were produced with read-only filesystem enumeration and CSV/manifest inspection on 2026-08-25. Dot-bracket crossing counts require a non-parenthesis bracket family. The TS85 CASP18 count was obtained directly from pair lists using the crossing criterion `i < k < j < l` (or its symmetric ordering). These are representation-level checks and do not independently assert a biological pseudoknot classification.

The benchmark roots are intentionally referenced by absolute path because the raw assets live outside this Git repository. Future runnable manifests should store stable logical IDs plus configurable data roots rather than copy or rewrite raw data.
