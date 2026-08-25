# Model Inventory

Last audited: 2026-08-25

## Scope and Status Labels

This inventory covers model assets linked from the current benchmark workspace and distinguishes models that can produce secondary-structure predictions from models that only produce or score 3D structures. It records local reproducibility state; it does not select the final 3-5 source predictors.

- **Verified runnable**: a local smoke test completed during this audit.
- **Installed, not smoke-tested**: code and required local assets appear present, but no inference was run during this audit.
- **Output-only**: historical predictions are present, but a complete local runner/checkpoint was not located.
- **Not a source 2D predictor**: useful elsewhere in the benchmark, but ineligible for the Phase 0 shared 2D evaluator as currently configured.

All smoke-test outputs were written under `/tmp`; no raw data or historical prediction was modified.

## Phase 0 Secondary-Structure Predictor Candidates

| Predictor | Local status | Version / checkpoint | Input | Primary output | Pair probabilities / confidence | Pseudoknot handling | Current Phase 0 role |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ViennaRNA RNAfold | Verified runnable | RNAfold 2.4.17 at `/usr/bin/RNAfold`; default packaged energy parameters unless a future protocol overrides them | One or more RNA sequences through FASTA/text file or stdin | MFE structure in standard dot-bracket plus free energy on stdout | Available on rerun with `-p`: partition-function base-pair probabilities are written in the dot plot; not retained in the existing legacy `.db` outputs | Standard MFE output is nested `()`; no pseudoknot prediction in this configuration | Initial deterministic source-predictor candidate |
| PETfold | Verified runnable | PETfold v2.0 executable at `/root/autodl-tmp/models/DRfold_repo/third_party/PETfold/bin/PETfold`; SHA-256 `99deeb0066a246b8f6ac79e13f2c60f62dd63e3f2774fb0649f0dd35ffe980ad` | Aligned RNA sequences in FASTA; single-sequence input is accepted, although the method is designed to benefit from multiple sequences | Consensus structure and score on stdout; FASTA-style output is optional | Available on rerun with `-r/--ppfile`; not retained in the existing legacy `.db` outputs | Observed/standard output uses nested `()` and alignment-gap `-`; no extended-bracket pseudoknot output was identified | Initial comparative candidate, subject to a frozen alignment/single-sequence protocol |
| trRosettaRNA2 native SS ensemble | Verified runnable on CPU | Local snapshot has no Git metadata. Ensemble checkpoints are `model_1_finetune`, `model_2_finetune`, and `model_3_finetune` under `/root/autodl-tmp/models/trRosettaRNA2/params/models_ss` | A3M MSA; the standalone wrapper also accepts a single-sequence FASTA laid out as A3M | Compressed NPZ with key `ss` and a DBN file decoded at a configurable threshold | Yes. The verified NPZ is `float32`, shape `L x L`, with sigmoid-like pair scores | The current standalone decoder greedily selects pairs and writes every selected pair as `()`; it cannot losslessly serialize crossing pairs | Initial learned source-predictor candidate; treat NPZ scores as the primary raw output and freeze a decoder before evaluation |
| Deterministic NMR/V11-2 prediction pipeline | Code and historical outputs present; not smoke-tested here | Scripts under `/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1/scripts`, including `recompute_nmr_pred_consistent.py`; no single model checkpoint | NMR-derived evidence, sequence, lookup tables, and candidate-space inputs | `NMR_PRED` matrix/extended DBN and V11-2 candidate topologies | Candidate scores exist inside the deterministic candidate workflow, but no normalized pair-confidence contract is frozen | Extended bracket families and explicit pair tables can represent crossings | Evidence-derived baseline/candidate only; do not relabel as GT or include in the initial source-model pool without a research decision |

### Verified trRosettaRNA2 SS Checkpoints

| Checkpoint | Size | SHA-256 |
| --- | ---: | --- |
| `model_1_finetune.pth.tar` | 25,379,918 bytes | `23defcc04f02613c07cf9ca4653e9367845480e249a4c90e32a61cfa82bb6ec8` |
| `model_2_finetune.pth.tar` | 25,379,918 bytes | `79ee6324fcf377950d63643a538b1ecd8f5b768f27f40ac63f83060ad66c25a2` |
| `model_3_finetune.pth.tar` | 25,379,918 bytes | `6ee709e30ff32f7b90791628b8bde7aa8bc877c2e7878b9f3bcb0e66b4af4eb3` |

The standalone entry point is:

```text
/root/autodl-tmp/models/trRosettaRNA2/scripts/tools/ss_predictor_standalone.py
```

The environment used by the successful smoke test was:

```text
/root/autodl-tmp/models/trRosettaRNA2/env_trRNA2/bin/python
```

## Installed Tools That Are Not Independent Source Predictors

