# Model Inventory

Last audited: 2026-08-25

## Scope and Status Definitions

This inventory covers RNA structure predictors that have a local executable, source/runner script, checkpoint, or benchmark output referenced by the current benchmark workspace. It distinguishes independent 2D predictors from 3D predictors that consume secondary structure.

- **WORKING**: local evidence establishes a successful smoke test or end-to-end run for the inventoried runner and assets.
- **UNTESTED**: a runner and some or all required assets exist, but the current end-to-end path was not verified in this inventory audit.
- **BROKEN**: the local assets are insufficient for a local rerun, even if historical outputs exist.
- **UNKNOWN**: the requested fact is not established by local code, documentation, manifests, or files.

No model was installed and no benchmark-scale inference was run during this audit. The smoke-test and end-to-end evidence cited below already existed locally.

## Predictor Summary

| Model name | Repository / path | Version or checkpoint | Secondary-structure role | Pair probability / logits / confidence | Status |
| --- | --- | --- | --- | --- | --- |
| ViennaRNA RNAfold | `/usr/bin/RNAfold` | RNAfold 2.4.17; default packaged energy parameters unless a later protocol freezes alternatives | Predicts 2D minimum-free-energy structure | **YES** — `-p` writes a dot plot containing `sqrt(p)` for base pairs; square the exported value to recover `p` | **WORKING** |
| PETfold | `/root/autodl-tmp/models/DRfold_repo/third_party/PETfold/bin/PETfold` | PETfold v2.0; binary SHA-256 `99deeb0066a246b8f6ac79e13f2c60f62dd63e3f2774fb0649f0dd35ffe980ad` | Predicts consensus 2D structure from an alignment | **YES, semantics need freezing** — `-r/--ppfile` writes PET reliabilities; local documentation does not establish them as calibrated pair probabilities | **WORKING** |
| trRosettaRNA2 native SS ensemble | `/root/autodl-tmp/models/trRosettaRNA2`; entry point `scripts/tools/ss_predictor_standalone.py` | Three `model_{1,2,3}_finetune.pth.tar` checkpoints under `params/models_ss`; local tree has no Git metadata | Predicts 2D structure; also supplies native SS to trRosettaRNA2 3D | **YES** — compressed NPZ key `ss`, `float32`, shape `L x L`, with sigmoid-like pair scores | **WORKING** |
| Deterministic NMR/V11-2 pipeline | `/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1/scripts` | No learned checkpoint; corrected exact-v3 package exists, but the standalone recomputation script and package README expose different default/tolerance expectations | Predicts candidate 2D topologies from NMR-derived evidence; does not consume a source predictor's 2D output | **NO per-pair confidence contract** — candidate-level maximum reconstruction error is stored | **UNTESTED** |
| RNAbpFlow | `/root/autodl-tmp/RNAbpFlow`; related source snapshot `/root/autodl-tmp/RNAbpFlow_src` | `RNA3DB.ckpt`, `CASP15.ckpt`, `CASP16.ckpt`; runnable tree has no Git metadata; related source snapshot is commit `0b28b79f63ca0ab850b070c4847668bebf8d8f70` | Consumes one or three 2D base-pair maps and predicts 3D | **NO** — base-pair maps are inputs; no output pair confidence is exposed by the local inference path | **UNTESTED** |
| trRosettaRNA2 3D | `/root/autodl-tmp/models/trRosettaRNA2`; entry point `trRNA2.predict` | 3D checkpoint `params/models/model_1.pth.tar`; SHA-256 `09e039f3e1383366438f159d27c663a253bd110412cece7da6232d6b31b01d3b` | Predicts native SS when custom SS is absent, or consumes custom dot-bracket/CT/BPSEQ/probability input; predicts 3D | **PARTIAL** — native SS scores are obtainable through the SS ensemble; 3D output also has per-residue pLDDT, which is not pair confidence | **UNTESTED** |
| DRfold | `/root/autodl-tmp/models/DRfold_repo`; historical outputs `/root/autodl-tmp/models/DRfold` | Upstream Git HEAD `9586990c79e4ca488e5f967fcc8bd5b06cd60273` plus documented local compatibility changes; 3 geometry and 6 end-to-end weights | Consumes RNAfold and PETfold secondary-structure features; predicts 3D | **NO normalized pair confidence** — `seq_ss.npy` and model geometry arrays are intermediates, not a frozen pair-score contract | **WORKING** |
| FARFAR2 / Rosetta | `/root/autodl-tmp/models/FARFAR2` | Rosetta `2025.03+HEAD.1f5080a079`, Git commit `1f5080a079a5261122c0e532c46f61a4f7e20df8` | Consumes a secondary-structure/topology file and predicts 3D ensembles | **NO** native pair probability/logit output located | **UNTESTED** |
| RhoFold+ remote wrapper | `/root/autodl-tmp/models/Rhofold+` | Model version/checkpoint **UNKNOWN**; the local directory contains benchmark-specific API wrappers and downloaded PDBs, not the model source | Local wrapper submits sequence-only FASTA to a remote 3D service; any internal SS role is **UNKNOWN** | **NO** pair-score output exposed by the wrapper | **UNTESTED** |
| AlphaFold 3 | Historical outputs indexed through `/root/autodl-tmp/RNA_benchmark_predictions` and `/root/autodl-tmp/data/TS85_AF3_output` | Version/checkpoint **UNKNOWN**; no local runner or weights found | 3D prediction; SS prediction/consumption is **UNKNOWN** from local assets | **UNKNOWN** | **BROKEN** for local rerun |

