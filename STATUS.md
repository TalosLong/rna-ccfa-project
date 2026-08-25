# Current Status

Last updated: 2026-08-25

## Current Stage

**Confirmed / 已确定:** Project definition + Phase 0 setup.

当前论文方向：

> **Evidence-Guided Selective Refinement for RNA Secondary Structure Prediction**

现有 RNA benchmark 工作仍作为基础设施推进，但目前没有已确认的 refinement 实验结果。

## Completed

- [x] 明确目标：形成一篇 CCF-A 级别的 RNA / AI4Science 论文。
- [x] 放弃“generalization / family-split benchmark 作为主课题”的方案。
- [x] 选择 RNA secondary-structure prediction refinement 作为当前研究方向。
- [x] 明确普通 post-processing 或 generic Transformer Refiner + 小幅 F1 提升不足以作为目标贡献。
- [x] 确定当前方法概念的三条主线：Selective、Cross-Model / Model-Agnostic、Evidence-Guided。
- [x] 将 2D -> 3D downstream validation 定位为 Candidate strengthening experiment，而不是项目起点。
- [x] 确定执行顺序：error analysis -> rule baseline -> selective refiner -> cross-model -> evidence -> ablation -> optional 3D。

## Running / In Progress

- 当前 RNA structure prediction benchmark 工作。
- Git / Codex 项目上下文整理。
- Phase 0：盘点可直接复用的数据、predictor、prediction、ground truth 和 evaluator。

## Current Findings

暂无本项目已确认的 empirical finding。

此前讨论中出现的 F1、RMSD 示例数值均为说明用示例，不得视为实验结果。

## Blockers

- refinement 项目最终 dataset 列表未确定。
- legacy 2D 资产有 121 个主序列/预测记录但有 123 个 GT 文件，需先冻结 ID 映射和额外记录处理规则。
- external77 的 `GT_ALL` / `GT_CON` 目标语义及 4 个含 `N` 序列的处理规则尚未冻结。
- 第一版 3-5 个 source predictor 未确定。
- 各 predictor 是否提供 pair probability / confidence 尚未盘点。
- prediction / ground truth 尚未统一成一种 schema。
- stem shift / truncation / extension 等 error definition 尚未锁定。
- final refiner architecture 未确定。
- real experimental evidence source 未确定。
- 最终 CCF-A venue 未确定。
- 3D validation subset 和 inference protocol 未确定。

## Immediate Next Steps

1. Inventory 当前 benchmark repository：datasets、predictors、predictions、ground truths、pair confidence/logits。
2. 建立统一 secondary-structure parser，将所有支持格式转换为 canonical base-pair representation。
3. 建立 shared evaluator + pair-level error extractor，并先产出第一版 cross-model error summary，不训练 refiner。

## Open Questions

- 第一版选哪 3-5 个 predictor？
- 哪些 dataset 可以在统一结构表示下公平比较？
- 哪些 predictor 可以提供 pair probability / logits？
- stem-level error 的精确定义是什么？
- pseudoknot 是否纳入 refiner v1？
- rule-based baseline 应该做到什么强度？
- selective refiner v1 用什么最小架构？
- leave-one-model-out 能否真正提升 unseen predictor？
- 首个 evidence 版本用 simulated base-pair evidence，还是直接寻找真实 SHAPE/DMS/NMR？
- refined 2D 是否值得进入 downstream 3D 主实验？
- 最终更适合 AAAI/KDD AI for Sciences，还是方法更强后尝试 ICML/NeurIPS？