| Tool | Local state | Reason not currently counted as a source predictor |
| --- | --- | --- |
| RNAplfold | Executable at `/usr/bin/RNAplfold` from the installed ViennaRNA 2.4.17 suite | Produces local pairing probabilities rather than one frozen full secondary structure; adding a decoder would create a new composite method that must be specified separately |
| Existing dot-bracket/matrix helper scripts | Multiple ad hoc helpers exist under trRosettaRNA2 and the external77 benchmark scripts | They differ in supported bracket families, validation, and decoding behavior; none is the shared parser/evaluator required by this project |

## 3D Predictors and Scorers in the Benchmark Workspace

These assets may support the Candidate 2D-to-3D experiment later. They are not eligible as Phase 0 2D source predictors merely because their workflows consume or internally predict secondary structure.

| Model / tool | Local reproducibility state | Version / checkpoint evidence | Input | Output | Pair-score availability relevant to this project | Current role |
| --- | --- | --- | --- | --- | --- | --- |
| RNAbpFlow | Installed, not smoke-tested in this audit; historical predictions and a local environment are present | Local snapshot has no Git metadata; checkpoints `RNA3DB.ckpt`, `CASP15.ckpt`, and `CASP16.ckpt` are present | FASTA plus one or three base-pair maps | Sampled PDB/mmCIF structures | Base-pair maps are inputs, not predictor confidence | Candidate downstream 3D pipeline |
| trRosettaRNA2 3D | Installed with historical runs; the native SS submodule was smoke-tested separately | Local snapshot has no Git metadata; 3D checkpoint `params/models/model_1.pth.tar` is present | A3M plus optional custom SS in dot-bracket, CT, BPSEQ, or probability format | PDB plus internal 2D NPZ and per-residue confidence | Internal arrays exist, but they are not normalized Phase 0 pair scores without an explicit extractor | Candidate downstream 3D pipeline; native SS submodule is inventoried separately above |
| DRfold | Installed tree and checkpoints are present; no inference smoke test in this audit | Upstream Git HEAD `9586990c79e4ca488e5f967fcc8bd5b06cd60273`, but the working tree contains local modifications and added reproduction assets, so HEAD alone does not identify the runnable state | FASTA; workflow generates/uses ViennaRNA and PETfold secondary-structure features | PDB and intermediate arrays | PETfold/Vienna intermediates exist for subsets; no shared confidence contract | Candidate downstream 3D pipeline and source of historical 2D intermediates |
| FARFAR2 / Rosetta | Installed, not smoke-tested in this audit | Local `rna_denovo.cxx11threadserialization.linuxclangrelease` executable and Rosetta database are present; exact Rosetta release was not located in a versioned manifest | FASTA plus secondary-structure/topology inputs and Rosetta options | PDB ensembles | No native pair-confidence output identified | Candidate downstream comparator only |
| RhoFold+ | Output-only in the current model directory | PDB outputs and run wrappers exist, but a complete local source tree/checkpoint was not located under `/root/autodl-tmp/models/Rhofold+` | Historical workflow input not frozen here | PDB | Not located | Historical 3D comparator; not currently reproducible from this directory alone |
| AlphaFold 3 | Output-only / externally executed | Consolidated CIF outputs exist; no local model runner or checkpoint is available | External service/workflow input | mmCIF | Not applicable | Historical 3D comparator only |
| lociPARSE | Local code is clean at Git commit `8c7acbe4e7c486122a4c261b1ea68fff7247b796`; not smoke-tested in this audit | Git-tracked source at `/root/autodl-tmp/lociPARSE` | RNA 3D structures/decoys | Structure-quality score | Not applicable | 3D scorer, not a structure predictor |

## Smoke-Test Record

The following checks completed successfully on 2026-08-25:

1. `RNAfold --noPS` folded a 10-nt synthetic RNA from stdin and returned a dot-bracket/MFE record.
2. PETfold v2.0 processed its packaged example alignment with `PETFOLDBIN` pointing to the local grammar directory and returned a consensus PETfold structure and score.
3. The trRosettaRNA2 standalone SS ensemble loaded all three checkpoints on CPU and processed `1XWU_16_hp_nmr_A.a3m`, writing an NPZ probability matrix and DBN under `/tmp`.

These checks establish local executability only. They are not benchmark results and do not validate model accuracy, historical output identity, or final inference settings.

## Inventory Conclusions and Remaining Decisions

- Three locally runnable 2D candidates are available for Phase 0: RNAfold, PETfold, and trRosettaRNA2 native SS.
- Only the existing trRosettaRNA2 native SS records already retain direct `L x L` pair scores. RNAfold and PETfold can emit probability information when rerun, but their legacy `.db` files contain structure only.
- PETfold requires an explicit alignment protocol. Treating a single sequence as equivalent to the intended comparative setting would be an unconfirmed methodological choice.
- The trRosettaRNA2 DBN decoder is not a canonical decoder for crossing structures. The raw NPZ plus a versioned decoding rule must be used for reproducible evaluation.
- The final initial 3-5 source-predictor set remains unfrozen. Additional predictors should be added only after their local version, output representation, and leakage/compatibility properties are inventoried to the same standard.
