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
│   ├── gateway/            # LLM 中转层（OpenAI-compatible proxy + Token统计）
│   │   ├── proxy.py        # LLMGateway / AsyncLLMGateway（同步/异步）
│   │   ├── token_logger.py # UsageRecord + TokenLogger（按step/tool统计）
│   │   └── server.py       # FastAPI 代理服务（本地监听，Agent侧透明）
│   ├── agent/              # Agent Runner & SWE-bench 接入
│   │   ├── runner.py       # AgentRunner（支持 mini-swe-agent / mock）
│   │   └── trajectory.py   # Trajectory + TrajectoryStep（轨迹记录）
│   ├── compression/        # Context Compression 方法
│   │   └── context_compressor.py  # TopKFileSelector / FunctionLevelTrimmer
│   │                               # TokenBudgetTrimmer / ContextCompressor
│   ├── pruning/            # Trajectory Pruning 方法
│   │   └── trajectory_pruner.py   # DeduplicationPruner / StepLimitPruner
│   │                               # SearchLimitPruner / EarlyStopPruner
│   └── analysis/           # 结果分析与可视化
│       ├── cost_analyzer.py  # CostAnalyzer（汇总表 / breakdown / pareto数据）
│       └── plotter.py        # ExperimentPlotter（Pareto曲线 / 对比柱状图）
├── configs/
│   ├── gateway.yaml                    # LLM Gateway 配置
│   └── experiments/
│       ├── baseline_vanilla.yaml       # 无优化基准
│       ├── exp1_compression.yaml       # Context Compression
│       ├── exp2_pruning.yaml           # Trajectory Pruning
│       ├── exp3_hybrid.yaml            # 组合（论文核心）
│       └── exp4_routing.yaml           # Model Routing（可选）
├── mini-swe-agent/         # git submodule → SWE-agent/mini-swe-agent
├── scripts/
│   ├── run_experiment.py   # 运行单个/批量实验
│   ├── analyze_results.py  # 分析结果，生成图表
│   ├── quick_test.py       # 本地验证框架（无需API）
│   └── setup_env.sh        # 一键初始化环境
├── experiments/            # 实验结果（gitignore，体积大）
├── logs/                   # 运行日志（gitignore）
├── figures/                # 生成的图表
├── tests/
│   ├── test_token_logger.py
│   └── test_compression.py
├── requirements.txt        # 项目依赖（宽松版本约束）
├── requirements.lock       # 精确锁定版本（pip freeze）
└── .env.example            # API Key 配置模板
```

---

## 快速开始

### 方法一：一键初始化（推荐）

```bash
git clone --recurse-submodules git@github.com:Dingzhen778/CodeAgentCostOptimization.git
cd CodeAgentCostOptimization
bash scripts/setup_env.sh
```

`setup_env.sh` 会自动完成：创建 venv → 安装依赖 → 安装 mini-swe-agent → 运行 quick_test 验证。

### 方法二：手动步骤

```bash
# 1. clone（含 submodule）
git clone --recurse-submodules git@github.com:Dingzhen778/CodeAgentCostOptimization.git
cd CodeAgentCostOptimization

# 2. 创建并激活 venv
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
pip install -e mini-swe-agent/

# 4. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 API key（DeepSeek / OpenRouter 等）

# 5. 验证安装
python scripts/quick_test.py
```

---

## 环境说明

### Python 版本

Python 3.12（推荐），3.10+ 均可。

### 依赖管理

使用 **venv**（非 conda），便于迁移和自动化：
- `requirements.txt` — 宽松版本约束，用于安装
- `requirements.lock` — `pip freeze` 精确锁定版本，用于复现

### 核心依赖版本（已验证）

| 包 | 版本 | 用途 |
|---|---|---|
| `litellm` | 1.82.6 | 多模型统一接入 |
| `openai` | 2.29.0 | OpenAI-compatible API 客户端 |
| `fastapi` + `uvicorn` | 0.135.1 / 0.42.0 | Gateway 代理服务 |
| `tiktoken` | 0.12.0 | Token 计数 |
| `pandas` + `numpy` | 3.0.1 / 1.26.4 | 数据分析 |
| `matplotlib` + `seaborn` | 3.10.8 / 0.13.2 | 可视化 |
| `loguru` + `rich` | 0.7.3 / 14.3.3 | 日志输出 |
| `pytest` | 8.1.1 | 单元测试 |
| `mini-swe-agent` | 2.2.7 | Code Agent 执行引擎（submodule） |

### 测试状态

```
5/5 tests passed — All tests passed! Framework is ready.

