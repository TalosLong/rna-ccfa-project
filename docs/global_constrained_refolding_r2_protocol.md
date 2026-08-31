# Global Evidence-Constrained Refolding R2 Protocol

## Status

**`R2_PROTOCOL_AMENDED_V1_0_2` — `R2_EXECUTION_COMPLETE`**

Protocol v1.0 was frozen before initial execution; v1.0.1 was frozen before
formal suite execution; v1.0.2 was frozen after the fail-closed capability
finding but before any formal performance metric. Amendment v1.0.1 is frozen
in `docs/global_constrained_refolding_r2_crossing_policy.md` and v1.0.2 in
`docs/global_constrained_refolding_r2_minimum_loop_policy.md`. Together they
govern the eligibility universe below.

Protocol v1.0 originally froze before execution. The crossing-evidence
capability blocker was discovered before formal execution and is resolved
prospectively by excluding an entire crossing manifest from B2, without
modifying delivered evidence. Formal R2 execution is authorized only on the
matched `R2_ELIGIBLE` universe; historical full-universe E1/B1 results remain
unchanged.

Protocol history is preserved: v1.0 is the initial protocol, v1.0.1 is the
crossing-evidence representability amendment, and v1.0.2 is the minimum-loop
representability amendment. v1.0.2 was frozen before any formal R2 performance
metric was computed.

## Scientific question

Given the same RNA sequence and sparse clean structural evidence, does
preserving an existing predictor output provide value over globally refolding
the sequence under hard evidence constraints? R2 establishes the mandatory
classical B2 comparator for the rebooted mainline:

```text
B0 Original predictor
vs B1 local hard evidence transformation
vs B2 global evidence-constrained refolding
vs future R4 post-hoc reconciliation
```

R2 is a classical baseline and does not train a learned model.

## Relationship to Project Reboot v2

R2 follows the R1 documentation freeze and precedes R3 reliability baselines
and any new R4 learned protocol. The historical
`evidence_guidance_stage_e2_v1` protocol remains immutable provenance and is
superseded before training; it is not this R2 experiment. R2 uses only
Legacy121 development data and does not open external77.

## Input universe and source comparison

The development universe is the 363 normalized Legacy121 source records:
121 each from RNAfold, PETfold, and trRosettaRNA2 native SS. B2 folding input
is deliberately source-agnostic and consists only of:

```text
sequence + delivered clean evidence items
```

The source prediction is never passed to RNAfold. For each unique RNA and
evidence realization, B2 produces one structure, which is reused in the
three source-stratified comparisons against B0 and B1. This is required to
avoid source identity entering B2 and to make the classical refolding baseline
identical across source comparisons. A separate source-specific B2 is not
permitted in the primary protocol.

Evidence uses the frozen `simulated_evidence_v1` clean manifests: channels
remain separate (`POSITIVE_PAIR_EVIDENCE` and
`UNPAIRED_NUCLEOTIDE_EVIDENCE`), densities are 0%, 1%, 5%, 10%, 20%, and 50%,
and evidence seeds are 101, 103, 107, 109, and 113. No noisy evidence, real
modality, or external77 data are allowed.

## Environment freeze

The audited primary executable is:

```text
/usr/bin/RNAfold
RNAfold 2.4.17
```

The first R2 implementation must invoke this absolute binary through a
non-shell subprocess and record stdout, stderr, command, runtime, and version.
The audited Python interpreters (`python`, `/root/miniconda3/bin/python`, and
`/root/miniconda3/envs/nufold_P/bin/python`) do not provide the `RNA` Python
binding. No ViennaRNA installation or upgrade is authorized by this protocol.

The frozen command for a single sequence is:

```text
/usr/bin/RNAfold --noPS -C --enforceConstraint
```

The FASTA header and sequence are followed on stdin by one constraint string.
`--noPS` prevents postscript side effects. No command-line option changes the
thermodynamic model: linear RNA, MFE decoding, default parameter set,
temperature 37 C, dangles=2, no `--noLP`, no `--noGU`, no
`--noClosingGU`, no `--gquad`, no circular mode, and no soft constraints.
There is no random seed for this deterministic MFE calculation.