Only RNAfold, PETfold, and the trRosettaRNA2 native SS ensemble are currently evidenced as runnable independent 2D source-predictor candidates. The NMR/V11-2 pipeline is evidence-derived and must not be relabeled as ground truth or silently added to the initial source-model pool.

## Inference Requirements and Commands

Commands below are the current local entry points or command templates found in the corresponding help text, README, or runner. Placeholders such as `input.fasta` and `output_dir` are intentional; no new fixed benchmark protocol is implied.

### ViennaRNA RNAfold

- **Input requirements:** RNA sequence as plain text or FASTA; multiple FASTA records are accepted.
- **Output format:** MFE dot-bracket and free energy on stdout. With `-p`, PostScript secondary-structure and dot-plot files are also written.
- **Current inference command:** `RNAfold --noPS input.fasta`; probability-producing form: `RNAfold -p input.fasta`.
- **Environment requirements:** system executable `/usr/bin/RNAfold`; no project-specific Python environment.
- **Known issues:** standard MFE output is nested `()` and does not predict pseudoknots. `-p` creates files and can overwrite same-named plot files. Existing legacy `.db` files do not retain probabilities.

### PETfold

- **Input requirements:** aligned RNA sequences in FASTA. A one-sequence alignment is accepted by the executable, but equivalence to the intended comparative setting is not established.
- **Output format:** consensus dot-bracket and PETfold score on stdout; optional FASTA-style output and reliability file.
- **Current inference command:** `PETFOLDBIN=/root/autodl-tmp/models/DRfold_repo/third_party/PETfold/bin /root/autodl-tmp/models/DRfold_repo/third_party/PETfold/bin/PETfold -f input.fasta -r pair_reliability.txt`.
- **Environment requirements:** native PETfold binary plus `article.grm` and `scfg.rate` in `PETFOLDBIN`; the local build uses the DRfold-packaged ViennaRNA 2.0.7 compatibility library.
- **Known issues:** an alignment protocol must be frozen before comparison. Output uses nested parentheses and alignment-gap `-`; no extended-bracket pseudoknot output was found. Existing legacy `.db` files omit reliability values.

### trRosettaRNA2 native SS ensemble

- **Input requirements:** A3M MSA. The standalone wrapper also accepts a single-record FASTA laid out as A3M.
- **Output format:** `<name>_ss_prob.npz` with key `ss`, plus a two-line DBN file and optional batch summary JSON.
- **Current inference command:** `/root/autodl-tmp/models/trRosettaRNA2/env_trRNA2/bin/python /root/autodl-tmp/models/trRosettaRNA2/scripts/tools/ss_predictor_standalone.py -i input.a3m -o output_dir --gpu -1`.
- **Environment requirements:** `/root/autodl-tmp/models/trRosettaRNA2/env_trRNA2` (Python 3.10.8, PyTorch 2.5.1+cu118); CPU execution was previously smoke-tested.
- **Known issues:** the wrapper's greedy decoder gives each residue at most one partner but writes every selected pair as `()`, so crossing pairs cannot be serialized losslessly. The probability NPZ and a frozen decoder must be treated as primary for reproducible evaluation.

### Deterministic NMR/V11-2 pipeline

