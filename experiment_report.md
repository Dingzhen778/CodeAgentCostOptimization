# 500 个 SWE-bench Verified 实例完整实验总结与分析报告

本报告是完整实验分析版，重点提供：

1. 完整实验设计
2. 各方法的详细解释与伪代码
3. `500` 条完整结果分析
4. 分阶段 token 分析
5. 代表性实例对比

统一结果目录：

- [experiments/subset_methods_verified500_steps40_combined](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined)

机器可读汇总：

- [verified500_summary.json](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/verified500_summary.json)
- [verified500_summary.csv](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/verified500_summary.csv)
- [verified500_summary.md](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/verified500_summary.md)
- [token_phase_methods_clean.json](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/token_phase_methods_clean.json)
- [combined_manifest.json](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/combined_manifest.json)

实验目录内详细副本：

- [final_experiment_report.md](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/final_experiment_report.md)

## 1. 实验目标

本轮实验的目标不是验证单个方法能否在少量样本上工作，而是基于完整 `500` 个 `SWE-bench Verified` 实例，对 `mini-swe-agent` 上下文压缩方案进行系统比较，回答以下问题：

1. 哪种方法能提高最终 `resolve rate`
2. 哪种方法能真正降低 token 成本
3. 哪种方法在“成功率-成本”之间给出最好的折中
4. 不同方法的 token 主要消耗在哪个阶段
5. 代表性实例上，不同方法的行为差异是什么

## 2. 实验设计

### 2.1 数据集

- 数据集：`SWE-bench Verified`
- 总实例数：`500`
- 合并来源：
  - `_19`
  - `_100`
  - `_381`

### 2.2 Agent 与环境

- Agent：`mini-swe-agent`
- 运行环境：官方 `SWE-bench Verified` Docker 镜像
- 模型：`MiniMaxAI/MiniMax-M2.5`
- 统一步数上限：`step = 40`

### 2.3 输出与统计

每个实例目录包含：

- `trajectory.json`
- `result.json`
- `patch.diff`

gateway 统一记录：

- `input_tokens`
- `output_tokens`
- `total_tokens`
- `calls`

## 3. 方法说明与伪代码

### `baseline_raw`

思路：原始 issue 直接交给 agent，不做压缩。

```text
input = problem_statement
agent.run(input)
```

### `rag_topk`

思路：先检索 top-k 候选文件，把文件片段提前注入上下文。

```text
terms = extract_query_terms(problem_statement)
candidate_files = rg_search(repo, terms)
selected_files = topk_select(candidate_files, k)
snippets = read_head(selected_files)
context = problem_statement + snippets
agent.run(context)
```

### `rag_function`

思路：在 `rag_topk` 基础上进一步裁到函数级。

```text
files = topk_select(rg_search(repo, terms), k)
trimmed = function_level_trim(files, query=problem_statement)
context = problem_statement + trimmed
agent.run(context)
```

### `llmlingua_original`

思路：用 LLMLingua 风格重排序候选文件，保留更高价值的跨文件上下文。

```text
candidates = rg_search(repo, terms)
ranked = llmlingua_rank(problem_statement, candidates)
selected = take_topk(ranked)
context = problem_statement + selected
agent.run(context)
```

### `skill_abstraction`

思路：注入结构化 workflow scaffold，减少搜索和规划空转。

```text
snippets = retrieve_candidates(problem_statement)
workflow = [
  understand_issue,
  narrow_files,
  locate_block,
  make_small_patch,
  focused_verify,
  submit_patch,
]
context = problem_statement + snippets + workflow
agent.run(context)
```

### `skill_memory_md`

思路：读取 `skills.md`，把可迁移经验注入 prompt。

```text
snippets = retrieve_candidates(problem_statement)
skill_memory = load('skills.md')
context = problem_statement + snippets + skill_memory
agent.run(context)
```

### `hybrid_llmlingua`

思路：组合 LLMLingua 排序、函数裁剪和 token budget 控制。

```text
candidates = retrieve_candidates(problem_statement)
ranked = llmlingua_rank(problem_statement, candidates)
trimmed = function_level_trim(ranked)
budgeted = token_budget_trim(trimmed)
context = problem_statement + budgeted
agent.run(context)
```

