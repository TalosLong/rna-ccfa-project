# Evidence Guidance Stage E2 Protocol

Status: **FROZEN BEFORE E2 TRAINING**

Protocol version: `evidence_guidance_stage_e2_v1`.

## Scientific question and immutable E1 interpretation

Stage E2 tests the preregistered hypothesis:

> A learned evidence-conditioned selective refiner can use sparse simulated
> structural evidence to improve risk-controlled deletion of false-positive
> predicted pairs, including pairs outside the directly evidenced and
> local-conflict region, beyond both an evidence-masked learned control and
> the frozen E1 hard-local baselines.

Stage E1 remains immutable development evidence. It established useful
`DIRECT_EVIDENCE_EFFECT` and `LOCAL_CONFLICT_EFFECT`, while its local hard
transformations produced exactly zero `NON_EVIDENCED_EFFECT`. The zero result
is not an E1 failure; it motivates a model in which every delivered evidence
item can affect every original predicted pair. Stage E2 permits this mechanism
but does not assume that useful propagation exists.

Legacy121 remains development data. Stage E2 does not authorize external77,
noise robustness, a real-modality claim, or independent generalization.

## Task and edit space

The prediction unit is one pair in the immutable original source prediction.
For an original predicted pair `p` and GT pair set `G`:

- `KEEP` iff `p in G`;
- `DELETE` iff `p not in G`;
- `DELETE` is the positive class.

Labels are used for fitting and evaluation only. At inference, the model may
keep or delete an original pair. It cannot add a pair, inject a supplied pair,
reassign a partner, recursively rebuild stems, or run a decoder that creates
pairs. An absent simulated positive-pair observation therefore remains absent
from the E2 output. `PAIR_HARD_ENFORCE` is an E1 direct-injection reference,
not an E2 learned output.

Deletion accounting is mandatory:

`beneficial + harmful = modified`,
`TP_after = TP_before - harmful`,
`FP_after = FP_before - beneficial`, and
`FN_after = FN_before + harmful`.

## Primary channel experiments

Two independent primary experiments are frozen:

- `E2_PAIR`: only clean `POSITIVE_PAIR_EVIDENCE`;
- `E2_UNPAIRED`: only clean `UNPAIRED_NUCLEOTIDE_EVIDENCE`.

The channels are never merged in primary E2. Both use densities
`0,1,5,10,20,50` percent and evidence seeds `101,103,107,109,113` from the
unchanged `simulated_evidence_v1` generator. Nominal density, evidence seed,
eligible-universe size, manifest GT hash, and unselected universe members are
not model inputs. Only sequence, immutable original prediction, and delivered
clean evidence items enter the inference feature path.

One conditional model per channel is trained across all 30 density-seed
realizations for each training RNA. A predicted pair therefore appears once
per realization, for 5,290 x 30 = 158,700 full-dataset pair-realization rows
per channel before splitting. These are augmentation rows, not independent
biological samples. No model is trained separately by density.

The primary model is pooled source-agnostic. RNAfold, PETfold, and
trRosettaRNA2 native SS records are retained, but source identity and
source-specific confidence are excluded. No source-aware condition is part of
the first E2 protocol; introducing one requires a later amendment and cannot
rescue the primary result.

## Frozen RNA splits

The exact existing file
`results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv` is used,
with SHA256
`810b04a3963acc7637b60fcb5c2246c765fac334f809a5af9f8f050824ed974f`.
It contains 121 unique RNAs assigned 25/24/24/24/24 across folds 0--4.

For rotation `k`:

- test = fold `k`;
- validation = fold `(k+1) mod 5`;
- training = the other three folds.

All source records, densities, evidence seeds, pair examples, and evidence
items belonging to one RNA stay in that RNA's partition. An identity component
cannot cross partitions. No evidence realization from a validation or test RNA
can contribute to fitting, preprocessing, class weighting, checkpoint
selection, or threshold selection outside its permitted role.

## Frozen base candidate features

The source-agnostic v1 feature contract is reused exactly:

- endpoint bases `base_i`, `base_j`;
- ordered `pair_type`;
- sequence length;
- raw and relative separation;
- singleton flag;
- strict-stem length;
- outer-to-inner stem position and normalized stem position;
- outer- and inner-boundary flags;
- immediate outward/inward stacked-neighbor existence and ordered pair type.

The 11 numeric fields and exact historical v1 categorical encoder produce a
78-dimensional candidate input: 11 numeric + 62 fixed vocabulary indicators
+ five explicit unknown-bucket indicators. The historical inward-neighbor
vocabulary has 17 entries (it omits `GG`); an inward `GG` therefore activates
that field's frozen unknown bucket exactly as in v1. This asymmetry is retained
for a matched base contract rather than silently repaired. Features are
extracted once from the immutable original prediction. No source name is
included.

## Candidate-relative evidence features

All coordinate denominators use `max(sequence_length-1,1)`. Continuous
features are finite and deterministic.

### `E2_PAIR` item vector: 17 dimensions

For candidate `(i,j)` and delivered pair `(a,b)`, the ten continuous fields
are normalized `|i-a|`, `|i-b|`, `|j-a|`, `|j-b|`, minimum and maximum of
those four distances, candidate span, evidence span, signed span difference
`((b-a)-(j-i))/(L-1)`, and absolute midpoint distance
`|(i+j)-(a+b)|/(2(L-1))`.

Three binary fields are exact-same-pair, any-shared-endpoint, and direct
conflict. Direct conflict is true exactly when the two unequal pairs share an
endpoint. A fixed four-way one-hot relation completes the vector:

1. `CONTAINING`: candidate interval contains the evidence interval; equality
   takes this relation by precedence;
2. `NESTED`: evidence interval contains the candidate interval and the first
   rule did not apply;
3. `CROSSING`: endpoints interleave strictly;
4. `DISJOINT`: all remaining non-overlapping cases.

The relation rules are evaluated in the order above and are exhaustive.

### `E2_UNPAIRED` item vector: 8 dimensions

For candidate `(i,j)` and delivered position `k`, the five continuous fields
are normalized `|i-k|`, `|j-k|`, their minimum, their maximum, and distance to
the pair midpoint `|(i+j)-2k|/(2(L-1))`. Three binary fields indicate `k==i`,
`k==j`, and strict interval membership `i<k<j`.

No feature states whether a delivered item is GT-correct. Correctness is part
of the frozen clean simulated-observation abstraction, not an input column.

## Evidence-set and candidate architecture

The channel-specific evidence item vector is processed independently by a
shared item MLP:

`Linear(item_dim,32) -> ReLU -> Linear(32,32) -> ReLU`.

There is no item-level dropout or attention. Item embeddings are pooled with
both elementwise mean and elementwise maximum, yielding 64 dimensions.
Padding is masked out of both operations. For an empty set, both pooled
vectors are fixed zeros; no learned missing-evidence or RNA embedding exists.

Two observable descriptors are added: delivered item count and delivered item
count divided by sequence length. Nominal density and GT-universe size are
excluded. For an empty set, the complete 66-dimensional evidence block
(pooled vectors plus descriptors) is explicitly all zero after preprocessing.

The candidate branch is:

`Linear(78,64) -> ReLU`.

The 64-dimensional candidate representation and 66-dimensional evidence block
form a 130-dimensional fusion input. The frozen classifier is:

`Linear(130,128) -> ReLU -> Dropout(0.10) ->`
`Linear(128,64) -> ReLU -> Dropout(0.10) ->`
`Linear(64,1)`.

The output is one DELETE logit. This explicit 130-to-128 projection resolves
the descriptor-induced dimension mismatch. No Transformer, GNN, recurrence,
pretrained language model, or global structure decoder is allowed.

Every delivered item is paired with every candidate original pair before
permutation-invariant pooling. The model can therefore alter the DELETE score
for a candidate that is neither evidenced nor endpoint-local. Such an edit is
a candidate non-evidenced propagation event; architecture access alone is not
evidence that propagation is useful.

## Preprocessing and leakage controls

