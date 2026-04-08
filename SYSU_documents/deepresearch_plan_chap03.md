# `chap03` Deep Research 信息收集计划

更新时间：`2026-04-06`

适用章节：

- [chap03.tex](/home/azureuser/jrh/CodeAgentCostOptimization/overleaf/paper/data/chap03.tex)

目标：

- 为“相关工作与研究基础”章节收集足够、系统、可引用的文献材料。
- 支撑以下主线：
  - 基于大语言模型的自动程序修复
  - 代码智能体与软件工程智能体
  - 仓库级代码任务与 GitHub Issue Resolution
  - 长上下文代码理解与上下文压缩
  - 成本优化与效率分析相关研究
  - 本文前期已发表/已投稿工作的定位

---

## 一、总目标

本次 deep research 的目标不是简单堆文献，而是回答以下问题：

1. 代码修复智能体这条线，现有研究做到哪里了？
2. 长上下文代码任务与上下文压缩这条线，已经形成了哪些主要结论？
3. GitHub issue resolution / benchmark 这条线，任务场景如何演进？
4. 成本优化与 agent overhead 这条线，现有工作关注到了什么粒度？
5. 你之前的两篇论文在整个研究脉络里分别处于什么位置？

---

## 二、调研输出要求

每条文献至少记录以下字段：

- `模块`
- `标题`
- `作者`
- `年份`
- `出处`
- `链接`
- `任务类型`
- `研究对象`
- `核心方法/贡献`
- `是否涉及成本/效率`
- `适合放入chap03哪一节`
- `与本文关系`
- `一句话摘要`

建议输出格式优先使用表格：

```markdown
| 模块 | 标题 | 年份 | 出处 | 链接 | 核心贡献 | 是否涉及成本 | 适合小节 | 与本文关系 |
|---|---|---:|---|---|---|---|---|---|
```

如果某篇文献比较复杂，也可以单独展开：

```markdown
### 文献标题
- 作者：
- 年份：
- 出处：
- 链接：
- 核心内容：
- 与本文关系：
- 适合放入chap03哪一节：
```

---

## 三、信息源优先级

优先使用：

- ACM / IEEE 正式页面
- ACL Anthology
- OpenReview
- arXiv 官方页面
- benchmark 官方页面
- 公司官方技术报告 / system card

尽量避免：

- 没有正式出处的博客二手总结
- 只看排行榜、不看论文
- 只有模型名、没有正式论文或官方说明

---

## 四、模块化调研计划

---

## 模块 A：基于大语言模型的自动程序修复

### 目标

梳理自动程序修复从传统 APR 到 LLM-based APR 的演化脉络。

### 重点回答的问题

1. 传统 APR 的主要技术路线有哪些？
2. LLM-based APR 的代表性工作有哪些？
3. 这些工作主要优化什么：成功率、补丁质量、泛化能力还是成本？
4. 仓库级修复与局部补丁生成的区别是什么？

### 建议检索词

- `LLM automated program repair`
- `large language models program repair`
- `automated program repair in the era of large pre-trained language models`
- `program repair benchmark large language model`

### 建议收集数量

- `8-12` 篇

### 建议优先保留

- 传统 APR 经典工作 `3-5` 篇
- LLM-based APR 代表工作 `5-7` 篇

### 调研记录

| 模块 | 标题 | 年份 | 出处 | 链接 | 核心贡献 | 是否涉及成本 | 适合小节 | 与本文关系 |
|---|---|---:|---|---|---|---|---|---|
| A |  |  |  |  |  |  |  |  |

---

## 模块 B：代码智能体与软件工程智能体

### 目标

梳理 agent 化软件工程研究的主线，形成“从单轮代码生成到工具调用与多轮交互”的叙事。

### 重点回答的问题

1. 代表性软件工程 agent 有哪些？
2. 这些工作如何设计工具调用与环境交互？
3. 主要 benchmark 是什么？
4. 是否显式讨论了成本、效率或框架开销？

### 建议检索词

- `software engineering agents large language models`
- `code agent software engineering`
- `SWE-agent`
- `AutoCodeRover`
- `Agentless`
- `repair agent llm`

### 建议收集数量

- `10-15` 篇

### 建议优先保留

- SWE-agent
- AutoCodeRover
- Agentless
- RepairAgent
- MAGIS
- CodeR
- 其他与你主线贴近的 `3-5` 篇

### 调研记录

| 模块 | 标题 | 年份 | 出处 | 链接 | 核心贡献 | 是否涉及成本 | 适合小节 | 与本文关系 |
|---|---|---:|---|---|---|---|---|---|
| B |  |  |  |  |  |  |  |  |

---

## 模块 C：仓库级代码任务与 GitHub Issue Resolution

### 目标

说明真实任务为什么从代码补全扩展到 repository-level 和 issue resolution。

### 重点回答的问题

1. repository-level code completion / QA / issue resolution 各自代表什么？
2. benchmark 是如何从 HumanEval 发展到仓库级任务的？
3. OmniGIRL 和 SWE-bench 分别解决什么问题？
4. 为什么 issue resolution 更接近真实软件工程？

### 建议检索词

- `repository-level code completion benchmark`
- `repository-level code understanding benchmark`
- `GitHub issue resolution benchmark`
- `SWE-bench`
- `OmniGIRL`
- `RepoQA`
- `CrossCodeEval`
- `CoderEval`

### 建议收集数量

- `8-12` 项

### 建议优先保留

