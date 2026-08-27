# Current Status

Last updated: 2026-08-27

## Current Stage

**Confirmed / 已确定:** Phase 0 complete; Phase 1 mainline error analysis and consolidation complete for Legacy121 v1. Pseudoknot-aware analysis is deferred to a separate PK-capable predictor side track. The Phase 2 minimal rule-based baseline specification is frozen; implementation and evaluation have not started.

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
- [x] 冻结 Phase 1 pair-level error taxonomy 并完成 Legacy121 抽取：`missing_pair` 与 `false_positive_pair` 严格等于 shared evaluator 的 FN/FP partitions，`wrong_partner` 作为共享端点的关系型注释，不是第三个互斥 metric partition。
- [x] 冻结 strict stacked-stem definition v1 并完成 Legacy121 descriptive inventory：仅连接直接相邻的 `(i+1,j-1)` pairs，最小 stem 长度为 2，singleton pairs 单独保留。
- [x] 冻结并实现 deterministic stem matching/error taxonomy v1：一对一候选匹配、歧义 component gate、exact/truncation/extension/shift/complex/missing/unmatched 状态及可审计阈值均已记录并在 Legacy121 上完成描述性抽取。
- [x] 完成 Legacy121 v1 pair sequence-separation analysis：从 121 个唯一 GT structures 冻结 relative-separation Q25/Q50/Q75/Q90 bins，保留 raw separation 作为次级变量，并完成 pair、wrong-partner 与 stem-state linkage 描述性汇总。
- [x] 完成 Phase 1 Error Analysis Consolidation：pair/stem/separation units 分开归一化汇总，生成 per-model/per-dataset/top/shared pattern tables、Phase 1 scientific summary、claim-evidence map 和 Phase 2 target priorities；未定义或执行任何结构编辑。
- [x] 冻结 Phase 2 minimal rule-based baseline v1：primary rules 仅使用 sequence + original predicted pair/stem/singleton features，预注册 R1 singleton deletion、R2 two-pair-stem cleanup、R3 narrow outer-terminal trimming 及两个有科学目的的组合；未实现或评估 edits。

## Running / In Progress

- 当前 RNA structure prediction benchmark 工作。
- Git / Codex 项目上下文整理。
- Phase 0 已完成：canonical parser、validation、shared evaluator、Legacy121 v1 explicit manifest、363 条 normalized prediction records、三个 source predictor 的 infrastructure baseline 及 historical metric mismatch audit 均已完成。
- Phase 1 当前主线已完成：pair-level `missing_pair` / `false_positive_pair` / `wrong_partner` taxonomy、extraction、Legacy121 descriptive counts 与 consolidation 均已完成。
- Phase 1 strict-stem infrastructure、stem matching/error extraction、data-driven long-range analysis 与 consolidation 已完成。
- Phase 1 stem matching protocol 已冻结并实现；Legacy121 候选审计显示 chosen filter 有 871 条 candidate edges、11 个潜在 shift candidates（其中 10 个 isolated、1 个 ambiguous）；greedy 与 maximum-weight assignment 在 363 条 records 上选择一致，但歧义 components 不被强制匹配。
- Phase 2 specification 已冻结，rule implementation 与 Legacy121 pilot evaluation 尚未开始。
- Pseudoknot-aware refinement 已从当前主线移至 future side track；该分支需要显式输出 crossing pairs 的 predictor，现有 PK inventory 保留不变。

## Current Findings

当前已确认的 empirical results 仅限以下 Phase 0 infrastructure audit、
Legacy121 v1 baseline 与 Phase 1 pair/stem-level descriptive counts；尚无 refinement empirical finding。

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

### Legacy121 v1 pair-level error counts

`missing_pair` 与 `false_positive_pair` 分别保持原 FN/FP 计数。
`wrong_partner` 仅标注 FP 与 FN 之间的共享端点关系；degree 为发生 GT
partner 冲突的 predicted-pair 端点数。

| Predictor | Missing | FP | Wrong-partner events | Degree 1 | Degree 2 | Pure FP | Linked missing | Pure missing | Samples with wrong partner |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RNAfold | 203 | 220 | 130 | 78 | 52 | 90 | 131 | 72 | 23 |
| PETfold | 213 | 241 | 136 | 85 | 51 | 105 | 137 | 76 | 25 |
| trRosettaRNA2 native SS | 215 | 432 | 169 | 35 | 134 | 263 | 158 | 57 | 20 |

