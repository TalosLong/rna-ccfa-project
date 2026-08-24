# RNA CCF-A Research Project Context

## Project Goal

**Confirmed / 已确定**

目标是在现有 RNA 结构预测 benchmark 工作基础上，形成一条可独立推进、具备 CCF-A 投稿潜力的研究线。

当前选定方向：

> **Evidence-Guided Selective Refinement for RNA Secondary Structure Prediction**

本项目不从零训练新的 RNA 二级结构预测器，而是研究：现有预测结果能否被选择性纠错、纠错是否能跨 predictor 泛化、稀疏/带噪结构证据是否能提高纠错可靠性，以及这些 2D 改进是否可能进一步改善下游 RNA 3D 预测。

CCF-A 是 **Confirmed / 已确定** 的投稿级别目标；具体会议尚未最终确定。

## Research Background

**Confirmed / 已确定**

当前工作主线是协助完成 RNA 结构预测 benchmark。现有 benchmark 可为本项目提供：

- RNA sequence；
- ground-truth secondary structure；
- 多个已有 predictor 的 prediction；
- 统一评测需求；
- 与 DRfold 相关的 2D -> 3D 下游验证基础。

因此，refinement 方向可以直接复用当前工作资产，不需要重新搭建一套完全独立的数据和模型体系。

## Current Scientific Question

**Confirmed / 已确定**

核心科学问题：

> Can errors in RNA secondary-structure predictions from existing predictors be detected and selectively corrected without re-predicting the whole structure, and can sparse or noisy structural evidence make this refinement more reliable?

拆分为：

1. 现有 RNA 二级结构预测模型主要会犯哪些错误？
2. 能否判断哪些 pair / region 应该保留，哪些应该修改？
3. 一个 refiner 能否用于多个 predictor，并对未见过的 predictor 有效？
4. 稀疏或带噪的结构证据能否进一步指导 refinement？
5. **Candidate / 待验证：** refined 2D 是否能改善 downstream RNA 3D prediction？

## Motivation

**Confirmed / 已确定**

普通“prediction -> generic refiner -> F1 小幅提升”的故事不够强，且 RNA post-processing 已有公开研究。因此本项目强调：

- **Selective**：正确部分尽量不动；
- **Model-Agnostic / Universal**：尽可能跨 predictor；
- **Evidence-Guided**：支持稀疏/带噪结构证据；
- **Candidate**：验证 2D refinement 的 3D downstream value。

目标流程：

```text
RNA sequence
    +
source prediction
    +
optional prediction confidence
    +
optional sparse/noisy evidence
                |
                v
       selective error detection
                |
          keep / modify
                |
                v
       constrained refinement
                |
                v
      refined RNA structure
```

## Existing Work

**Confirmed / 已确定 from discussion**

已讨论的相关工作包括：

- ICML 2024 的 RNA secondary-structure post-processing / assignment-problem framework；
- RFold：structured matching 形式的 RNA secondary-structure prediction；
- PriFold：引入 RNA-specific priors；
- BEACON：RNA benchmark 作为独立研究贡献的案例；
- DRfold 等 RNA 3D predictor：说明 secondary structure 可以作为 3D 结构预测的重要输入/先验。

因此：

> 单纯实现一个普通 Transformer Refiner 并报告少量 F1 增益，不应作为本项目的最终论文贡献。

## Proposed Direction

### Confirmed Core Direction

**Evidence-Guided Selective Refinement for RNA Secondary Structure Prediction**

目标属性：

1. **Selective**
   - 检测可能错误的 pair / region；
   - 尽量保留已经正确的结构。

2. **Model-Agnostic / Universal**
   - 使用多个 predictor 的 prediction 训练；
   - 通过 leave-one-model-out 测试是否能修复未见过的 predictor。

3. **Evidence-Guided**
   - 接收可选的 sparse structural evidence；
   - 在 evidence 不完整或有噪声时学习 prediction 与 evidence 的信任关系。

### Candidate Extension

**Candidate / 待验证：Downstream-aware 2D -> 3D validation**

```text
Original 2D -> 3D predictor -> 3D structure
Refined 2D  -> 3D predictor -> 3D structure
GT 2D       -> 3D predictor -> 3D structure
```

## Dataset / Benchmark

### Confirmed Requirements

项目优先复用当前 benchmark 数据和预测结果。

每个样本最终需要规范化为：

```text
RNA ID
sequence
ground-truth secondary structure
source predictor
predicted secondary structure
optional pair probability / confidence
metadata when available
```

### Not Yet Fixed

**Candidate / 待验证**

- 具体 dataset 列表尚未锁定；
- 第一版 source predictor 数量建议 3-5 个；
- 完整论文阶段可扩展到 2-3 个 dataset；
- 是否第一版就纳入 pseudoknot 取决于数据和 evaluator 是否能统一处理。

