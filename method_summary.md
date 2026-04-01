# 方法汇总

本文档汇总当前 `mini-swe-agent` 压缩/省 token 方法的定义，以及在 `19` 个已解决 `verified` 实例、`step=40` 条件下的阶段性实验结果与初步分析。

## 一、方法定义

### 1. `baseline_raw`

- 类型：基线方法
- 做法：不做任何压缩，直接把原始 `problem_statement` 交给 agent
- 作用：作为后续所有压缩方法的对照组

### 2. `rag_topk`

- 类型：上下文压缩
- 做法：根据 issue 先检索出 top-k 候选文件，并把这些文件片段提前提供给 agent
- 目标：减少全仓库范围搜索，减少无关文件阅读

### 3. `rag_function`

- 类型：上下文压缩
- 做法：在 `rag_topk` 的基础上，进一步把候选文件裁剪到函数级或局部代码块
- 目标：进一步减少单文件内部的大段无关代码

### 4. `llmlingua_original`

- 类型：上下文压缩
- 做法：使用原始风格 LLMLingua 对候选文件重排序，保留更高价值的跨文件上下文
- 目标：减少低价值文件上下文，提升保留内容的语义相关性

### 5. `skill_abstraction`

- 类型：流程压缩
- 做法：不额外提供新知识，而是在任务前注入一个固定的结构化 workflow scaffold
- 目标：减少 agent 在搜索、阅读和验证中的空转

### 6. `skill_memory_md`

- 类型：可迁移经验注入
- 做法：读取 `skills.md`，把可跨 instance 复用的启发式经验作为外部 skill memory 注入给 agent
- 目标：减少重复探索，复用已有修复经验

说明：
- 当前它是静态 memory 文件方案
- 不是在线自学习 skill 系统

### 7. `hybrid_llmlingua`

- 类型：混合压缩
- 做法：结合 LLMLingua 文件排序、函数级裁剪和 token budget 控制
- 目标：同时减少文件数量和代码片段长度

## 二、实验设置

- 数据集：`19` 个已成功 resolved 的 `SWE-bench Verified` 实例
- Agent：`mini-swe-agent`
- 模型：`MiniMaxAI/MiniMax-M2.5`
- 环境：官方 Docker 镜像
- step 设置：`40`
- 统计来源：gateway 实时 token 日志

## 三、最终结果

### 1. 最终 Resolve 结果

| 方法 | resolve 数 | 总实例数 | resolve rate |
|---|---:|---:|---:|
| `rag_topk` | 10 | 19 | 52.63% |
| `llmlingua_original` | 10 | 19 | 52.63% |
| `hybrid_llmlingua` | 10 | 19 | 52.63% |
| `skill_abstraction` | 9 | 19 | 47.37% |
| `baseline_raw` | 7 | 19 | 36.84% |
| `rag_function` | 7 | 19 | 36.84% |
| `skill_memory_md` | 7 | 19 | 36.84% |

### 2. 最终平均 Token 结果

| 方法 | 平均 token | 总 token |
|---|---:|---:|
| `skill_abstraction` | 315,220 | 5,989,178 |
| `rag_topk` | 335,868 | 6,381,489 |
| `rag_function` | 347,186 | 6,596,542 |
| `hybrid_llmlingua` | 347,513 | 6,602,739 |
| `llmlingua_original` | 350,372 | 6,657,067 |
| `skill_memory_md` | 357,786 | 6,797,925 |
| `baseline_raw` | 360,289 | 6,845,486 |

## 四、初步分析

### 1. 当前最值得关注的方法

#### `rag_topk`

- 在最终结果里，它同时处于：
  - 最高 resolve 率梯队
  - 低于 baseline 的明显 token 成本
- 说明简单、稳定的文件级检索缩减已经能带来比较好的成本收益平衡
- 从当前实验看，它是最适合作为主方法继续推进的方案

#### `llmlingua_original`

- resolve 率同样达到第一梯队
- 说明 LLMLingua 的原始风格文件重排序确实有帮助
- 但 token 成本高于 `rag_topk`
- 因此它更像是一个有效但成本收益略逊于 `rag_topk` 的备选主方法

#### `skill_abstraction`

- 它不是最高 resolve 率的方法
- 但它的平均 token 最低
- 说明结构化 workflow scaffold 确实有助于减少无效步骤和推理空转
- 它适合作为“低成本方案”或者“流程控制 baseline”

### 2. 当前表现一般的方法

#### `hybrid_llmlingua`

- resolve 率达到最高梯队
- 但 token 成本没有优势
- 说明“多种压缩手段叠加”并不自动带来更好的 cost-performance tradeoff
- 当前看，它更复杂，但没有明显优于 `rag_topk`

#### `skill_memory_md`

- 预期是通过可迁移经验减少重复探索
- 但当前实验没有体现出明显优势
- 成功率和 baseline 接近，token 也没有更低
- 这说明当前 `skills.md` 的经验注入方式还比较粗，后续若继续做，需要更细的设计

### 3. 当前最不理想的方法

#### `rag_function`

- resolve 率没有提升
- token 成本也没有明显下降
- 说明当前函数级裁剪方式可能裁掉了对修复有帮助的上下文，或没有真正减少高价值阅读成本
- 在当前版本下，它是最不值得继续优先投入的方法

## 五、当前结论

基于这一轮 `19 instance + step=40` 的实验结果，可以先得到以下结论：

1. `rag_topk` 是当前最值得继续推进的主方法  
   它在成功率和 token 成本之间取得了最好的平衡。

2. `llmlingua_original` 是可行的备选方案  
   它同样提升了 resolve 率，但成本收益比略逊于 `rag_topk`。

3. `skill_abstraction` 适合作为低成本方法  
   它的成功率略低，但 token 最省，说明流程约束本身有价值。

4. `rag_function` 与 `skill_memory_md` 当前版本表现不够理想  
   如果继续研究，需要重新设计，而不是直接沿用当前实现。

## 六、后续建议

基于当前结果，下一步建议优先考虑：

- 继续重点研究 `rag_topk`
- 保留 `llmlingua_original` 作为对照或备选主方法
- 保留 `skill_abstraction` 作为低成本方案
- 暂时降低 `rag_function` 和 `skill_memory_md` 的优先级