在 trRosettaRNA2 native SS 的 432 个 FP 中，pure FP 为 263，wrong-partner
events 为 169；因此其 FP 在当前冻结 taxonomy 下多数为 pure FP。这是确定性
pair-level 计数，不包含生物学或因果解释。

### Legacy121 v1 strict-stem inventory

以下仅为 strict stacked-stem 与 singleton 的描述性计数；没有进行 GT/prediction
stem matching，也没有赋予任何 stem error label。

| Structure | Structures | Strict stems | Stem pairs | Fraction pairs in stems | Singleton pairs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ground truth | 121 | 335 | 1636 / 1676 | 0.976134 | 40 |
| RNAfold prediction | 121 | 326 | 1680 / 1693 | 0.992321 | 13 |
| PETfold prediction | 121 | 312 | 1694 / 1704 | 0.994131 | 10 |
| trRosettaRNA2 native SS prediction | 121 | 295 | 1830 / 1893 | 0.966719 | 63 |

表中 fraction 为 stem pairs / total pairs；strict stem 的最小长度为 2，所有
singleton pairs 均保留。

### Legacy121 v1 stem-matching protocol audit

本轮仅完成 deterministic protocol design 与 read-only candidate audit，未生成
stem-level error labels/counts。chosen bilateral candidate filter 产生 871 条
candidate edges，其中 11 条为潜在 register-shift candidates；758 条为 isolated
one-to-one edges，53 个 components 存在多 GT/多 prediction ambiguity。greedy 与
maximum-weight assignment 在 363 条 records 上选择一致，但 ambiguous components
统一保留为 `complex_mismatch` residual，不强行分配。详细阈值比较与 pathological
examples 见 `docs/stem_matching_protocol_audit.md`。

此前讨论中出现的 F1、RMSD 示例数值均为说明用示例，不得视为实验结果。

### Legacy121 v1 stem-level descriptive error analysis

严格按照冻结 taxonomy 实现；ambiguous components 不进行强制 GT↔prediction 配对，
而统一记录为 `complex_mismatch` residual。

| Predictor | Exact | Truncation | Extension | Shift | Isolated complex | Ambiguous components | Missing GT | Unmatched predicted |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RNAfold | 227 | 5 | 44 | 2 | 1 | 5 | 46 | 42 |
| PETfold | 203 | 4 | 42 | 2 | 1 | 16 | 48 | 44 |
| trRosettaRNA2 native SS | 112 | 1 | 103 | 6 | 5 | 32 | 40 | 36 |

全局 stem instances 为 GT 1005、prediction 933；isolated one-to-one components
758，ambiguous components 53（GT 113、prediction 53）。最终 isolated
`stem_shift` 为 10，另有 1 个 zero-overlap shift candidate 位于 ambiguous
component，因此未计入 shift。上述结果仅为描述性 taxonomy counts，不作生物学原因解释。

### Legacy121 v1 pair sequence-separation analysis

GT-only distribution 使用 121 个唯一 structures、1676 个 pairs，不按三个 predictor
重复计数。raw separation 的 min/Q10/Q25/median/Q75/Q90/Q95/max 为
3/7/11/20/32/54/72/221 nt；relative separation 对应为
0.01794/0.13433/0.25/0.51429/0.8/0.93333/1/1。

主分箱采用 GT-only relative Q25/Q50/Q75/Q90，五个 bins 的 GT pair counts 为
428/412/418/251/167。冻结 long-range stratum 为
`relative_separation > 0.9333333333333333`，包含 167 pairs（9.9642%）并覆盖
100/121 RNAs。相比之下，raw `>Q90=54 nt` 的上尾仅覆盖 20 RNAs，因此未选为主定义。

在最高 relative-separation bin，RNAfold、PETfold、trRosettaRNA2 native SS 的
TP/FP/FN 分别为 167/6/0、167/5/0、167/15/0；对应 FP 仅占各模型全部 FP 的
2.73%、2.07%、3.47%。三个模型的 FN 均主要位于较低 bins，而非最高 bin。
wrong-partner events 在最高 bin 分别为 0、0、10。以上仅说明 Legacy121 v1
的描述性集中模式，不推断生物学难度或因果机制。

### Phase 1 consolidated empirical conclusions

