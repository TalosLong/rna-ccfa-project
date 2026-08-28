# Cross-Model Refinement Phase Conclusion

Status: **CLOSED FOR THE CURRENT MAINLINE**

The Legacy121 cross-model development sequence is complete. Its immutable
decisions remain:

- v1 topology-only learned selective refinement: `DEVELOPMENT_GATE_FAIL`;
- v2 replacement CROSS classifier: `V2_DEVELOPMENT_GATE_FAIL`;
- v3 recalibrated consensus-veto primary condition:
  `V3_DEVELOPMENT_GATE_FAIL`.

No result is erased or reinterpreted as a pass. external77 was not evaluated
by any v1/v2/v3 learned or selective refinement condition.

## What the phase established

The observable v1 topology features contain a source-dependent FP-detection
signal, but did not satisfy the preregistered pooled preservation and
cross-source requirements. Adding cross-model features in v2 raised deletion
precision and preservation but made the classifier too conservative and left
only 8/25 primary global thresholds deployable. v3 then isolated exact
three-model consensus as a protection mechanism rather than a replacement
score.

That mechanism was strong on Legacy121 development data. Applying the frozen
`V3_VETO2_FIXED` veto to the authoritative v1 score prevented 211/282 harmful
BASE deletions (74.82%) while preventing only 18/1,571 beneficial deletions
(1.15%). Precision rose from 0.847814 to 0.956281, preservation from 0.987173
to 0.996771, and macro/micro delta F1 from +0.014761/+0.018770 to
+0.017160/+0.023046. The preregistered recalibrated v3 primary nevertheless
failed because threshold deployability was 22/25 and pooled preservation was
0.987946 rather than at least 0.99.

## Scientific value and boundary

The failed gates are useful: they separate three roles that should not be
conflated. A learned score can supply error-likelihood/recall information;
cross-model exact agreement can supply protection information; and
validation calibration can impose risk control. The phase also shows that
internal predictor agreement alone does not yet provide a gate-passing,
source-general refiner.

`V3_VETO2_FIXED` remains a development-only mechanistic baseline for future
comparisons. It is not a successful primary method, independent evidence, or
evidence of unseen-predictor transfer.

Further post-hoc v4/v5 rule or threshold tuning on the same Legacy121
predictions is not authorized as the current mainline. The project instead
moves to simulated external structural evidence, where the first question is
whether sparse information outside the three predictor outputs provides
benefit beyond direct enforcement. Legacy121 remains development data;
external77 remains locked.
