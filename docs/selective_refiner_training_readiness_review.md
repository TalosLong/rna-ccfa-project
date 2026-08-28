# Selective-refiner training readiness review

**Status: NOT_READY**

The Legacy121 grouped five-fold file exists and its recorded checks pass:
same-RNA source records are co-located and no cross-fold global identity at or
above 0.80 was observed. The pair-feature MLP plan is explicit and uses only
inference-time observables; external77 is not read by training, preprocessing,
class weighting, early stopping, or threshold selection.

The independent test gate is not yet satisfied. RNAfold is valid for 42/42,
and the query-only trRosettaRNA2 native-SS source condition has been recovered
and run for the frozen external candidates. PETfold remains NONREPRODUCIBLE
under historical semantics because the Legacy121 alignment inputs and the
alignment-gap-to-ungapped-query projection are absent. Consequently no
126-record normalized matrix exists and training must not start.

Readiness can become `READY_FOR_FIRST_MLP_TRAINING` only after all 126 source
records pass schema-v1 validation, the PETfold source condition is either
recovered or explicitly replaced by a separately named new-source study, and
the resulting test manifest is immutable. This review does not authorize
training or any use of external77 labels for model decisions.