## 4. 完整 500 条结果

| 方法 | resolve | resolve rate | avg total tokens | avg input | avg output |
|---|---:|---:|---:|---:|---:|
| `baseline_raw` | 170/500 | 34.00% | 354,628.94 | 346,838.44 | 7,790.50 |
| `rag_topk` | 189/500 | 37.80% | 354,855.42 | 347,205.98 | 7,649.44 |
| `rag_function` | 166/500 | 33.20% | 352,488.01 | 344,955.77 | 7,532.24 |
| `llmlingua_original` | 165/500 | 33.00% | 334,278.02 | 327,190.93 | 7,087.09 |
| `skill_abstraction` | 182/500 | 36.40% | 344,855.90 | 337,272.82 | 7,583.08 |
| `skill_memory_md` | 186/500 | 37.20% | 347,069.46 | 339,856.91 | 7,212.55 |
| `hybrid_llmlingua` | 181/500 | 36.20% | 345,300.57 | 337,886.73 | 7,413.84 |

### 相对 baseline 的变化

- `rag_topk`: `+3.8` 个百分点 resolve，token `+0.06%`
- `rag_function`: `-0.8` 个百分点 resolve，token `-0.60%`
- `llmlingua_original`: `-1.0` 个百分点 resolve，token `-5.74%`
- `skill_abstraction`: `+2.4` 个百分点 resolve，token `-2.76%`
- `skill_memory_md`: `+3.2` 个百分点 resolve，token `-2.13%`
- `hybrid_llmlingua`: `+2.2` 个百分点 resolve，token `-2.63%`

### 更细的结果结构

只看总 resolve rate 仍然过于粗。把 `500` 个实例按“被多少种方法成功解决”拆开后，可以看到：

- `203` 个实例被 `0/7` 方法解决
- `76` 个实例被 `7/7` 方法全部解决
- `60` 个实例只被 `1/7` 方法解决

这意味着方法差异真正发生在中间层，而不是最容易或最困难的两端。对论文更有价值的，不是“谁平均更高”，而是“谁能把更多边缘实例从不可解推到可解”。

### 独占成功实例

不同方法在“只被它自己解出来”的实例数上差异明显：

- `rag_topk`: `15`
- `skill_memory_md`: `13`
- `skill_abstraction`: `9`
- `hybrid_llmlingua`: `7`
- `llmlingua_original`: `6`
- `rag_function`: `6`
- `baseline_raw`: `4`

这个指标说明：

1. `rag_topk` 的优势不只是平均上多解了一些实例，它确实拿下了最多的独占样本，说明文件级检索在某些问题上提供了不可替代的定位帮助。
2. `skill_memory_md` 的独占成功数也很高，说明显式经验迁移不是简单复刻 `RAG`，而是在一批需要策略提示的问题上发挥了独立价值。

## 5. Patch 完整性检查

额外检查结果：

- `success_count == patch_nonempty_count == success_with_nonempty_patch_count`

这意味着：

- 最终 `500` 条结果里没有“成功但空 patch”的条目
- 当前 resolve 统计可以直接视为“非空 patch 产出率”

## 6. 分阶段 token 对比

阶段分析文件：

- [token_phase_methods_clean.json](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/subset_methods_verified500_steps40_combined/token_phase_methods_clean.json)

总体结论：

1. 所有方法的 token 主体仍然在 `understand` 阶段，普遍在 `50%+`
2. 成功样本的 `submit` 占比显著更高
3. 失败样本更多消耗在 `read/search/other`
4. `skill_abstraction` 和 `skill_memory_md` 的优势主要是帮助 agent 更早进入 `validate/submit`
5. `llmlingua_original` 的优势主要是降低输入 token，而不是提升成功率

### 成功与失败轨迹的分离

从 `trajectory.json` 的 `api_calls` 和 `runtime` 看，所有方法都呈现出非常稳定的二分结构：

- 成功样本平均只用 `28.8` 到 `30.5` 步
- 失败样本几乎全部跑到 `39.9` 到 `40.0` 步上限
- 成功样本平均 runtime 约 `119` 到 `134` 秒
- 失败样本平均 runtime 约 `441` 到 `472` 秒