- **Input requirements:** asset directories containing metadata, sequence and matrix files, plus a CSV lookup table and NMR-derived evidence. The inspected `recompute_nmr_pred_consistent.py` synthesizes its theoretical NMR vector from `gt_ss.csv` for controlled reconstruction/audit.
- **Output format:** candidate matrices in `nmr_pred_candidates.npz`, rank-1 structure matrix CSV, theoretical NMR vector CSV, and summary/audit records.
- **Current inference command:** `python3 scripts/recompute_nmr_pred_consistent.py --assets-root <assets_root> --lookup <lookup.csv> --out <output_dir> --tolerance <frozen_value> --max-error <frozen_value>` from the external77 package root.
- **Environment requirements:** Python 3 and NumPy; no learned checkpoint.
- **Known issues:** this inspected script is not a blind sequence-only predictor because GT is used to synthesize controlled evidence. Its defaults (`0.15`, `0.30`) differ from the external77 v3 README's exact noiseless `1e-5` protocol, so parameters and the intended builder must be frozen before rerun.

### RNAbpFlow

- **Input requirements:** per-target FASTA, one or three `L x L` NumPy base-pair maps, and `Inputs/list.txt`; inference settings and checkpoint path come from `configs/inference.yaml`.
- **Output format:** sampled PDB, mmCIF, or both under the configured prediction directory.
- **Current inference command:** `cd /root/autodl-tmp/RNAbpFlow` followed by `/root/autodl-tmp/RNAbpFlow/venv/bin/python inference.py`.
- **Environment requirements:** local venv with Python 3.10.8 and PyTorch 2.1.2+cu118; README/config expect GPU inference and Hydra configuration.
- **Known issues:** the runnable tree lacks Git metadata, and correspondence to the separate Git snapshot is not proven. Input maps must exactly match sequence length. Checkpoint choice (`RNA3DB`, `CASP15`, or `CASP16`) is dataset-dependent and not frozen for this project.

### trRosettaRNA2 3D

- **Input requirements:** A3M MSA; optional custom SS in dot-bracket, CT, BPSEQ, or text probability-matrix form.
- **Output format:** unrelaxed/optionally relaxed PDB, `model_1_2D.npz` intermediate geometry arrays, and `plddt.csv`.
- **Current inference command:** from `/root/autodl-tmp/models/trRosettaRNA2`, run `/root/autodl-tmp/models/trRosettaRNA2/env_trRNA2/bin/python -m trRNA2.predict -i input.a3m -o output_dir -relax_steps 0`.
- **Environment requirements:** the local `env_trRNA2` environment; GPU is the normal inference path, with optional PyRosetta refinement requiring additional licensed/local dependencies.
- **Known issues:** local tree has no Git commit. Custom SS bypasses native SS, so the condition must be recorded. Internal 2D arrays and per-residue pLDDT must not be mislabeled as normalized pair confidence.

### DRfold

- **Input requirements:** one-record RNA FASTA. The wrapper generates RNAfold and PETfold SS features before geometry/e2e prediction and refinement.
- **Output format:** final `DPR.pdb`, six `DPR_0.pdb`-`DPR_5.pdb` candidates, geometry/e2e NumPy intermediates, and logs.
- **Current inference command:** from `/root/autodl-tmp/models/DRfold_repo`, run `bash DRfold.sh input.fasta output_dir`.
- **Environment requirements:** `envs/drfold` (Python 3.9.23, NumPy 1.23.5, SciPy 1.10.1, PyTorch 1.13.1+cu117, OpenMM 8.1.1), RNAfold 2.4.17, local PETfold 2.0, and Arena.
- **Known issues:** the working tree intentionally differs from upstream HEAD through compatibility changes and installed assets, so the commit hash alone is insufficient; `REPRODUCTION.md`, `environment.yml`, and `checksums.sha256` are required provenance. A documented 77-nt end-to-end run took about 79 minutes, so this is not a lightweight 2D source predictor.

### FARFAR2 / Rosetta

- **Input requirements:** FASTA plus secondary-structure file and Rosetta sampling options.
- **Output format:** Rosetta silent file and extracted PDB ensemble.
- **Current inference command:** source `/root/autodl-tmp/models/FARFAR2/env.sh`, then run `rna_denovo -fasta input.fasta -secstruct_file input.db -nstruct 5 -minimize_rna false -out:file:silent run.out` and extract models with `rna_extract`.
- **Environment requirements:** local Rosetta executables, `ROSETTA3_DB`, `ROSETTA_BIN`, and database configured by `env.sh`.
- **Known issues:** stochastic sampling requires seeds and `nstruct` to be frozen. No pair confidence is produced. Existing scripts include long benchmark-specific timeouts and are not a fast Phase 0 2D path.

### RhoFold+ remote wrapper

