# CodeAgentCostOptimization

> 📌 毕业设计项目：面向 SWE-bench 的 Code Agent 推理成本优化

---

## 研究动机

当前 Code Agent（如 Claude Code）在 SWE-bench 等软件工程任务上的任务成功率不断提升，但**推理成本（token 消耗）急剧上升**：

- ❌ 每个任务需要大量上下文（整个 repo / 多文件）
- ❌ 多轮交互导致 token 爆炸
- ❌ Agent 存在大量无效探索（重复 search / read）
- ❌ 同一 repo 的多个任务重复计算

**核心观察：** Code Agent 的成本主要来自 **上下文冗余 + 行为冗余 + 跨任务冗余**

---

## 项目目标

1. 构建可量化评估 Code Agent 推理成本的实验框架
2. 分析 token 消耗结构（breakdown）
3. 实现 Context Compression + Trajectory Pruning
4. 画出 **Cost vs Performance Pareto 曲线**

**预期结果：token ↓ 30–70%，pass rate ↓ < 5%**

---

## 系统架构

```
SWE-bench Task
      ↓
Code Agent（mini-swe-agent / Claude Code）
      ↓
LLM Gateway（中转层，廉价 API 接入）
    ├── Context Compression（上下文压缩）
    ├── Trajectory Pruning（轨迹剪枝）
    └── Token Logger（成本追踪）
      ↓
多个模型（Claude / DeepSeek / Qwen / GLM）
```

---

## 项目结构

```
CodeAgentCostOptimization/
├── src/
│   ├── gateway/          # LLM 中转层（OpenAI-compatible proxy）
│   ├── agent/            # Agent Runner & SWE-bench 接入
│   ├── compression/      # Context Compression 方法
│   ├── pruning/          # Trajectory Pruning 方法
│   └── analysis/         # Token 分析与可视化
├── configs/              # 实验配置（YAML）
├── experiments/          # 实验结果存储
├── logs/                 # 详细运行日志
├── scripts/              # 运行脚本
├── notebooks/            # 分析 Notebook
├── tests/                # 单元测试
└── requirements.txt
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API

```bash
cp .env.example .env
# 编辑 .env，填入你的 API key
```

### 3. 启动 LLM Gateway

```bash
python -m src.gateway.server --config configs/gateway.yaml
```

### 4. 运行 Baseline 实验

```bash
python scripts/run_experiment.py \
    --config configs/experiments/baseline_vanilla.yaml \
    --instances swe-bench-lite \
    --output experiments/baseline_vanilla/
```

### 5. 分析结果

```bash
python scripts/analyze_results.py --exp-dir experiments/baseline_vanilla/
# 或打开 notebooks/cost_analysis.ipynb
```

---

## 实验矩阵

| 实验 | 方法 | 预期 token 节省 | 预期 pass rate 变化 |
|------|------|----------------|-------------------|
| Baseline-Vanilla | 无优化 | - | - |
| Baseline-SmallModel | 替换小模型 | ↓ 50–80% | ↓ 10–30% |
| Exp1-ContextCompression | top-k + token budget | ↓ 20–40% | ↓ 0–5% |
| Exp2-TrajectoryPruning | 去重 + 限制步骤 | ↓ 15–30% | ↓ 0–3% |
| Exp3-Hybrid | Compression + Pruning | ↓ 35–60% | ↓ 0–8% |
| Exp4-ModelRouting | search→小模型, edit→大模型 | ↓ 30–50% | ↓ 0–5% |

---

## 核心指标

### 效果指标
- **Pass Rate**（SWE-bench resolve rate）

### 成本指标
- `total_tokens`（核心）
- `input_tokens` / `output_tokens`
- `tool_calls` 次数
- `steps` 数
- `runtime`（秒）

### 综合指标
```
Efficiency = Pass Rate / Avg Token Cost × 10^6
```

---

## 分阶段规划

| Phase | 内容 | 时长 |
|-------|------|------|
| Phase 1 | 框架搭建 + baseline token 记录 | 1 周 |
| Phase 2 | Token 消耗结构分析（breakdown）| 1 周 |
| Phase 3 | Context Compression 实现 | 1–2 周 |
| Phase 4 | Trajectory Pruning 实现 | 1–2 周 |
| Phase 5 | 综合实验 + Pareto 曲线 | 1 周 |

---

## 参考

- [SWE-bench](https://www.swebench.com/)
- [mini-swe-agent](https://github.com/SWE-bench/mini-swe-agent)
- [LiteLLM](https://github.com/BerriAI/litellm)
- [Claude Code](https://claude.ai/code)