这说明当前成本黑洞不是“单步太贵”，而是“失败样本几乎总会烧满整个预算”。因此，后续优化重点不应该只放在继续压输入，而应该加入更强的 trajectory-level 早停或策略切换。

进一步看，不同方法在成功轨迹上的风格并不一样：

- `skill_abstraction` 的成功样本平均 runtime 最低：`119.34s`
- `llmlingua_original` 次之：`122.96s`
- `baseline_raw` 为 `125.35s`
- `rag_topk` 成功率最高，但成功样本平均 runtime 反而最长：`133.76s`

这说明：

- `rag_topk` 更像“用更好的候选文件覆盖率换更多成功”，但不一定更快
- `skill_abstraction` 更像“在已有可解路径上缩短收敛时间”
- `llmlingua_original` 更像“减少输入冗余，让可解任务更快进入提交阶段”

## 7. 更深入的方法特性分析

### 7.1 `baseline_raw`

`baseline_raw` 不只是对照组。它仍然独占了 `4` 个实例，说明在一类依赖完整问题语义的样本上，任何前置裁剪都可能破坏原本可行的求解路径。代表性例子是 `django__django-13810`：

- `baseline_raw`：成功，`137.95s`
- 其余 `6` 种方法：全部失败，并且都跑满 `40` 步、`600s+`

因此 baseline 的意义不是“旧方法”，而是保留完整语义的保真模式。

### 7.2 `rag_topk`

`rag_topk` 的核心特征是提升覆盖率，而不是降低单实例成本。它有最高的总 resolve `189/500`，也是独占成功最多的方法 `15` 个。它相对 baseline 是 `plus 58 / minus 39`，说明它新增可解实例多于它引入的回归。

repo 级别上，它对以下代码库最有效：

- `astropy`: 从 `31.8%` 提升到 `45.5%`
- `psf/requests`: 从 `25.0%` 提升到 `62.5%`
- `django`: 从 `43.3%` 提升到 `48.5%`

它更像“定位增强器”：当问题描述里有足够明确的符号或模块线索时，top-k 文件缩小搜索空间能明显降低早期迷路概率。

### 7.3 `rag_function`

`rag_function` 的问题不是压缩不够，而是压缩位置不对。它把文件级检索进一步压到函数级后，resolve 反而降到 `33.2%`，低于 baseline。repo 上尤其明显：

- `astropy`: `31.8% -> 18.2%`
- `pydata/xarray`: `22.7% -> 9.1%`

这说明很多实例依赖的不是单个函数片段，而是函数簇、相邻调用链、类级状态和多文件边界条件。当前版本的 function-level slicing 过早切断了横向上下文。

### 7.4 `llmlingua_original`

`llmlingua_original` 的真实特征不是“更会解题”，而是“更会节流”。它是全场最低 token 方法，平均 `334,278`，比 baseline 低 `5.74%`，但 resolve 只有 `33.0%`。

它在一些 repo 上仍然很强：

- `pytest-dev/pytest`: 从 `31.6%` 提升到 `42.1%`
- `sympy`: 从 `25.3%` 提升到 `36.0%`

但在 `matplotlib`、`sphinx-doc` 上明显回退，说明它更适合代码结构相对局部、关键信号可由少量上下文重建的任务，而不适合需要较宽语义背景的实例。

### 7.5 `skill_abstraction`

`skill_abstraction` 是当前最值得强调的原创方法之一。后验看，它的价值不在于改变“看什么”，而在于稳定“怎么做”。它不是最高 resolve 方法，但：

- 平均 token 低于 baseline：`344,855.90`
- 成功样本平均 runtime 最低：`119.34s`
- 独占成功 `9` 个实例

这说明它提供的不是额外知识，而是结构化 workflow 约束。它更像一个 process-level regularizer：帮助 agent 更快从理解阶段进入修改、验证和提交。代表性例子是 `django__django-11149`：

- 只有 `skill_abstraction` 成功：`217.83s`
- 其余 `6` 种方法全部失败并跑满 `40` 步

这个现象很关键，因为它证明了原创 skill 方法不是简单 prompt engineering，而是在 trajectory 层面改进了 agent 的决策质量。

### 7.6 `skill_memory_md`

`skill_memory_md` 是另一条原创方法线，而且它的特性与 `skill_abstraction` 不同。它不是最低 token，也不是最高 resolve，但它兼具：

