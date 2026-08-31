# Global Evidence-Constrained Refolding R2 — Partial Execution Blocker Report

Status: **`R2_EXECUTION_PARTIAL_BLOCKED_MINIMUM_LOOP_CONSTRAINT`**
Date: 2026-08-31

## Scope

This document records the fixed-command R2 execution and its fail-closed
blocker. It is not a completed B0/B1/B2 results report. No structural metric,
edit-decomposition, scope, evidence-efficiency, or Gate A analysis was run
after the blocker was observed.

## Empirical execution result

The runner verified the frozen clean-manifest, eligibility, and matched-B1
hashes and used `/usr/bin/RNAfold` 2.4.17 with the frozen command and defaults.
Source identity and source-predicted structures were not folding inputs.

| Execution outcome | Count |
| --- | ---: |
| Frozen protocol realization rows | 7,260 |
| Frozen `R2_ELIGIBLE` rows sent to RNAfold | 7,173 |
| PASS: parsed, valid, constraint-compliant | 7,153 |
| `R2_INELIGIBLE_CROSSING_EVIDENCE`: skipped as frozen | 87 |
| `CONSTRAINT_SATISFACTION_FAIL` | 20 |

All 20 failures are positive-pair manifests across four RNAs. Each contains
one forced exact pair with `j-i=3`, so only two nucleotides are enclosed.
ViennaRNA emitted the warning that the pairing partners violate its minimum
loop size setting of 3 nt and omitted the constraint. The four zero-based
offending pairs are:

| RNA | Forced pair | Affected manifests |
| --- | --- | ---: |
| `2ES5_23_hp_nmr_A` | `(9,12)` | 6 |
| `2MTJ_47_3wj_nmr_A` | `(12,15)` | 3 |
| `2N3Q_62_3wj_nmr_A` | `(17,20)` | 3 |
| `8JHP_27_hpbulge_nmr_A` | `(11,14)` | 8 |

Failure counts by density are 2 at 5%, 4 at 10%, 4 at 20%, and 10 at 50%.
There were no nonzero exits, timeouts, parse failures, illegal output pairs,
or unexpected crossing outputs.

## Integrity findings

- All 1,210 zero-density rows passed.
- For every one of 121 RNAs, the five pair-channel seeds and five unpaired-
  channel seeds shared one identical folding input and one identical B2 output.
- Historical RNAfold and R2 0% exact pair sets were identical for 121/121 RNAs.
  This is a provenance/context audit, not a requirement or R2 performance result.
- Constraint satisfaction was 7,153/7,173 among frozen eligible rows, not 100%.
- The 87 crossing manifests were not executed, rewritten, resampled, deleted,
  imputed, or counted as technical folding failures.
- No learned model, historical E2, R3/R4, pseudoknot solver, external77, or
  2D-to-3D path was used.

## Protocol consequence

The current eligibility policy excludes crossing evidence only. The 20
minimum-loop failures therefore belong to the frozen eligible universe and
cannot be silently removed. The same fixed command cannot resolve them because
the solver deterministically omits the constraints.

Potential resolutions would change at least one frozen scientific component:
the comparison universe, delivered-evidence semantics, or ViennaRNA model
settings. No resolution is selected here. Per the stop rule, the formal
summarizer was not implemented or run, and no partial-case performance result
is reported.

## Interpretation

The observation is a solver/model representability blocker, not evidence that
B2 is scientifically strong or weak. It says only that noncrossing dot-bracket
syntax is insufficient to guarantee executability under the frozen ViennaRNA
model: minimum-loop feasibility must also be prospectively resolved.

## Limitations

- The partial PASS structures do not form the frozen complete comparison
  universe and must not be used for B0/B1/B2 performance claims.
- No Macro/Micro F1, TP preservation, FP removal, modification precision,
  DIRECT/LOCAL/NON_EVIDENCED behavior, density response, or evidence efficiency
  has been computed.
- Gate A remains untested, and R3/R4 remain unauthorized.

## Reproducible artifacts

- `results/global_constrained_refolding_r2/integrity/execution_integrity_summary.json`
- `results/global_constrained_refolding_r2/integrity/execution_blocker_audit.json`
- `results/global_constrained_refolding_r2/integrity/failed_skipped_realizations.csv`
- `results/global_constrained_refolding_r2/integrity/zero_density_identity_audit.csv`
- `results/global_constrained_refolding_r2/integrity/historical_rnafold_vs_r2_zero_audit.csv`
- `results/global_constrained_refolding_r2/parsed/b2_structures.csv`
- local raw provenance: `results/global_constrained_refolding_r2/raw/execution_records.jsonl`

The raw execution file is retained locally and ignored by Git because it
contains the complete repeated stdout/stderr payload. Parsed structures,
failure rows, hashes, and integrity summaries are the versioned compact view.
