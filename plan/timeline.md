# Timeline

## Phase 0 — Benchmark and Data Setup

**Target period: 2026-08-24 to 2026-09-06**

目标：

建立 refinement 实验可复用的数据、prediction、parser 和 evaluator 层。

任务：
- [ ] Inventory 当前 benchmark datasets。
- [ ] Inventory 当前可运行 source predictors。
- [ ] 标记各 predictor 是否输出 pair probability / logits / confidence。
- [ ] 定义 normalized prediction schema。
- [ ] 实现/验证统一 secondary-structure -> base-pair parser。
- [ ] 实现 shared evaluator。
- [ ] 用 shared evaluator 重算 source predictor baseline。
- [ ] 记录与现有 benchmark 指标的任何差异。

产出：

- dataset/model inventory；
- normalized prediction format；
- shared parser/evaluator；
- reproduced baseline table。

完成标准：

至少 3 个 source predictor 可以通过同一 evaluator 从 normalized output 得到 per-sample 和 aggregate 指标。

---

## Phase 1 — Error Analysis

**Target period: 2026-09-07 to 2026-09-20**

目标：

明确现有 RNA predictor 的主要错误类型和跨模型共有错误。

任务：
- [ ] missing pair extractor。
- [ ] false-positive pair extractor。
- [ ] wrong-partner extractor。
- [ ] 定义并实现 stem extraction。
- [ ] 定义 stem missing/truncation/extension/shift。
- [ ] long-range pair analysis。
- [ ] pseudoknot analysis（仅在表示一致时）。
- [ ] 输出 per-model/per-dataset error summary。

产出：

- error taxonomy v1；
- per-sample error records；
- cross-model error summary。

完成标准：

能够回答：当前 benchmark 中最常见的三个 error type 是什么，哪些在多个 predictor 中重复出现？

---

## Phase 2 — Rule-Based Refinement Baseline

**Target period: 2026-09-21 to 2026-10-04**

目标：

建立 learned method 必须超越的简单 correction baseline。

任务：
- [ ] 固定最小 rule set。
- [ ] structural validity / conflict checks。
- [ ] confidence-aware rule（若可用）。
- [ ] 记录每个 modification。
- [ ] Original vs Rule-based evaluation。
- [ ] beneficial/harmful edit analysis。

产出：

- rule-based refiner；
- baseline comparison table；
- edit-quality analysis。

完成标准：

无论总体 F1 是否提升，都能定量说明简单 post-processing 的上限和副作用。

---

## Phase 3 — Selective Refiner

**Target period: 2026-10-05 to 2026-10-25**

目标：

验证 selective correction 是否优于 generic learned correction。

任务：
- [ ] 定义 refiner train/val/test split。
- [ ] 构建 error labels。
- [ ] non-selective learned baseline。
- [ ] error detector / modification mask。
- [ ] refined pair score prediction。
- [ ] constrained decoder（若需要）。
- [ ] preservation objective。
- [ ] Original / Rule / Non-selective / Selective comparison。

产出：

- selective refiner v1；
- method comparison；
- first ablation。

完成标准：

至少在一个稳定 benchmark setting 上获得可复现 selective-refinement 结果。

Go/No-Go：

若 selective refinement 没有稳定 signal，先诊断 error detection / decoding / correction headroom，不进入 evidence 阶段。

---

## Phase 4 — Cross-Model / Universal Refinement

**Target period: 2026-10-26 to 2026-11-15**

目标：

测试 Refiner 是否跨 source predictor transfer。

任务：
- [ ] pooled multi-model training。
- [ ] model-specific baseline。
- [ ] leave-one-model-out evaluation。
- [ ] with/without source-model ID（若实现）。
- [ ] weak vs strong predictor analysis。

产出：

- leave-one-model-out table；
- universal vs model-specific comparison。

完成标准：

明确支持或否定 model-agnostic claim。

---

## Phase 5 — Evidence-Guided Refinement

**Target period: 2026-11-16 to 2026-12-06**

目标：

验证 sparse/noisy structural evidence 的独立价值。

任务：
- [ ] controlled simulated-evidence generator。
- [ ] candidate evidence-density experiments。
- [ ] hard-evidence baseline。
- [ ] evidence-aware selective refiner。
- [ ] controlled noise injection。
- [ ] learned trust mechanism（若结果需要）。
- [ ] 评估是否需要真实 SHAPE/DMS/NMR 数据。

产出：

- density response curve；
- noise robustness curve；
- evidence-guided comparison。

完成标准：

能够判断 evidence 是否提供 prediction-only refinement 之外的独立收益。

---

## Phase 6 — Full Experiments and Ablation

**Target period: 2026-12-07 to 2026-12-20**

目标：

冻结方法，完成论文级主实验。

任务：
- [ ] freeze architecture/training protocol。
- [ ] 跑全部已选 predictor/dataset。
- [ ] 完成核心 ablation。
- [ ] error-specific analysis。
- [ ] length / long-range / PK analysis（若有效）。
- [ ] paired statistical analysis（根据最终数据选择）。
- [ ] 记录 runtime/resource（若属于 claim）。

产出：

- final main-result tables；
- final ablation tables；
- final analysis figures。

完成标准：

主要 paper claim 不再依赖新的大规模方法修改。

---

## Phase 7 — Candidate 2D -> 3D Validation

**Target period: 2026-12-21 to 2027-01-05**

**Candidate / 待验证**

目标：

判断 refined 2D 是否改善 RNA 3D prediction。

任务：
- [ ] 选择有 GT 3D 的 RNA subset。
- [ ] freeze 一个 3D inference pipeline。
- [ ] 准备 original/refined/GT 三种 2D input。
- [ ] 同配置跑 3D inference。
- [ ] 汇总 RMSD/TM-score/lDDT（按可用性）。
- [ ] 分析关键 error correction 与 3D improvement 的关系。

产出：

- 2D-to-3D comparison table；
- per-target downstream analysis。

完成标准：

明确决定 3D validation 进入 main paper、secondary analysis，还是不进入 paper claim。

---

## Phase 8 — Paper Writing and Submission Preparation

**Target period: 2027-01 onward**

目标：

将已经验证的结果组织成 CCF-A submission。

任务：
- [ ] freeze paper claims。
- [ ] 删除未被实验支持的 claim。
- [ ] 写 Introduction / Related Work / Method / Experiments。
- [ ] 建 claim-evidence map。
- [ ] 整理 reproducibility appendix。
- [ ] 最终确认 CCF-A venue classification、track、paper type、deadline。

产出：

- manuscript draft；
- figure/table set；
- reproducibility materials；
- final venue decision。

完成标准：

论文只包含被完成实验支持的贡献，并与最终会议 scope 匹配。
