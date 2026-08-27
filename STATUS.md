# Current Status

Last updated: 2026-08-27

## Current Stage

**Confirmed / 已确定:** Phase 0 complete; Phase 1 pair-level error analysis is next.

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
- [x] 完成 Legacy121 v1 normalization：从冻结 manifest 生成 363 条 schema-v1 records，363/363 有效；121 个 trRosettaRNA2 normalized pair-score sidecars 仅对副本执行 `set_diagonal_to_zero`，原始 NPZ 哈希保持不变，off-diagonal 最大绝对变化为 0。
- [x] 完成 Legacy121 v1 shared baseline evaluation：仅评估 363 条 normalized records 中的历史 `predicted_structure.pairs`，保存 per-sample metrics、精确 TP/FP/FN pair partitions 及 model-level macro/micro summaries；未使用 pair scores，未计算 MCC。
- [x] 完成 Legacy121 historical metric reproduction / mismatch audit：系统检索到 2 组历史指标资产，分类为 0 `COMPATIBLE`、1 `PARTIALLY_COMPATIBLE`、1 `INCOMPATIBLE`、0 `UNKNOWN`；未对不兼容数值作 reproduction-failure 判定。

## Running / In Progress

- 当前 RNA structure prediction benchmark 工作。
- Git / Codex 项目上下文整理。
- Phase 0 已完成：canonical parser、validation、shared evaluator、Legacy121 v1 explicit manifest、363 条 normalized prediction records、三个 source predictor 的 infrastructure baseline 及 historical metric mismatch audit 均已完成。
- Phase 1 尚未开始；下一项仅为 pair-level `missing_pair` / `false_positive_pair` / `wrong_partner` analysis。

## Current Findings

当前已确认的 empirical results 仅限以下 Phase 0 infrastructure audit 与
Legacy121 v1 baseline；尚无 refinement empirical finding。

Normalization infrastructure audit：363/363 records 有效；RNAfold、PETfold 和
trRosettaRNA2 native SS 各 121 条。仅 trRosettaRNA2 的 121 条 records
包含 pair scores。原始矩阵共有 5,038 个非零对角元素；normalized
sidecars 的对角线全部为零，且所有 off-diagonal 值逐元素保持不变。
这是表示层 normalization QA，不是 predictor 性能结果。

### Legacy121 v1 infrastructure baseline

使用 exact canonical base-pair equality 和共享的
`rna_ccfa.metrics.evaluate_pairs`，对每个 predictor 的 121 条历史结构输出进行评估。
Pair scores 未用于解码或评分；以下为 empirical Legacy121-v1 infrastructure
baseline，不是 refinement 结果或 paper-level performance claim。

| Predictor | Macro P | Macro R | Macro F1 | Micro P | Micro R | Micro F1 | TP | FP | FN | Median F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RNAfold | 0.906937 | 0.913867 | 0.905818 | 0.870053 | 0.878878 | 0.874443 | 1473 | 220 | 203 | 0.972973 |
| PETfold | 0.895256 | 0.907779 | 0.896849 | 0.858568 | 0.872912 | 0.865680 | 1463 | 241 | 213 | 0.947368 |
| trRosettaRNA2 native SS | 0.790564 | 0.912085 | 0.842871 | 0.771791 | 0.871718 | 0.818717 | 1461 | 432 | 215 | 0.909091 |

全部 363 条 records 的输入不变量、count identities、pair-partition 完整性和
metric finite/range checks 均通过。MCC 与 pseudoknot-specific metrics 仍按协议暂缓。

### Legacy121 historical metric audit

对 `/root/autodl-tmp` 内的历史脚本、结果表、日志和报告进行了系统的
read-only 检索。共识别 2 个需要审计的历史 metric source bundles：

- trRosettaRNA2 native threshold SS quality：`PARTIALLY_COMPATIBLE`。它对 119 条
  Legacy121 RNA 使用一致 GT 与 exact-pair scoring，但排除了 2 条长度超过
  150 nt 的 RNA，并将 raw NPZ 以 `>0.5` 阈值重新解码，而非评估冻结的历史
  DBN pairs。审计脚本精确复现了其 119 条 stored rounded P/R/F1
  数值；历史 MCC 仅作清单记录而未重算。这些数值与 shared baseline 的差异不被定义为
  reproduction failure。
- NMR-derived topology F1：`INCOMPATIBLE`。其 121 条成功的 single-chain IDs
  与 Legacy121 匹配，但 prediction 是 NMR-derived selected topology，不是 RNAfold、
  PETfold 或 trRosettaRNA2 native SS。

未发现真正 `COMPATIBLE` 的历史指标源，因此 compatible numerical comparisons 和
compatible mismatches 均为 0。详细证据、兼容性轴和未解项记录在
`docs/legacy121_metric_reproduction_audit.md`。冻结 shared evaluator 未修改，MCC 仍暂缓。

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

1. Phase 1 — Pair-level error analysis: `missing_pair` / `false_positive_pair` / `wrong_partner`.

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