- 第二高 resolve：`37.2%`
- 独占成功 `13` 个实例
- 在 `sympy`、`django`、`sphinx-doc` 上较稳定的正向增益

这说明它补的不是文件定位，而是跨实例可迁移的修复先验。更准确地说，它在做的是 externalized repair memory：把修复套路、验证顺序和提交策略外部化，然后在新实例上复用。

代表性例子是 `astropy__astropy-13453`：

- 只有 `skill_memory_md` 成功：`264.9s`
- 其余方法全部失败

这说明 `skills.md` 并不是单纯增加 prompt 长度，而是在一部分模式相似的问题上，提供了纯检索方法无法给出的策略迁移能力。

### 7.7 `hybrid_llmlingua`

`hybrid_llmlingua` 的特点是更激进，但不总是更稳。它把多种压缩偏置叠在一起后，确实能在部分实例上提高 resolve，但也更容易在另一部分实例上过度裁剪。因此它更适合作为强策略版本，而不是默认方案。

## 7. 代表性实例

### `astropy__astropy-12907`

- `rag_topk` / `skill_memory_md` 成功，baseline 失败
- 说明检索缩减或经验注入可能帮助 agent 更快聚焦

### `astropy__astropy-13236`

- `llmlingua_original` / `skill_memory_md` / `hybrid_llmlingua` 成功
- baseline 和 RAG 失败
- 说明压缩排序在某些实例上比文件级检索更有效

### `astropy__astropy-13398`

- 所有方法都失败
- 说明部分困难实例上，成本压缩并不能自动转化为成功率提升

### `django__django-11149`

- `skill_abstraction` 独占成功
- 说明 workflow scaffold 有真实价值

### `django__django-13810`

- `baseline_raw` 独占成功
- 说明压缩方法在个别实例上会破坏原本可行的路径

## 8. 更有建设性的结论与建议

结合完整 `500` 条结果，更有价值的 insight 不是“哪种方法最好”，而是下面这几条：

1. 不同方法优化的是不同瓶颈，而不是同一个目标。  
`rag_topk` 改善的是文件定位，`llmlingua_original` 改善的是上下文冗余，`skill_abstraction` 改善的是工作流稳定性，`skill_memory_md` 改善的是修复经验迁移。后续不应再把它们简单视为同质压缩基线。

2. 失败成本远大于成功成本，下一阶段最值钱的是失败早停。  
几乎所有失败样本都烧满 `40` 步，而成功样本普遍只需要 `29-30` 步左右。后续如果要继续降 token，优先级最高的可能不是更狠的输入压缩，而是 trajectory-level 的无进展检测、提前终止或策略切换。

3. 文件级裁剪明显优于函数级裁剪。  
这说明代码修复需要保留跨边界线索。后续如果继续做更细粒度方法，应考虑相关函数簇或小型调用子图，而不是单函数切片。

4. `skill` 类方法主要改善的是决策与执行过程。  
它们不是在最难实例上神奇翻盘，也不是在最简单实例上制造差异，而是在中等难度、容易空转的实例上提供真实帮助。这正是原创方法最值得强调的部分：它们不是 knowledge booster，而是 decision stabilizer。

5. 最合理的下一轮方案不是单一冠军方法，而是分层组合。  
如果只保留一条主线，`rag_topk` 最像主方法；但从结构上看，更合理的下一步是：
- 第一层：`rag_topk` 缩小候选文件
- 第二层：`skill_abstraction` 或 `skill_memory_md` 稳定流程
- 第三层：加入失败轨迹早停

也就是说，后续重点不该是再找一个更强的“单方法”，而应该是把“定位、收敛、止损”拆成三层来做。

## 9. 结论

1. `rag_topk` 最擅长提升 solve rate  
2. `llmlingua_original` 最擅长压 token  
3. `skill_memory_md` / `skill_abstraction` 更适合作为折中方案  
4. `rag_function` 当前版本不值得优先继续  

如果从论文叙事角度看，最清晰的结论不是“只有一个最优方法”，而是：

- `RAG` 更偏向提高成功率
- `LLMLingua` 更偏向降低成本
- `Skill` 路线更偏向取得成本-性能折中
