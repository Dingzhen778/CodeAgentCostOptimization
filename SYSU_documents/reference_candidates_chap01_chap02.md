# `chap01` / `chap02` 参考文献候选与补充建议

更新时间：`2026-04-06`

适用范围：

- [chap01.tex](/home/azureuser/jrh/CodeAgentCostOptimization/overleaf/paper/data/chap01.tex)
- [chap02.tex](/home/azureuser/jrh/CodeAgentCostOptimization/overleaf/paper/data/chap02.tex)

说明：

- 本文档先给出“候选文献 + 来源链接 + 使用建议”，方便后续统一导入 Zotero 或批量写入 `refs.bib`。
- 当前以“高质量候选项”为目标，不直接假设已完成最终校对。
- 原则上优先使用：会议/期刊正式页面、ACL Anthology、OpenReview、arXiv 官方页面、公司官方技术报告或 system card。

---

## 一、当前最需要补齐的核心引用

这部分基本对应 `chap01/02` 已经出现但 `refs.bib` 尚不存在的 key。

### 1. Transformer / 基础大模型

#### `vaswani2017attention`

- 题目：Attention Is All You Need
- 用途：Transformer 架构基础引用
- 建议来源：
  - arXiv: https://arxiv.org/abs/1706.03762

#### `brown2020language`

- 题目：Language Models are Few-Shot Learners
- 用途：GPT-3 / in-context learning 的经典基础引用
- 建议来源：
  - NeurIPS 页面：https://proceedings.neurips.cc/paper/2020/hash/1457c0d6bfcb4967418bfb8ac142f64a-Abstract.html
  - OpenAI 页面：https://openai.com/index/language-models-are-few-shot-learners/

#### `achiam2023gpt`

- 题目：GPT-4 Technical Report
- 用途：GPT-4 技术报告
- 建议来源：
  - arXiv: https://arxiv.org/abs/2303.08774

#### `team2023gemini`

- 题目：Gemini: A Family of Highly Capable Multimodal Models
- 用途：Gemini 模型族背景
- 建议来源：
  - arXiv: https://arxiv.org/abs/2312.11805

#### `touvron2023llama`

- 题目：Llama 2: Open Foundation and Fine-Tuned Chat Models
- 用途：Llama 系列代表性基础模型
- 建议来源：
  - arXiv: https://arxiv.org/abs/2307.09288

---

### 2. 商业模型引用：建议谨慎处理

#### `anthropic2024claude`

- 当前正文用途：作为 Claude 的代表性模型引用
- 问题：
  - Claude 没有像 GPT-4 / Gemini 那样统一、稳定的学术论文入口。
  - 直接写成 `anthropic2024claude` 容易模糊到底是 Claude 3、3.5 Sonnet 还是 system card。
- 建议方案：
  - 如果你只是想举“代表性模型”例子，可以保留，但引用改为官方发布或 system card。
  - 更稳妥的写法是把句子改成“以 GPT-4、Gemini、Llama、DeepSeek 等模型为代表”，弱化对 Claude 单独学术引用的依赖。
- 候选来源：
  - Claude 3.5 Sonnet 官方发布：https://www.anthropic.com/news/claude-3-5-sonnet
  - Anthropic system cards：https://www.anthropic.com/system-cards

#### `liu2024deepseek`

- 当前正文用途：作为 DeepSeek 的代表性模型引用
- 问题：
  - “DeepSeek”是公司/系列名，不是单篇稳定论文名。
- 建议方案：
  - 如果段落讲“代码能力”，优先改引为 DeepSeek-Coder。
  - 如果段落讲“通用大模型”，可改引为 DeepSeek-V2。
- 候选来源：
  - DeepSeek-Coder: https://arxiv.org/abs/2401.14196
  - DeepSeek-V2: https://arxiv.org/abs/2405.04434

建议：

- `chap01` 和 `chap02` 里凡是泛称“Claude”“DeepSeek”的位置，后续统一成“用哪一篇来代表哪一代模型”。
- 不建议在学位论文里保留模糊 citation key。

---

### 3. 代码模型与代码预训练

#### `chen2021evaluating`

- 题目：Evaluating Large Language Models Trained on Code
- 用途：Codex / 早期大模型代码生成能力
- 建议来源：
  - arXiv: https://arxiv.org/abs/2107.03374

