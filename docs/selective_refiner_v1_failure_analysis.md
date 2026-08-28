# Selective-refiner v1 failure analysis

Status: **FROZEN RETROSPECTIVE LEGACY121 DEVELOPMENT AUDIT**

This analysis reconstructs v1 from final fold/seed score files and normalized
Legacy121 records. It does not alter v1, train v2, or access external77.
Legacy121 was already used for development, so all findings below are
development evidence only.

## Independent reconstruction

The final tree contains 8 preregistered variants × 5 folds × 5 seeds = 200
configs, score files, and successful seed summaries, with zero final training
failures. Recomputed deletion and structure metrics reproduce the frozen
headline values to absolute error below `1e-12`.

Selective deployability was lower than training success: validation found a
threshold for 16/25 pooled source-aware and 20/25 pooled source-agnostic runs.
The frozen reported selective means condition on these deployable runs. The
LOMO deployable counts were RNAfold 15/25, PETfold 21/25, and trRosettaRNA2
17/25. The duplicated rows in the old `threshold_summary.csv` are a v1
summarizer artifact; directory-level unique run counts are used here and the
v1 file is not modified.

| Variant | Mode | Mod. precision | DELETE recall | Preservation | Macro ΔF1 | Micro ΔF1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Pooled source-aware | Ungated | 0.4830 | 0.7017 | 0.8494 | -0.0278 | -0.0277 |
| Pooled source-aware | Selective | 0.8754 | 0.4397 | 0.9881 | +0.0183 | +0.0239 |
| Pooled source-agnostic | Ungated | 0.4845 | 0.7028 | 0.8512 | -0.0258 | -0.0265 |
| Pooled source-agnostic | Selective | 0.8572 | 0.4284 | 0.9851 | +0.0185 | +0.0235 |

Selective gating clearly improved precision and preservation over threshold
0.50, but did not meet the frozen safety and cross-source gates.

## Exact development-gate failure

### A. Preservation

- Source-aware pooled preservation was 0.9880796 versus required 0.99,
  margin `-0.0019204`.
- Source-agnostic pooled preservation was 0.9850926 versus required 0.99,
  margin `-0.0049074`.
- Mean source preservations remained above the separate 0.98 floor. They were
  0.9894/0.9841/0.9907 for aware and 0.9859/0.9828/0.9865 for agnostic
  RNAfold/PETfold/trRosettaRNA2 results. Thus the failing condition was the
  stricter pooled target, with PETfold the lowest-preservation source.

### B. Per-source structure effect

The gate required positive macro and micro ΔF1 for at least two sources.
Only trRosettaRNA2 passed:

| Variant | Source | Macro ΔF1 | Micro ΔF1 | Both positive? |
| --- | --- | ---: | ---: | --- |
| Aware | RNAfold | -0.00268 | -0.00390 | no |
| Aware | PETfold | -0.00050 | -0.00162 | no |
| Aware | trRosettaRNA2 | +0.05806 | +0.07425 | yes |
| Agnostic | RNAfold | -0.00257 | -0.00458 | no |
| Agnostic | PETfold | -0.00043 | -0.00185 | no |
| Agnostic | trRosettaRNA2 | +0.05836 | +0.07450 | yes |

Observed qualifying-source count was 1 versus required 2, margin `-1 source`.

### C. LOMO transfer

The frozen model-agnostic transfer gate required every held-out source to have
modification precision at least 0.80, positive macro/micro ΔF1, and
preservation at least 0.98.

- Held-out RNAfold: precision 0.3144 (`-0.4856` margin), macro/micro ΔF1
  -0.00109/-0.00189; failed three criteria despite 0.9940 preservation.
- Held-out PETfold: precision 0.6594 (`-0.1406`), macro/micro ΔF1
  +0.00083/-0.00033; failed precision and micro effect.
- Held-out trRosettaRNA2: precision 0.9078, macro/micro ΔF1
  +0.03382/+0.04220, preservation 0.9832; passed the individual transfer gate.

RNAfold is therefore the hardest deletion/transfer source; trRosettaRNA2 is
the best-transferring source. v1 does not support model agnosticism.

