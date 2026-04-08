# Progress

## 当前状态

更新时间：`2026-04-08`

完整 `500` 条 `SWE-bench Verified` 主实验已经完成，当前仓库处于“结果整理与论文写作”阶段，而不是继续跑主实验阶段。

统一汇总目录：

- [experiments/subset_methods_verified500_steps40_combined](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined)

根目录总报告：

- [experiment_report.md](/home/azureuser/jrh/CodeAgentCostOptimization/experiment_report.md)

## 实验设置

- 数据集：`SWE-bench Verified`
- 总实例数：`500`
- Agent：`mini-swe-agent`
- 模型：`MiniMaxAI/MiniMax-M2.5`
- 环境：官方 `SWE-bench Verified` Docker
- 最大步数：`40`
- 方法数：`7`
- 统一输出：
  - `trajectory.json`
  - `result.json`
  - `patch.diff`
- 统一 token 统计：
  - `input_tokens`
  - `output_tokens`
  - `total_tokens`
  - `calls`

实验按三批完成并最终合并：

- `_19`: `experiments/subset_methods_resolved19_steps40_live/`
- `_100`: `experiments/subset_methods_new100_steps40_live/`
- `_381`: `experiments/subset_methods_remaining381_steps40_live/`

## 完整 500 条结果

| 方法 | resolve | resolve rate | avg input | avg output | avg total |
|---|---:|---:|---:|---:|---:|
| `baseline_raw` | 170/500 | 34.00% | 346,838.44 | 7,790.50 | 354,628.94 |
| `rag_topk` | 189/500 | 37.80% | 347,205.98 | 7,649.44 | 354,855.42 |
| `rag_function` | 166/500 | 33.20% | 344,955.77 | 7,532.24 | 352,488.01 |
| `llmlingua_original` | 165/500 | 33.00% | 327,190.93 | 7,087.09 | 334,278.02 |
| `skill_abstraction` | 182/500 | 36.40% | 337,272.82 | 7,583.08 | 344,855.90 |
| `skill_memory_md` | 186/500 | 37.20% | 339,856.91 | 7,212.55 | 347,069.46 |
| `hybrid_llmlingua` | 181/500 | 36.20% | 337,886.73 | 7,413.84 | 345,300.57 |

## 当前结论

1. `rag_topk` 是完整 `500` 条上的最高 resolve 方法  
   `37.80%`，说明文件级检索缩减最能提高成功率。

2. `llmlingua_original` 是最低 token 方法  
   平均总 token `334,278.02`，比 baseline 降低约 `5.74%`，但 resolve 低于 baseline。

3. `skill_memory_md` 是最好的折中方案之一  
   resolve `37.20%`，同时 token 比 baseline 低约 `2.13%`。

4. `skill_abstraction` 是稳健的低风险改进  
   resolve 提升 `+2.4` 个百分点，token 降低约 `2.76%`。

5. `rag_function` 当前版本不值得优先继续  
   成功率下降，token 收益也不明显。

## Patch 完整性

本轮对 `result.json / trajectory.json / patch.diff` 做了额外清洗。

结果：

- `success_count == patch_nonempty_count == success_with_nonempty_patch_count`

因此：

- 当前 `resolve rate` 可以直接视为“非空 patch 产出率”
- 最终 500 条结果里没有“成功但空 patch”的条目

## 分阶段 token 结论

阶段分析文件：

- [token_phase_methods_clean.json](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/token_phase_methods_clean.json)

核心结论：

1. 所有方法的 token 主体仍然在 `understand` 阶段，普遍在 `50%+`
2. 成功样本的 `submit` 占比显著更高
3. 失败样本更多消耗在 `read/search/other`
4. `skill_abstraction` 和 `skill_memory_md` 的优势主要是帮助 agent 更早进入 `validate/submit`
5. `llmlingua_original` 的优势主要是压缩输入 token，而不是提升成功率

## 当前建议

如果按研究方向继续推进：

- 想强调 **最高成功率**：优先写 `rag_topk`
- 想强调 **最低成本**：优先写 `llmlingua_original`
- 想强调 **成本-性能折中**：优先写 `skill_memory_md` 或 `skill_abstraction`

## 文档分工

- [README.md](/home/azureuser/jrh/CodeAgentCostOptimization/README.md)
  项目概览与目录入口
- [progress.md](/home/azureuser/jrh/CodeAgentCostOptimization/progress.md)
  当前最终状态与结果摘要
- [experiment_report.md](/home/azureuser/jrh/CodeAgentCostOptimization/experiment_report.md)
  完整实验分析报告
