# RNA CCF-A Research Project Context

Last updated: 2026-08-31

## Project Goal

**Confirmed / 已确定**

目标是在现有 RNA structure-prediction benchmark 基础上，形成一条具备 CCF-A 投稿潜力的独立研究线。

当前工作题目：

> **Post-hoc Evidence Reconciliation for RNA Secondary Structure Predictions**

项目不从零训练新的 RNA 二级结构 predictor。核心对象是已有 predictor 已经输出的结构，以及如何利用稀疏外部结构证据对其 residual errors 做可靠性估计和选择性纠错，同时尽可能保留原 prediction 中已经正确的结构信息。

CCF-A 是目标级别；具体 venue 尚未冻结。

## Reboot v2 Scientific Question

**Confirmed / 已确定**

> Given an RNA sequence, an already-computed secondary-structure prediction from an existing predictor, and sparse external structural evidence, can a post-hoc method identify and selectively correct residual pair errors while preserving predictor information that is already correct?

关键对比不再只是 `Original vs Refined`，而是：

```text
Original predictor
vs
local evidence enforcement
vs
global evidence-constrained refolding
vs
post-hoc evidence reconciliation
```

因此项目必须回答：

> **为什么不直接在同样 evidence 下重新 fold？保留已有 predictor output 是否有独立价值？**

## Research Questions

1. **RQ1 — Post-hoc necessity**：原 predictor 中是否包含 global constrained refolding 会丢失或覆盖的正确信息？
2. **RQ2 — Safe residual-error correction**：sparse evidence 能否在高 TP preservation 下提高 FP removal？
3. **RQ3 — Useful non-local propagation**：非直接 evidence 区域的变化是否真正 beneficial，而非 collateral damage？
4. **RQ4 — Generalization**：reliability/correction signal 能否跨 RNA、跨 predictor、跨 dataset 保持？
5. **RQ5 — Noise and reality**：controlled noisy evidence 和真实 SHAPE/DMS/PARS 等 evidence 下是否仍有价值？
6. **Candidate**：若 2D 方法稳定，进一步测试 2D improvement 是否改善 downstream RNA 3D prediction。

## Task Definition

对 sequence `x`、原始 predicted pair set `S`、外部 evidence set `E`，以及一个 original predicted pair `p=(i,j) in S`，目标是估计：

```text
q_ij = P(p is incorrect | x, S, E)
```

Primary edit space：

- `KEEP`；
- `DELETE`；
- `ABSTAIN`。

第一版不做：

- 添加 absent pair；
- partner reassignment；
- recursive stem reconstruction；
- 创建新 pair 的全局 decoder。

这样保持任务是 post-hoc quality control，而不是重新训练一个 secondary-structure predictor。

## Prior-Art Boundary

**Confirmed / 已确定 for current planning**

以下内容不能单独作为 novelty claim：

- canonical pairing / stem / stacking 等基础 RNA 结构规则；
- isolated-pair / short-stem cleanup；
- thermodynamic base-pair probability / confidence；
- thermodynamic + evolutionary evidence fusion；
- multi-predictor consensus；
- evidence-constrained global folding；
- generic post-hoc pair-level quality assessment 这一抽象范式。

候选 novelty boundary 是：

> **Predictor-output-preserving evidence reconciliation for RNA secondary-structure predictions**：把已有 predictor output 本身视为需要保留和校准的信息源，与 sparse external evidence 做 post-hoc reconciliation，而不是完全从 sequence + evidence 重新 fold。

是否可以进一步称为 `model-agnostic`、`unseen-predictor transferable`、`real-evidence robust`，必须由实验支持。

## Existing Development Evidence

历史结果全部保留，不重新解释：

- Phase 0 normalization/evaluator infrastructure：完成；
- Phase 1 pair/stem/separation error analysis：完成；
- rule baseline：完成；
- selective-refiner v1：`DEVELOPMENT_GATE_FAIL`；
- selective-refiner v2：`V2_DEVELOPMENT_GATE_FAIL`；
- selective-refiner v3 primary：`V3_DEVELOPMENT_GATE_FAIL`；
- prediction-only cross-model mainline：已关闭，不允许用 Legacy121 做 post-hoc v4/v5 rescue tuning；
- simulated clean evidence Stage E1：完成，证明 direct/local utility，但 `NON_EVIDENCED_EFFECT == 0`；
- historical Stage E2 protocol：已冻结但 **未训练，并被 Reboot v2 在训练前 supersede**；
- external77 three-source protocol：PASS，42 RNA x 3 sources = 126/126 normalized records，继续锁定为 independent test。

## Data Roles

### Legacy121 v1