The CLI advertises hard constraints (`-C`/`--constraint`), exact round-bracket
enforcement (`--enforceConstraint`), forced-unpaired symbols, and soft SHAPE
constraints. Soft constraints are audited as available but excluded from R2
v1. Although `-C` accepts an optional filename, ViennaRNA 2.4.17 treats that
file as a command-file interface rather than a plain one-line dot-bracket
constraint file. R2 therefore uses the unambiguous stdin sequence-plus-
constraint form above; `--commands=<filename>` is not used.

## Constraint semantics and coordinate contract

Project pair coordinates are canonical zero-based `(i,j)`, `i < j`.
ViennaRNA positions are one-based and the only conversion is:

```text
vienna_position = project_position + 1
```

For a delivered positive pair `(i,j)`, the adapter writes `(` at
`i+1` and `)` at `j+1`, with `.` elsewhere, and invokes
`--enforceConstraint`. In the audited CLI this requires the specified partner
pair, not merely that both endpoints be paired. The weaker `|` symbol (paired
to any partner) is not semantically equivalent and is forbidden for B2.

For a delivered unpaired position `k`, the adapter writes `x` at `k+1` and
`.` elsewhere. ViennaRNA then forbids pairing at that exact position. Multiple
noncrossing positive pairs are represented by their matching parentheses;
multiple unpaired positions use multiple `x` symbols.

Before invoking RNAfold, the adapter must reject and classify
`UNSATISFIABLE_CONSTRAINT` when an endpoint has two forced partners, when a
forced-unpaired position is also forced paired, or when forced pairs cross.
It must not delete an offending evidence item and must not downgrade a forced
pair to “paired with any partner.”

## Pseudoknot policy and eligibility amendment

Standard ViennaRNA dynamic programming and ordinary dot-bracket parentheses
represent nested structures but not general pseudoknots/crossing pairs. The
frozen clean suite contains 7,260 manifests total and 3,630 pair-channel
manifests; 87 pair-channel manifests (2.3967%) across 11 RNAs contain at least
one crossing pair among delivered evidence items. They are therefore not
representable by the standard B2 interface. R2 remains a non-pseudoknot
mainline and makes no pseudoknot-support claim.

The prospective v1.0.1 policy is a solver-capability/representability
exclusion, not a performance or GT selection. A complete delivered pair set
is `R2_ELIGIBLE` iff it is noncrossing. Any crossing relation marks the whole
manifest `R2_INELIGIBLE_CROSSING_EVIDENCE`; B2 is skipped for that manifest and
no item is dropped. Primary B0/B1/B2 comparisons use identical eligible
manifest IDs, with B1 filtered by ID only. RNA-balanced macro aggregation and
zero-coverage handling are frozen in the amendment document.

## Minimum-loop capability amendment v1.0.2

Under the unchanged ViennaRNA 2.4.17 model, a forced exact pair `(i,j)` is
representable only when at least three nucleotides occur inside it:
`j-i-1>=3`, equivalently `j-i>3`. A complete positive-pair manifest is
eligible only when it is both noncrossing and every delivered pair satisfies
that minimum-loop condition. Crossing and minimum-loop capability flags are
stored independently; a manifest with both receives
`R2_INELIGIBLE_MULTIPLE_CAPABILITIES`. A minimum-loop-only manifest receives
`R2_INELIGIBLE_MINIMUM_LOOP_EVIDENCE`.

This is a whole-manifest solver-capability exclusion. No offending item is
deleted or weakened, no evidence is replaced or resampled, and no ViennaRNA
parameter is changed. The unpaired channel remains governed by its original
hard-unpaired semantics. Complete details are frozen in
`docs/global_constrained_refolding_r2_minimum_loop_policy.md`.

## Folding output and validation contract

For each supported future RNA/evidence realization, retain at least:

- `rna_id`, channel, density, evidence seed, and delivered item count;
- the complete constraint string and one-based coordinate mapping;
- absolute RNAfold path, version, command, configuration, stdout/stderr, and runtime;
- output DBN and canonical zero-based pair set;
- sequence length, pair legality, one-partner validation, and constraint
  satisfaction status;
