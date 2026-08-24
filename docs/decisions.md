# Research Decisions

## Discussion — Target a CCF-A paper rather than only completing the assigned benchmark

### Decision

**Confirmed / 已确定**

把现有 RNA structure prediction benchmark 作为基础设施，同时发展一条可独立形成 CCF-A 投稿的研究线。

### Reason

仅执行 benchmark 对个人研究积累较单薄；需要一个独立科学问题和方法贡献。

### Alternatives Considered

- 只继续老师安排的 benchmark；
- 从零训练新的 RNA predictor；
- 开始完全无关的 AI4Science 方向。

### Consequence

新课题优先复用现有数据、prediction 和 evaluator，但必须形成独立 research question。

---

## Discussion — Do not use cross-family generalization benchmarking as the main topic

### Decision

**Confirmed / 已确定**

放弃“RNA secondary-structure generalization / family-split benchmark”作为主课题。

### Reason

文献搜索发现已有直接相关的 cross-family/generalization 研究；同时该方向被认为不够直观，不适合作为当前主线。

### Alternatives Considered

- random vs family split；
- sequence-identity ladder；
- OOD/reliability benchmark。

### Consequence

严格 split / leakage control 仍可作为 evaluation safeguard，但不再是 main paper question。

---

## Discussion — Select RNA secondary-structure refinement as the current direction

### Decision

**Confirmed / 已确定**

当前工作题目：

> **Evidence-Guided Selective Refinement for RNA Secondary Structure Prediction**

### Reason

方向直观、可直接复用当前 benchmark predictions、能先从 error analysis 得到中间结果，并且不要求从零训练大型 predictor。

### Alternatives Considered

- pseudoknot-only study；
- long-RNA study；
- predictor ensemble；
- interpretability；
- generalization benchmark。

### Consequence

当前第一科研任务是分析 prediction errors，而不是写最终网络。

---

## Discussion — Plain refinement is not sufficient as the intended CCF-A contribution

### Decision

**Confirmed / 已确定**

不把“generic neural refiner + small F1 gain”作为目标贡献。

### Reason

已存在 RNA post-processing 工作，包括讨论过的 ICML 2024 assignment-problem-based framework；普通 refiner 新颖性不足。

### Alternatives Considered

- simple Transformer Refiner；
- 纯 rule-based post-processing；
- 单一 predictor 的专用纠错器。

### Consequence

方法必须至少尝试在 selective correction、cross-predictor transfer、evidence guidance、downstream 3D value 中建立更强贡献。

---

## Discussion — Error analysis must precede model design

### Decision

**Confirmed / 已确定**

在训练主 Refiner 前，必须先完成 cross-model error taxonomy。

### Reason

Refiner 应由真实 error distribution 驱动，而不是先假设网络结构。

### Alternatives Considered

- 直接训练 predicted structure -> GT 的 Transformer；
- 只参考文献设计网络。

### Consequence

Phase 1 是 mandatory gate；第一项真正结果是 error summary，不是 neural model score。

---

## Discussion — Rule-based refinement is a required baseline

### Decision

**Confirmed / 已确定**

在 learned refiner 前实现 deterministic correction baseline。

### Reason

Learned method 必须证明价值超过 obvious structural cleanup / confidence thresholding。

### Alternatives Considered

- 跳过简单 baseline，直接上 neural refiner。

### Consequence

所有 learned refinement 结果都要和 Original + Rule-based 同时比较。

---

## Discussion — Use selective rather than unconditional refinement

### Decision

**Confirmed / 已确定 at concept level**

目标方法显式学习 keep / modify，而不是全结构重写。

### Reason

Source prediction 中大量结构可能本来正确；full rewrite 会引入 destructive edits。

### Alternatives Considered

- full re-prediction；
- unconditional structure translation。

### Consequence

计划加入 error detector / modification mask 和 preservation mechanism。

具体实现仍为 **Candidate / 待验证**。

---

## Discussion — Cross-predictor transfer is a key strengthening experiment

### Decision

**Confirmed / 已确定 as planned evaluation**

使用 leave-one-model-out 测试 Refiner 对未参与训练的 predictor 是否有效。

### Reason

若成功，说明模型学习的是更一般的 RNA prediction error pattern，而非单一 predictor bias。

### Alternatives Considered

- 每个 predictor 单独训练一个 refiner；
- 只在 seen predictor 上测试。

### Consequence

没有 unseen-model transfer 证据时，不得声称 model-agnostic。

---

## Discussion — Evidence guidance is part of the direction, but evidence source is not fixed

### Decision

**Confirmed / 已确定 at direction level**

研究 sparse/noisy structural evidence 对 refinement 的作用。

### Reason

Evidence guidance 比普通 post-processing 有更清晰的 AI4Science 问题：模型如何在不完整/不可靠结构证据与 source prediction 之间做选择。

### Alternatives Considered

- prediction-only refinement；
- hard constraints only。

### Consequence

Evidence 实验排在 selective + cross-model 之后。

具体 evidence 仍为 **Candidate / 待验证**：known pairs、unpaired positions、contacts/distances、SHAPE、DMS、NMR。

---

## Discussion — Treat 2D -> 3D validation as a candidate strengthening experiment

### Decision

**Confirmed / 已确定 as optional status**

3D downstream validation 不作为项目启动前提，而作为 2D Refiner 稳定后的 Candidate strengthening experiment。

### Reason

3D 验证价值高，但引入额外计算和 pipeline 复杂度；应该在 2D 方法有稳定 signal 后再做。

### Alternatives Considered

- 一开始就以 3D 为主课题；
- 完全不做 3D。

### Consequence

顺序固定为：

```text
2D error analysis
-> selective refinement
-> cross-model
-> evidence
-> Candidate 2D-to-3D validation
```

现有 DRfold-related workflow 是候选起点，但未最终锁定。

---

## Discussion — Benchmark work is infrastructure, not the main claimed contribution

### Decision

**Confirmed / 已确定**

以下内容是基础设施，不作为 main method contribution：

- predictor output normalization；
- shared metrics；
- 跑多个现有模型；
- 基础 benchmark tables。

### Reason

CCF-A 目标要求比简单比较 existing systems 更强的研究贡献。

### Consequence

Benchmark 用于支撑 error taxonomy、refinement 和 downstream validation。

---

## Discussion — CCF-A goal is fixed; specific venue is not

### Decision

**Confirmed / 已确定**

目标等级：CCF-A。

具体 venue 为 **Candidate / 待验证**。

### Reason

最终选择依赖结果形态：

- RNA-specific method + strong AI4Science validation：AAAI / KDD AI for Sciences 候选；
- 更一般的 structured refinement / optimization 方法：ICML / NeurIPS 候选；
- IJCAI 可作为其他候选。

### Consequence

当前不围绕某个 CFP 过早优化。方法稳定后再重新核对 classification、track、paper type、deadline。

---

## Discussion — Preserve a strict Go/No-Go execution order

### Decision

**Confirmed / 已确定**

固定顺序：

```text
Error Analysis
-> Rule-Based Baseline
-> Selective Refiner
-> Cross-Model Evaluation
-> Evidence Guidance
-> Full Ablation
-> Candidate 2D-to-3D Validation
```

### Reason

避免在 basic correction value 尚未验证时就把系统做得过大。

### Alternatives Considered

- 所有模块同时实现；
- 从 evidence 开始；
- 从 3D 开始。

### Consequence

Codex 不应因为后续阶段看起来更“新”就跳过前置 gate。
