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

## 当前进度（2026-03-30）

当前仓库已经从“框架草图”推进到“mini-swe-agent + official SWE-bench Docker + gateway token统计 + 阶段化token分析”都能真实跑通的状态。

已经完成：
- New API（`https://newapi.deepwisdom.ai/v1`）真实可用，已验证 `deepseek-v3.2`、`glm-4.7`、`kimi-k2.5`
- New API 额外可用模型已验证 `MiniMax-M2.5`、`MiniMax-M2.7`
- 当前 Scitix provider（`.env` 中 `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`）已验证可用模型：
  - `zai-org/GLM-5`
  - `moonshotai/Kimi-K2.5`
  - `MiniMaxAI/MiniMax-M2.5`
  - `Qwen/Qwen3.5-397B-A17B`
- `scripts/test_newapi_models.py` 可直接列模型并发最小请求
- `scripts/smoke_test_e2e.py` 可自动完成 `gateway -> direct chat -> mini-swe-agent` 冒烟
- `src/gateway/server.py` 会把 `instance_id / experiment / strategy` 写入 `logs/gateway/gateway_token_log.jsonl`
- `scripts/aggregate_gateway_logs.py` 可把 gateway 全局日志聚合成实例级 summary
- `src/analysis/cost_analyzer.py` 已改为优先读取 `gateway_instance_summary.json`
- `src/agent/runner.py` 已从旧的 `sweagent.run` 改为使用 `mini-swe-agent` 的 SWE-bench Docker 配置路径
- 本机 Docker 已可用，已成功拉起官方 `SWE-bench Verified` 镜像并在容器内执行真实 issue
- `src/gateway/server.py` 已修复“显式请求模型被 routing.default 覆盖”的问题，`DPSK / GLM / MINIMAX` 现在会按指定模型真实发出请求
- 已完成一轮 `verified_model_sweep_150` 中途暂停实验，并沉淀阶段化 token 分析产物
- `src/analysis/token_phase_analyzer.py` 与 `scripts/analyze_token_phases.py` 已可输出阶段化 token 画像
- 配置支持 `${VAR:-default}`，只配 `NEW_API_KEY` 也能跑默认链路
- `FunctionLevelTrimmer` 的真实失败测试已经修复，`tests/test_compression.py` 现已通过

当前推荐默认模型路由：
- `NEW_API_MODEL=deepseek-v3.2`
- `NEW_API_EDIT_MODEL=glm-4.7`
- `NEW_API_WRITE_MODEL=glm-4.7`

当前这轮 provider 试跑的经验结论：
- 如果目标是“先把题跑通 + token 不要太高”，优先考虑 `zai-org/GLM-5`
- `moonshotai/Kimi-K2.5` 可用，但要注意 `temperature=1`
- `MiniMaxAI/MiniMax-M2.5`、`Qwen/Qwen3.5-397B-A17B` 可用，但输出风格偏 reasoning-heavy
- `deepseek-ai/DeepSeek-V3.2` 虽然能在 `/models` 中列出，但当前 provider 实际调用返回 404，暂时不要作为正式实验默认模型

已知边界：
- `glm-4.7` / `kimi-k2.5` 有时会把主要内容放进 `reasoning_content`
- `kimi-k2.5` 需要 `temperature=1`
- `MiniMax-M2.5` / `MiniMax-M2.7` 也会偏向把输出放进 `reasoning_content`
- `verified_model_sweep_150` 是一次真实中途暂停的 sweep，不是最终 benchmark；目录里既有成功落盘的结果，也有被暂停或 APIError 提前终止的实例目录
- `Qwen/Qwen3.5-397B-A17B` 可用，但这轮小题测试中 token 消耗高于 `GLM-5`
- 当前 Scitix provider 上 `deepseek-ai/DeepSeek-V3.2` 在 `chat.completions` 和 `completions` 两条路径都返回 404
- Docker 可用性取决于当前服务器；正式 SWE-bench benchmark 之前必须先确认 `docker --version` 和单题实例拉起是否正常
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

如果你当前主要使用的是 Scitix provider（即 `.env` 中 `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` 这组变量），建议先单独做一轮最小模型验证，再决定正式实验默认模型。

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

如果要跑官方 `SWE-bench Verified` 的大规模实验，推荐优先用单独脚本控制批次和模型：

```bash
python scripts/run_verified_model_sweep.py \
  --batch minimax \
  --per-model 10 \
  --max-steps 60 \
  --start-index 0 \
  --output-dir experiments/verified_model_sweep_150
```

