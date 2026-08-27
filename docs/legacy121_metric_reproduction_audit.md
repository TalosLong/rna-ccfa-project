# Legacy121 Historical Metric Reproduction / Mismatch Audit

Status: **Phase 0 audit passed**

Audited: 2026-08-27

## Outcome

A systematic read-only search found two retained historical secondary-structure
metric source bundles relevant enough to audit. Neither is genuinely compatible
with the frozen Legacy121-v1 source-predictor baseline:

| Historical source bundle | Classification | Reason |
| --- | --- | --- |
| trRosettaRNA2 native threshold SS quality | `PARTIALLY_COMPATIBLE` | Same GT for 119 Legacy121 RNAs and exact pair membership scoring, but it excludes two RNAs longer than 150 nt and thresholds raw NPZ scores at `>0.5` instead of evaluating the stored historical DBN pairs. |
| NMR-derived topology F1 | `INCOMPATIBLE` | Its 121 successful single-chain IDs match Legacy121 v1, but the evaluated predictions are selected NMR-derived topologies, not RNAfold, PETfold, or trRosettaRNA2 native SS. |

No `COMPATIBLE` source was found. Consequently, there is no valid direct
historical-versus-shared numerical mismatch and no reproduction-failure claim.
The apparent numerical differences from the partial source are documented only
as compatibility evidence.

No historical Legacy121 secondary-structure Precision/Recall/F1 result or
evaluation script was found for RNAfold or PETfold.

## Frozen Shared-Evaluator Baseline

These values remain authoritative and were not changed by this audit:

| Predictor | Macro P | Macro R | Macro F1 | Micro P | Micro R | Micro F1 | TP | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RNAfold | 0.9069374162 | 0.9138670307 | 0.9058176119 | 0.8700531601 | 0.8788782816 | 0.8744434550 | 1473 | 220 | 203 |
| PETfold | 0.8952556024 | 0.9077787599 | 0.8968492212 | 0.8585680751 | 0.8729116945 | 0.8656804734 | 1463 | 241 | 213 |
| trRosettaRNA2 native SS | 0.7905636557 | 0.9120849106 | 0.8428713642 | 0.7717908082 | 0.8717183771 | 0.8187167274 | 1461 | 432 | 215 |

The shared evaluator uses the 121 frozen manifest RNAs, historical
`predicted_structure.pairs`, exact canonical 0-based pair equality, full-
precision per-sample values for macro aggregation, and summed counts for micro
aggregation. Pair scores are not used.

## Search Procedure

The search covered `/root/autodl-tmp` read-only, including the benchmark
workspace index, model projects, data/result roots, shared scripts, reports,
notebooks, logs, Markdown/HTML source reports, and presentation/PDF filenames.
Searches combined:

- `RNAfold`, `PETfold`, `trRosettaRNA2`, `native SS`, and `ss_native`;
- Legacy/RNA-Puzzles/NMR identifiers and the 121/123 sample counts;
- `precision`, `recall`, `F1`, `MCC`, pair overlap, and secondary-structure
  quality terms;
- known Legacy121 IDs and historical `data/ss/{gt,rnafold,petfold}` paths.

Dependency, environment, and package-cache trees were screened and then
excluded from content searches. Hard-linked or copied assets were not counted
as independent metric sources. The following relevant-but-noncomparable areas
were also checked:

- the external77 standard benchmark scripts/results, which evaluate a different
  dataset and predominantly 3D metrics;
- FARFAR2, DRfold, and RNAbpFlow evaluation assets, whose RNAfold/PETfold
  references are 3D workflow inputs or other datasets rather than Legacy121 2D
  accuracy tables;
- trRosettaRNA2 RMSD/TM-score tables such as
  `/root/autodl-tmp/models/trRosettaRNA2/results/ss_native_v11_eval.csv`, which
  do not report secondary-structure pair metrics;
- archived prediction outputs and report/PPT derivatives, which did not reveal
  another independent Legacy121 pair-metric source.

The reproducible audit implementation is
`scripts/audit_legacy121_historical_metrics.py`. It reads historical assets and
the frozen baseline, writes only new audit artifacts, checks source hashes, and
verifies that the normalized input SHA-256 remains
`e8ce10ce2670739be70b1f98c02604b8d19e783497ce05e4d11d3282aebe5c22`.

## Compatibility Criteria

`COMPATIBLE` requires the same sample IDs, GT and prediction artifacts,
representation, pair membership semantics, indexing, matching rule, empty-set
convention, metric formula, aggregation, and filtering/skipping policy.

`PARTIALLY_COMPATIBLE` shares enough components to explain a historical value,
but at least one material axis differs. `INCOMPATIBLE` evaluates a different
prediction target, predictor, or task. `UNKNOWN` is reserved for a reference
whose retained evidence is insufficient even to determine whether it evaluates
the same task.

## Source 1: trRosettaRNA2 Native Threshold SS Quality