- HumanEval / MBPP 作为早期参照
- CrossCodeEval
- RepoQA
- SWE-bench
- SWE-bench Verified
- OmniGIRL
- 多语言 issue benchmark `1-2` 个

### 调研记录

| 模块 | 标题 | 年份 | 出处 | 链接 | 核心贡献 | 是否涉及成本 | 适合小节 | 与本文关系 |
|---|---|---:|---|---|---|---|---|---|
| C |  |  |  |  |  |  |  |  |

---

## 模块 D：长上下文代码理解与上下文压缩

### 目标

支撑“长上下文代码任务”和“当前毕设主线”之间的桥梁关系。

### 重点回答的问题

1. 长上下文代码任务有哪些 benchmark？
2. 现有压缩方法有哪些？
3. 它们是通用文本压缩迁移到代码，还是专门面向代码？
4. 压缩与任务效果的 trade-off 如何被讨论？

### 建议检索词

- `long context code benchmark`
- `long context code understanding`
- `context compression code large language models`
- `LLMLingua code`
- `prompt compression code generation`
- `repository-level code completion compression`

### 建议收集数量

- `10-15` 篇

### 建议优先保留

- 长上下文 benchmark 论文
- LLMLingua / LongLLMLingua / LLMLingua-2
- code-specific 或 code-relevant compression 工作
- 你的长上下文代码压缩论文最后作为“本文研究基础”

### 调研记录

| 模块 | 标题 | 年份 | 出处 | 链接 | 核心贡献 | 是否涉及成本 | 适合小节 | 与本文关系 |
|---|---|---:|---|---|---|---|---|---|
| D |  |  |  |  |  |  |  |  |

---

## 模块 E：成本优化、效率优化与 Agent Overhead

### 目标

证明“成本优化”在当前研究中的空白与必要性，这是毕设 research gap 的关键支撑。

### 重点回答的问题

1. 有哪些工作明确讨论 token cost、latency、budget 或 efficiency？
2. 它们是在通用 agent、通用 LLM，还是代码 agent 场景中讨论的？
3. 有没有工作对 agent 过程成本做阶段化分析？
4. 有没有研究 repair success 与 cost 的 trade-off？

### 建议检索词

- `LLM agent cost optimization`
- `token efficiency software engineering agents`
- `agent overhead large language models`
- `budgeted inference llm agents`
- `cost efficient program repair llm`
- `latency token cost coding agents`

### 建议收集数量

- `8-12` 篇

### 建议优先保留

- 明确谈 cost-efficient / budget / overhead 的工作
- Agentless
- CIGAR 这类成本导向 APR 工作
- trajectory-level cost analysis 相关工作

### 调研记录

| 模块 | 标题 | 年份 | 出处 | 链接 | 核心贡献 | 是否涉及成本 | 适合小节 | 与本文关系 |
|---|---|---:|---|---|---|---|---|---|
| E |  |  |  |  |  |  |  |  |

---

## 模块 F：你自己的前期工作定位

### 目标

不是找外部文献，而是明确你两篇论文在整个研究脉络里的位置。

### 需要回答的问题

#### 论文 1：`How to Compress Long-Context Code? An Exploratory Study`

- 它研究的是哪类任务？
- 它解决的是压缩方法效果评估，还是提出了新方法？
- 它给当前毕设提供了什么研究基础？
- 它的边界是什么，为什么不能直接等同于当前毕设？

#### 论文 2：`OmniGIRL / SwebenchX`

- 它研究的是 benchmark 还是方法？
- 它说明了 issue resolution 的哪些复杂性？
- 它给当前毕设提供了什么任务场景基础？
- 为什么它适合放在背景或研究基础，而不是核心实验章？

### 调研记录模板

```markdown
## 前期工作 1
- 名称：
- 类型：
- 研究对象：
- 核心贡献：
- 与当前毕设关系：
- 最适合融入哪一章：

## 前期工作 2
- 名称：
- 类型：
- 研究对象：
- 核心贡献：
- 与当前毕设关系：
- 最适合融入哪一章：
```

---

## 五、最低建议工作量

建议至少达到以下材料规模：

- 模块 A：`8` 篇
- 模块 B：`10` 篇
- 模块 C：`8` 项
- 模块 D：`10` 篇
- 模块 E：`8` 篇
- 前期工作定位：`2` 项

总计大约 `40` 篇左右。

注意：

- 不一定全部都写进正文
- 但这个规模足够后续筛选出 `chap03` 的正式内容

---

## 六、回传给模型时的建议格式

你 deep research 完成后，建议直接按以下任一形式回传：

### 形式 A：分模块表格

```markdown
## 模块A
| 标题 | 年份 | 出处 | 链接 | 核心贡献 | 是否涉及成本 | 与本文关系 |
|---|---:|---|---|---|---|---|

## 模块B
| 标题 | 年份 | 出处 | 链接 | 核心贡献 | 是否涉及成本 | 与本文关系 |
|---|---:|---|---|---|---|---|
```

### 形式 B：每篇单独说明

```markdown
## 模块A

### 文献1
- 标题：
- 作者：
- 年份：
- 出处：
- 链接：
- 核心内容：
- 与本文关系：
- 适合放入chap03哪一节：
```

---

## 七、后续处理方式

你把 deep research 结果回传后，后续模型可以继续完成：

1. 从所有材料中筛出最值得写入 `chap03` 的核心文献。
2. 形成“相关工作 -> 研究空白 -> 本文切入点”的正式章节结构。
3. 产出一版更完整的 `chap03.tex`。
4. 顺手整理需要补入 `refs.bib` 的候选引用条目。
