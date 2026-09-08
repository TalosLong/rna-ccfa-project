# Phase II Protocol Freeze Manifest

Status: **`PHASE2_PROTOCOL_FREEZE_MANIFEST_COMPLETE`**

Protocol: **`PHASE2_DTP_V1.0`**

Freeze date: **2026-09-09 UTC**

Frozen base commit: **`27334a7a7146bb2d724b253149573edb89a8b8cb`**

Containing commit: **resolve with `git log -1 --format=%H -- docs/phase2_protocol_freeze_manifest.md`**

Hash algorithm: **SHA256 over exact UTF-8 file bytes**

## 1. Canonical document hashes

| Contract artifact | SHA256 |
| --- | --- |
| `docs/phase2_dataset_and_task_protocol.md` | `efb90e01a68da096781099d1ff4eae91dc2b7214434172f573b9c1cc172a77ef` |
| `docs/phase2_dataset_source_audit.md` | `033ddfc6e9816c2326e72aab46a58c9a849a625a798158cb99a6df55bc0815ae` |
| `docs/phase2_structured_decoder_protocol.md` | `a9d8caffe542fb2c465e918e82407406d5f28ba58b8f26168c7b164b2f133a9e` |
| `docs/phase2_risk_control_design.md` | `68bdbd3ffd89488c5a389b2a5498318673fa3592f27c07e523d581c8b3303915` |
| `docs/phase2_p3_minimal_baseline_implementation_plan.md` | `aa847112bf4b350b866805cf18a55a1275e7be3bd5b81f876fb0886393cb3cf4` |

## 2. Required semantic hashes

Section hashes use exact bytes beginning with the named `##` heading and
ending immediately before the next stated `##` boundary. A trailing newline is
included. They allow a reviewer to detect semantic-section changes even when
several contracts share one canonical file.

| Required item | Exact section range | SHA256 |
| --- | --- | --- |
| Dataset protocol hash | Complete `docs/phase2_dataset_and_task_protocol.md` | `efb90e01a68da096781099d1ff4eae91dc2b7214434172f573b9c1cc172a77ef` |
| Predictor panel hash | `## 7.` up to before `## 8.` | `647860298a79cd47fffdbfc0ff74a961538ab87a4cd8efe52142701d44b53518` |
| Structured task hash | `## 8.` up to before `## 13.` | `e4b6282493a704237813d22b2202086517987b84d4625744b93663cd747c6e4b` |
| Decoder hash | Complete `docs/phase2_structured_decoder_protocol.md` | `a9d8caffe542fb2c465e918e82407406d5f28ba58b8f26168c7b164b2f133a9e` |
| E0/transport evidence semantics hash | `## 13.` up to before `## 15.` | `753b5aeda01f738562607927a7dc04cb095fab18d20d43d1b1f2a55b51460471` |
| Risk protocol hash | Complete `docs/phase2_risk_control_design.md` | `68bdbd3ffd89488c5a389b2a5498318673fa3592f27c07e523d581c8b3303915` |
| Split/leakage policy hash | `## 3.` up to before `## 7.` | `c92d458af82509079394646238955428477266e8b366cf92343a8ee59e4cc01e` |
| Metric/gate hash | `## 16.` up to before `## 18.` | `9329b2c703fc299f47d256b135770733d00e4d3d09dc2d4d877fbbbac21b9c5f` |

## 3. Reproduction commands

```bash
sha256sum docs/phase2_dataset_and_task_protocol.md \
  docs/phase2_dataset_source_audit.md \
  docs/phase2_structured_decoder_protocol.md \
  docs/phase2_risk_control_design.md \
  docs/phase2_p3_minimal_baseline_implementation_plan.md

awk '/^## 7\./{f=1} /^## 8\./{f=0} f' \
  docs/phase2_dataset_and_task_protocol.md | sha256sum
awk '/^## 8\./{f=1} /^## 13\./{f=0} f' \
  docs/phase2_dataset_and_task_protocol.md | sha256sum
awk '/^## 13\./{f=1} /^## 15\./{f=0} f' \
  docs/phase2_dataset_and_task_protocol.md | sha256sum
awk '/^## 3\./{f=1} /^## 7\./{f=0} f' \
  docs/phase2_dataset_and_task_protocol.md | sha256sum
awk '/^## 16\./{f=1} /^## 18\./{f=0} f' \
  docs/phase2_dataset_and_task_protocol.md | sha256sum
```

## 4. Freeze assertions

```text
PHASE2_DATASET_AND_TASK_PROTOCOL_FROZEN
PHASE2_IMPLEMENTATION_NOT_AUTHORIZED
EXTERNAL77_LOCKED
LEGACY121 = PHASE1_HISTORICAL_DIAGNOSTIC_DATA
EXTERNAL77 = PHASE1_BRIDGE_INDEPENDENT_ASSET
INDEPENDENT_V2 = FUTURE_PHASE2_PRIMARY_ONE_SHOT_SET
```

No model/training/experiment/evidence/data-sample artifact is part of this
manifest. A mismatch requires a prospective `PHASE2_DTP_V1.x` amendment before
any outcome is observed; it cannot be repaired after a failed gate.