### Retained assets

Primary table:

`/root/autodl-tmp/models/trRosettaRNA2/results/ss_quality_vs_3d.csv`

Supporting assets:

- `/root/autodl-tmp/models/trRosettaRNA2/scripts/tools/ss_quality_analysis.py`;
- `/root/autodl-tmp/models/trRosettaRNA2/reports/实验总结_20260516-0703.md`;
- `/root/autodl-tmp/models/trRosettaRNA2/scripts/plot_step_figures.py`.

Classification: **`PARTIALLY_COMPATIBLE`**.

### Compatibility audit

| Axis | Historical source | Frozen shared baseline | Finding |
| --- | --- | --- | --- |
| Sample universe | 119 Legacy IDs after `max_length=150` | All 121 manifest IDs | Different. Historical source excludes `2N1Q_155_4wj_nmr_A` and `9G7C_224_4wj_cryoEM_A`. |
| 121 vs 123 handling | Starts from sequence files, so GT-only `8Q4O`/`8TNS` never enter; then length-filters 121 to 119 | Explicit 121-row manifest; two GT-only files excluded | Partially aligned, but final universes differ. |
| GT source | `gt_ss_dir_full/<rna_id>.dbn` | Normalized provenance points to `data/ss/gt/*_matrix.db` | All 119 historical GT pair sets exactly match normalized GT pair sets. |
| Prediction source | Raw `*_ss_prob.npz`, array `ss`, thresholded at `>0.5` | Stored historical `*.dbn` structure pairs | Materially different. Pair-score thresholding is not the frozen baseline prediction. |
| Representation | Symmetric dense binary matrix after threshold/OR | Canonical matching pair list parsed from DBN | Only 60/119 pair sets are identical; only 62/119 pair counts are identical. |
| Pseudoknot handling | Upper-triangle pair membership; extended GT bracket families are parsed | Crossing canonical pairs retained | No explicit pseudoknot filtering in either, but the prediction representations differ. |
| Canonical/noncanonical filtering | No base chemistry filter | No base chemistry filter | Compatible on chemistry filtering. |
| Partner validity | Does not enforce one partner per nucleotide | Historical DBN is a matching validated by schema v1 | 57/119 thresholded predictions contain at least one nucleotide with multiple partners. |
| Indexing | Matrix upper triangle `i < j`, effectively 0-based unordered pairs | Canonical 0-based `[i,j]`, `i < j` | Compatible for individual matrix-cell pair identities. |
| Pair matching | Exact same matrix cell | Exact canonical pair equality | Compatible; no relaxed/slippage matching found. |
| Empty convention | Any zero denominator yields 0, including both structures empty | Both empty yields P=R=F1=1; other zero denominators yield 0 | Latently different. No GT or frozen DBN prediction is empty in Legacy121 v1. |
| P/R/F1 formula | Standard TP/FP/FN formulas; F1 is harmonic mean of P/R; values rounded to 4 decimals per sample | Same non-empty formulas using full precision | Formula agrees for non-empty samples; precision before macro differs. |
| Aggregation | Arithmetic mean of stored rounded per-sample values; no historical micro summary | Full-precision macro and count-first micro | Macro precision policy and available aggregates differ. |
| Skips/failures | No failed row among the 119 selected IDs | No failed row among 121 | Different only because of the explicit length filter. |
| RNA length/class filter | `length <= 150`; no class filter | None | Materially different. |

### Reproduction of the historical convention

The audit copied only the historical script's metric logic into the new audit
script and applied it read-only to the original NPZ/GT inputs. This was done to
identify the convention, not to redefine the baseline. All 119 stored rounded
Precision, Recall, and F1 rows were reproduced exactly. Historical MCC values
were inventoried from the retained table but were not recomputed.

The historical table's arithmetic means are:

| Metric | Historical threshold table, 119 | Shared evaluator on same 119 IDs | Frozen shared baseline, 121 |
| --- | ---: | ---: | ---: |
| Macro Precision | 0.8064344538 | 0.7902522733 | 0.7905636557 |
| Macro Recall | 0.9893831933 | 0.9169177948 | 0.9120849106 |
| Macro F1 | 0.8836621849 | 0.8455526757 | 0.8428713642 |
| Macro MCC | 0.8882033613 | not computed | not computed |

No absolute differences are reported because neither the prediction pair set
nor the sample universe is compatible. The higher historical recall is
consistent with thresholding many matrix cells: the audit reconstructed
TP/FP/FN = 1541/382/22 over 119 RNAs, while 57 predictions violate the frozen
one-partner representation. These are not the historical DBN predictions.

For completeness, the audit-derived count-first values for that historical
threshold convention are P=0.8013520541, R=0.9859245042, and F1=0.8841078600.
The historical source did not report those as micro metrics, so they are not a
direct comparison target.