## Source concentration of pooled gains

The complete distribution (mean, population SD, median, and range of
fold-level seed means) is in `v1_pooled_source_distribution.csv`. Key means
show strong source concentration:

| Variant/source | Mod. precision | DELETE recall | Preservation | Macro ΔF1 | Micro ΔF1 | Modified RNAs/run |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Aware/RNAfold | 0.269 | 0.020 | 0.989 | -0.0027 | -0.0039 | 2.50 |
| Aware/PETfold | 0.571 | 0.129 | 0.984 | -0.0005 | -0.0016 | 5.13 |
| Aware/trRosettaRNA2 | 0.961 | 0.735 | 0.991 | +0.0581 | +0.0742 | 20.31 |
| Agnostic/RNAfold | 0.329 | 0.036 | 0.986 | -0.0026 | -0.0046 | 2.85 |
| Agnostic/PETfold | 0.586 | 0.120 | 0.983 | -0.0004 | -0.0018 | 4.75 |
| Agnostic/trRosettaRNA2 | 0.945 | 0.737 | 0.986 | +0.0584 | +0.0745 | 20.25 |

Across deployable runs, trRosettaRNA2 supplied 90.7% of aware and 89.4% of
agnostic beneficial edit events. The pooled gain was therefore predominantly,
though not numerically exclusively, driven by trRosettaRNA2.

## Harmful deletions

`harmful_edit_feature_breakdown.csv` records beneficial and harmful edit-event
counts for both pooled variants by singleton, strict/two-pair stem, outer and
inner boundary, stem interior, pair type, raw/relative separation bins, and
stem length. Counts are fold-seed edit events, not unique biological pairs.

For source-aware selective inference, RNAfold had 22 beneficial versus 52
harmful events; 47/52 harmful events were strict-stem pairs and 43/52 were
outer or inner boundaries. PETfold had 82/77 beneficial/harmful; 73/77 harmful
events were strict-stem pairs and 52/77 were boundaries. trRosettaRNA2 had
1015/44, with harmful events distributed across strict stems (30) and
singletons (14). AU was the most frequent harmful pair type for aware RNAfold
and PETfold (26 and 31 events), but no pair-type rule is introduced from this
post-hoc observation. Separation and stem-length strata similarly show no
single topology-only stratum that safely repairs all three sources.

## Cross-model agreement enrichment

Cross-model features were computed using only the immutable three-source
predictions; GT labels were joined afterward. Exact support gave:

| Other-model support | Pairs | TP | FP | FP fraction | Correct fraction |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 504 | 80 | 424 | 0.8413 | 0.1587 |
| 1 | 586 | 216 | 370 | 0.6314 | 0.3686 |
| 2 | 4200 | 4101 | 99 | 0.0236 | 0.9764 |

The correct-pair probability increases monotonically for every source. Zero
support FP fractions are RNAfold 0.9375 (15/16), PETfold 1.0000 (23/23), and
trRosettaRNA2 0.8301 (386/465). Relative to each source's overall FP rate,
zero support enriches FPs by 7.21×, 7.07×, and 3.64×. The small RNAfold and
PETfold zero-support denominators are an important limitation; their larger
one-support groups still have FP fractions 0.621 and 0.658. No-support plus
partner conflict contains 212/272 FPs pooled; no-support singleton contains
61/74.

Classification: **CROSS_MODEL_SIGNAL_PROMISING**. The signal is strong,
monotonic, GT-free at inference, and directionally consistent across sources.
This classification authorizes a preregistered Legacy121 v2 development
experiment, not external evaluation or a claim that H2 is already proven.

## What v1 established—and did not

v1 established that observable topology features contain selective deletion
signal, that validation gating substantially improves risk control over
ungated inference, and that trRosettaRNA2 FPs are especially learnable. It did
not establish pooled 99% preservation, useful effects on two sources,
cross-model transfer, model agnosticism, or independent generalization.

The supported working claim remains limited to high-risk-pair identification.
Cross-model agreement is now a justified hypothesis for correction evidence;
transfer to an unseen predictor remains unsupported.
