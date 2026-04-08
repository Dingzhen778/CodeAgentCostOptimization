# CodeAgentCostOptimization

面向 `SWE-bench Verified` 代码修复智能体的 token 成本优化实验仓库。项目基于 `mini-swe-agent + 官方 Docker + 本地 gateway token 统计`，系统比较多种上下文压缩与流程压缩方法在真实 patch 生成任务上的成本与成功率。

## 项目定位

本仓库关注的不是单纯“能不能做出 patch”，而是：

1. 哪些方法能提高 `resolve rate`
2. 哪些方法能降低 `token cost`
3. 哪些方法在“成功率-成本”之间给出更好的折中

## 当前结论

完整 `500` 条 `SWE-bench Verified` 主实验已经完成：

- 数据集：`SWE-bench Verified`
- 实例数：`500`
- Agent：`mini-swe-agent`
- 模型：`MiniMaxAI/MiniMax-M2.5`
- 环境：官方 Docker
- 最大步数：`40`
- 方法数：`7`

最终结果总表：

| 方法 | resolve | resolve rate | avg total tokens |
|---|---:|---:|---:|
| `baseline_raw` | 170/500 | 34.00% | 354,628.94 |
| `rag_topk` | 189/500 | 37.80% | 354,855.42 |
| `rag_function` | 166/500 | 33.20% | 352,488.01 |
| `llmlingua_original` | 165/500 | 33.00% | 334,278.02 |
| `skill_abstraction` | 182/500 | 36.40% | 344,855.90 |
| `skill_memory_md` | 186/500 | 37.20% | 347,069.46 |
| `hybrid_llmlingua` | 181/500 | 36.20% | 345,300.57 |

核心结论：

- `rag_topk`：最高 resolve 方法
- `llmlingua_original`：最低 token 方法
- `skill_memory_md` / `skill_abstraction`：最好的折中方案候选
- `rag_function`：当前版本不值得优先继续

另外，完整 `500` 条结果里：

- `success_count == patch_nonempty_count == success_with_nonempty_patch_count`

也就是说，没有“成功但空 patch”的条目。

## 文档入口

根目录文档分工如下：

- [README.md](/home/azureuser/jrh/CodeAgentCostOptimization/README.md)
  项目概览、最终结论、目录入口
- [progress.md](/home/azureuser/jrh/CodeAgentCostOptimization/progress.md)
  当前阶段状态、最终实验结果表、关键补充说明
- [experiment_report.md](/home/azureuser/jrh/CodeAgentCostOptimization/experiment_report.md)
  完整实验设计、方法解释、伪代码、阶段分析、代表性实例分析

## 关键结果目录

完整 `500` 条统一目录：

- [experiments/subset_methods_verified500_steps40_combined](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined)

其中包含：

- [verified500_summary.json](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/verified500_summary.json)
- [verified500_summary.csv](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/verified500_summary.csv)
- [verified500_summary.md](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/verified500_summary.md)
- [token_phase_methods_clean.json](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/token_phase_methods_clean.json)
- [combined_manifest.json](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/combined_manifest.json)
- [final_experiment_report.md](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/final_experiment_report.md)

## 方法列表

当前比较的 7 种方法：

- `baseline_raw`
- `rag_topk`
- `rag_function`
- `llmlingua_original`
- `skill_abstraction`
- `skill_memory_md`
- `hybrid_llmlingua`

## 代码结构

```text
CodeAgentCostOptimization/
├── src/                         # 核心代码
│   ├── agent/                   # runner / task context / trajectory
│   ├── gateway/                 # OpenAI-compatible gateway + token logging
│   ├── compression/             # RAG / trimming / LLMLingua adapter
│   ├── analysis/                # token 阶段分析
│   └── scripts/                 # 实验入口与聚合脚本
├── configs/                     # gateway 与实验配置
├── experiments/                 # 实验输出、输入子集、汇总文件
├── logs/                        # gateway / 运行日志
├── mini-swe-agent/              # 上游 submodule
├── tests/                       # 测试
├── skills.md                    # `skill_memory_md` 使用的静态 skill memory
├── README.md
├── progress.md
└── experiment_report.md
```

## 说明

- 根目录只保留长期有效文档和总报告
- `skills.md` 保留在根目录，因为 `skill_memory_md` 的实现直接读取它
