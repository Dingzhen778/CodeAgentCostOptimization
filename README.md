# CodeAgentCostOptimization

面向 `SWE-bench` 代码修复智能体的 token 成本优化实验仓库。当前主线是基于 `mini-swe-agent + official SWE-bench Docker + 本地 gateway token 统计`，比较不同上下文压缩方法在 patch 生成任务上的成本与成功率。

## 当前状态

- `mini-swe-agent` 真实 patch 生成链路已跑通
- `SWE-bench Verified` 官方 Docker 镜像已跑通
- gateway 可按 `instance / experiment / strategy` 记录 token
- `19` 条 `Verified` 子集的 7 种方法对比实验已完成
- 新的 `100` 条 `Verified` 随机子集实验正在运行中
- 当前总实验口径是：
  - 旧 `19` 条 `_19`
  - 新 `100` 条 `_100`
  - 合并后 `119` 条唯一 `instance`

实时进度和阶段结论见 [progress.md](/home/azureuser/jrh/CodeAgentCostOptimization/progress.md)。

## 主要方法

当前比较的 7 种方法：

- `baseline_raw`
- `rag_topk`
- `rag_function`
- `llmlingua_original`
- `skill_abstraction`
- `skill_memory_md`
- `hybrid_llmlingua`

方法定义、实验结论和中间判断不再单独散落在根目录文档里，统一收敛到：

- [README.md](/home/azureuser/jrh/CodeAgentCostOptimization/README.md)：长期稳定说明
- [progress.md](/home/azureuser/jrh/CodeAgentCostOptimization/progress.md)：当前实验进度与阶段结论

## 关键目录

```text
CodeAgentCostOptimization/
├── src/                         # 核心代码
│   ├── agent/                   # Agent runner / task context / trajectory
│   ├── gateway/                 # OpenAI-compatible gateway + token logging
│   ├── compression/             # RAG / trimming / LLMLingua adapter
│   ├── analysis/                # token 阶段分析
│   └── scripts/                 # 实验入口与聚合脚本
├── configs/                     # gateway 与实验配置
├── experiments/                 # 实验输出、输入子集、汇总文件
├── logs/                        # gateway / 运行日志
├── mini-swe-agent/              # 上游 submodule
├── tests/                       # 测试
├── skills.md                    # `skill_memory_md` 运行时使用的静态 skill memory
├── README.md
└── progress.md
```

## 关键实验结果

### 已完成：`19` 条 `Verified` 子集，`step=40`

最终 resolve 数：

- `baseline_raw`: `7/19`
- `rag_topk`: `10/19`
- `rag_function`: `7/19`
- `llmlingua_original`: `10/19`
- `skill_abstraction`: `9/19`
- `skill_memory_md`: `7/19`
- `hybrid_llmlingua`: `10/19`

最终平均 token：

- `baseline_raw`: `360,289`
- `rag_topk`: `335,868`
- `rag_function`: `347,186`
- `llmlingua_original`: `350,372`
- `skill_abstraction`: `315,220`
- `skill_memory_md`: `357,786`
- `hybrid_llmlingua`: `347,513`

这轮上，`rag_topk` 是最好的综合方案，`skill_abstraction` 是最低成本方案。

### 正在运行：新的 `100` 条 `Verified` 随机子集，`step=40`

- 随机采样且保证每个 repo 至少 1 条
- 与旧 `19` 条不重叠
- 新 `100` 的 token 日志独立写入 `logs/gateway_scitix_minimax_100/`
- 最终会和旧 `_19` 结果合并成 `119×7` 的总统计

## 常用入口

### 运行单个实验

```bash
./.venv/bin/python src/scripts/run_experiment.py \
  --config experiments/subset_methods_new100_steps40_live/configs/subset_rag_topk.yaml \
  --split verified \
  --workers 1 \
  --instance-file experiments/llmlingua_eval_inputs/verified_new_100_excluding_old19.json
```

### 启动本地 gateway

```bash
./.venv/bin/python -m src.gateway.server \
  --config configs/gateway.scitix-minimax.yaml \
  --host 127.0.0.1 \
  --port 18110
```

### 查看 patch 结果

标准输出目录：

```text
experiments/{experiment}/{instance_id}/
├── trajectory.json
├── result.json
└── patch.diff
```

已成功 resolve 的历史实例列表已移到实验目录：

- [resolved_instances.md](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/resolved_instances.md)

## 说明

- 根目录只保留长期有效说明文档；阶段性实验分析统一写入 `progress.md`
- `skills.md` 当前保留在根目录，是因为正在运行的 `skill_memory_md` 方法会实时读取它