- **Input requirements:** one-record FASTAs from hard-coded TS85 holdout or CASP directories; working network access to the remote API.
- **Output format:** downloaded PDB files plus JSON job-status records.
- **Current inference command:** `python3 /root/autodl-tmp/models/Rhofold+/run_holdout_5seed.py` or `python3 /root/autodl-tmp/models/Rhofold+/run_casp_5seed.py`.
- **Environment requirements:** Python standard library and external service availability; no local model environment or checkpoint is present.
- **Known issues:** commands are benchmark-wide remote submission loops, not generic single-target inference. They have side effects, depend on an external service, and cannot establish the underlying model version. The wrapper notes deterministic behavior despite submitting five times.

### AlphaFold 3

- **Input requirements:** **UNKNOWN** from local runnable assets.
- **Output format:** historical mmCIF predictions are present and indexed in the consolidated manifest.
- **Current inference command:** **UNKNOWN** — no local runner was found.
- **Environment requirements:** **UNKNOWN** — no local checkpoint/environment was found.
- **Known issues:** only historical outputs and consolidation/evaluation scripts exist. Local reproduction is currently impossible, so AlphaFold 3 is not a runnable source predictor for this project.

## Checkpoint Registry

| Model | Checkpoint | Size / checksum evidence |
| --- | --- | --- |
| trRosettaRNA2 SS | `model_1_finetune.pth.tar` | 25,379,918 bytes; SHA-256 `23defcc04f02613c07cf9ca4653e9367845480e249a4c90e32a61cfa82bb6ec8` |
| trRosettaRNA2 SS | `model_2_finetune.pth.tar` | 25,379,918 bytes; SHA-256 `79ee6324fcf377950d63643a538b1ecd8f5b768f27f40ac63f83060ad66c25a2` |
| trRosettaRNA2 SS | `model_3_finetune.pth.tar` | 25,379,918 bytes; SHA-256 `6ee709e30ff32f7b90791628b8bde7aa8bc877c2e7878b9f3bcb0e66b4af4eb3` |
| RNAbpFlow | `RNA3DB.ckpt` | 203,034,292 bytes; SHA-256 `bb598a736193734541f63c59dae75d45db8c04f01a8414a758677367c4b1e213` |
| RNAbpFlow | `CASP15.ckpt` | 203,025,869 bytes; SHA-256 `0030f14aa854d7eff8ab762fe5581877833cbf430ea84c25b064b24173d99bc6` |
| RNAbpFlow | `CASP16.ckpt` | 203,045,389 bytes; SHA-256 `8ed7deadcea6a7fd025454ab8a4ef542d6d9c4a4365ef7319fc17b5b1d599a66` |
| DRfold | 3 geometry + 6 end-to-end weights | Paths and SHA-256 values are frozen in `/root/autodl-tmp/models/DRfold_repo/checksums.sha256` |

## Existing Verification Evidence

The following local evidence predates this update and is not reported as a benchmark result:

1. RNAfold 2.4.17 previously completed a 10-nt synthetic smoke test.
2. PETfold v2.0 previously processed its packaged example alignment.
3. The trRosettaRNA2 standalone SS ensemble previously loaded all three checkpoints on CPU and produced an NPZ/DBN pair under `/tmp`.
4. DRfold's local `REPRODUCTION.md` records a successful 77-nt end-to-end run with final `test/DRfold_out_repro/DPR.pdb` and verified intermediate/model assets.

Historical output volume alone was not used to promote RNAbpFlow, trRosettaRNA2 3D, FARFAR2, or RhoFold+ to `WORKING`, because their current end-to-end runner/configuration was not revalidated during this inventory.

## Excluded Tools

- `RNAplfold` exists at `/usr/bin/RNAplfold` and produces local pairing probabilities, but it does not emit one frozen full secondary structure. Adding a decoder would define a new composite predictor.
- `lociPARSE` exists at `/root/autodl-tmp/lociPARSE` (Git commit `8c7acbe4e7c486122a4c261b1ea68fff7247b796`) but is a 3D structure-quality scorer, not a structure predictor.
- Parser, conversion, evaluation, and consolidation helpers are not models and are inventoried elsewhere.

## Phase 0 Conclusions

- The currently evidenced independent 2D candidates remain RNAfold, PETfold, and trRosettaRNA2 native SS.
- trRosettaRNA2 directly retains an `L x L` pair-score matrix. RNAfold and PETfold can emit probability/reliability information on rerun, but the historical legacy DB files do not preserve it.
- PETfold's alignment protocol and the trRosettaRNA2 probability-to-structure decoder must be frozen before baseline reproduction.
- The initial 3-5 source-predictor set remains a research choice; this inventory does not promote downstream 3D models into that set.
