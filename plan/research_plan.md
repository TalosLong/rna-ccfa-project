# Research Plan

## 1. Research Question

**Confirmed / 已确定**

> Can RNA secondary-structure predictions from existing predictors be selectively corrected, without re-predicting the entire structure, and can sparse or noisy structural evidence make this correction more reliable?

子问题：

1. 多个 predictor 是否存在稳定、重复的 error pattern？
2. selective correction 是否优于 unconditional re-prediction？
3. 一个 refiner 是否可以跨 source predictor 泛化？
4. sparse / noisy evidence 是否能提高 refinement？
5. **Candidate / 待验证：** refined 2D 是否改善 downstream 3D？

## 2. Hypothesis

以下全部为 **Candidate / 待验证**：

- H1：不同 predictor 存在部分共享的结构化错误模式。
- H2：显式 keep/modify 的 selective refiner 优于 non-selective refiner。
- H3：部分 error pattern 可跨 predictor transfer。
- H4：少量结构证据可提高 refinement。
- H5：证据含噪时，learned trust 比 hard enforcement 更稳健。
- H6：修复部分关键 2D error，尤其 long-range / pseudoknot-related error，可能改善 3D。

## 3. Overall Experimental Design

```text
A. Benchmark normalization
-> B. Error analysis
-> C. Rule-based refinement
-> D. Selective learned refinement
-> E. Cross-model evaluation
-> F. Evidence-guided refinement
-> G. Full benchmark + ablation
-> H. Candidate 2D -> 3D validation
```

### Benchmark Work vs Paper Contribution

**Benchmark / infrastructure：**

- 收集已有 predictor outputs；
- 统一格式；
- 统一 evaluator；
- 复现 source predictor 指标；
- 输出 per-sample metrics。

这些是必要基础设施，不作为主要 CCF-A contribution。

**Potential paper contribution：**

- cross-model error taxonomy；
- selective refinement；
- leave-one-model-out transfer；
- sparse/noisy evidence-aware correction；
- Candidate downstream 3D benefit。

## 4. Baselines

### B0 — Original Predictor Output

**Confirmed / 已确定**

所有方法都必须和 source predictor 原始 prediction 比较。

### B1 — Rule-Based Refinement

**Confirmed / 已确定 as required baseline**

候选规则：

- structural validity / pair conflict correction；
- isolated low-confidence pair removal；
- compatible high-confidence candidate addition；
- basic pairing plausibility；
- 可选简单 energy / pairing score。

具体规则在检查 predictor output 后锁定。

### B2 — Non-Selective Learned Refiner

**Confirmed / 已确定 as comparison concept**

用于验证 selective mechanism 是否真的有价值。

### B3 — Selective Refiner

**Confirmed / 已确定 as target method family**

包含 error detector / modification mask + refinement。

### B4 — Published RNA Post-Processing Baseline

**Candidate / 待验证**

若代码和输入兼容，加入已讨论过的 assignment-problem-based RNA post-processing 方法。

## 5. Experiments

### Experiment 1 — Benchmark Normalization and Reproduction

Goal:
建立所有后续实验共用的输入、parser 和 evaluator。

Input:
现有 benchmark datasets、ground truth、source predictor outputs、可选 pair scores。

Method:
统一格式，转换为 canonical base-pair list，使用 shared evaluator 重算指标。

Comparison:
shared evaluator vs 现有 benchmark 已保存结果（若有）。

Metrics:
Precision、Recall、F1、MCC（若定义一致）、per-sample TP/FP/FN。

Expected conclusion:
不是科学结论；目标是确认后续实验的 evaluation protocol 可复现。

---

### Experiment 2 — Cross-Model Error Taxonomy

Goal:
确认主要 error types，以及这些错误是否在多个 predictor 中重复出现。

Input:
normalized predictions + ground truth。

Method:
提取：

- missing pair；
- false-positive pair；
- wrong partner；
- stem missing / truncation / extension / shift；
- long-range interaction error；
- pseudoknot-related error（若支持）。

Comparison:
不同 predictor、不同 dataset。

Metrics:
各 error type 数量、占比、per-RNA error count、按 RNA length / pair separation 分层统计。

Expected conclusion:
**Candidate / 待验证：** 存在足够稳定的 shared error patterns，为 Universal Refiner 提供依据。

---

### Experiment 3 — Rule-Based Refinement

Goal:
验证简单 deterministic post-processing 是否已有明显 correction headroom。

Input:
sequence、original prediction、pair confidence（若有）。

Method:
固定一组简单规则进行纠错，并记录每次修改。

Comparison:
Original vs Rule-based refined。

Metrics:
Precision、Recall、F1、MCC、修改次数、beneficial/harmful edit ratio。

Expected conclusion:
建立 learned method 必须超越的强简单 baseline。

---

### Experiment 4 — Selective Refiner v1

Goal:
验证 selective correction 是否优于 generic learned refinement。

Input:
sequence、predicted structure、optional pair confidence、local structural features。

Method:

```text
input
-> error detector / modification mask
-> refined pair scores
-> constrained decoder
-> refined structure
```

Candidate objectives:

```text
L_structure + L_error_detection + L_preserve
```

Comparison:
Original / Rule-based / Non-selective Refiner / Selective Refiner。

Metrics:
Precision、Recall、F1、MCC、modification precision、modification recall、correct-pair preservation rate。

Expected conclusion:
**Candidate / 待验证：** selective mechanism 能减少 destructive edits 并提高整体结构质量。

---

### Experiment 5 — Leave-One-Model-Out Cross-Model Refinement

Goal:
验证 Refiner 是否学习到 predictor-independent error patterns。

Input:
多个 source predictor 的 predictions。