- input manifest hash and output/provenance hashes where appropriate.

The output parser must use the existing project canonical parser and
`validate_pairs`; it must not reimplement pair metrics. Any malformed DBN,
length mismatch, illegal pair, unsatisfied hard constraint, or nonzero process
exit is an explicit failed realization. The no-constraint 0% condition must
be run as standard unconstrained RNAfold and must not be forced to match all
three historical source predictions. Equality with the historical RNAfold
output is required only after a separate provenance audit confirms identical
protocols.

## Evaluation plan after blocker resolution

R2 must compare B0, B1, and B2 on identical RNA/evidence realizations and
report macro/micro Precision, Recall, F1, TP preservation, FP removal,
modification precision, source-wise and density-wise effects, and evidence
efficiency (`FP_removed / evidence_items` and optionally `delta_F1 /
evidence_items`). Reuse the E1 DIRECT / LOCAL_CONFLICT / NON_EVIDENCED scopes
where their evidence-defined semantics are valid, and report non-evidenced
modification precision, FP removal, and TP loss.

B2 is a full refold and can add and delete pairs, so deletion-only identities
are not used. Relative to an original source pair set `S`, ground truth `G`,
and B2 output `R`, the mutually exclusive edit decomposition is:

```text
preserved_TP = S ∩ G ∩ R
lost_TP      = S ∩ G \ R
removed_FP   = (S \ G) \ R
new_TP       = (R \ S) ∩ G
new_FP       = (R \ S) \ G
```

The evaluator must verify these sets are disjoint and exhaustive over the
original/new pair partitions, and separately report pair additions, pair
deletions, unchanged pairs, and any one-partner/validity failures. Direct,
local, and non-evidenced scope assignment is based on the union of `G`, `S`,
and `R`, with the same delivered evidence set used for B0, B1, and B2.

### Pre-execution metric clarification (2026-08-31)

This clarification was frozen before any formal R2 folding output or metric
was generated. It does not change the eligible universe, folding command,
constraint semantics, scope partition, or aggregation unit.

The primary matched B1 condition is the channel-appropriate completed hard
transformation: `PAIR_HARD_ENFORCE` for positive-pair evidence and
`UNPAIRED_HARD_DELETE` for unpaired-nucleotide evidence. The historical
`PAIR_PROTECT_ONLY` condition remains an immutable E1 contextual reference but
is not substituted for B1 in the primary B0/B1/B2 table.

For a full refold, beneficial and harmful modifications are defined only from
the decomposition above:

```text
beneficial_changes      = removed_FP + new_TP
harmful_changes         = lost_TP + new_FP
modified_pair_events    = beneficial_changes + harmful_changes
modification_precision  = beneficial_changes / modified_pair_events
```

The same definition is used after restricting all pair sets to a frozen
DIRECT, LOCAL_CONFLICT, or NON_EVIDENCED scope. A zero denominator is always
reported as NA, never as zero or one. The same uniform NA rule applies to
`TP_preservation` when original TP is zero, `FP_removal` when original FP is
zero, and evidence-efficiency ratios when delivered evidence count is zero.
Event-pooled values are computed from pooled numerators and denominators.
RNA-balanced values first pool eligible realization counts within RNA and then
average the defined RNA-level ratios; denominator-zero RNA values remain NA.

## Go / No-Go relation

R2 is not itself a learned-method success/fail gate. It supplies the mandatory
Gate A comparison. If B2 dominates post-hoc reconciliation on the frozen
TP-preservation/FP-removal risk–utility comparison, record Gate A failure and
stop the post-hoc mainline. If B2 leaves headroom, R3 may freeze the simple
reliability baselines; only then may a new R4 protocol be designed.

R2 execution and formal summarization are authorized only on v1.0.2
`R2_ELIGIBLE` manifests after the coordinate-only capability audit, matched
views, tests, and 100% eligible-output reuse/completion gate pass. No
pseudoknot-capable solver, evidence rewrite, or ViennaRNA model change is
authorized.