#### `feng2020codebert`

- 题目：CodeBERT: A Pre-Trained Model for Programming and Natural Languages
- 用途：代码预训练模型背景
- 建议来源：
  - ACL Anthology: https://aclanthology.org/2020.findings-emnlp.139/

#### `wang2021codet5`

- 题目：CodeT5: Identifier-aware Unified Pre-trained Encoder-Decoder Models for Code Understanding and Generation
- 用途：代码理解/生成模型背景
- 建议来源：
  - ACL Anthology: https://aclanthology.org/2021.emnlp-main.685/

---

### 4. 自动程序修复（APR）经典工作

#### `le2011genprog`

- 题目：GenProg: A Generic Method for Automatic Software Repair
- 用途：搜索式 APR 经典工作
- 建议来源：
  - DOI: https://doi.org/10.1109/TSE.2011.104

#### `nguyen2013semfix`

- 题目：SemFix: Program Repair via Semantic Analysis
- 用途：语义约束式 APR 经典工作
- 建议来源：
  - DOI: https://doi.org/10.1109/ICSE.2013.6606623

#### `liu2019tbar`

- 题目：TBar: Revisiting Template-Based Automated Program Repair
- 用途：模板式 APR 代表工作
- 建议来源：
  - DOI: https://doi.org/10.1145/3293882.3330577

---

### 5. SWE-bench 与代码智能体

#### `jimenez2023swe`

- 当前正文中的 key 建议更名。
- 原因：
  - 该工作正式发表版本是 `ICLR 2024`，用 `jimenez2023swe` 容易与 arXiv 年份混淆。
- 推荐改为：`jimenez2024swebench`
- 题目：SWE-bench: Can Language Models Resolve Real-World GitHub Issues?
- 建议来源：
  - OpenReview: https://openreview.net/forum?id=VTF8yNQM66
  - arXiv: https://arxiv.org/abs/2310.06770

#### `chowdhury2024swebenchverified`

- 当前正文用途：SWE-bench Verified
- 问题：
  - 目前没有像原始 SWE-bench 那样容易定位的正式会议论文入口。
- 建议方案：
  - 暂时可用官方 Verified 页面或 OpenAI 官方说明页。
  - 写作时明确它是“官方数据集说明/发布页”，不要伪装成正式会议论文。
- 候选来源：
  - 官方 Verified 页面：https://www.swebench.com/verified.html
  - OpenAI 介绍页：https://openai.com/index/introducing-swe-bench-verified/

#### `yang2024swe`

- 题目：SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering
- 用途：代码智能体 / ACI / SWE-agent
- 建议来源：
  - arXiv: https://arxiv.org/abs/2405.15793

#### `zhang2024autocoderover`

- 题目：AutoCodeRover: Autonomous Program Improvement
- 用途：仓库级自动修复 / 检索与结构化搜索
- 建议来源：
  - arXiv: https://arxiv.org/abs/2404.05427

#### `xia2024agentless`

- 题目：Agentless: Demystifying LLM-based Software Engineering Agents
- 用途：低开销、非复杂 agent 框架对比
- 建议来源：
  - arXiv: https://arxiv.org/abs/2407.01489

---

## 二、建议新增但正文还没显式引用的文献

这些文献可以后续用于第三章“相关工作”，也能强化 `chap01/02` 的论证。

### 1. 代码智能体动作与工具调用

- CodeAct: Your LLM Agent Acts Better when Generating Code
  - 官方页面：https://machinelearning.apple.com/research/codeact
  - 用途：说明 agent 行为空间设计、代码动作统一接口

### 2. 代码相关大模型

- DeepSeek-Coder: When the Large Language Model Meets Programming -- The Rise of Code Intelligence
  - arXiv: https://arxiv.org/abs/2401.14196
  - 用途：代码模型背景，替代泛化的 `DeepSeek` 引用

### 3. 关于 SWE-bench / Verified 局限性的材料

- Why SWE-bench Verified no longer measures frontier coding capabilities
  - OpenAI: https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/
  - 用途：如果后面论文讨论基准局限性，可以引用；不建议放在前两章主线里

---

## 三、正文层面的修改建议

### 1. 建议统一改 citation key

