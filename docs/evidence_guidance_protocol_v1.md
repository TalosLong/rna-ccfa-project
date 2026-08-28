# Simulated Evidence Guidance Protocol v1

Status: **FROZEN BEFORE EVIDENCE-GUIDED EVALUATION**

Protocol/schema version: `simulated_evidence_v1`.

This protocol defines abstract simulated structural evidence. It does not
represent or claim any real assay. In particular, the generated items must not
be described as SHAPE, DMS, NMR, or another experimental modality. Real
modality mapping is deferred to Stage E5.

## Evidence channels

The channels are separate and are never merged into one token.

### `POSITIVE_PAIR_EVIDENCE`

An item is a zero-based canonical-coordinate pair `(i,j)`, with `i<j`, drawn
from the exact GT pair set. It is an abstract observation supporting a
specific pair/contact. It may later motivate a pair/contact modality mapping,
but no such mapping is currently authorized.

### `UNPAIRED_NUCLEOTIDE_EVIDENCE`

An item is a zero-based position `i` drawn from the positions not paired in
the exact GT structure. It is an abstract observation supporting an unpaired
or accessible state. It is not actual reactivity or accessibility assay data.

Every future result must identify channel, density, noise level, and evidence
seed.

## Eligible universes and untargeted sampling

For each Legacy121 RNA:

- pair universe: every exact GT canonical pair;
- unpaired universe: every position absent from all GT pair endpoints.

Sequence length, GT pair count, and GT-unpaired count are recorded. Sampling
uses only RNA ID, sequence, and exact GT pairs. Predictor outputs, FP/FN/TP,
wrong-partner relations, confidence, model disagreement, error labels, and
stem difficulty cannot enter sampling. Consequently evidence is not targeted
to known prediction errors. The two evidence universes are sampled
independently.

## Clean density and deterministic selection

The frozen density grid is `0,1,5,10,20,50` percent, measured against the
eligible universe of the selected channel for each RNA. The selected count is

`min(N, floor((N * density_percent + 50) / 100))`,

which is nearest-integer round-half-up using exact integer arithmetic. Zero
percent always selects zero. At a positive density, if `N>0` and this formula
returns zero, exactly one item is selected. An empty universe stays empty.

The frozen evidence seeds are `101,103,107,109,113`. For each manifest, the
eligible universe is lexicographically/numerically sorted and sampled without
replacement using a deterministic PRNG seeded by a SHA256 digest of protocol
version, RNA ID, channel, density, evidence seed, and operation label. Thus a
manifest is reproducible from exactly those identifiers and the frozen GT
input.

## Noise and corruption

The frozen candidate noise grid is `0,5,10,20,30` percent. Noise is not used
in Stage E1. It is implemented and mechanism-tested at E0 for later Stage E4.
The number requested for corruption is round-half-up of noise percentage
times selected observations, without minimum-one behavior. A SHA256-seeded
sample chooses which selected item indices are corrupted. The realized noise
fraction is successful corruptions divided by selected observations;
unavailable corruptions are reported explicitly.

For positive-pair evidence, the primary corruption policy preserves one
deterministically selected endpoint and replaces the partner with a
deterministically selected alternative. The delivered pair must be in range,
ordered, non-self, unique, one-partner compatible with other delivered
evidence, one of `AU/UA/GC/CG/GU/UG`, and not an exact GT pair. It therefore
represents an abstract wrong-partner/contact observation. If no candidate
exists, status is `CORRUPTION_UNAVAILABLE` and no invalid item is delivered.

For unpaired evidence, corruption replaces the clean unpaired position with a
unique position that is actually paired in GT while claiming it is unpaired.
If no unused paired position is available, status is
`CORRUPTION_UNAVAILABLE`.

## Manifest contract and provenance

Each manifest records RNA ID, sequence length, channel, density, evidence
seed, noise level, eligible-universe size, selected/delivered counts,
minimum-one status, source-GT SHA256, and payload SHA256. Every item records a
contiguous item index, `CLEAN`, `CORRUPTED`, or
`CORRUPTION_UNAVAILABLE` status, corruption-request flag, original clean item,
and delivered item. Deterministic canonical JSON serialization fixes suite
hashes.

The generator input contract is exactly `rna_id`, `sequence`, and
`ground_truth_pairs`. Prediction/error fields are forbidden and tested.

## Frozen hard baselines for future evaluation

These definitions are frozen but are not evaluated in Stage E0.

- `ORIGINAL`: no refinement.
- `V3_VETO2_FIXED`: exact frozen development-only v3 semantics; it remains a
  failed-phase internal-information comparator.
- `PAIR_PROTECT_ONLY`: for each evidenced pair, retain it if already present,
  remove predicted pairs conflicting at either endpoint, and never add the
  absent evidence pair.
- `PAIR_HARD_ENFORCE`: remove endpoint conflicts, add an absent evidenced pair,
  and force it to remain. This is a direct-injection upper/reference baseline,
  not learned generalization.
- `UNPAIRED_HARD_DELETE`: remove every predicted pair touching an evidenced
  unpaired position and add nothing.

All transformations must preserve valid coordinates, ordered unique pairs,
and the one-partner constraint. They may modify only the stated evidence
consequences.

## Anti-tautology evaluation scopes

Future evaluation reports standard `FULL_STRUCTURE` metrics and a mandatory
partition of effects. The partition is defined on the union of GT, original
prediction, and refined prediction pairs for each RNA.

For positive-pair evidence:

- `DIRECT_EVIDENCE_EFFECT`: the exact delivered evidence pairs themselves;
- `LOCAL_CONFLICT_EFFECT`: all non-direct pairs touching any delivered
  evidence endpoint;
- `NON_EVIDENCED_EFFECT`: all remaining pairs, which neither equal an
  evidence pair nor touch an evidence endpoint.

For unpaired evidence:

- `DIRECT_EVIDENCE_EFFECT`: nucleotide-level compliance for each delivered
  unpaired state; it contains no pair-level member;
- `LOCAL_CONFLICT_EFFECT`: all pairs touching a delivered evidenced position;
- `NON_EVIDENCED_EFFECT`: all pairs touching no delivered evidenced position.

These scopes do not overlap. Unavailable items have no delivered consequence
and enter none of the three scopes. Direct evidence recovery/compliance and
local conflict corrections are reported separately. Directly injected GT
pairs and endpoint-conflicting pairs are excluded from non-evidenced metrics.
A future claim that evidence improves refinement beyond direct enforcement
requires positive `NON_EVIDENCED_EFFECT`; recovering supplied truth alone is
insufficient.

## Future endpoints

For every channel × density × evidence seed × source predictor, clean-evidence
evaluation must report full macro/micro P/R/F1, delta F1 versus ORIGINAL,
evidence compliance, direct recovery, local conflict corrections,
non-evidenced macro/micro delta F1, correct-pair preservation outside
evidence, beneficial/harmful edits, and modified-RNA fraction.
`PAIR_HARD_ENFORCE` must additionally report the fraction of total F1 gain
attributable directly to inserted evidence pairs.

## Development sequence and locks

The frozen sequence is E0 protocol/generator/feasibility; E1 clean hard
baselines; E2 separately frozen learned protocol only if E1 supports a
non-direct signal; E3 learned Legacy121 development; E4 noise robustness; E5
real-modality feasibility; E6 separately frozen independent evaluation.

No neural model is trained at E0 or E1. Legacy121 is development data.
external77 is not used for sampling, design, feasibility, or E1 and remains
locked.
