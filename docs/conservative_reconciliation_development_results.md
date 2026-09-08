# Conservative Evidence Reconciliation development results

Status: `CONSERVATIVE_DEV_GATE_FAIL`

Legacy121 role: `DEVELOPMENT_ONLY` (not independent confirmation).

## EMPIRICAL RESULT

The frozen 200-run CER/CCEG matrix, 200 branch calibrations, 100 policy calibrations, and 100 threshold seals completed. All five prescribed seeds contribute; no seed or channel was selected.

| Condition | Track | event AUPRC | RNA AUPRC | event TP pres. | RNA TP pres. | event FP removal | RNA FP removal | event mod. precision | RNA delta F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CER | positive_pair | 0.791080 | 0.896231 | 0.992479 | 0.993221 | 0.465827 | 0.663897 | 0.918815 | 0.028315 |
| CER | unpaired | 0.782007 | 0.886754 | 0.990715 | 0.992703 | 0.484099 | 0.700656 | 0.914063 | 0.031077 |
| CER | combined | 0.785956 | 0.887721 | 0.991586 | 0.992930 | 0.475575 | 0.682200 | 0.916103 | 0.029648 |
| CER_EVIDENCE_MASKED | positive_pair | 0.771408 | 0.891472 | 0.992380 | 0.993514 | 0.399240 | 0.626081 | 0.905578 | 0.025309 |
| CER_EVIDENCE_MASKED | unpaired | 0.773384 | 0.889141 | 0.991403 | 0.993573 | 0.375588 | 0.604421 | 0.899350 | 0.024273 |
| CER_EVIDENCE_MASKED | combined | 0.771726 | 0.884302 | 0.991886 | 0.993570 | 0.386622 | 0.615236 | 0.902350 | 0.024784 |

Combined reliability details:

| Condition | level | AUPRC | AUROC | Brier | ECE |
| --- | --- | ---: | ---: | ---: | ---: |
| CER | event | 0.785956 | 0.921983 | 0.064995 | 0.022584 |
| CER | rna | 0.887721 | 0.928589 | 0.056824 | 0.090896 |
| CER_EVIDENCE_MASKED | event | 0.771726 | 0.915677 | 0.067810 | 0.024127 |
| CER_EVIDENCE_MASKED | rna | 0.884302 | 0.921939 | 0.059538 | 0.097619 |

Fixed reliability bins are retained in the evaluation artifacts. Utility artifacts include coverage, complete beneficial/harmful edit accounting, precision, recall, F1, and delta F1.

### Actions and scopes (combined Track E, five-seed means)

| Condition | KEEP | DELETE | ABSTAIN | outside-explicit delete fraction |
| --- | ---: | ---: | ---: | ---: |
| CER | 277536.8 | 26073.8 | 7227.4 | 0.770451 |
| CER_EVIDENCE_MASKED | 289309.0 | 21529.0 | 0.0 | 0.884573 |

| Condition | Scope | event TP pres. | RNA TP pres. | event mod. precision | mean lost TP |
| --- | --- | ---: | ---: | ---: | ---: |
| CER | DIRECT | 1.000000 | 1.000000 | N/A | 0.0 |
| CER | LOCAL_CONFLICT | N/A | N/A | 1.000000 | 0.0 |
| CER | NON_EVIDENCED | 0.990864 | 0.992543 | 0.891170 | 2192.8 |
| CER_EVIDENCE_MASKED | DIRECT | 0.994022 | 0.992551 | 0.000000 | 123.2 |
| CER_EVIDENCE_MASKED | LOCAL_CONFLICT | N/A | N/A | 1.000000 | 0.0 |
| CER_EVIDENCE_MASKED | NON_EVIDENCED | 0.991702 | 0.993584 | 0.896084 | 1991.6 |

The primary combined five-seed means were event/RNA TP preservation 0.991586314/0.992930425 and event/RNA FP removal 0.475575027/0.682200011. NON_EVIDENCED TP preservation was 0.990863828/0.992542949, with mean lost TP 2192.8, below the descriptive frozen R4 value 2687.8.

### Evidence attribution and R4 gain retention

The matched evidence-masked FP-removal means were 0.386621527 (event) and 0.615236069 (RNA-balanced). Thus G_event=0.088953500 and G_RNA=0.066963942. Relative to frozen R4 ERN-minus-B4 increments, the retained fractions were 1.000493 and 1.469486.