Method:

```text
train: A + B + C
test: held-out D
```

Comparison:
model-specific refiner / pooled multi-model refiner / leave-one-model-out refiner。

Metrics:
F1 delta、Precision/Recall delta、modification precision、weak vs strong predictor improvement。

Expected conclusion:
**Candidate / 待验证：** unseen predictor 仍能得到可复现 improvement。

---

### Experiment 6 — Sparse Evidence Guidance

Goal:
确定部分结构证据在多稀疏时仍有帮助。

Input:
source prediction + sequence + sparse structural evidence。

Method:
先使用 ground truth 构造 controlled simulated evidence。

Candidate density：

```text
0%, 1%, 5%, 10%, 20%, 50%
```

Comparison:
prediction-only refiner / hard evidence injection / evidence-guided selective refiner。

Metrics:
F1、Precision、Recall、evidence satisfaction rate、correct-pair preservation。

Expected conclusion:
**Candidate / 待验证：** sparse evidence 在较低密度下即可提供独立增益。

---

### Experiment 7 — Noisy Evidence Robustness

Goal:
测试错误或冲突 evidence 是否会破坏 refinement。

Input:
Experiment 6 的 sparse evidence。

Method:
Controlled noise injection。

Candidate noise：

```text
5%, 10%, 20%, 30%
```

Comparison:
hard constraint / evidence-guided without trust / evidence-guided with learned trust（若实现）。

Metrics:
F1 vs noise、harmful modification ratio、evidence satisfaction、trust/calibration behavior（若实现）。

Expected conclusion:
**Candidate / 待验证：** learned evidence trust 比盲目 hard enforcement 更稳健。

---

### Experiment 8 — Full Error-Specific Benchmark

Goal:
说明最终方法到底修复了哪些结构错误。

Input:
Best refiner from Experiments 4-7。

Method:
按 error type、RNA length、pair separation、PK/non-PK 分层。

Comparison:
Original vs Refined across source predictors。

Metrics:
Overall F1/MCC、error-specific recovery、long-range pair F1、PK F1（若有效）。

Expected conclusion:
明确 method boundary 和真实 improvement source。

---

### Experiment 9 — Candidate 2D -> 3D Validation

**Candidate / 待验证**

Goal:
测试 refined 2D 是否能改善 RNA 3D prediction。

Input:
sequence、original 2D、refined 2D、GT 2D、GT 3D。

Method:
同一 3D predictor、同一 inference config，三种 2D input：

```text
A: original 2D
B: refined 2D
C: ground-truth 2D
```

Comparison:
A vs B vs C。

Metrics:
Candidate: RMSD、TM-score、lDDT。

Expected conclusion:
**Candidate / 待验证：** 2D correction 的 downstream value 是否真实存在。

## 6. Ablation Studies

**Confirmed planned concepts：**

- w/o selective mechanism；
- w/o evidence；
- w/o pair confidence（若使用）；
- w/o constrained decoding（若使用）；
- w/o preservation objective（若使用）。

**Candidate：**

- with/without source-model identity；
- pair-level vs stem-aware representation；
- evidence type；
- evidence density；
- evidence noise；
- weak vs strong source predictor。

## 7. Analysis

必须保留：

1. cross-model error distribution；
2. 每个 RNA 的 modification count；
3. beneficial / neutral / harmful edit ratio；
4. correct-pair preservation；
5. RNA length analysis；
6. pair sequence-separation analysis；
7. pseudoknot analysis（若合法）；
8. weak vs strong predictor analysis；
9. leave-one-model-out transfer；
10. evidence density/noise curves。

统计显著性：

**Candidate / 待验证。** 最终 sample set 固定后，再根据 paired per-RNA metric 分布选择合适检验，不提前硬编码统计方法。

## 8. Potential Method Contribution

**Candidate / 待验证**

目标方法表述：

> A selective, model-agnostic RNA secondary-structure refinement framework that detects likely errors, preserves already-correct structure, and uses sparse/noisy structural evidence through a learned trust mechanism.

候选组件：

- error detector；
- modification mask；
- preservation-aware objective；
- constrained decoder；
- cross-predictor training；
- evidence encoder；
- prediction-vs-evidence trust。

最终架构必须由 error analysis 和 baseline 结果驱动，不为了“复杂”而加模块。

## 9. Paper Contribution

### Supporting / Benchmark Contribution

- shared evaluation pipeline；
- cross-model error taxonomy；
- error-specific benchmark analysis。

这些目前不被视为足够的 main contribution。

### Candidate Main Contribution

1. Selective refinement；
2. Cross-predictor transfer；
3. Sparse/noisy evidence-aware correction；
4. Candidate 2D -> 3D downstream benefit。

最终论文只保留被实验支持的 claim。

## 10. Risks and Alternative Plans

- Universal transfer 失败 -> 改为 model-conditioned / model-specific，不宣称 model-agnostic。
- 部分 predictor 无 confidence -> shared refiner 使用 structure + sequence，confidence 仅作为 subset ablation。
- Rule baseline 很强 -> 把重点转向 cross-model / evidence / downstream。
- Refiner 伤害强模型 -> 加强 selective keep/modify 与 preservation objective。
- simulated evidence 不够真实 -> 再评估 SHAPE/DMS/NMR 数据，但必须先定义 dataset/protocol。
- pseudoknot 表示不一致 -> 第一版不强行纳入。
- 2D 提升不转化为 3D -> 3D 作为 negative/secondary analysis，不作为主 claim。
- 方法对顶会仍太窄 -> AI4Science 路线加强科学验证；ICML/NeurIPS 路线需加强一般化 structured-refinement 方法贡献。