**Development only**：用于 baseline、architecture、calibration、threshold、ablation、simulated evidence 和 Go/No-Go。

### external77-derived 42-RNA set

**Locked independent test**：RNAfold、PETfold、trRosettaRNA2 native SS 均 42/42 valid；126/126 normalized records 已准备完成。在 final development protocol 冻结前不得用于 feature/threshold/model selection。

## Evidence Ladder

### E0 — Clean symbolic evidence

- known positive pair；
- known unpaired nucleotide。

仅用于 mechanism / upper-bound development。

### E1 — Controlled noisy symbolic evidence

使用冻结的 corruption mechanism 和 candidate noise levels，测试 robustness 和 trust/reconciliation necessity。

### E2 — Real experimental evidence

候选包括 SHAPE、DMS、PARS 等。真实 probing signal 是 probabilistic evidence，不是 ground truth；必须单独做 dataset/provenance audit。

## Required Baselines

- **B0 Original**：原 predictor output，不修改。
- **B1 Local Hard Evidence**：已完成的 Stage E1 local hard transformations。
- **B2 Global Evidence-Constrained Refolding**：**新的 mandatory baseline**；使用同样 sequence + delivered evidence，通过可复现的 ViennaRNA/RNAfold constraint protocol 全局重新 fold。
- **B3 Prediction-Only Reliability Baselines**：rule、v1 topology score、v3 fixed consensus veto、可比的 BPP/consensus 等。
- **B4 Evidence-Masked Learned Control**：同 architecture/checkpoint 条件下屏蔽 evidence，验证增益是否来自 evidence。

## Evaluation Principles

### Pair reliability

优先：AUPRC、Brier score、ECE、reliability diagram；AUROC 为辅助。

### Refinement utility

必须报告：

```text
TP_preservation = TP_after / TP_before
FP_removal = (FP_before - FP_after) / FP_before
modification_precision = beneficial_edits / modified_pairs
```

同时保留 Precision、Recall、macro/micro F1、edit counts、beneficial/harmful accounting。

### Risk–utility

主要比较不是单一 `Delta F1`，而是 risk–utility trade-off，例如：

```text
x-axis: TP loss / 1 - TP preservation
y-axis: FP removal
```

### Non-evidenced effect

分别报告 non-evidenced modification precision、FP removal、TP loss。问题不是“是否传播”，而是传播是否有益。

### Evidence efficiency

报告 `FP_removed / evidence_items`、`Delta_F1 / evidence_items` 等。

### Matching robustness

历史与 primary metric 继续使用 exact canonical pair equality；最终 paper-level evaluation 额外加入 +/-1 endpoint flexible matching robustness，不改写历史 exact 结果。

## Reboot Roadmap

```text
R0 Literature & novelty freeze        COMPLETE
R1 Task/protocol redefinition         COMPLETE
R2 Global constrained-refolding       COMPLETE
R3 Reliability baseline suite
R4 Clean learned evidence reconciliation
R5 Noise robustness
R6 Cross-predictor transfer / LOMO
R7 Locked external77 independent test
R8 Real evidence
R9 Final calibrated selective correction
Optional 2D -> 3D validation
```

## Go / No-Go

- **Gate A — Post-hoc necessity**：若 global constrained refolding 在 preservation/FP-removal trade-off 上全面支配 post-hoc 方法，停止 post-hoc mainline。
- **Gate B — Learned utility**：在 prospectively frozen high-preservation operating point（当前目标 `TP_preservation >= 0.99`）下，learned method 必须优于 strongest frozen non-learned baseline，且不能只依赖单一 source。
- **Gate C — Noise robustness**：若 5–10% controlled noise 即导致负 structure utility 或不可接受 TP loss，不进入 real-evidence claim，除非先冻结新的 trust mechanism。
- **Gate D — Independent generalization**：external77 只打开一次；若 development effect 不能保持方向，不得在 external77 上调参救结果。

## Immediate Constraint

**Do not train historical Stage E2.**

R2 v1.0.2 已前瞻性冻结 crossing 与 minimum-loop capability eligibility。
amended universe 为 7,153 个 realization（pair 3,523；unpaired 3,630），
全部通过 provenance、parser、validity 与 constraint 检查。正式 B0/B1/B2
analysis 已完成；B2 overall Macro/Micro F1 为 0.924648/0.904747，B1 为
0.889352/0.872422，B0 为 0.878635/0.861068。

下一项任务是：

> **解释已完成的 R2 comparator，并前瞻性冻结 R3 reliability-baseline
> protocol；不要自动启动 R3 implementation。**

R2、R3 冻结并完成后，才允许冻结新的 R4 learned protocol。

详细 reboot specification 见 `docs/project_reboot_v2.md`。