## Current Pipeline

```text
existing benchmark
    -> collect predictions
    -> normalize formats
    -> structure representation -> base-pair list
    -> shared evaluator
    -> pair/stem-level error extraction
    -> error taxonomy
    -> rule-based baseline
    -> selective ML refiner
    -> cross-model evaluation
    -> evidence-guided refinement
    -> full ablation
    -> Candidate: 2D -> 3D validation
```

当前没有已确认的 refinement 实验结果。第一阶段目标是建立可复现的 error-analysis 与 evaluation pipeline，而不是立即训练模型。

## Candidate Method

**Candidate / 待验证**

### 1. Error Detector

输入可包含：

- RNA sequence context；
- predicted structure；
- candidate pair positions；
- pair probability / confidence（若可获得）；
- local structural context。

初始输出：

```text
correct / incorrect
```

### 2. Modification Mask

对 pair / structural element 预测是否需要修改：

```text
M(i, j) in [0, 1]
```

### 3. Refined Pair Scores + Constrained Decoding

Refiner 输出 corrected pair scores，再通过 constrained decoder 得到合法 secondary structure。

具体网络结构尚未确定。Transformer 只是 Candidate，不是既定方案。

### 4. Preservation Objective

**Candidate / 待验证**

目标是避免破坏原本正确的 pair。候选形式：

```text
L = L_structure
  + lambda * L_preserve
  + beta * L_error_detection
```

具体 loss 和权重尚未确定。

## Evaluation Strategy

### Core Metrics

**Confirmed / 已确定**

- Precision
- Recall
- F1
- MCC（若当前结构表示支持一致定义）
- pair-level TP / FP / FN

### Error-Specific Analysis

**Confirmed / 已确定**

需要分析：

- missing pair；
- false-positive pair；
- wrong partner；
- stem-level error；
- long-range pair error；
- pseudoknot-related error（前提是表示和 evaluator 一致）。

候选 stem taxonomy：

- missing stem；
- stem truncation；
- stem extension；
- stem shift；
- wrong-partner stem。

具体定义必须在报告结果前固定。

### Cross-Model Evaluation

**Confirmed / 已确定 as planned experiment**

```text
train refiner on A + B + C
hold out D
evaluate on D
```

如果 transfer 失败，不得继续声称 model-agnostic。

### Evidence-Guided Evaluation

**Candidate / 待验证**

候选 evidence density：

```text
0%, 1%, 5%, 10%, 20%, 50%
```

候选 noise level：

```text
5%, 10%, 20%, 30%
```

讨论过的 evidence 类型：

- known base pairs；
- known unpaired nucleotides；
- contact / distance constraints；
- SHAPE；
- DMS；
- NMR。

目前没有确定真实实验数据源。

### Candidate 3D Metrics

- RMSD
- TM-score
- lDDT

最终使用哪些取决于 3D predictor 和数据。

## Expected Contributions

以下均为 **Candidate / 待验证**，只有实验支持后才能写成论文 claim：

1. 多 predictor 的 RNA secondary-structure prediction error taxonomy；
2. selective refinement：显式避免修改已经正确的结构；
3. model-agnostic refinement：跨 predictor transfer；
4. sparse/noisy evidence-aware refinement；
5. downstream 2D -> 3D benefit。

Benchmark normalization 和简单多模型对比只是基础设施，不作为主要贡献。

## Known Risks

1. 不同 predictor 的错误分布可能差异太大，Universal Refiner 难以成立。
2. 并非所有 predictor 都提供 pair probability / logits。
3. Refiner 可能只改善弱模型，却破坏强模型。
4. Rule-based baseline 可能已经覆盖大部分可修复收益。
5. 2D F1 改善未必带来 3D 改善。
6. Simulated evidence 可能无法代表真实实验数据。
7. Pseudoknot 在不同工具/数据中的表示可能不一致。
8. Refiner train/test 必须严格避免 sample leakage。
9. 最终 CCF-A venue 与 deadline 尚未锁定。
10. 如果最终只有小幅 aggregate F1 gain，而没有 cross-model / evidence / downstream 价值，论文强度可能不足。

## Important Constraints

**Confirmed / 已确定**

- 不虚构实验结果。
- 不把 benchmark-only 工作包装成主要贡献。
- 不从大型新 predictor / foundation model 开始。
- 先做 error analysis，再设计最终 refiner。
- 所有 source predictor 使用同一个 evaluator。
- 保存 raw prediction、normalized prediction 和 per-sample result。
- 控制 refiner 数据泄漏。
- 每个阶段先得到可复现 signal，再进入下一阶段。

固定执行顺序：

```text
Error Analysis
-> Rule-Based Baseline
-> Selective Refiner
-> Cross-Model Evaluation
-> Evidence Guidance
-> Full Ablation
-> Candidate 2D-to-3D Validation
```