说明：
- `--batch dpsk|glm|minimax|all` 控制跑哪个模型批次
- 当前脚本会把前 `3 * per-model` 个 verified instance 切成互不重叠的 3 段
- `verified_model_sweep_150` 是真实 sweep 产物目录，不是固定配置名；可以换成新的输出目录重复实验

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
6. 当前机器已经可以运行 Docker；如果换到新服务器，先确认 `docker` 可用，再跑正式 SWE-bench instance
7. 如果只想验证上层链路是否通，优先先跑 `python scripts/smoke_test_e2e.py`，不要直接开大规模 experiment
8. 如果分析结果 token 还是空，先检查：
   - `logs/gateway/gateway_token_log.jsonl` 是否存在
   - 日志里是否带 `instance_id`
   - `experiments/<experiment>/gateway_instance_summary.json` 是否生成
9. 如果要继续做论文实验，下一步最值得推进的是：
   - 基于 `token_phase_analysis.json` 先做 token 消耗结构分析
   - 优先推进 `search + read` 侧的 token 节省方法（RAG / observation compression）
   - 再做 `exp4_routing` 的真实多模型路由实验

---

## 下一步实验方案

以下方案按“先验证基础设施，再拿有效数据”的顺序组织，适合下一台能起 Docker 的服务器继续执行。

### Phase 1: 环境与单题验证

目标：
- 确认 Docker 可用
- 确认单个 SWE-bench instance 能正常拉起镜像
- 确认 gateway token 日志包含 `instance_id`

建议步骤：
1. 检查 `docker --version`
2. 跑一个单题实例（优先 SWE-bench Lite，`workers=1`）
3. 检查：
   - `logs/gateway/gateway_token_log.jsonl`
   - `experiments/<experiment>/<instance_id>/trajectory.json`
   - `experiments/<experiment>/gateway_instance_summary.json`

成功标准：
- agent 能提交 `submission/patch`
- gateway log 中出现该 `instance_id`
- analyzer 能读取该实验 token

### Phase 2: 模型筛选实验

目标：
- 在同一小批样本上比较不同模型的 token / latency / 可用性
- 选出正式实验的 base model

建议候选模型：
- `zai-org/GLM-5`
- `moonshotai/Kimi-K2.5`
- `MiniMaxAI/MiniMax-M2.5`
- `Qwen/Qwen3.5-397B-A17B`

暂不建议作为默认模型：
- `deepseek-ai/DeepSeek-V3.2`
原因：当前 provider 实际调用 404

建议设置：
- 单次只跑 `lite` 子集前 `5~10` 题
- `workers=1`
- 固定 prompt / config

输出指标：
- `pass_rate`
- `avg_total_tokens`
- `avg_runtime`
- `tool_breakdown`

### Phase 3: 方法实验

目标：
- 比较 baseline / compression / pruning / hybrid

建议顺序：
1. `baseline_vanilla`
2. `exp1_compression`
3. `exp2_pruning`
4. `exp3_hybrid`

建议规模：
- 第一轮：每个实验 `10~20` 题
- 第二轮：筛掉明显差的配置，再扩大到 `50+` 题

### Phase 4: 路由实验

目标：
- 验证不同动作用不同模型是否能降低成本

建议起步配置：
- `read/search/bash` -> `zai-org/GLM-5`
- `edit/write_file` -> `Qwen/Qwen3.5-397B-A17B` 或 `MiniMaxAI/MiniMax-M2.5`

观察重点：
- edit 类动作的 patch 成功率是否提高
- token 是否明显下降
- reasoning-heavy 模型是否导致 tool call 风格不稳定

### Phase 5: 论文数据沉淀

最终需要固定保存：
- 每个实验的 `experiment_summary.json`
- 每个实验的 `gateway_instance_summary.json`
- `figures/` 下的 Pareto / comparison / breakdown 图

最终表格建议至少包含：
- model
- experiment
- instances
- pass_rate
- avg_total_tokens
- token_saving_pct
- efficiency

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

### `experiments/` 目录说明

当前 `experiments/` 里既有历史 smoke run，也有真实 issue run 和中途暂停的 sweep。目录名本身就是实验语义的一部分，后续继续加实验时应尽量沿用这种命名风格。

常见目录含义如下：

- `local_docker_smoke/`
  - 最早的本地 Docker 冒烟验证
  - 目标是确认 `mini-swe-agent -> docker -> patch -> token统计` 链路是否可用
  - patch 不是正式 benchmark patch

