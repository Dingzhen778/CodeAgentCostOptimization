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
│   ├── aggregate_gateway_logs.py # 聚合 gateway 全局日志到实例级汇总
│   ├── quick_test.py       # 本地验证框架（无需API）
│   ├── smoke_test_e2e.py   # gateway + mini-swe-agent 端到端冒烟测试
│   ├── test_newapi_models.py # 列出/验证 New API 模型
│   └── setup_env.sh        # 一键初始化环境
├── experiments/            # 实验结果（gitignore，体积大）
├── logs/                   # 运行日志（gitignore）
├── figures/                # 生成的图表
├── tests/
│   ├── test_token_logger.py
│   ├── test_compression.py
│   ├── test_config_utils.py
│   ├── test_gateway_log_aggregation.py
│   └── test_cost_analyzer_gateway.py
├── requirements.txt        # 项目依赖（宽松版本约束）
├── requirements.lock       # 精确锁定版本（pip freeze）
└── .env.example            # API Key 配置模板
```

---

## 当前进度（2026-03-25）

当前仓库已经从“框架草图”推进到“New API 可真实跑通、gateway token 可按 instance 汇总、分析链可优先读取真实 token”的状态。

已经完成：
- New API（`https://newapi.deepwisdom.ai/v1`）真实可用，已验证 `deepseek-v3.2`、`glm-4.7`、`kimi-k2.5`
- New API 额外可用模型已验证 `MiniMax-M2.5`、`MiniMax-M2.7`
- `scripts/test_newapi_models.py` 可直接列模型并发最小请求
- `scripts/smoke_test_e2e.py` 可自动完成 `gateway -> direct chat -> mini-swe-agent` 冒烟
- `src/gateway/server.py` 会把 `instance_id / experiment / strategy` 写入 `logs/gateway/gateway_token_log.jsonl`
- `scripts/aggregate_gateway_logs.py` 可把 gateway 全局日志聚合成实例级 summary
- `src/analysis/cost_analyzer.py` 已改为优先读取 `gateway_instance_summary.json`
- `src/agent/runner.py` 已从旧的 `sweagent.run` 改为使用 `mini-swe-agent` 的 SWE-bench Docker 配置路径
- 配置支持 `${VAR:-default}`，只配 `NEW_API_KEY` 也能跑默认链路
- `FunctionLevelTrimmer` 的真实失败测试已经修复，`tests/test_compression.py` 现已通过

当前推荐默认模型路由：
- `NEW_API_MODEL=deepseek-v3.2`
- `NEW_API_EDIT_MODEL=glm-4.7`
- `NEW_API_WRITE_MODEL=glm-4.7`

已知边界：
- `glm-4.7` / `kimi-k2.5` 有时会把主要内容放进 `reasoning_content`
- `kimi-k2.5` 需要 `temperature=1`
- `MiniMax-M2.5` / `MiniMax-M2.7` 也会偏向把输出放进 `reasoning_content`
- 当前这台机器不能启动 Docker，因此 `AgentRunner` 的 SWE-bench Docker 路径已经接好，但尚未在本机完成容器级验证
- `tests/test_compression.py::test_function_trimmer` 已修复；如果压缩测试再失败，应优先检查 `FunctionLevelTrimmer` 相关性匹配逻辑

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
# 编辑 .env，填入你的 API key（推荐 New API）

# 推荐：直接使用 New API 环境变量
export NEW_API_BASE_URL=https://newapi.deepwisdom.ai/v1
export NEW_API_KEY=你的NEW_API_KEY
export NEW_API_MODEL=deepseek-v3.2
export NEW_API_EDIT_MODEL=glm-4.7
export NEW_API_WRITE_MODEL=glm-4.7

# 5. 验证安装
python scripts/quick_test.py

# 6. 验证 New API 模型
python scripts/test_newapi_models.py --models deepseek-v3.2 glm-4.7 kimi-k2.5

# 7. 端到端冒烟测试（gateway + mini-swe-agent + token日志）
python scripts/smoke_test_e2e.py
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
当前新增链路已验证：

✅ TokenLogger      — token记录与JSONL写入
✅ Trajectory       — 轨迹记录与去重查询
✅ ContextCompressor — 10→3 文件压缩，ratio=0.30
✅ TrajectoryPruner  — 去重+步骤限制，2次剪枝
✅ AgentRunner(mock) — 完整运行流程（无需API）
✅ New API Model Test — deepseek/glm/kimi 最小调用通过
✅ E2E Smoke Test — gateway + mini-swe-agent 跑通
✅ Gateway Aggregation — instance级 token 汇总通过
✅ CostAnalyzer(gateway-first) — 优先读取真实 gateway token
✅ FunctionLevelTrimmer Fix — 真实失败测试已修复
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

# 聚合 gateway token 日志为实例级成本文件
python scripts/aggregate_gateway_logs.py \
    --log-file logs/gateway/gateway_token_log.jsonl \
    --output experiments/exp3_hybrid/gateway_instance_summary.json \
    --experiment exp3_hybrid