Candidate numeric, candidate-relative evidence numeric, and nonempty-set count
descriptors are standardized using only training-partition incidences:

`z = (x - train_mean) / max(train_std,1e-8)`.

The empty evidence block is overridden to exact zero after preprocessing.
Fixed categorical vocabularies are not learned from data. Statistics are
serialized by channel and fold. Candidate statistics are computed over the
expanded training pair-realization rows; evidence-item statistics are computed
over training candidate-item incidences; count statistics are computed over
nonempty training pair-realization rows. Validation/test rows never enter.

The inference adapter exposes only delivered items, not clean originals for a
corrupted item, manifest universe size, source-GT hash, nominal density, or
evidence seed. The following are forbidden inputs: full GT structure beyond
delivered items, GT labels at inference, unselected GT pairs or unpaired
positions, TP/FP/FN and wrong-partner labels, error summaries, predictor
confidence, source name, family/dataset identity, external77, noise data, and
real-modality data. Evidence remains untargeted and cannot be resampled using
error, loss, disagreement, confidence, or source identity.

## Training and checkpoint selection

Each channel has 5 folds x 5 model seeds = 25 primary training runs; the two
channels total 50 future runs. Model seeds are `17,29,41,53,67`.

Frozen optimization is:

- class-weighted `BCEWithLogitsLoss`, DELETE positive;
- `pos_weight = KEEP_train / DELETE_train` from expanded training labels only;
- AdamW, learning rate `1e-3`, weight decay `1e-4`;
- batch size 256 pair-realization examples;
- maximum 100 epochs, patience 12;
- gradient norm clipping 5.0;
- dropout 0.10 only at the two frozen fusion-classifier locations.

Every density and evidence seed is retained once per training RNA/source/pair;
there is no label-aware resampling. Because expansion is uniform, class ratios
equal the original training-pair ratios. A zero DELETE training count is a
hard training failure.

Future implementation uses
`torch.device("cuda" if torch.cuda.is_available() else "cpu")`, moves model
and all tensors to that device, records PyTorch/CUDA/device/GPU metadata, and
does not alter hyperparameters based on hardware.

Checkpoint selection uses WITH_EVIDENCE validation rows only. The primary
metric is event-pooled validation DELETE F1 at threshold 0.5 across all six
densities, five evidence seeds, validation RNAs, and three sources for that
channel. Ties select higher event-pooled correct-pair preservation, then the
earlier epoch. No test outcome selects an epoch.

## Evidence-masked matched control

`E2_WITH_EVIDENCE` uses the delivered set. `E2_EVIDENCE_MASKED` uses the exact
same checkpoint and candidate rows but replaces the delivered set with the
empty evidence block at held-out inference. It is not separately trained or
recalibrated. This comparison holds learned parameters and decision threshold
fixed while changing only the evidence input.

At zero density, WITH_EVIDENCE and EVIDENCE_MASKED probabilities and decisions
must match bit-for-bit in deterministic evaluation mode. A mismatch is an
integrity failure.

## Risk-controlled threshold and abstention

One global threshold is selected per channel x fold x model seed from
WITH_EVIDENCE validation probabilities. The frozen grid is
`0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95`.

For each threshold and each density separately, validation preservation is
the event-pooled retained-original-TP count divided by original-TP opportunity
count across validation RNAs, all sources, and all five evidence seeds. A
threshold is eligible only if preservation is at least 0.99 at every one of
the six densities. Among eligible thresholds, event-pooled DELETE F1 across
all validation densities/seeds/sources is maximized; ties choose the higher
threshold and then fewer total edits.

The selected threshold is applied unchanged to both WITH_EVIDENCE and
EVIDENCE_MASKED on the held-out fold and to every density/source/evidence seed.
No density- or source-conditional threshold is permitted.

If no threshold is eligible, both conditions deploy
`ABSTAIN_NO_REFINEMENT`: no edits, DELETE recall 0, preservation 1, structure
delta F1 0, and modification precision NA. Abstention keeps evaluation
defined but does not count as an actual threshold. The primary deployment gate
requires 25/25 real validation-selected thresholds per channel. This is a
strict but mathematically possible requirement and is not relaxed in advance.