- `local_docker_smoke_v2/`
  - 第二版本地 Docker 冒烟
  - 在 `runner` 支持从 gateway 日志回填 token 之后重跑
  - 用于验证 `result.json` 里能写入真实 token 字段

- `resolve_pandas_63136_try1/`
- `resolve_pandas_63136_fullrun_1/`
- `resolve_pandas_63136_steps60_try2/`
  - 针对本地 `pandas__pandas-63136` 镜像的真实 issue 运行
  - 用于验证“不是 smoke task，而是真实问题描述”时的 agent 行为
  - `fullrun` / `steps60` 反映了不同 step budget 或不同尝试轮次

- `verified_astropy_14365_try1/`
- `verified_astropy_14365_glm47/`
- `verified_astropy_14365_minimax27/`
- `tmp_glm_verified_14365*`
- `tmp_minimax_verified_14365*`
  - 单实例的官方 `SWE-bench Verified` 探针实验
  - 作用是验证：
    - 官方镜像能否拉起
    - 指定模型是否真的生效
    - `mini-swe-agent` 是否能消费对应模型的输出格式

- `verified_parallel10_steps60/`
  - 一次并发 10 个 verified instance、`step=60` 的中间实验目录
  - 该目录主要用于观察“更高 step + 并发”时的收敛情况
  - 目录里可能只有 `trajectory.json` 而没有完整 `result.json`

- `verified_model_sweep_150/`
  - 当前最重要的实验目录
  - 这是 `DPSK / GLM / MINIMAX` 三个模型分批 sweep 的输出根目录
  - 子目录：
    - `verified_dpsk_50/`
    - `verified_glm_50/`
    - `verified_minimax_50/`
  - 每个子目录下再按 `instance_id/` 存放单实例结果
  - 注意：这是一次中途暂停的真实 sweep，所以有些实例是完整结果，有些是部分轨迹，有些是 APIError 提前结束

- `sample_20_instance_comparison.json`
  - 论文/汇报用的 mock summary 数据
  - 不是线上真实实验结果

### `verified_model_sweep_150/` 内部文件说明

这个目录现在同时承担了“中间实验结果仓库”和“阶段分析产物仓库”的角色。

- `verified_*_50/<instance_id>/trajectory.json`
  - mini-swe-agent 原始轨迹
  - 是做 step-level / phase-level token 分析的主数据源

- `verified_*_50/<instance_id>/result.json`
  - 单实例最终结果
  - 包含 `success`、`runtime`、`input_tokens`、`output_tokens`、`total_tokens`

- `verified_*_50/<instance_id>/patch.diff`
  - 仅在成功提交 patch 时存在

- `verified_*_50_gateway.log`
  - 当次批量运行时本地 gateway 的 stdout/stderr 日志
  - 用于排查模型路由、APIError、健康检查等问题

- `token_phase_analysis.json`
  - 详细阶段分析结果
  - 包含每个实验、每个实例的 phase breakdown

- `token_phase_summary.json`
  - 从详细分析中抽出的机器可读摘要
  - 适合后续脚本消费

- `token_phase_summary.csv`
  - 表格化汇总
  - 适合直接导入 Excel / pandas / 画图脚本

- `token_phase_findings.md`
  - 当前阶段分析的文字结论
  - 适合快速了解“token 到底花在哪”

### 后续维护建议

- 新增实验目录时，优先用“任务语义 + 轮次/设置”命名，例如：
  - `verified_minimax_steps40_try1`
  - `rag_verified_minimax_20`
  - `compression_ablation_v1`
- 如果是中途暂停或 probe 实验，目录名里显式写出 `tmp`、`probe`、`tryN`，避免后续误当最终 benchmark
- 如果目录里主要是分析产物，应把结论文档和机器可读摘要都放在同一层，保持和 `verified_model_sweep_150/` 一样的组织方式

---

## 分阶段规划

| Phase | 内容 | 时长 | 状态 |
|-------|------|------|------|
| Phase 0 | 框架搭建 + 环境配置 + 基础模块 | 1 周 | ✅ 完成 |
| Phase 1 | 接入真实 API + baseline token 记录 | 1 周 | ✅ 完成 |
| Phase 2 | Token 消耗结构分析（breakdown） | 1 周 | ✅ 第一版完成 |
| Phase 3 | Context Compression / Retrieval 实验 | 1–2 周 | 🔲 待开始 |
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
