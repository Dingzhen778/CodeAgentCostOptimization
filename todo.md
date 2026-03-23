好的，我直接给你一份**可直接粘到论文 / proposal / README 的完整 Markdown 实验方案**，结构我帮你整理成：

> Motivation → 高层实验设计 → 系统架构 → 指标与日志 → 实验矩阵 → 分阶段规划

---

# 📌 SWE-bench Token Cost Optimization 实验方案（初版）

---

# 一、Motivation（研究动机）

随着代码智能体（Code Agent）在软件工程任务中的应用（如 SWE-bench），当前方法主要通过提升模型能力来提高任务成功率，但**推理成本（尤其是 token 消耗）迅速上升**，带来以下问题：

* ❌ 每个任务需要大量上下文（整个 repo / 多文件）
* ❌ 多轮交互导致 token 爆炸
* ❌ agent 存在大量无效探索（重复 search / read）
* ❌ 同一 repo 的多个任务重复计算

👉 核心观察：

> Code Agent 的成本主要来自 **上下文冗余 + 行为冗余 + 跨任务冗余**

---

## 🎯 本实验目标

构建一个**可量化评估 Code Agent 推理成本的实验框架**，并回答：

1. Code Agent 在 SWE-bench 上的 token 消耗结构是什么？
2. 是否可以通过压缩 / 剪枝降低成本？
3. 在降低 token 的同时，性能（pass rate）下降多少？
4. 是否存在更优的 **performance-cost tradeoff**

---

# 二、高层实验设计（High-Level Design）

---

## 🧠 核心思路

本实验围绕：

> **“在 SWE-bench 上，降低 Code Agent token 消耗，同时尽量保持任务成功率”**

展开

---

## 🧪 实验核心变量

### 1️⃣ 模型维度（Model）

* Claude（高性能高成本）
* GLM / Qwen / DeepSeek（中低成本）

---

### 2️⃣ Agent策略（Strategy）

* Vanilla（无优化）
* Context Compression（上下文压缩）
* Trajectory Pruning（过程剪枝）
* Hybrid（组合方法）

---

### 3️⃣ 成本指标（Cost）

* token（核心）
* tool 调用数
* step 数
* latency

---

## 📊 核心输出

每个实验输出：

```text
Instance → Pass/Fail + Token Cost + Steps + Tool Usage
```

最终形成：

* cost vs performance 曲线（核心图）
* 不同策略对比

---

# 三、系统架构设计（System Architecture）

---

## 🧱 整体架构

```text
SWE-bench Task
      ↓
Code Agent（mini-swe-agent / Claude Code）
      ↓
LLM Gateway（中转层）
      ↓
多个模型（Claude / GLM / Qwen / DeepSeek）
```

---

## 🔌 中转层设计（关键）

### 推荐两种方案：

---

### ✅ 方案1：LiteLLM（推荐）

特点：

* OpenAI-compatible API
* 支持多模型
* 自动统计 token usage
* 支持 routing / fallback

---

### ✅ 方案2：OpenRouter（快速方案）

特点：

* 无需部署
* 多模型统一入口
* 按 token 计费

---

## 🔁 调用流程

```text
Agent → OpenAI API → LiteLLM → 实际模型
```

---

## 🧾 Token统计来源

每次请求记录：

```json
{
  "model": "xxx",
  "input_tokens": 1234,
  "output_tokens": 456,
  "total_tokens": 1690
}
```

---

# 四、日志与指标设计（Logging & Metrics）

---

## 📁 日志结构（核心）

每个 instance 生成：

```text
logs/
  ├── instance_id/
  │     ├── trajectory.jsonl
  │     ├── request_log.jsonl
  │     ├── summary.json
```

---

## 📌 request_log.jsonl（最重要）

```json
{
  "step": 3,
  "tool": "read_file",
  "model": "deepseek-chat",
  "input_tokens": 1200,
  "output_tokens": 200,
  "total_tokens": 1400,
  "latency": 1.2
}
```

---

## 📌 trajectory.jsonl

```json
{
  "step": 3,
  "action": "read_file",
  "target": "utils.py",
  "result": "..."
}
```

---

## 📌 summary.json

```json
{
  "instance_id": "...",
  "success": true,
  "total_tokens": 24500,
  "total_steps": 18,
  "tool_calls": 12,
  "runtime": 120
}
```

---

## 📊 关键评估指标

---

### 🎯 1. 效果指标

* Pass Rate（SWE-bench）
* Patch correctness

---

### 💰 2. 成本指标（重点）

* total tokens（核心）
* input tokens
* output tokens
* tool calls
* steps
* runtime

---

### 📈 3. 综合指标

```text
Efficiency = Pass Rate / Avg Token Cost
```

或画：

```text
x: token cost
y: pass rate
```

---

# 五、实验矩阵设计（Experiment Matrix）

---

## 🧪 Baselines

---

### Baseline 1：Vanilla Agent

* 无压缩
* full context
* 正常搜索

---

### Baseline 2：Naive RAG

* embedding top-k file
* 无结构信息

---

### Baseline 3：Small Model

* 替换模型
* 不改策略

---

## 🧪 我们的方法

---

### Exp 1：Context Compression

* top-k file
* function-level selection
* token budget

---

### Exp 2：Trajectory Pruning

* 限制 search 次数
* 限制 read 次数
* 去重访问

---

### Exp 3：Hybrid（核心）

* context + pruning

---

### Exp 4：Model Routing（可选）

* search → 小模型
* edit → 大模型

---

# 六、初步实验规划（Execution Plan）

---

## 🥇 Phase 1：基础框架搭建（1周）

目标：

* 跑通 SWE-bench（mini-swe-agent）
* 接入 LiteLLM / OpenRouter
* 能记录 token

任务：

* [ ] 接入 API gateway
* [ ] 打印 usage
* [ ] 实现 request_log

输出：

* baseline token cost

---

## 🥈 Phase 2：成本分析（1周）

目标：

* 分析 token 分布

任务：

* [ ] 统计：

  * read_file token
  * search token
  * reasoning token

输出：

* cost breakdown 图

---

## 🥉 Phase 3：Context Compression（1–2周）

目标：

* 减少输入 token

任务：

* [ ] top-k files
* [ ] function-level trimming
* [ ] token budget

输出：

* token ↓多少
* pass rate变化

---

## 🏅 Phase 4：Trajectory Pruning（1–2周）

目标：

* 减少步骤

任务：

* [ ] 去重 read
* [ ] 限制 search
* [ ] early stop

输出：

* step ↓
* token ↓

---

## 🏆 Phase 5：综合实验（1周）

目标：

* 最终对比

输出：

* Pareto curve（最重要）
* cost vs performance

---

# 七、预期结果（Expected Outcome）

---

## 🎯 你要证明：

> 在 SWE-bench 上：

* token ↓ 30%–70%
* pass rate ↓ < 5%

---

## 📈 最终图（论文核心）

```text
Vanilla Agent:     高成本，高性能
你的方法:         低成本，接近性能（Pareto优）
```

---

# 八、这个实验框架的价值（可以写在论文里）

---

## 学术价值

* 从“模型能力”转向“推理效率”
* 引入 agent-level pruning

---

## 工程价值

* 降低 API 成本
* 提升部署可行性

---

# 🚀 如果你下一步要继续推进

我强烈建议下一步做这个👇：

👉 **我帮你把：**

### ✅ mini-swe-agent 的 logging + token统计代码写出来（直接可用）

或者：

### ✅ context compression 的第一版实现（top-k + token budget）

这一步是你实验能不能跑起来的关键。