建议优先调整：

- `jimenez2023swe` -> `jimenez2024swebench`
- `anthropic2024claude` -> 更具体的 key，如 `anthropic2024claude35sonnet`
- `liu2024deepseek` -> 根据实际含义改为 `guo2024deepseekcoder` 或 `deepseekai2024deepseekv2`

这样后面 `refs.bib` 会更稳定，也方便 Zotero / Better BibTeX 自动生成一致 key。

### 2. 建议缩减“举例型模型引用”

在 [chap01.tex](/home/azureuser/jrh/CodeAgentCostOptimization/overleaf/paper/data/chap01.tex) 与 [chap02.tex](/home/azureuser/jrh/CodeAgentCostOptimization/overleaf/paper/data/chap02.tex) 中，像“GPT-4、Claude、DeepSeek”这种列举式句子，如果后续文献维护压力太大，可以改成：

- “以 GPT-4、Gemini、Llama 和 DeepSeek-Coder 等模型为代表……”

这样可以优先保留有稳定技术报告或论文入口的模型。

### 3. SWE-bench Verified 的引用策略

建议：

- 如果只是定义数据集，可引用官方 Verified 页面。
- 如果要写“经人工核验的 500 样本子集”等描述，也可以直接引用官方页面。
- 不建议在没有找到正式论文前，硬造一个看起来像会议论文的 BibTeX 条目。

---

## 四、推荐的补文献工作流

### A. 工具

优先推荐：

- Zotero Desktop
- Zotero Connector
- Better BibTeX for Zotero

官方参考：

- Zotero 添加条目文档：https://www.zotero.org/support/adding_items_to_zotero
- Better BibTeX：https://retorque.re/zotero-better-bibtex/

### B. 批量补文献步骤

1. 先把本文件中的候选论文逐条加入 Zotero。
2. 优先从论文官网、OpenReview、ACL Anthology、arXiv 官方页导入。
3. 导入后人工核对：
   - 作者
   - 标题大小写
   - venue / journal
   - 年份
   - DOI / URL
4. 用 Better BibTeX 导出到 `overleaf/paper/ref/refs.bib`。
5. 最后统一修正文中的 citation key。

### D. 当前仓库内可直接参考的论文源文件

当前与 issue resolution / code agent 相关的本地论文源文件有两份：

- `papers/arXiv-2505.04606v1.tar.gz`
- `papers/ISSTA2025_IssueResolution.zip`

使用建议：

- `arXiv-2505.04606v1.tar.gz` 可用于确认论文题目、作者列表与部分 Bib 条目。
- `ISSTA2025_IssueResolution.zip` 内含较丰富的 `ref.bib`，适合补 issue resolution、agent、benchmark 相关候选文献。
- 但 `ISSTA2025_IssueResolution.zip` 中的 `main.tex` 仍带有投稿模板占位信息，如示例性的 `acmDOI`、`acmYear`、`Conference acronym 'XX'` 等，不应直接作为“正式发表元数据”的最终来源。

因此：

- 若要补相关工作条目，可以优先参考 `ISSTA2025_IssueResolution.zip` 中的 `ref.bib`。
- 若要确定你自己论文的最终发表题目、venue、DOI、年份，应再以正式出版页面或已确认的最终版本为准。

### C. 对已有“手写参考文献信息”的补救

如果你后面已经攒了一批半成品参考文献字符串，可以用：

- Crossref Simple Text Query
  - https://www.crossref.org/documentation/retrieve-metadata/simple-text-query/

用途：

- 批量把“作者-标题-年份”字符串匹配成 DOI
- 后续再用 DOI 导入 Zotero

---

## 五、建议的优先级

### 第一优先级：必须先补

- Transformer
- GPT-3
- GPT-4
- Codex
- CodeBERT
- CodeT5
- GenProg
- SemFix
- TBar
- SWE-bench
- SWE-agent
- AutoCodeRover
- Agentless

### 第二优先级：建议补

- Gemini
- Llama 2
- DeepSeek-Coder 或 DeepSeek-V2

### 第三优先级：可暂缓

- Claude 相关官方发布/系统卡
- SWE-bench Verified 官方说明页

这两类都能用，但不如正式论文条目稳定，适合在主干文献补齐后再处理。