所有 ranking 均在同一统计单位内完成。Pair error-event partition 使用 `FP+FN`
为 denominator：RNAfold/PETfold 的第一模式是 missing pair（47.99%/46.92%），
随后为 wrong-partner FP；trRosettaRNA2 第一模式是 pure FP（40.65%），随后为
missing pair。GT-stem error dispositions 使用 335 GT stems 为 denominator：
RNAfold/PETfold 均以 missing（13.73%/14.33%）和 extension
（13.13%/12.54%）为首；trRosettaRNA2 以 extension（30.75%）和 ambiguous GT
stems（20.30%）为首。unmatched predicted-stem rates 单独使用 predicted stems
为 denominator，三模型相近（12.88%/14.10%/12.20%）。

trRosettaRNA2 的 FP excess 不能归结为 unmatched false stems：extension stems
含 146 个 FP pairs，unmatched predicted stems 含 125 个，ambiguous predicted
stems 含 83 个。其 predicted stems 少于 GT（295 vs 335）但 predicted pairs 更多
（1893 vs 1676），同时 predicted strict stems 更长（mean 6.20 vs 4.88）且
extension/merged ambiguous patterns 更多。这是结构性描述，不解释训练或生物机制。

Phase 1 支持“在 Legacy121 和三个 predictor 上存在 structured error patterns”的
有限描述性结论；不支持 learnable、correctable、model-agnostic、evidence-guided、
3D benefit 或 cross-dataset claims。highest-separation bin 未出现 error enrichment，
因此 long-range 不作为第一轮 rule baseline 的 shared target。

### Phase 2 minimal rule baseline specification

本节仅记录冻结设计，不是 refinement empirical finding。Primary baseline v1
预注册三个 confidence-free、GT-free、deletion-only atomic rules：R1 删除 original
predicted singleton pairs；R2 删除冻结最小长度的 two-pair strict stems，明确作为
high-risk short-stem cleanup baseline；R3 仅在长度至少 3 的 original strict stem
外端 pair 不属于 `AU/UA/GC/CG/GU/UG`、且 immediate inward pair 属于该集合时，
删除最多一个 original outer pair。所有 triggers 从同一 immutable original
snapshot 计算，不递归、不添加 pair、不重分配 partner。

Read-only observable audit 中，R1 trigger counts 为 RNAfold/PETfold/trRosettaRNA2
的 13/10/63 pairs；R2 为 36/34/22 stems（72/68/44 pairs）；R3 为
0/0/20 stems。363 条 normalized predictions 的 multiple-partner conflicts 均为
0。上述仅为不使用 GT 的 trigger-volume audit，不是 beneficial/harmful edit 结果。
全量 non-Watson-Crick/wobble cleanup、generic AU/GU trimming、confidence filtering、
wrong-partner reassignment 与 missing-stem addition 均未进入 primary v1。

## Blockers

- refinement 项目最终 dataset 列表未确定。
- external77 的 `GT_ALL` / `GT_CON` 目标语义及 4 个含 `N` 序列的处理规则尚未冻结。
- 第一版 3-5 个 source predictor 未确定。
- 目前只有 legacy 121 同时具备 RNAfold、PETfold 和 trRosettaRNA2 native SS 的完整历史 2D 输出；external77 缺少完整的三模型 2D prediction matrix，进入首轮多模型评测前需要按冻结协议重跑。
- 初始三个可运行 2D 候选中，现有 trRosettaRNA2 native SS 输出保留了 pair-score NPZ；RNAfold/PETfold 可在重跑时输出概率，但 legacy `.db` 未保留这些值。
- final refiner architecture 未确定。
- real experimental evidence source 未确定。
- 最终 CCF-A venue 未确定。
- 3D validation subset 和 inference protocol 未确定。

## Immediate Next Steps

1. Implement the frozen minimal rule-based refinement baseline and run Legacy121 pilot evaluation.

## Open Questions

- 第一版选哪 3-5 个 predictor？
- 哪些 dataset 可以在统一结构表示下公平比较？
- 哪些 predictor 可以提供 pair probability / logits？
- rule-based baseline 应该做到什么强度？
- selective refiner v1 用什么最小架构？
- leave-one-model-out 能否真正提升 unseen predictor？
- 首个 evidence 版本用 simulated base-pair evidence，还是直接寻找真实 SHAPE/DMS/NMR？
- refined 2D 是否值得进入 downstream 3D 主实验？
- 最终更适合 AAAI/KDD AI for Sciences，还是方法更强后尝试 ICML/NeurIPS？