## Evaluation scopes and matched endpoints

The E1 partition is reused on the union of GT, original, and condition output
pairs:

- `DIRECT_EVIDENCE_EFFECT`;
- `LOCAL_CONFLICT_EFFECT`;
- `NON_EVIDENCED_EFFECT`.

For a positive-pair item, DIRECT is the delivered pair, LOCAL is every other
pair touching a delivered endpoint, and NON_EVIDENCED is the remainder. For
an unpaired item, DIRECT is nucleotide compliance, LOCAL is every pair touching
the delivered position, and NON_EVIDENCED is the remainder. Scopes are
disjoint and exhaustive. The same delivered-evidence-defined scopes are used
to evaluate WITH_EVIDENCE and its masked control, even though the masked model
does not receive those items.

Every held-out realization reports FULL_STRUCTURE and all three scopes using
the shared exact-pair empty-set convention. It preserves per-pair scores,
decisions, beneficial/harmful deletions, modification precision, preservation,
modified-RNA status, compliance, and deletion accounting.

The central propagation endpoint at identical RNA, source, density, evidence
seed, fold, and model seed is:

`NON_EVIDENCED delta F1 = F1(WITH_EVIDENCE) - F1(EVIDENCE_MASKED)`.

The total evidence endpoint is the analogous matched FULL_STRUCTURE delta F1.
Non-evidenced beneficial/harmful deletions, modification precision, and
preservation are mandatory. ORIGINAL is not a substitute for the causal
masked control.

## Frozen aggregation semantics

Biological RNA is the biological unit. Evidence and model seeds are repeated
realizations, never independent biological replicates.

For each density, channel, condition, source stratum, model seed, and evidence
seed, the five held-out folds are concatenated so each of 121 RNAs appears
once. Macro metrics are unweighted means over RNA rows. Micro metrics are
computed from summed TP/FP/FN counts. Seed summaries then report the arithmetic
mean, population standard deviation, minimum, and maximum over the 25
model-seed x evidence-seed realizations; no seed is selected.

Matched macro differences are computed per RNA/source/realization first and
then averaged over RNAs, evidence seeds, and model seeds. Matched micro
differences are computed after concatenating the five folds separately for
each model-seed x evidence-seed realization, then averaged over the 25
realizations. Source-specific summaries use the same procedure within source.

For pooled moderate-density gates, densities 5, 10, and 20 are concatenated.
Modification precision, DELETE recall, and preservation are event-pooled
ratios from summed beneficial deletions, original FP opportunities, and
retained/original TP counts across all held-out folds, three densities, three
sources, evidence seeds, and model seeds. Per-source ratios use the same sums
within source. Zero-edit modification precision is NA and fails any criterion
that requires a numeric value.

Pooled moderate matched macro delta F1 is the unweighted mean of per-RNA
WITH-minus-MASKED deltas across the three densities and repeated realizations.
Pooled moderate matched micro delta F1 is the mean of the 75 density x
model-seed x evidence-seed micro differences after each difference combines
all held-out folds. NON_EVIDENCED metrics use the same hierarchy on the
evidence-defined non-evidenced scopes.

Evidence responsiveness at a density uses eligible realizations defined as
one held-out RNA x source x evidence seed x model seed with at least one
delivered item and at least one original predicted pair. A realization differs
when the WITH and MASKED deleted-pair sets are unequal. The response fraction
is differing eligible realizations divided by all eligible realizations.

## Frozen comparators and ablations

Each channel reports ORIGINAL and historical V3_VETO2_FIXED context. E2_PAIR
also reports E1 PAIR_PROTECT_ONLY and PAIR_HARD_ENFORCE; E2_UNPAIRED reports
UNPAIRED_HARD_DELETE. Historical/hard outputs are not retuned.

Required E2 ablations are:

1. `WITH_EVIDENCE`: primary checkpoint and delivered set;
2. `EVIDENCE_MASKED`: same checkpoint, exact empty block;
3. `NO_COUNT_DESCRIPTORS`: separately trained matched architecture with the
   two count descriptors removed; the 128-dimensional candidate-plus-pooling
   vector passes through `Linear(128,128)` to preserve depth;
4. `NO_CANDIDATE_RELATIVE_GEOMETRY`: separately trained matched architecture
   whose item input contains only absolute evidence summaries. Pair items use
   normalized `a`, `b`, span, and midpoint (4 dimensions); unpaired items use
   normalized `k` (1 dimension). Count descriptors remain. No candidate-item
   relation field is present;
5. `BASE_V1_TOPOLOGY_ONLY`: existing authoritative v1
   POOLED_SOURCE_AGNOSTIC fold/seed scores, not retrained.

Ablations use identical folds/seeds and cannot rescue a failed primary channel
gate. No larger grid is authorized.

## Frozen channel gate

Each channel independently resolves to `E2_PAIR_GATE_PASS/FAIL` or
`E2_UNPAIRED_GATE_PASS/FAIL`. Every criterion below is conjunctive:

1. 25/25 primary runs finish and obtain an actual validation-selected
   threshold; abstention is not deployability.
2. WITH_EVIDENCE pooled moderate modification precision >= 0.80 and
   correct-pair preservation >= 0.99.
3. WITH_EVIDENCE moderate preservation >= 0.98 for every source.
4. At least two of densities 5%, 10%, and 20% have strictly positive matched
   WITH-minus-MASKED FULL_STRUCTURE macro and micro delta F1.
5. At least two moderate densities have strictly positive matched
   NON_EVIDENCED macro and micro delta F1.
6. At least two sources have strictly positive matched FULL_STRUCTURE macro
   and micro delta F1 over the pooled moderate regime, and at least one is
   RNAfold or PETfold.
7. WITH_EVIDENCE event-pooled moderate NON_EVIDENCED modification precision
   >= 0.70 and correct-pair preservation >= 0.99.
8. WITH and MASKED deleted-pair sets differ on at least 10% of eligible
   realizations at one or more moderate densities.

Any false criterion, missing run, accounting/integrity failure, missing
threshold, or required NA produces channel FAIL. A channel cannot be rescued
by the other channel, source-aware analysis, 1%/50% results, a hard baseline,
or an ablation.

Overall `E2_DEVELOPMENT_GATE_PASS` requires at least one independently passing
channel; if neither passes, it is `E2_DEVELOPMENT_GATE_FAIL`. Only a passing
channel may proceed to a separately frozen noise/real-modality feasibility
stage. Even a pass does not authorize external77; an independent protocol must
later identify a final frozen channel/model/checkpoint/threshold without using
external outcomes.

## Density interpretation and allowable claims

All six densities are reported. The 1% condition is the coarse minimum-one
regime; 5--20% is the primary moderate sparse regime; 50% is a high-evidence
reference. A main claim cannot be based only on 50%.

If a channel passes, the allowed Legacy121 development statement is:
"simulated sparse structural evidence improves a learned selective refiner."
Only if the non-evidenced criteria also pass may the result state that useful
information propagates beyond directly evidenced or locally conflicting
positions. The protocol never authorizes assay-specific, experimentally
validated, real-evidence, independent, cross-dataset, or model-agnostic claims.

## Future artifact contract

Future outputs live under `results/evidence_guidance/stage_e2/`. For each
channel/fold/model seed they include `config.json`, RNA ID split files,
`checkpoint.pt`, `validation_curves.csv`, `selected_threshold.json`, and
validation/test pair scores. Evaluations retain `per_rna_metrics.csv`,
`scope_metrics.csv`, and `evidence_response_metrics.csv`. Summary files are
`training_summary.csv`, `threshold_deployability.csv`,
`full_structure_by_density.csv`, `non_evidenced_by_density.csv`,
`matched_evidence_effect.csv`, `metrics_by_source.csv`,
`ablation_summary.csv`, and `stage_e2_gate.json`. Large checkpoints/raw score
artifacts follow repository ignore policy; configs and lightweight summaries
must remain auditable.
