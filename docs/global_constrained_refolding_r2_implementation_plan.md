# Global Constrained Refolding R2 Implementation Plan

## Status and execution boundary

This is an implementation plan only. The environment audit and toy interface
checks passed. Prospective amendment v1.0.1 now classifies the 87 crossing
positive-pair manifests as solver-capability-ineligible and authorizes the
runner on the matched `R2_ELIGIBLE` universe only. No Legacy121 benchmark,
learned training, noisy evidence, real modality, or external77 access is part
of this plan.

## Proposed module and adapter

Create `src/rna_ccfa/global_refolding_r2.py` with small, testable components:

1. `project_to_vienna(position)` performs the single `0-based + 1` conversion.
2. `build_constraint_string(length, pair_items, unpaired_items)` validates
   bounds, one-partner consistency, forced-pair/forced-unpaired conflicts,
   and noncrossing support before emitting `()`, `x`, and `.` symbols.
3. `ViennaRNAConfig` freezes `/usr/bin/RNAfold`, version 2.4.17, MFE,
   temperature 37 C, dangles=2, default parameters, linear mode, noLP off,
   noGU off, noClosingGU off, gquad off, and `--noPS -C --enforceConstraint`.
4. `run_constrained_rnafold(sequence, constraint, config)` uses a non-shell
   subprocess, captures command/stdout/stderr/return code/runtime, and applies
   a timeout. It must never write over historical predictions.
5. `parse_and_validate_output` reuses `rna_ccfa.structure.parse_structure`
   and `validate_pairs`, checks sequence length and one-partner legality, and
   verifies every forced pair and `x` position in the returned structure.

The adapter must return a typed result with explicit statuses such as
`PASS`, `UNSATISFIABLE_CONSTRAINT`, `UNSUPPORTED_CROSSING_CONSTRAINT`,
`RNAFOLD_NONZERO_EXIT`, `OUTPUT_PARSE_ERROR`, and
`CONSTRAINT_SATISFACTION_FAIL`. Unsupported items are never silently removed.

## Manifest loading and evidence mapping

Reuse `rna_ccfa.simulated_evidence.build_clean_evidence_manifest` and the
existing E0 manifest/index hashes. The future runner loads only the frozen
Legacy121 manifest universe and verifies `simulated_evidence_v1`, noise level
zero, channels, densities, seeds, sequence length, and manifest hash.

For `POSITIVE_PAIR_EVIDENCE`, map each delivered `(i,j)` to matching
parentheses. For `UNPAIRED_NUCLEOTIDE_EVIDENCE`, map each delivered `k` to
`x`. Keep channels separate. A B2 structure is generated once per unique
RNA/evidence realization and reused for the RNAfold, PETfold, and
trRosettaRNA2 source comparison rows; source prediction records are never
inputs to folding.

## Output schema

Future per-realization JSONL/CSV rows under
`results/global_constrained_refolding_r2/` should include:

- `rna_id`, channel, density, evidence seed, delivered item count;
- clean manifest ID/payload hash and evidence item coordinates;
- constraint string and project-to-Vienna coordinate map;
- executable path, `RNAfold --version` output, command/configuration;
- stdout, stderr, return code, runtime, and status;
- output DBN, zero-based canonical pair set, output hash;
- sequence length, output validity, constraint compliance;
- explicit unsupported/unsatisfiable reason where no structure is emitted.

Keep raw command records, parsed structures, per-realization metrics, and
aggregate summaries in separate files. Apply repository ignore policy only to
large raw artifacts; keep configuration, hashes, and integrity summaries
versioned.

## Future runner and evaluation

After the blocker is resolved, add
`scripts/run_global_constrained_refolding_r2.py`. It should:

- verify the frozen fold/provenance inputs without using folds for parameter
  selection;
- run the six densities and five evidence seeds separately for both channels;
- run 0% as unconstrained RNAfold and verify its identity with constrained
  empty evidence where applicable;
- fail closed on unsupported/unsatisfied constraints;
- reuse the shared canonical parser and metrics rather than reimplementing
  them;
- produce B2 structures once per RNA/evidence realization and join source
  comparisons only after folding.

Add `scripts/summarize_global_constrained_refolding_r2.py` only after the
execution protocol is unblocked. It must compare B0 Original, B1 E1 local hard
baseline, and B2 using exact pair metrics, TP preservation, FP removal,
modification precision, direct/local/non-evidenced scopes, evidence
efficiency, source/density summaries, and risk–utility tables. Use the
full-refold edit decomposition frozen in the R2 protocol:

```text
preserved_TP = S ∩ G ∩ R
lost_TP      = S ∩ G \ R
removed_FP   = (S \ G) \ R
new_TP       = (R \ S) ∩ G
new_FP       = (R \ S) \ G
```

Verify these sets are mutually exclusive and exhaustive, and report
non-evidenced TP loss, FP removal, modification precision, and evidence
efficiency without substituting ORIGINAL for a matched comparator.

## Tests and audits

Create `tests/test_global_constrained_refolding_r2.py` with:

- first/last/internal coordinate conversion tests;
- exact forced-pair partner tests, including nested pairs;
- exact forced-unpaired tests at first, last, and internal positions;
- constraint-string length, pair legality, and one-partner checks;
- explicit rejection tests for crossing pairs, duplicate partners, and
  pair/unpaired conflicts;
- CLI toy integration tests using `--noPS` and the frozen executable;
- parser round-trip tests through the existing canonical parser;
- reproducibility checks for identical toy command/configuration inputs;
- a guard that the future runner does not import external77, noise, or real
  modality paths and does not pass source predictions into the fold adapter.

The current audit scripts are `scripts/audit_global_constrained_refolding_r2.py`
and `scripts/audit_r2_manifest_eligibility.py`. They are limited to
environment metadata, deterministic clean-manifest eligibility/coverage, the
manifest-ID-filtered B1 view, and seven short toy checks; outputs are retained
under `results/global_constrained_refolding_r2/integrity/`.

## Completion criteria

R2 is `R2_PROTOCOL_AMENDED — READY_FOR_R2_EXECUTION` after the v1.0.1
eligibility, coverage, matched-universe, aggregation, and test checks. Formal
R2 execution remains a separate task and must use eligible manifests only.