# 分析结果，生成图表
python scripts/analyze_results.py --exp-dir experiments/ --output figures/
```

说明：
- `scripts/run_experiment.py` 现在会在实验结束后自动尝试写入 `experiments/<experiment>/gateway_instance_summary.json`
- `src/analysis/cost_analyzer.py` 会优先读取这个 gateway 实例级汇总做 Pareto / summary / breakdown
- 如果该文件不存在，才回退到旧的 `summary.json` / `request_log.jsonl`

---

## How To Use

### 1. 新机器最短上手路径

```bash
git clone --recurse-submodules <repo>
cd CodeAgentCostOptimization
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e mini-swe-agent/
cp .env.example .env
```

`.env` 至少保证有：

```bash
export NEW_API_KEY=你的token
```

可选但推荐：

```bash
export NEW_API_BASE_URL=https://newapi.deepwisdom.ai/v1
export NEW_API_MODEL=deepseek-v3.2
export NEW_API_EDIT_MODEL=glm-4.7
export NEW_API_WRITE_MODEL=glm-4.7
```

### 2. 先验证 API 是否可用

```bash
python scripts/test_newapi_models.py --filter deepseek glm kimi --list
python scripts/test_newapi_models.py --models deepseek-v3.2 glm-4.7 kimi-k2.5
```

### 3. 跑完整冒烟

```bash
python scripts/smoke_test_e2e.py
```

这一步会验证：
- gateway 能启动
- gateway 能真实转发到 New API
- mini-swe-agent 能经由 gateway 完成一个最小任务
- 轨迹文件能落盘

### 4. 跑真实实验

如果机器可以运行 Docker，优先走这条路径。
当前 `AgentRunner` 已按 `mini-swe-agent` 的 SWE-bench benchmark 方式配置为 Docker 环境。

```bash
python scripts/run_experiment.py \
  --config configs/experiments/exp3_hybrid.yaml \
  --split lite \
  --instances 10 \
  --workers 1
```

如果当前机器不能运行 Docker：
- 不要直接用 `run_experiment.py` 跑正式 SWE-bench 实验
- 先只使用 `test_newapi_models.py`、`smoke_test_e2e.py` 和分析脚本维护上层链路
- 等换到能起 Docker 的服务器后，再跑正式 benchmark

### 5. 分析真实 token 成本

通常 `run_experiment.py` 结束后会自动写：

```bash
experiments/<experiment>/gateway_instance_summary.json
```

如果没有自动写出来，手动执行：

```bash
python scripts/aggregate_gateway_logs.py \
  --log-file logs/gateway/gateway_token_log.jsonl \
  --output experiments/exp3_hybrid/gateway_instance_summary.json \
  --experiment exp3_hybrid
```

然后分析：

```bash
python scripts/analyze_results.py --exp-dir experiments --output figures
```

---

## 接手说明

给下一位 Codex / 新服务器的最重要信息：

1. 真实 token 成本的“真来源”现在是 gateway 日志，不是旧的本地 `request_log.jsonl`
2. `src/analysis/cost_analyzer.py` 已经优先读取 `gateway_instance_summary.json`
3. `scripts/aggregate_gateway_logs.py` 是连接“全局 gateway 日志”和“实验级分析”的关键桥梁
4. `src/agent/runner.py` 现在依赖 `minisweagent.run.mini`，不要再切回旧的 `sweagent.run`
5. `src/agent/runner.py` 现在会按 SWE-bench Docker 路径构造镜像名：
   - 优先使用 `instance["image_name"]` 或 `instance["docker_image"]`
   - 否则回退到 `docker.io/swebench/sweb.eval.x86_64.<instance_id>:latest`
6. 如果当前机器不能起 Docker，优先先跑 `python scripts/smoke_test_e2e.py`，不要直接开大规模 experiment
7. 如果换到新服务器，先确认 `docker` 可用，再跑正式 SWE-bench instance
8. 如果分析结果 token 还是空，先检查：
   - `logs/gateway/gateway_token_log.jsonl` 是否存在
   - 日志里是否带 `instance_id`
   - `experiments/<experiment>/gateway_instance_summary.json` 是否生成
9. 如果要继续做论文实验，下一步最值得推进的是：
   - 把更多 tool hint（search / edit / read_file）真正传到 gateway
   - 做 `exp4_routing` 的真实多模型路由实验
   - 把 gateway instance summary 自动 merge 回每个 `summary.json`

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
    ├── request_log.jsonl   # 旧的本地 token logger（mock/旧链路）
    ├── trajectory.json     # mini-swe-agent 轨迹
    ├── summary.json        # 汇总统计（tokens/steps/success）
    ├── result.json         # 最终结果
    └── patch.diff          # 生成的代码补丁
```

全局 gateway 真实 token 日志：

```
logs/gateway/
    ├── gateway_token_log.jsonl         # 每次代理请求一条
    └── gateway_instance_summary.json   # 按 instance 聚合后的汇总
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