| Source | CER RNA FP removal | masked RNA FP removal | P3 RNA FP removal | CER−P3 | CER−masked |
| --- | ---: | ---: | ---: | ---: | ---: |
| rnafold | 0.255911 | 0.116483 | 0.013109 | 0.242802 | 0.139428 |
| petfold | 0.315454 | 0.191609 | 0.099320 | 0.216134 | 0.123845 |
| trrosettarna2_native_ss | 0.799780 | 0.752038 | 0.630129 | 0.169651 | 0.047741 |

CER improved RNA-balanced FP removal over P3 and over its matched evidence-masked control in all three current predictor sources. This is development evidence only and does not establish unseen-predictor transfer.

### Frozen comparator context

| Frozen comparator | event TP pres. | RNA TP pres. | event FP removal | RNA FP removal |
| --- | ---: | ---: | ---: | ---: |
| E1 LOCAL_CONFLICT | 1.000000 | 1.000000 | 0.119048 | 0.142946 |
| P3 V3_VETO2_FIXED | 0.996771 | 0.997588 | 0.347816 | 0.489748 |
| R4 ERN | 0.989682 | 0.991936 | 0.475531 | 0.660806 |
| B2 FULL_REFOLD_REFERENCE | 0.981767 | 0.975358 | 0.645883 | 0.775728 |

CER exceeded E1 and P3 FP removal in both aggregations while preserving less TP than either comparator. Relative to R4 ERN, CER moved above the event 0.99 preservation line while retaining similar event FP removal and higher RNA-balanced FP removal; this is post-R4 development evidence, not an independent rescue of R4. B2 removed more FP but preserved materially less TP and operates by full refolding, so the existing bounded Gate A non-dominance decision is unchanged.

## INTERPRETATION

The conservative policy achieved both overall 0.99 preservation bars and retained the evidence-attributable FP-removal increment. However, the central hypothesis required usable evidence not to reduce NON_EVIDENCED TP preservation relative to the matched masked action mechanism. CER was lower than the masked control under both event and RNA aggregation, so the conjunctive development gate fails even though CER's absolute NON_EVIDENCED preservation remained at least 0.99. The evidence benefit therefore came with evidence-attributable NON_EVIDENCED harm under the prospectively frozen comparison.

Legacy121 is internal development/hypothesis-generation data. These results do not restore independence. B2 remains a different FULL_REFOLD_REFERENCE operating space; R4 Gate A remains boundedly non-dominated and R4 Gate B remains failed.

## GATE DECISION

The one frozen conjunctive decision is `CONSERVATIVE_DEV_GATE_FAIL`:

- `event_tp_preservation_gte_0_99`: **PASS**
- `rna_tp_preservation_gte_0_99`: **PASS**
- `event_fp_removal_gt_0_347816`: **PASS**
- `rna_fp_removal_gt_0_489748`: **PASS**
- `event_non_evidenced_tp_preservation_gte_0_99`: **PASS**
- `rna_non_evidenced_tp_preservation_gte_0_99`: **PASS**
- `event_non_evidenced_preservation_gte_masked`: **FAIL**
- `rna_non_evidenced_preservation_gte_masked`: **FAIL**
- `mean_non_evidenced_lost_tp_lt_2687_8`: **PASS**
- `g_event_gt_0`: **PASS**
- `g_rna_gt_0`: **PASS**
- `source_wise_positive_2_of_3_including_rnafold_or_petfold`: **PASS**
- `event_r4_gain_retention_gt_0_50`: **PASS**
- `rna_r4_gain_retention_gt_0_50`: **PASS**
- `p3_source_condition`: **PASS**

The two failures are `event_non_evidenced_preservation_gte_masked` and `rna_non_evidenced_preservation_gte_masked`. All other numerical, source, attribution, and gain-retention conditions passed. Per the frozen protocol, the next authorized task is `PAPER_STORY_AND_RESULTS_CONSOLIDATION`; no alternative CCEG, larger model, threshold rescue, or seed/channel selection is authorized. `R4_GATE_B_FAIL` remains unchanged.

## UNSUPPORTED CLAIMS

This experiment does not establish independent generalization, unseen-predictor/model-agnostic performance, noisy-evidence robustness, real SHAPE/DMS/PARS utility, 3D benefit, or that threshold/model rescue would succeed. external77 data were not read or used.
