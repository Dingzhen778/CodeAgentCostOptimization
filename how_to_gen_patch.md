# How To Generate Patch

## 1. Patch 生成流程在哪里

当前仓库里，真实 patch 生成链路的核心入口是：

- [src/agent/runner.py](/home/azureuser/jrh/CodeAgentCostOptimization/src/agent/runner.py)
  - `AgentRunner._run_mini_swe_agent()`
  - 这里会调用：
    - `python -m minisweagent.run.mini`
  - 并加载官方 benchmark 配置：
    - `mini-swe-agent/src/minisweagent/config/benchmarks/swebench.yaml`

patch 提交规则来自官方 `mini-swe-agent` 的 SWE-bench 配置：

- [mini-swe-agent/src/minisweagent/config/benchmarks/swebench.yaml](/home/azureuser/jrh/CodeAgentCostOptimization/mini-swe-agent/src/minisweagent/config/benchmarks/swebench.yaml)

关键提交动作是：

1. agent 在容器内先生成 `patch.txt`
2. 然后执行：

```bash
echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt
```

`mini-swe-agent` 环境层在看到这条命令后，会把 patch 记到 trajectory 的 `info.submission`。

本仓库后处理逻辑：

- [src/agent/runner.py](/home/azureuser/jrh/CodeAgentCostOptimization/src/agent/runner.py)
  - `_extract_submission_patch()` 从 `trajectory.json` 里取出 `info.submission`
  - `InstanceResult.save()` 再把它写成本地的 `patch.diff`

## 2. 常用运行方式

### 2.1 最小链路冒烟

这个只验证“能不能生成 patch”，不追求修真实 benchmark 问题：

```bash
source .venv/bin/activate
python scripts/smoke_test_e2e.py
```

相关脚本：

- [scripts/smoke_test_e2e.py](/home/azureuser/jrh/CodeAgentCostOptimization/scripts/smoke_test_e2e.py)

### 2.2 跑真实实验入口

通用实验入口：

```bash
source .venv/bin/activate
python scripts/run_experiment.py \
  --config configs/experiments/exp3_hybrid.yaml \
  --split lite \
  --instances 10 \
  --workers 1
```

相关脚本：

- [scripts/run_experiment.py](/home/azureuser/jrh/CodeAgentCostOptimization/scripts/run_experiment.py)

### 2.3 跑官方 verified sweep

如果要直接按模型批次跑官方 verified Docker：

```bash
source .venv/bin/activate
python scripts/run_verified_model_sweep.py \
  --batch minimax \
  --per-model 10 \
  --max-steps 60 \
  --start-index 0 \
  --output-dir experiments/verified_model_sweep_150
```

相关脚本：

- [scripts/run_verified_model_sweep.py](/home/azureuser/jrh/CodeAgentCostOptimization/scripts/run_verified_model_sweep.py)

参数说明：

- `--batch dpsk|glm|minimax|all`
- `--per-model`：每个模型跑多少个 instance
- `--max-steps`：传给 `mini-swe-agent` 的 `agent.step_limit`
- `--start-index`：从 verified 数据集的哪个位置开始切片
- `--output-dir`：实验输出根目录

## 3. 运行前提

需要满足：

1. 已安装依赖与 submodule

```bash
pip install -r requirements.txt
pip install -e mini-swe-agent/
```

2. 已配置 API 环境变量

最少需要：

```bash
export NEW_API_KEY=你的KEY
```

推荐：

```bash
export NEW_API_BASE_URL=https://newapi.deepwisdom.ai/v1
export NEW_API_MODEL=deepseek-v3.2
export NEW_API_EDIT_MODEL=glm-4.7
export NEW_API_WRITE_MODEL=glm-4.7
```

3. 本机 Docker 可用

```bash
docker ps
```

## 4. patch 生成后会落到哪里

单个 instance 成功后，标准输出目录结构是：

```text
experiments/{experiment}/{instance_id}/
├── trajectory.json
├── result.json
└── patch.diff
```

具体含义：

- `trajectory.json`
  - mini-swe-agent 原始轨迹
  - 里面的 `info.submission` 是 patch 原始来源

- `result.json`
  - 本仓库写出的实例级结果
  - 包含 `success`、`runtime`、`input_tokens`、`output_tokens`、`total_tokens`

- `patch.diff`
  - 本仓库从 `trajectory.json -> info.submission` 提取后写出的最终 patch 文件

## 5. 当前仓库里已经存在的 patch 结果在哪里

真实已有 patch 产物主要在：

- smoke:
  - [experiments/local_docker_smoke/pandas__pandas-63136/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/local_docker_smoke/pandas__pandas-63136/patch.diff)
  - [experiments/local_docker_smoke_v2/pandas__pandas-63136/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/local_docker_smoke_v2/pandas__pandas-63136/patch.diff)

- verified sweep:
  - [experiments/verified_model_sweep_150/verified_dpsk_50/astropy__astropy-13977/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_dpsk_50/astropy__astropy-13977/patch.diff)
  - [experiments/verified_model_sweep_150/verified_dpsk_50/astropy__astropy-14309/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_dpsk_50/astropy__astropy-14309/patch.diff)
  - [experiments/verified_model_sweep_150/verified_glm_50/django__django-11603/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_glm_50/django__django-11603/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13128/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13128/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13158/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13158/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13195/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13195/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13212/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13212/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13297/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13297/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13315/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13315/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13343/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13343/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13346/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13346/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13363/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13363/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13401/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13401/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13410/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13410/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13417/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13417/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13512/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13512/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13516/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13516/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13551/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13551/patch.diff)
  - [experiments/verified_model_sweep_150/verified_minimax_50/django__django-13568/patch.diff](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/verified_minimax_50/django__django-13568/patch.diff)

## 6. 如何快速检查某个 patch 是否存在

例如查看所有已生成 patch：

```bash
find experiments -name patch.diff | sort
```

例如只看 verified sweep：

```bash
find experiments/verified_model_sweep_150 -name patch.diff | sort
```

## 7. 当前推荐理解方式

如果你只是想知道“patch 是怎么来的”，按这条链理解就够了：

1. `scripts/run_experiment.py` 或 `scripts/run_verified_model_sweep.py`
2. `src/agent/runner.py`
3. `python -m minisweagent.run.mini`
4. 容器内执行修复
5. `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt`
6. `trajectory.json -> info.submission`
7. 本仓库写出 `patch.diff`
