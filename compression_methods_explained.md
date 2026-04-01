# 压缩方法说明

这份文档用于解释当前 `mini-swe-agent` 实验中使用的几种省 token 方法。
重点说明三件事：

- 每种方法想省的是哪一部分 token
- 它的输入是什么
- 它最终输出给 agent 的是什么

## 统一前提

所有方法共享同一套基础输入：

- `problem_statement`：SWE-bench 的 issue 描述
- `repository environment`：对应 instance 的 Docker 代码环境
- `mini-swe-agent`：真正执行搜索、编辑、验证、提交 patch 的下游 agent

这些方法本身并不直接生成 patch。  
它们做的是：在 agent 开始前，对上下文进行筛选、压缩或结构化，尽量减少后续无效搜索、无关阅读和重复推理。

## 1. `baseline_raw`

核心思路：
- 不做任何压缩。
- 把原始 issue 直接交给 agent，自主搜索和修复。

输入：
- 原始 `problem_statement`

输出：
- 未修改的 `problem_statement`

省 token 逻辑：
- 这个方法本身不省 token。
- 它的作用是作为对照组，所有其他方法都拿它做比较。

## 2. `rag_topk`

核心思路：
- 在 agent 开始前，先根据 issue 检索出少量候选文件。
- 让 agent 少做大范围搜索，尽快聚焦到可能相关的文件。

输入：
- `problem_statement`
- Docker 环境中的代码仓库文件

处理过程：
- 从 issue 中抽取关键词
- 在仓库里搜索可能相关的文件
- 选出 top-k 个候选文件
- 读取这些文件的片段

输出：
- 原始 `problem_statement`
- 少量候选文件片段

预期省 token 点：
- 减少全仓库范围搜索
- 减少无关文件整文件阅读

## 3. `rag_function`

核心思路：
- 先做和 `rag_topk` 一样的文件级检索
- 再把候选文件进一步裁到函数级或局部代码块

输入：
- `problem_statement`
- 检索得到的候选文件

处理过程：
- top-k 文件检索
- 对检索到的文件做函数级裁剪

输出：
- 原始 `problem_statement`
- 比 `rag_topk` 更短、更聚焦的代码片段

预期省 token 点：
- 减少单个文件内的大段无关代码
- 让 agent 直接看到更小范围的代码区域

## 4. `llmlingua_original`

核心思路：
- 使用原始风格的 LLMLingua 选择逻辑，对候选文件重新排序
- 尽量保留更有价值的跨文件上下文，丢掉价值较低的文件

输入：
- `problem_statement`
- 初步收集到的候选文件

处理过程：
- 先收集一批候选文件
- 用 LLMLingua 对这些文件重新排序
- 保留排名更高的文件

输出：
- 原始 `problem_statement`
- 经 LLMLingua 排序后的候选文件片段

预期省 token 点：
- 减少低价值跨文件上下文
- 比简单关键词检索更强调“哪些文件更值得保留”

## 5. `skill_abstraction`

核心思路：
- 不额外给模型新的知识
- 而是给它一个更紧凑的工作流程，减少乱搜和空转

输入：
- `problem_statement`
- 检索得到的候选文件

处理过程：
- 在任务前加入一个固定 workflow scaffold：
  - 理解问题
  - 缩小文件范围
  - 定位函数或代码块
  - 做最小 patch
  - 做聚焦验证
  - 最后提交

输出：
- 原始 `problem_statement`
- 候选文件片段
- 固定的结构化工作流提示

预期省 token 点：
- 减少漫无目的的搜索
- 减少重复 read/search
- 更早进入 edit/verify 阶段

## 6. `skill_memory_md`

核心思路：
- 额外加入一个可迁移的 `skills.md`
- 把跨 instance 可复用的修复启发式经验注入给 agent

输入：
- `problem_statement`
- 检索得到的候选文件
- [skills.md](/home/azureuser/jrh/CodeAgentCostOptimization/skills.md)

处理过程：
- 读取 `skills.md` 中的启发式经验
- 作为外部 skill memory 注入到任务里

输出：
- 原始 `problem_statement`
- 候选文件片段
- 可迁移的经验性启发式提示

预期省 token 点：
- 减少跨 instance 的重复探索
- 让 agent 更快做出更高价值的搜索、阅读、编辑和验证选择

说明：
- 当前它是“静态经验库”方案
- 不是在线自学习 skill 系统

## 7. `hybrid_llmlingua`

核心思路：
- 组合多种压缩方法
- 先用 LLMLingua 排序文件，再做裁剪和 token budget 控制

输入：
- `problem_statement`
- 初步收集到的候选文件

处理过程：
- LLMLingua 文件重排序
- 函数级裁剪
- token budget 截断

输出：
- 原始 `problem_statement`
- 多阶段压缩后的上下文包

预期省 token 点：
- 同时减少文件数量和片段长度
- 尝试把“语义排序”和“局部裁剪”结合起来

## 输入输出总表

| 方法 | 主要输入 | 输出给 Agent 的内容 | 主要想省哪里 |
|---|---|---|---|
| `baseline_raw` | 原始 issue | 原始 issue | 不压缩，仅作对照 |
| `rag_topk` | issue + 仓库文件 | issue + top-k 文件片段 | 减少广泛搜索 |
| `rag_function` | issue + 检索文件 | issue + 更短代码片段 | 减少大段代码阅读 |
| `llmlingua_original` | issue + 候选文件 | issue + LLMLingua 排序后的文件 | 减少低价值跨文件上下文 |
| `skill_abstraction` | issue + 候选文件 | issue + 文件片段 + workflow scaffold | 减少空转步骤 |
| `skill_memory_md` | issue + 文件 + `skills.md` | issue + 文件片段 + 可迁移经验 | 减少重复探索 |
| `hybrid_llmlingua` | issue + 候选文件 | issue + 排序后且裁剪过的上下文 | 同时压文件数和片段长度 |

## 关键说明

- 这些方法都不会改变 `mini-swe-agent` 的核心 patch 生成循环。
- 真正执行 bash、改代码、验证、提交 patch 的仍然是下游 agent。
- 它们主要优化的是：
  - 输入上下文
  - 轨迹前期的搜索/阅读成本
  - 或者整体 solve 流程的紧凑程度
- `skill_memory_md` 目前仍然是静态 memory 文件，不是自动总结并迁移的新型在线 skill 系统。