The old script reports MCC using all unordered upper-triangle residue pairs as
the negative universe. It is inventoried but not adopted. Shared MCC remains
deferred under `docs/mcc_definition_audit.md`.

## Source 2: NMR-Derived Topology F1

### Retained assets

Primary table:

`/root/autodl-tmp/models/trRosettaRNA2/data/nmr_f1_top1_matrices/nmr_f1_top1_summary.csv`

Supporting assets:

- `/root/autodl-tmp/models/trRosettaRNA2/data/nmr_f1_top1_matrices/run.log`;
- `/root/autodl-tmp/models/trRosettaRNA2/scripts/evaluate/eval_nmr_f1.py`;
- `/root/autodl-tmp/models/trRosettaRNA2/results/nmr_f1_stratified.csv`.

Classification: **`INCOMPATIBLE`**.

### Compatibility audit

| Axis | Historical source | Frozen shared baseline | Finding |
| --- | --- | --- | --- |
| Sample universe | 314 total rows across dataset classes; 123 `single_chain` rows, 121 successful | 121 Legacy121 manifest IDs | The 121 successful single-chain IDs match exactly, but the overall historical task is broader. |
| 121 vs 123 handling | Includes `8Q4O` and `8TNS` as failed rows with `No Active Target NMR`; 121 other rows succeed | Explicitly excludes those two GT-only records | Effective IDs align, but failure/exclusion semantics differ. |
| GT source | Original `NMR_secondary` matrices/paths; retained summary has pair counts | Frozen Legacy GT | All 121 retained GT pair counts match, but original matrices are no longer present for pairwise verification. |
| Prediction source | Best selected NMR-derived topology/candidate | Three historical source predictors | Incompatible by prediction identity. |
| Representation | Retained extended dot-bracket plus pair-count summaries; original matrices referenced under a missing root | Canonical pairs from historical predictor outputs | Not a source-predictor representation. |
| Pseudoknot handling | Extended brackets appear in retained selected structures | Crossing pairs retained | Detailed generator behavior is unavailable. |
| Canonical/noncanonical filtering | Unknown from retained generator evidence | No chemistry filtering | Unresolved, but not outcome-determinative because prediction identity already differs. |
| Indexing/matching | Not fully recoverable; generator script is absent | Exact canonical 0-based pair equality | Unknown historical implementation. |
| Empty convention | Not documented | Frozen shared convention | Unknown. |
| P/R/F1 formula | Stored P/R/F1 are internally consistent with harmonic F1; all 121 successful single-chain precision values are 1 | Shared exact-pair formulas | Formula appearance alone does not establish task compatibility. |
| Aggregation | Per-record source table; later consumer aggregates 301 mixed-dataset successes | Separate 121-sample per-model macro/micro summaries | Incompatible. |
| Skips/filters | Two failed GT-only single-chain records; additional dataset classes included | No failed records | Different provenance and selection. |

The audit-derived arithmetic means over the 121 successful single-chain rows
are Precision=1.0000000000, Recall=0.9355494628, and F1=0.9626252810. They are
shown in the comparison CSV only to prevent accidental reuse. They are not
RNAfold, PETfold, or trRosettaRNA2 native-SS results and must not be compared to
the frozen predictor baseline.

## Compatible Comparisons and Mismatches

- Compatible sources: **0**.
- Direct compatible numerical comparisons: **0**.
- Compatible mismatches: **0**.

The historical threshold-table values and NMR-derived values above are not
reproduction failures. Their inputs and/or evaluated predictions differ from
the frozen baseline contract.

## Unresolved Items

1. No retained historical Legacy121 2D metric source was found for RNAfold or
   PETfold.
2. `ss_quality_analysis.py` was modified after the stored CSV and currently
   names `benchmark_results/` as its output directory, while the observed table
   resides under `results/`. Its retained logic still reproduces all 119 stored
   rounded metric rows.
3. The decoder/settings that produced the historical trRosettaRNA2 DBN remain
   unknown. The threshold source is not that decoder and provides no valid
   one-partner conflict resolution.
4. The historical report says 119 F1-stratified samples but its printed bins sum
   to 120: it lists 14 samples in `0.7-0.8`, whereas the retained CSV contains
   13 in that bin.
5. The NMR-derived topology generator and its referenced
   `/root/autodl-tmp/NMR_secondary` output root are absent. Exact candidate
   selection, indexing, and matching implementation therefore remain
   unrecoverable from the retained summary.

These uncertainties do not block Phase 0 because no genuinely compatible
historical source exists and no unsupported direct mismatch is asserted.

## Decision

The historical search and compatibility audit are sufficiently complete.
Phase 0 is complete. The frozen shared evaluator and Legacy121-v1 baseline are
unchanged. The next stage is Phase 1 pair-level error analysis limited initially
to `missing_pair`, `false_positive_pair`, and `wrong_partner`.

This audit did not start Phase 1, run predictor inference, modify normalized or
raw assets, train a model, or implement MCC.
