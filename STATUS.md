# Current Status

Last updated: 2026-08-26

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
- [x] 完成当前本机模型资产盘点；确认 RNAfold、PETfold 和 trRosettaRNA2 native SS 为可运行的 Phase 0 2D 候选，并区分 downstream-only 3D 模型。
- [x] 完成现有 prediction outputs 的路径、格式、数量、覆盖范围和 provenance 盘点，未修改原始输出。
- [x] 冻结 normalized prediction schema v1：JSONL record、0-based canonical pairs、pair-score sidecar 和完整 provenance contract。
- [x] 实现 standard/extended dot-bracket、explicit pair list 和 dense pair matrix 到 canonical pairs 的 parser 与 validation，并以单元测试覆盖 crossing pairs 和 malformed inputs。
- [x] 实现 exact canonical-pair shared evaluator，输出 per-sample TP/FP/FN pair sets、counts、Precision、Recall 和 F1；完成 MCC negative-universe 审计并暂缓 MCC。
- [x] 冻结 Legacy121 v1 sample/ID protocol：121 个 primary sequence rows 全部具备 sequence、GT、三个历史 2D prediction 与 trRosettaRNA2 pair-score NPZ，并通过 canonical parser 和长度校验；两条 GT-only records 被保留但明确排除。

## Running / In Progress

- 当前 RNA structure prediction benchmark 工作。
- Git / Codex 项目上下文整理。
- Phase 0：canonical parser、validation、shared evaluator 和 Legacy121 v1 explicit manifest 已完成；下一项为从冻结 manifest 构建 normalized prediction records。

## Current Findings

暂无本项目已确认的 empirical finding。

此前讨论中出现的 F1、RMSD 示例数值均为说明用示例，不得视为实验结果。

## Blockers

- refinement 项目最终 dataset 列表未确定。
- external77 的 `GT_ALL` / `GT_CON` 目标语义及 4 个含 `N` 序列的处理规则尚未冻结。
- 第一版 3-5 个 source predictor 未确定。
- 目前只有 legacy 121 同时具备 RNAfold、PETfold 和 trRosettaRNA2 native SS 的完整历史 2D 输出；external77 缺少完整的三模型 2D prediction matrix，进入首轮多模型评测前需要按冻结协议重跑。
- 初始三个可运行 2D 候选中，现有 trRosettaRNA2 native SS 输出保留了 pair-score NPZ；RNAfold/PETfold 可在重跑时输出概率，但 legacy `.db` 未保留这些值。
- stem shift / truncation / extension 等 error definition 尚未锁定。
- final refiner architecture 未确定。
- real experimental evidence source 未确定。
- 最终 CCF-A venue 未确定。
- 3D validation subset 和 inference protocol 未确定。

## Immediate Next Steps

1. 从 `manifests/legacy121_v1.csv` 为 RNAfold、PETfold 和 trRosettaRNA2 native SS 的现有历史输出构建 normalized prediction records；不运行新的 predictor inference。

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
