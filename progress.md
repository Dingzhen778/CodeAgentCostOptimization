# Progress

## 当前实验进度

更新时间：`2026-04-05`

当前主线实验分两部分：

- `_19`：`19` 条 `SWE-bench Verified` 子集，已全部完成
- `_100`：新的 `100` 条 `SWE-bench Verified` 随机子集，正在运行

两部分没有重叠，因此合并后是 `119` 条唯一 `instance`。最终总统计会按 `_19 + _100` 合并，避免遗漏和串日志。

### `_19` 已完成结果

实验目录：

- [subset_methods_resolved19_steps40_live](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_resolved19_steps40_live)

最终结果：

| 方法 | resolve | 总数 | resolve rate | avg tokens |
|---|---:|---:|---:|---:|
| `baseline_raw` | 7 | 19 | 36.84% | 360,289 |
| `rag_topk` | 10 | 19 | 52.63% | 335,868 |
| `rag_function` | 7 | 19 | 36.84% | 347,186 |
| `llmlingua_original` | 10 | 19 | 52.63% | 350,372 |
| `skill_abstraction` | 9 | 19 | 47.37% | 315,220 |
| `skill_memory_md` | 7 | 19 | 36.84% | 357,786 |
| `hybrid_llmlingua` | 10 | 19 | 52.63% | 347,513 |

阶段结论：

- `rag_topk`：19 条子集上的最佳综合方案
- `skill_abstraction`：最低 token 方案
- `rag_function`、`skill_memory_md`：当前版本不占优

### `_100` 运行中结果

实验目录：

- [subset_methods_new100_steps40_live](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_new100_steps40_live)

当前完成数：

| 方法 | completed | resolved |
|---|---:|---:|
| `baseline_raw` | 18 | 10 |
| `rag_topk` | 16 | 8 |
| `rag_function` | 14 | 6 |
| `llmlingua_original` | 17 | 10 |
| `skill_abstraction` | 17 | 9 |
| `skill_memory_md` | 13 | 4 |
| `hybrid_llmlingua` | 18 | 11 |

当前总完成结果数：`113`

`_100` 当前 token 累计：

| 方法 | seen instances | total tokens |
|---|---:|---:|
| `baseline_raw` | 19 | 5,704,599 |
| `rag_topk` | 17 | 5,754,164 |
| `rag_function` | 15 | 5,584,983 |
| `llmlingua_original` | 18 | 6,035,828 |
| `skill_abstraction` | 18 | 5,870,247 |
| `skill_memory_md` | 14 | 5,278,706 |
| `hybrid_llmlingua` | 19 | 6,727,856 |

当前阶段判断：

- `_100` 上，`hybrid_llmlingua` 和 `llmlingua_original` 的 resolve 走势目前最好
- `baseline_raw` 依然非常稳，而且成本不高
- `rag_topk` 在新 `100` 条上的优势没有在 `19` 条里那么明显
- `skill_memory_md` 仍然最弱

这说明：

- 小样本与大样本上的方法排序可能会变化
- 后续最终结论必须以 `119` 条总结果为准，不能只看 `19` 条

## 当前方法说明

| 方法 | 省 token 逻辑 |
|---|---|
| `baseline_raw` | 不压缩，作为对照 |
| `rag_topk` | 先检索 top-k 候选文件，减少广泛搜索和整仓阅读 |
| `rag_function` | 在文件级检索后再裁到函数级，进一步缩短输入代码片段 |
| `llmlingua_original` | 用 LLMLingua 风格重排序候选文件，保留高价值跨文件上下文 |
| `skill_abstraction` | 注入结构化 workflow scaffold，减少空转步骤 |
| `skill_memory_md` | 从 `skills.md` 注入可迁移启发式经验 |
| `hybrid_llmlingua` | LLMLingua 排序 + 函数裁剪 + token budget 的组合版 |

## 文档整理策略

根目录现在只保留：

- [README.md](/home/azureuser/jrh/CodeAgentCostOptimization/README.md)
- [progress.md](/home/azureuser/jrh/CodeAgentCostOptimization/progress.md)

另外保留：

- [skills.md](/home/azureuser/jrh/CodeAgentCostOptimization/skills.md)

原因：

- `skills.md` 不是说明文档，而是 `skill_memory_md` 正在使用的运行时输入
- 当前实验还没跑完，删除它会影响正在运行的进程

历史说明文档、临时分析文档和过时计划文档已从根目录移除或迁入实验目录。