✅ TokenLogger      — token记录与JSONL写入
✅ Trajectory       — 轨迹记录与去重查询
✅ ContextCompressor — 10→3 文件压缩，ratio=0.30
✅ TrajectoryPruner  — 去重+步骤限制，2次剪枝
✅ AgentRunner(mock) — 完整运行流程（无需API）
```

---

## 实验矩阵

| 实验 | 方法 | 预期 token 节省 | 预期 pass rate 变化 |
|------|------|----------------|-------------------|
| `baseline_vanilla` | 无优化 | — | — |
| `baseline_small_model` | 替换小模型 | ↓ 50–80% | ↓ 10–30% |
| `exp1_compression` | top-k + token budget | ↓ 20–40% | ↓ 0–5% |
| `exp2_pruning` | 去重 + 限制步骤 | ↓ 15–30% | ↓ 0–3% |
| `exp3_hybrid` | Compression + Pruning | ↓ 35–60% | ↓ 0–8% |
| `exp4_routing` | search→小模型, edit→大模型 | ↓ 30–50% | ↓ 0–5% |

### 运行实验

```bash
source .venv/bin/activate

# Mock 模式（本地调试，无需 API）
python scripts/run_experiment.py \
    --config configs/experiments/baseline_vanilla.yaml \
    --mock --instances 5

# 真实模式
python scripts/run_experiment.py \
    --config configs/experiments/exp3_hybrid.yaml \
    --split lite --instances 50 --workers 4

# 分析结果，生成图表
python scripts/analyze_results.py --exp-dir experiments/ --output figures/
```

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

### 综合效率指标
```
Efficiency = Pass Rate / Avg Token Cost × 10^6
```

### 日志结构

每个 instance 运行后生成：

```
experiments/{exp_name}/{instance_id}/
    ├── request_log.jsonl   # 每次 LLM 调用记录（step/tool/tokens/latency）
    ├── trajectory.jsonl    # 每步 Agent 动作记录
    ├── summary.json        # 汇总统计（tokens/steps/success）
    ├── result.json         # 最终结果
    └── patch.diff          # 生成的代码补丁
```

---

## 分阶段规划

| Phase | 内容 | 时长 | 状态 |
|-------|------|------|------|
| Phase 0 | 框架搭建 + 环境配置 + 基础模块 | 1 周 | ✅ 完成 |
| Phase 1 | 接入真实 API + baseline token 记录 | 1 周 | 🔲 进行中 |
| Phase 2 | Token 消耗结构分析（breakdown） | 1 周 | 🔲 待开始 |
| Phase 3 | Context Compression 实验 | 1–2 周 | 🔲 待开始 |
| Phase 4 | Trajectory Pruning 实验 | 1–2 周 | 🔲 待开始 |
| Phase 5 | 综合实验 + Pareto 曲线 | 1 周 | 🔲 待开始 |

---

## API 配置

项目通过 `.env` 文件管理 API Key，支持多个廉价中转站：

```bash
cp .env.example .env
```

推荐优先使用（低成本）：
- **DeepSeek** — `deepseek-chat`，性价比极高
- **OpenRouter** — 统一入口，支持多模型
- **Qwen / GLM** — 国内访问稳定

详见 `.env.example`。

---

## 参考

- [SWE-bench](https://www.swebench.com/)
- [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent)
- [LiteLLM](https://github.com/BerriAI/litellm)
- [Claude Code](https://claude.ai/code)
- [OpenRouter](https://openrouter.ai/)
- [DeepSeek API](https://platform.deepseek.com/)
