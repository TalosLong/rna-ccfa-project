# Global Evidence-Constrained Refolding R2 Protocol

## Status

**`R2_PROTOCOL_BLOCKED`**

Freeze checkpoint: **FROZEN BEFORE R2 EXECUTION**. The specification below is
not an authorization to run the blocked benchmark.

This protocol is frozen before any R2 execution for the semantically supported
non-pseudoknot cases. A complete Legacy121 R2 benchmark is not authorized
because 87 frozen positive-pair evidence manifests contain mutually crossing
delivered pairs, which standard ViennaRNA non-pseudoknot constraints cannot
represent simultaneously. No evidence item may be silently dropped,
replaced, or reinterpreted to bypass this blocker.

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

## Pseudoknot policy and current blocker

Standard ViennaRNA dynamic programming and ordinary dot-bracket parentheses
represent nested structures but not general pseudoknots/crossing pairs. The
frozen clean suite contains 7,260 manifests total and 3,630 pair-channel
manifests; 87 pair-channel manifests (2.3967%) across 11 RNAs contain at least
one crossing pair among delivered evidence items. They are therefore not
representable by the standard B2 interface. R2 remains a non-pseudoknot
mainline and makes no pseudoknot-support claim.

The current blocker is semantic, not a missing option: excluding those
manifests, dropping crossing items, sequentially folding each pair, or using a
different pseudoknot-capable algorithm would change the frozen primary
comparison and requires a new prospective decision. Until that decision is
made, no Legacy121 R2 benchmark or R2 result table may be generated.

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

## Go / No-Go relation

R2 is not itself a learned-method success/fail gate. It supplies the mandatory
Gate A comparison. If B2 dominates post-hoc reconciliation on the frozen
TP-preservation/FP-removal risk–utility comparison, record Gate A failure and
stop the post-hoc mainline. If B2 leaves headroom, R3 may freeze the simple
reliability baselines; only then may a new R4 protocol be designed.

No R2 execution is authorized while the crossing-evidence blocker remains
unresolved.
