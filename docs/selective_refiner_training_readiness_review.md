# Selective-refiner training readiness review

**Status: READY_FOR_FIRST_MLP_TRAINING**

The Legacy121 grouped five-fold file exists and its recorded checks pass:
same-RNA source records are co-located and no cross-fold global identity at or
above 0.80 was observed. The pair-feature MLP plan is explicit and uses only
inference-time observables; external77 is not read by training, preprocessing,
class weighting, early stopping, or threshold selection.

The independent test gate is satisfied. PETfold reproduces the historical
single-sequence condition exactly for 121/121 Legacy121 RNAs. RNAfold, PETfold,
and trRosettaRNA2 native SS are each valid for 42/42 external RNAs, and the
normalized external matrix contains 126/126 records.

The frozen Legacy121 grouped-CV checks pass: deterministic five-fold
assignment, same-RNA source co-location, no identity-connected component
crossing partitions, input-only features, train-only normalization and class
weights, and validation-only threshold selection. The external77 manifest is
immutable and was not used for fitting, tuning, normalization statistics, class
weights, or threshold selection. This status authorizes the next task to begin
first MLP training; no training was performed here.
