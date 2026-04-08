# 面向代码修复智能体的相关工作与研究基础文献调研

## 研究范围与信息源

本调研面向毕业论文（chap03“相关工作与研究基础”）的可写作素材收集与脉络化组织，覆盖六条主线：基于大语言模型的自动程序修复（APR）、代码/软件工程智能体、仓库级任务与 Issue Resolution、长上下文代码理解与上下文压缩、成本与效率（含 agent overhead）、以及两篇前期工作的定位。

信息源严格偏向“可引用的一手来源”：论文官方页面与论文 PDF（如 arXiv、ACL Anthology、OpenReview、ACM DL、IEEE/Computer Society 等），以及 benchmark 官方页面与系统/平台官方技术报告（例如 SWE-bench 系列站点与官方发布说明）。例如 SWE-bench 任务定义与构造方式以其论文与官方站点为准。citeturn13search12turn19search8 诸如 SWE-bench Verified 的“人工验证子集”定义，优先引用官方站点与官方发布说明。citeturn0search3turn0search15

为了直接服务 chap03 写作，表格中给出每条文献的：模块、标题、作者、年份、出处（会议/期刊/技术报告/基准站点）、链接（以可点击引用代替裸 URL）、任务类型、研究对象、核心方法/贡献、是否涉及成本/效率、适合放入 chap03 的小节、与本文关系、一句话摘要。每条记录至少对应一个一手引用来源。

## 主线问题回答与关键结论

代码修复智能体这条线的“做到哪里了”，可以用“APR 范式演进 + 任务场景外延”概括：传统 APR 以“生成-验证（Generate & Validate, G&V）”为主（如 GenProg、PAR、SPR），强调在测试用例约束下搜索/枚举/模板化生成候选补丁，并以测试通过作为验证门槛。citeturn1search4turn2search4turn21search0 其后学习式 APR（含神经翻译/集成等）将补丁生成从手工模板进一步数据驱动（例如 CoCoNuT）。citeturn3search2turn3search6 进入大模型时代后，关键变化不是仅“更强的生成”，而是：一方面出现了系统化评测与“无需/少量 APR 监督数据”的直接修复研究（如 ICSE’23 对大模型用于 APR 的系统评估），citeturn24view1 另一方面出现“更接近真实修复过程”的交互式/对话式修复（如 ChatRepair 将失败反馈纳入下一轮生成），并开始出现明确计量成本（按 token/美元/时间）的方法与报告方式。citeturn2search3

长上下文代码任务与上下文压缩的“主要结论”，在 2024–2026 逐渐清晰：其一，长上下文能力不能仅看模型宣称窗口，真实长代码理解在更长输入下存在明显性能衰减，例如 LONGCODEU 报告当代码长度超过 32K 后性能显著下降并指出“超长窗口≠稳定能力”。citeturn9search1turn9search5 其二，针对代码的长上下文 benchmark 体系开始形成：从 cross-file completion（RepoBench、CrossCodeEval）扩展到长上下文“理解/检索”（RepoQA），再到百万级上下文的综合评测（LongCodeBench、LoCoBench、Long Code Arena）。citeturn6search1turn5search7turn9search3turn9search2turn8search11turn9search0 其三，上下文压缩主线从通用 prompt compression（LLMLingua 系列）发展到面向代码结构与依赖闭包的 code-specific 压缩（如 LongCodeZip）以及“以修复充分性为目标”的任务驱动压缩（如 SWEzze/OCD）。citeturn8search0turn14search8turn23view3

GitHub issue resolution/benchmark 场景的演进呈现“函数级 → 仓库级 → 真实 issue 修复”的递进：HumanEval/MBPP 以“单函数/短程序”可执行正确性为主，citeturn5search0turn5search1 随后出现显式要求跨文件上下文的 completion（CrossCodeEval、RepoBench、RepoCoder/RepoEval），citeturn5search7turn6search1turn10search0 再向“真实软件维护”过渡为 SWE-bench：给定完整仓库与 issue 描述，要求编辑代码并通过测试。citeturn6search15turn19search8 随着可复现性与数据质量需求提高，又出现 Verified、人类过滤/验证子集。citeturn0search3turn0search15 语言/模态扩展也在发生：多语言、多模态 issue（SWE-bench Multimodal、Multi-SWE-bench、OmniGIRL）推动“更真实的软件工程分布”。citeturn7search3turn7search2turn18view3

成本优化与 agent overhead 这条线目前呈现“粒度不统一但趋势上升”：APR 方向已有直接以 token 成本为目标的工具（CigaR）并给出 token 级节省量；citeturn12search0 交互式修复与修复智能体也开始在论文中给出“每 bug token/美元”统计（ChatRepair、RepairAgent）。citeturn2search3turn4search1 但在 issue resolution 的 agent 流程里，长期存在“只看 resolve rate、不看失败也烧钱”的盲点，因此出现面向 SWE agent 的“资源约束下有效性”再评价（SWE-Effi）与“轨迹冗余削减”类工作（AgentDiet）。citeturn23view2turn23view0 这为“本文研究空白（research gap）”提供了直接支点：需要把成本纳入设计目标，并在流程阶段（定位/检索/编辑/测试/重试）上可分解、可度量。

两篇前期工作的定位上：OmniGIRL 明显处于“任务/基准扩展”链路上，解决的是 issue resolution 的多语言、多模态、多领域分布问题，而不是提出某个修复算法；citeturn18view3turn13search9 另一篇“长上下文代码压缩”工作（从标题看应偏研究基础/桥梁）更接近“为后续成本优化的修复智能体提供上下文工程手段”，与当前毕业论文的“成本—效果 trade-off”主线天然耦合（但其是否提出新方法或仅做评测，需要以论文正文为准；本次未能在公开一手索引中定位到该标题的可引用条目，详见末节说明）。

## 基于大语言模型的自动程序修复

这一模块建议在 chap03 中采用“传统 APR → 学习式 APR → LLM-based APR（含交互/检索增强/评测）”的叙事：传统 APR 的代表（GenProg、PAR、SPR、Prophet）奠定了以测试为 oracle 的 G&V 结构与“补丁空间+排序/搜索”的思路。citeturn1search4turn2search4turn21search0turn21search1 在此基础上，学习式 APR 用神经模型替代手工规则/模板并形成一批标准基准（如 Defects4J）。citeturn2search2turn3search2 大模型时代的关键进展，一是对“直接用大模型修复”的系统评估与修复设置设计（生成整段、infilling、单行修复、patch ranking 等），citeturn24view1 二是把失败反馈（测试失败/编译失败）融入多轮修复循环（ChatRepair），citeturn2search3 三是逐渐开始报告速度、编译率、成本等工程指标。citeturn24view1turn2search3

| 模块 | 标题 | 作者 | 年份 | 出处 | 链接 | 任务类型 | 研究对象 | 核心方法/贡献 | 是否涉及成本/效率 | 适合放入 chap03 哪一节 | 与本文关系 | 一句话摘要 |
|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| A | Automated Program Repair | Claire Le Goues et al. | 2019 | CACM（综述） | citeturn3search7 | 综述 | APR 全景 | 总结 APR 关键挑战：可扩展性、补丁质量、评测与可用性等 | 部分（讨论代价/维护成本语境） | 3.1 传统 APR 与挑战综述 | 作为传统 APR 的“脉络总览”引用源 | 经典综述，为“传统→LLM”的演化叙事提供锚点 |
| A | Automatically Finding Patches Using Genetic Programming | Westley Weimer et al. | 2009 | ICSE’09（IEEE/ACM） | citeturn1search4 | Test-suite-based APR | 真实程序缺陷 | GenProg 早期代表：基于遗传编程搜索补丁，使测试通过 | 间接（搜索开销但非成本导向） | 3.1 传统 APR：搜索/生成-验证 | 作为“G&V 范式”代表对照 LLM 修复 | 用搜索+测试验证自动生成补丁的代表作 |
| A | SemFix: Program Repair via Semantic Analysis | Hoang Duong Thien Nguyen et al. | 2013 | ICSE’13 | citeturn1search10 | 语义约束修复 | 表达式/条件修复 | 符号执行+约束求解+程序合成生成修复表达式 | 否（主打有效性） | 3.1 传统 APR：语义/合成路线 | 对比 LLM“无显式语义约束”修复 | 以语义分析与合成替代纯搜索，提高修复质量/效率路径之一 |
| A | Automatic Patch Generation Learned from Human-Written Patches | Dongsun Kim et al. | 2013 | ICSE’13 | citeturn2search4 | 模式/模板驱动 APR | 大规模人类补丁 | 提取常见修复模式（fix patterns）并自动生成补丁 | 否（主打可接受性/质量） | 3.1 传统 APR：模板/模式学习 | 作为“模板化补丁空间”的代表；可对比 LLM 的泛化与幻觉 | 从人类补丁中学习模式以提升自动补丁可接受性 |
| A | Staged Program Repair with Condition Synthesis | Fan Long & Martin Rinard | 2015 | FSE’15 | citeturn21search0 | G&V + 规则空间搜索 | 条件/分支相关缺陷 | 分阶段搜索+条件合成，结合 transformation schemas 扩展可修复缺陷面 | 间接（强调可搜索性） | 3.1 传统 APR：分阶段搜索与条件合成 | 为“补丁空间设计/搜索策略”提供对照 | 通过分阶段与条件合成，使更丰富的补丁空间可被高效搜索 |
| A | Automatic Patch Generation by Learning Correct Code | Fan Long & Martin Rinard | 2016 | POPL’16（ACM） | citeturn21search1 | 学习排序的 APR | 人类成功补丁/代码库 | Prophet：学习“正确性模型”对候选补丁排序并验证 | 否（主要关注正确性排序） | 3.1 传统 APR：学习引导的补丁排序 | 对照 LLM 中的 patch ranking / self-check 思路 | 用数据驱动的正确性模型为候选补丁排序以提升命中正确补丁概率 |
| A | Defects4J: a database of existing faults to enable controlled testing studies for Java programs | René Just et al. | 2014 | ISSTA’14（ACM） | citeturn2search2 | 基准/数据集 | Java 真实缺陷与测试 | 提供可复现的真实缺陷与测试套件，成为 APR/FL 常用基准 | 否 | 3.1 APR 评测基准 | 作为 RepairAgent/CigaR 等工作的共同评测基础 | 为 APR 提供标准化、可复现的真实缺陷基准 |
| A | Combining Context-Aware Neural Translation Models using Multi-Task Learning for Automated Program Repair | Thibaud Lutellier et al. | 2020 | ISSTA’20（ACM） | citeturn3search2 | 学习式 APR（NMT/集成） | 多语言/多项目修复 | CoCoNuT：用神经翻译/集成学习替代手工规则，强调跨语言适配 | 否（主打效果） | 3.1 从传统到学习式 APR | 作为“LLM 前的学习式 APR”过渡材料 | 用神经翻译与集成学习推进数据驱动 APR |
| A | Automated Program Repair in the Era of Large Pre-trained Language Models | Chunqiu Steven Xia et al. | 2023 | ICSE’23（论文 PDF） | citeturn24view1 | LLM-based APR（系统评估） | 多模型多数据集 | 系统性评估多种 LLM 在不同修复设置下的能力（生成/infilling/单行等），并讨论生成速度、编译率等 | 是（包含速度/编译率等工程指标） | 3.1 LLM-based APR：修复设置与能力评测 | 为本文选择 LLM 修复设置、评测维度提供依据 | 系统揭示 LLM 直接用于 APR 的真实能力与设置差异 |
| A | Impact of Code Language Models on Automated Program Repair | Nan Jiang et al. | 2023 | ICSE’23（arXiv/论文 PDF） | citeturn21search3 | Code LM → APR（评测+微调） | 多 APR 基准 | 评测多种代码语言模型并展示微调带来的大幅提升，同时分析时间/内存等效率因素 | 是（包含 size/time/memory efficiency 分析） | 3.1 LLM-based APR：模型选择与效率因素 | 支撑“效果之外要看效率/资源”的论点 | 系统比较代码模型在 APR 上的收益与效率代价 |
| A | Keep the Conversation Going: Fixing 162 out of 337 bugs for $0.42 each using ChatGPT | Chunqiu Steven Xia & Lingming Zhang | 2023 | arXiv（后续有正式出版条目） | citeturn2search3 | 对话式 LLM-APR | APR 基准（多 bug） | ChatRepair：将测试失败/成功反馈融入多轮对话式修复循环，并报告单位 bug 成本 | 是（明确给出每 bug 美元成本） | 3.1 LLM-based APR：交互式/反馈驱动修复 | 为本文“多轮修复 vs 成本”提供直接例证 | 用对话式反馈循环提升修复并量化单位缺陷成本 |
| A | A Survey of LLM-based Automated Program Repair | （综述作者见论文） | 2025 | arXiv（综述） | citeturn2search19 | 综述 | 2022–2025 LLM-APR 系统 | 归纳 LLM-APR 设计范式与分类（检索增强/分析增强等），总结机会与挑战 | 部分（涉及效率/增强方式） | 3.1 LLM-based APR：分类框架与研究空白 | 用作 chap03 的“LLM-APR 版图”结构化引用 | 系统整理 LLM-APR 研究范式，便于定位本文切入点 |

## 代码智能体与软件工程智能体

“代码智能体/软件工程智能体”主线的核心是：从“单轮生成一段代码”走向“在真实开发环境中多轮交互、工具调用、执行测试、迭代修复/实现”。通用层面，ReAct 将“推理轨迹+动作”交织，成为后续工具调用式 agent 的典型范式之一。citeturn22search1 软件工程场景中，SWE-agent 强调 agent-computer interface（编辑/浏览/运行等接口设计）对修复成功率的重要性；citeturn0search0turn22search15 AutoCodeRover 将问题求解显式拆为“定位+修改”并结合代码搜索/调试能力；citeturn0search1turn0search9 Agentless 则反向提出“尽量去 agent 化”，用更简单的三阶段流程（定位-修复-验证）挑战复杂脚手架的必要性；citeturn4search6turn4search2 RepairAgent 代表了更 APR 导向的“自主工具调用修复 agent”。citeturn4search1turn4search5 这些工作共同构成 chap03 可写作的“从 code generation 到 SE agent”的主干叙事。

| 模块 | 标题 | 作者 | 年份 | 出处 | 链接 | 任务类型 | 研究对象 | 核心方法/贡献 | 是否涉及成本/效率 | 适合放入 chap03 哪一节 | 与本文关系 | 一句话摘要 |
|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| B | ReAct: Synergizing Reasoning and Acting in Language Models | Shunyu Yao et al. | 2022 | arXiv | citeturn22search1 | 通用 agent 范式 | 工具交互/多步决策 | 提出 Reason+Act 交织轨迹范式，影响后续工具调用式代码 agent | 间接（多步带来 token 增长动因） | 3.2 智能体范式基础 | 作为“工具调用式 agent”方法论基座 | 以可解释轨迹把推理与行动统一起来的代表范式 |
| B | SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering | John Yang et al. | 2024 | NeurIPS’24（论文） | citeturn22search15 | GitHub issue resolution / repo-level 修复 | 代码仓库+命令行环境 | 提出 ACI（编辑/浏览/执行/上下文管理）显著提升 agent 在仓库级任务中的能力 | 间接（有上下文管理设计但非成本主线） | 3.2 软件工程智能体代表 | 作为本文对标的主流 agent 框架之一 | 通过更合适的人机/机机接口设计提升软件工程任务完成率 |
| B | AutoCodeRover: Autonomous Program Improvement | Y. Zhang et al. | 2024 | ISSTA’24（ACM） | citeturn0search9 | GitHub issue resolution（bug/feature） | 多仓库代码修改 | 结合代码搜索与调试/定位能力，强调更 SE-oriented 的 issue 求解流程 | 是（报告经济性/耗时等实践指标） | 3.2 软件工程智能体代表 | 作为本文对比方法与成本/流程拆解参考 | 在 SWE-bench Lite 等任务上给出可复现的自动 issue 修复流程 |
| B | Agentless: Demystifying LLM-based Software Engineering Agents | Chunqiu Steven Xia et al. | 2024 | arXiv /（后续有正式版本） | citeturn4search6 | Issue resolution（去 agent 化） | SWE-bench 类任务 | 用“定位-修复-验证”的简化流程替代复杂 agent 决策，讨论脚手架必要性 | 强相关（强调简单流程、减少 overhead 的动机） | 3.2 智能体设计对照：agent vs agentless | 支撑本文“overhead/成本”论证与基线选择 | 用结构化而非自由规划的流程降低复杂 agent 的必要性 |
| B | RepairAgent: An Autonomous, LLM-Based Agent for Program Repair | Islem Bouzenia et al. | 2024 | arXiv（后续 ICSE’25） | citeturn4search1 | APR agent | Defects4J（Java） | 以工具调用/状态机引导的自主修复 agent，显式报告平均 token 成本 | 是（给出每 bug token/美元） | 3.2 APR 智能体 | 为本文“修复 agent 成本计量与流程阶段”提供参照 | 将 APR 建模为工具调用 agent，并对成本给出明确量化 |
| B | MAGIS: LLM-Based Multi-Agent Framework for GitHub Issue Resolution | Wei Tao et al. | 2024 | NeurIPS’24 | citeturn4search12 | 多智能体 issue resolution | SWE-bench | Manager/Repo Custodian/Dev/QA 分工协作，作为多 agent 软件演化框架 | 间接（多 agent 带来更高开销动因） | 3.2 多智能体软件工程 | 作为“多 agent 协作”范式对照，讨论其 overhead | 以角色分工协作提升 issue 解决流程完整性 |
| B | CodeR: Issue Resolving with Multi-Agent and Task Graphs | （作者见论文） | 2024 | arXiv | citeturn4search8 | 多智能体 issue resolving | SWE-bench 类 | 用 task graph 组织多 agent 协作，面向 issue resolution 的结构化规划 | 间接 | 3.2 多智能体软件工程 | 对比“结构化任务图”与本文的流程/阶段设计 | 用任务图把 issue resolving 的步骤显式结构化 |
| B | ChatDev: Communicative Agents for Software Development | Chen Qian et al. | 2024 | ACL’24（长文） | citeturn22search4 | 多智能体“软件开发流水线” | 设计-编码-测试 | 用对话链与“去幻觉沟通”组织多角色协作覆盖开发阶段 | 间接（更关注流程与协作） | 3.2 从单轮生成到多轮协作 | 作为“多轮交互与协作”背景材料 | 用多智能体沟通把软件流程端到端串起来 |
| B | OpenHands: An Open Platform for AI Software Developers as Generalist Agents | （作者见论文） | 2024 | arXiv / OpenReview | citeturn22search6 | 平台/框架 | 代码执行+网页/工具交互 | 提供通用软件开发 agent 平台（沙箱执行、基准接入等） | 间接（工程开销维度） | 3.2 工程化 agent 平台 | 作为“可复现评测与工程框架”参考 | 以平台视角降低构建与评测软件 agent 的门槛 |
| B | The OpenHands Software Agent SDK | （作者见论文） | 2025 | arXiv | citeturn22search2 | SDK/工程框架 | 可组合 agent 组件 | 面向生产级软件 agent 的可组合 SDK，强调可靠执行与交互接口 | 间接 | 3.2 工程化与可复现性 | 为本文实验框架与工程实现提供参考 | 用 SDK 抽象提升软件 agent 的可扩展与可复现实验能力 |
| B | SWE-Fixer: Training Open-Source LLMs for Effective and Efficient Issue Resolution | （作者见论文） | 2025 | ACL Findings | citeturn0search22 | 训练/方法 | issue resolution | 训练开源模型面向 issue resolution，聚焦可复现与开源可用 | 部分（含 efficiency 诉求） | 3.2 训练与方法补充 | 为本文“方法/模型训练”路线提供备选参考 | 以开源模型训练推进 issue resolution 的可复现研究 |
| B | SWE-MERA: A Dynamic Benchmark Platform for Agentic SWE Evaluation（系统演示） | （作者见论文） | 2025 | EMNLP Demos | citeturn4search7 | 评测平台 | SWE agent 评测环境 | 提供更透明、可复现的 SWE agent 评测平台与数据过滤思路 | 间接（关注评测稳定性） | 3.2 评测基础设施 | 作为本文实验评测平台与可复现性讨论素材 | 用平台化方式提升 SWE agent 评测的可复现与透明度 |

## 仓库级代码任务与 GitHub Issue Resolution

本模块建议在 chap03 中用“任务复杂度与上下文需求递增”的方式叙事：HumanEval/MBPP 主要测试函数级生成的可执行正确性；citeturn5search0turn5search1 当社区认识到真实工程需要跨文件依赖与仓库级检索时，CrossCodeEval、RepoBench、RepoCoder 等开始显式构造需要跨文件上下文的 completion/检索-生成流程；citeturn5search7turn6search1turn10search0 再进一步，RepoQA 将评测从“生成”扩展到“长上下文代码理解/检索”；citeturn9search3turn17view2 SWE-bench 则把任务推到“真实 issue→修改仓库→测试验证”的软件维护场景，并衍生出 Lite/Verified 等子集以平衡成本与质量。citeturn6search15turn0search3turn6search3 随后，多语言与多模态扩展（OmniGIRL、Multi-SWE-bench、SWE-bench Multimodal）让“真实分布”更贴近前端/多语言生态与带图 issue。citeturn18view3turn7search2turn7search3

| 模块 | 标题 | 作者 | 年份 | 出处 | 链接 | 任务类型 | 研究对象 | 核心方法/贡献 | 是否涉及成本/效率 | 适合放入 chap03 哪一节 | 与本文关系 | 一句话摘要 |
|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| C | Evaluating Large Language Models Trained on Code（HumanEval） | Mark Chen et al. | 2021 | arXiv | citeturn5search0 | 函数级代码生成评测 | HumanEval | 提出 HumanEval 与 pass@k 评测范式，代表早期“函数级”能力衡量 | 否 | 3.3 早期代码生成基准 | 作为仓库级/issue 任务的早期参照点 | 用短函数任务衡量代码生成可执行正确性 |
| C | Program Synthesis with Large Language Models（MBPP） | Jacob Austin et al. | 2021 | arXiv | citeturn5search1 | 短程序合成评测 | MBPP | 提出 MBPP 等基准，强调规模与可执行验证 | 否 | 3.3 早期代码生成基准 | 为“从函数级到仓库级”的演进提供对照 | 用更接近入门编程题的短程序任务衡量合成能力 |
| C | CrossCodeEval: A Diverse and Multilingual Benchmark for Cross-File Code Completion | Y. Ding et al. | 2023 | NeurIPS Datasets & Benchmarks | citeturn5search7 | 跨文件补全评测 | 多语言真实仓库 | 静态分析生成“必须跨文件才能补全”的样本，凸显仓库级上下文 | 否 | 3.3 仓库级 code completion | 支撑本文“仓库级任务为何必要”的论述 | 用强约束样本逼迫模型利用跨文件上下文完成补全 |
| C | RepoBench: Benchmarking Repository-Level Code Auto-Completion Systems | T. Liu et al. | 2023 | arXiv（后续 ICLR’24） | citeturn6search1 | 仓库级补全/检索评测 | 多文件仓库场景 | 明确提出 repository-level completion 评测框架，填补单文件基准缺口 | 否 | 3.3 仓库级 code completion | 为本文“长上下文与仓库级任务”提供基准线 | 用仓库级任务衡量检索与补全结合能力 |
| C | RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation（含 RepoEval） | Fengji Zhang et al. | 2023 | arXiv / EMNLP’23（ACL） | citeturn10search0turn10search4 | 检索增强仓库级补全 | 多文件仓库 | 迭代“检索-生成”流水线，并提出 RepoEval 基准，体现上下文选择/压缩思路 | 间接（通过检索控制上下文长度） | 3.3 仓库级任务：检索增强 | 与本文“上下文压缩/选择”存在方法论关联 | 通过迭代检索把分散在仓库中的信息逐步纳入生成 |
| C | RepoQA: Evaluating Long Context Code Understanding | Jiawei Liu et al. | 2024 | arXiv / OpenReview PDF | citeturn9search3turn17view2 | 长上下文代码理解评测 | 多语言仓库代码检索 | 提出 SNF（Searching Needle Function）任务，强调“理解+检索”而非纯 needle 检索 | 否（主打能力评测） | 3.3→3.4 长上下文理解桥梁 | 为本文“长上下文代码理解难点”提供直接基准 | 用“找函数”任务评测模型对长仓库上下文的理解与检索能力 |
| C | SWE-bench: Can Language Models Resolve Real-World GitHub Issues? | Carlos E. Jimenez et al. | 2023 | arXiv / 官方站点 | citeturn0search7turn19search8 | Issue resolution（修 bug/加特性） | 真实 issue-PR 对 + 测试验证 | 定义 issue resolution 评测框架：给 issue 描述与仓库，产出补丁并以测试验证 | 间接（评测成本高引出 Lite/Verified） | 3.3 GitHub issue resolution 任务定义 | 作为本文核心任务场景与评测框架基石 | 把真实软件维护任务引入 LLM/agent 评测体系 |
| C | SWE-bench Lite | （基准维护团队） | 2024 | 官方基准页面 | citeturn6search3 | 低成本 issue resolution 子集 | 300 任务子集 | 为降低评测成本、加速迭代引入 Lite 子集并说明抽样原则 | 是（明确以降低评测成本为目标） | 3.3 评测子集与成本动机 | 为本文“成本-效果权衡”提供 benchmark 层面的动机材料 | 用更小子集支持更低成本、更快迭代的评测 |
| C | SWE-bench Verified | （基准维护团队 / 官方合作说明） | 2024 | 官方基准页面 + 官方发布说明 | citeturn0search3turn0search15 | 高质量 issue resolution 子集 | 500 人工验证任务 | 人工审核任务清晰度/可解性/测试补丁正确性，提高评测可靠性 | 间接（提高质量而非降成本） | 3.3 数据质量与可解性 | 作为本文“高质量主评测集”优先对齐对象 | 用人工验证子集提升 SWE benchmark 可信度与可比性 |
| C | SWE-bench Multimodal: Do AI Systems Generalize to Visual Software Domains? | John Yang et al. | 2024 | arXiv | citeturn7search3 | 多模态 issue resolution | JS 视觉/前端相关仓库 | 引入含图 issue 与 JS 生态，评测跨语言与视觉信息处理能力 | 是（多模态输入带来额外成本/复杂度） | 3.3 多模态 issue 场景 | 支撑本文“真实 issue 含图/跨语言”的必要性 | 把视觉元素与 JS 域引入 SWE-bench 家族评测 |
| C | OmniGIRL: A Multilingual and Multimodal Benchmark for GitHub Issue Resolution | Lianghong Guo et al. | 2025 | ISSTA’25（ACM；To appear） | citeturn18view3turn13search9 | 多语言+多模态 issue resolution | 4 语言、8 领域、含图 issue | 提出 959 实例的多维多样性基准，并报告现有模型在该分布上整体表现有限 | 否（主打任务难度与分布） | 3.3 任务场景扩展：多语言/多模态 | 与本文任务基础强相关（作为更真实评测/扩展实验集） | 用多语言多模态多领域基准揭示 issue resolution 的泛化挑战 |
| C | Multi-SWE-bench: A Multilingual Benchmark for Issue Resolving | Daoguang Zan et al. | 2025 | arXiv / OpenReview | citeturn7search2turn7search9 | 多语言 issue resolving | 7+ 语言软件生态 | 扩展 SWE-bench 到多语言，强调高质量人工标注与跨语言评测 | 否（主打语言覆盖） | 3.3 多语言 issue 场景 | 为本文“跨语言泛化/任务迁移”提供 benchmark 参照 | 用多语言数据集检验 agent/模型在不同生态的可迁移性 |

## 长上下文代码理解与上下文压缩

这一模块建议在 chap03 里承担“桥梁”角色：解释为什么 issue resolution/仓库级任务天然依赖长上下文，以及为什么必须研究“上下文压缩（compression）/选择（selection）/管理（management）”。RepoQA 明确把评测聚焦在“长仓库上下文上的理解与检索”，而不是纯粹把 needle 复制出来。citeturn9search3turn17view2 LONGCODEU 则指出当长度超过 32K 后表现显著下降，提醒“上下文窗口扩展≠能力线性提升”。citeturn9search1turn9search5 在百万级上下文窗口逐渐普及后（LongCodeBench、LoCoBench 等），评测开始覆盖更复杂的长程依赖、多文件工作流与更长输入尺度。citeturn9search2turn8search11turn9search0

压缩方法方面出现两条路线：通用 prompt compression（LLMLingua、LongLLMLingua、LLMLingua-2）强调在保证语义/任务相关信息的前提下降 token 并降低延迟；citeturn8search0turn8search1turn8search2 而 code-specific 压缩（LongCodeZip）指出通用方法忽略代码结构与依赖，提出分层压缩与预算分配机制；citeturn14search8turn13search3 更进一步，面向 issue resolution 的压缩（SWEzze/OCD）把目标直接定义为“保留修复所需 ingredients、减少噪声干扰”，并报告压缩率、token 预算下降、成功率提升与延迟权衡。citeturn23view3 还有探索性方向把代码渲染为视觉 token 以保持全局结构（LongCodeOCR）。citeturn10search3turn10search19

| 模块 | 标题 | 作者 | 年份 | 出处 | 链接 | 任务类型 | 研究对象 | 核心方法/贡献 | 是否涉及成本/效率 | 适合放入 chap03 哪一节 | 与本文关系 | 一句话摘要 |
|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| D | RepoQA: Evaluating Long Context Code Understanding | Jiawei Liu et al. | 2024 | arXiv / OpenReview | citeturn9search3turn17view2 | 长上下文理解评测 | 多语言仓库 SNF 任务 | 首批面向“长仓库上下文理解/检索”的 benchmark 之一 | 否 | 3.4 长上下文代码理解基准 | 作为本文长上下文理解能力的直接引用源 | 用“找函数”任务量化模型对长仓库上下文的理解能力 |
| D | RepoBench: Benchmarking Repository-Level Code Auto-Completion Systems | T. Liu et al. | 2023 | arXiv | citeturn6search1 | 仓库级补全 | 多文件仓库任务 | 强调真实工程多文件依赖并提出 repo-level completion 基准 | 否 | 3.4 仓库级任务与上下文需求 | 作为“需要跨文件上下文”论据之一 | 用 repo-level completion 显式提出“单文件基准不足” |
| D | CrossCodeEval: Cross-File Code Completion Benchmark | Y. Ding et al. | 2023 | NeurIPS D&B | citeturn5search7 | 跨文件补全 | 4 语言真实仓库 | 静态分析筛选必须依赖跨文件信息的样本 | 否 | 3.4 长上下文与跨文件依赖 | 支撑“上下文必须精准选择”的动机 | 通过严格样本构造逼迫模型利用跨文件上下文 |
| D | Long Code Arena: a Set of Benchmarks for Long-Context Code Models | E. Bogomolov et al. | 2025 | OpenReview | citeturn9search0 | 长上下文代码多任务评测 | 生成/修复/总结等 6 基准 | 提供覆盖多任务的长上下文代码评测套件 | 否 | 3.4 长上下文代码任务版图 | 为本文选择长上下文任务类型提供参考 | 用多任务套件刻画“长上下文代码能力”的不同维度 |
| D | LONGCODEU: Benchmarking Long-Context Language Models on Long Code Understanding | Jia Li et al. | 2025 | ACL’25（长文） | citeturn9search4turn9search5 | 长代码理解评测 | 8 任务、4 能力维度 | 指出长代码长度超过 32K 后显著退化，并细分理解能力维度 | 否 | 3.4 长上下文能力结论 | 作为“长上下文能力衰减”关键证据 | 证明长窗口声称与真实长代码理解之间存在显著差距 |
| D | LongCodeBench: Evaluating Coding LLMs at 1M Context Windows | Stefano Rando et al. | 2025 | arXiv / OpenReview | citeturn9search10turn9search6 | 百万级上下文代码评测 | 长上下文代码任务集合 | 把评测推进到 1M 级上下文窗口并覆盖真实编码任务 | 否 | 3.4 超长上下文评测 | 为本文讨论“超长窗口时代仍需压缩/选择”提供素材 | 在百万级上下文下评测编码任务，揭示长上下文仍是短板 |
| D | LoCoBench: A Benchmark for Long-Context LLMs in Software Development Scenarios | J. Qiu et al. | 2025 | arXiv | citeturn8search11 | 长上下文软件开发评测 | 多场景长上下文任务 | 以更贴近软件开发工作流的长上下文评测补齐“任务范围缺口” | 否 | 3.4 长上下文软件开发场景 | 为本文“实际工作流需要什么长上下文能力”提供论据 | 面向真实软件工作流构造长上下文评测场景 |
| D | LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models | Huiqiang Jiang et al. | 2023 | arXiv | citeturn8search0 | Prompt compression（通用） | 多任务长 prompt | 粗到细压缩、预算控制与 token 级迭代压缩，显式以降低推理成本为目标 | 是（降低 token/加速推理） | 3.4 通用压缩方法迁移到代码 | 为本文提供通用压缩 baseline/思路 | 用预算控制把长 prompt 压缩以降低推理成本 |
| D | LongLLMLingua: Prompt Compression for Long Context Scenarios | Huiqiang Jiang et al. | 2023 | arXiv | citeturn8search1 | 长上下文 prompt 压缩 | 长上下文多场景（含代码完成） | 面向长上下文场景的压缩与位置偏差讨论，报告成本与延迟收益 | 是（成本/延迟与性能同时报告） | 3.4 长上下文压缩 | 作为“压缩提升性能+降成本”的典型证据 | 用压缩提高长上下文关键信息密度并降低成本 |
| D | LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression | Zhuoshi Pan et al. | 2024 | arXiv | citeturn8search2 | 任务无关压缩模型 | Token 分类压缩 | 以蒸馏与 token 分类学习压缩策略，强调泛化性与速度（小模型更快） | 是（3–6× 更快等效率描述） | 3.4 压缩方法演进 | 为本文提供更“可部署”的压缩路线参考 | 用数据蒸馏把压缩学成更快、更可泛化的模型 |
| D | LongCodeZip: Compress Long Context for Code Language Models | Yuling Shi et al. | 2025 | ASE’25 / arXiv | citeturn13search3turn14search8 | code-specific 压缩 | 长代码上下文 | 分层（函数级→块级）压缩与预算分配，指出通用压缩忽略代码依赖结构 | 是（以降低成本/延迟为动机） | 3.4 面向代码的压缩 | 对本文“代码结构约束下的压缩”非常关键 | 在保留代码结构/依赖的前提下做长代码上下文压缩 |
| D | Compressing Code Context for LLM-based Issue Resolution（SWEzze / OCD） | Haoxiang Jia et al. | 2026 | arXiv | citeturn23view3turn15search3 | 面向 issue resolution 的上下文压缩 | SWE-bench Verified | OCD 蒸馏“修复充分上下文”，训练 SWEzze 在推理时压缩并提升成功率、降低 token 预算 | 是（报告压缩率、token/延迟与成功率） | 3.4 压缩与修复效果 trade-off | 直接支撑本文“压缩→降成本且可增效”的主张 | 以“保留修复 ingredients”为目标的任务驱动压缩框架 |
| D | LongCodeOCR: Visual Code Compression for Long-Context Code Understanding | J. Zhong et al. | 2026 | arXiv | citeturn10search3turn10search19 | 视觉压缩（VLM） | 超长代码上下文 | 把代码渲染为压缩图像序列以维持全局结构视图，探索新型压缩范式 | 是（解决长上下文成本/窗口限制） | 3.4 新型压缩范式补充 | 作为前沿方向材料，可用于“未来工作”或动机拓展 | 通过视觉 token 维持全局结构，探索超长代码压缩的新路径 |

## 成本优化、效率优化与 Agent Overhead

该模块的写作建议聚焦两个层次：其一，成本/效率被怎样“量化”（token、美元、延迟、时间预算等）；其二，成本被优化到什么“粒度”（整条轨迹、阶段化流程、单次调用、失败重试等）。在 APR 与修复 agent 中，已经出现“直接把 token 成本作为优化目标”的工作（CigaR），citeturn12search0 也出现了将“每 bug 的 token/美元成本”写入论文结论的工作（ChatRepair、RepairAgent）。citeturn2search3turn4search1 在 issue resolution agent 侧，SWE-bench Lite 本身就是为降低评测成本而设计；citeturn6search3 更进一步，SWE-Effi 主张把 resolve rate 扩展为“资源约束下有效性”，并指出“昂贵失败（expensive failures）”会在传统指标下被隐藏。citeturn23view2turn23view1 轨迹级别的 token 控制也开始出现系统方法（AgentDiet 通过推理时轨迹裁剪减少冗余信息）。citeturn23view0

为了在 chap03 中形成 research gap，建议强调：当前工作往往要么偏“通用 LLM 成本控制”（如 FrugalGPT、TimeBill、token budget reasoning），citeturn11search0turn11search5turn11search17 要么偏“某一类 SE 任务的成本计量”，但对“代码修复智能体流程（定位/检索/编辑/验证/重试）上的阶段化成本-成功率 trade-off”仍缺少统一、可复现的分析框架与优化方法（这正是本文可以切入的空白点）。

| 模块 | 标题 | 作者 | 年份 | 出处 | 链接 | 任务类型 | 研究对象 | 核心方法/贡献 | 是否涉及成本/效率 | 适合放入 chap03 哪一节 | 与本文关系 | 一句话摘要 |
|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| E | FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance | Lingjiao Chen et al. | 2023 | arXiv / OpenReview PDF | citeturn11search0turn11search16 | 成本优化（通用） | LLM API 调用 | 提出级联/近似/prompt 适配等策略，并以 FrugalGPT 作为实例降低成本 | 是（以成本为主目标） | 3.5 通用成本优化思想 | 为本文提供“成本优化”方法论背景（级联/预算） | 用级联策略在保持效果下显著减少 LLM 调用成本 |
| E | TimeBill: Time-Budgeted Inference for Large Language Models | Q. Fan et al. | 2026 | AAAI’26 | citeturn11search5turn11search1 | 时延预算推理 | LLM 推理系统 | 把“时间预算”作为约束，预测输出长度与执行时间以平衡效率与性能 | 是（时间预算） | 3.5 延迟/预算受限推理 | 为本文“latency 作为成本维度”提供引用 | 用时间预算驱动推理调度以控制端到端延迟 |
| E | BudgetThinker: Budget-aware Reasoning for LLMs | （作者见论文） | 2025 | OpenReview | citeturn11search9 | 预算受限推理 | 推理长度控制 | 讨论如何在预算下控制“思考长度”以降低资源消耗 | 是（预算控制） | 3.5 预算受限推理 | 为本文“预算化 agent”提供通用技术参考 | 用预算约束显式控制推理计算量与输出长度 |
| E | Token-Budget-Aware LLM Reasoning | T. Han et al. | 2025 | ACL Findings | citeturn11search17 | token 预算推理 | 受限推理任务 | 以 token 预算为约束研究推理策略与效果 | 是（token budget） | 3.5 token 成本控制基础 | 为本文把 token 作为成本目标提供 NLP 侧先例 | 在 token 预算下优化推理行为以平衡效果与成本 |
| E | CigaR: Cost-efficient Program Repair with LLMs | Dávid Hidvégi et al. | 2024 | arXiv | citeturn12search0 | 成本导向 LLM-APR | Defects4J 等 | 明确以 token 成本最小化为目标，报告 token 节省比例与修复效果 | 是（核心目标） | 3.5 成本导向 APR | 直接支撑本文“成本可作为一等优化目标” | 用精心 prompt 与策略在保证修复下显著降低 token 开销 |
| E | Keep the Conversation Going: Fixing 162 out of 337 bugs for $0.42 each using ChatGPT | Chunqiu Steven Xia & Lingming Zhang | 2023 | arXiv | citeturn2search3 | 对话式 LLM-APR | 多 bug 修复 | 报告单位 bug 成本（美元）并用失败反馈驱动多轮修复 | 是（成本显式报告） | 3.5 成本-成功率 trade-off 例证 | 为本文提供“成本量化口径”的直接引用 | 用对话式反馈循环修复并给出可复现的单位成本估计 |
| E | RepairAgent: An Autonomous, LLM-Based Agent for Program Repair | Islem Bouzenia et al. | 2024 | arXiv / ICSE’25 | citeturn4search1turn4search5 | APR agent 成本统计 | Defects4J | 报告平均每 bug token 成本并以工具调用 agent 实现自主修复 | 是（token 成本） | 3.5 Agent 成本口径 | 为本文建立“每阶段/每 bug token”的比较基线 | 把 APR 做成工具调用 agent，并给出 token 成本量化 |
| E | SWE-bench Lite | （基准维护团队） | 2024 | 官方基准页面 | citeturn6search3 | 低成本评测子集 | issue resolution 评测 | 明确以“降低评测成本、加速迭代”为目标构造子集 | 是（评测成本） | 3.5 评测成本动机 | 为本文“成本驱动研究空白”的 benchmark 侧证据 | 用 benchmark 子集设计降低研究与迭代成本 |
| E | SWE-Effi: Re-Evaluating Software AI Agent System Effectiveness Under Resource Constraints | Zhiyu Fan et al. | 2025 | OpenReview / arXiv | citeturn23view2turn23view1 | 资源约束下有效性评测 | SWE agent 脚手架 | 提出多维 effectiveness 指标，指出“昂贵失败”等现象并重排榜单 | 是（token/time 等资源） | 3.5 Agent overhead 与评测指标 | 为本文提出“阶段化成本/失败成本”提供直接论据 | 不只看 resolve rate，而是把资源消耗纳入系统有效性定义 |
| E | Reducing Cost of LLM Agents with Trajectory Reduction（AgentDiet） | Yuan-An Xiao et al. | 2026 | PACMSE / FSE（页面信息） | citeturn23view0 | 轨迹级成本优化 | 多轮代码 agent | 推理时删除冗余/过期轨迹信息，报告 token 与总成本下降且保持性能 | 是（核心目标） | 3.5 轨迹级 overhead | 为本文“上下文/轨迹压缩降低成本”提供 agent 侧证据 | 通过轨迹裁剪减少 token snowball，降低多轮 agent 成本 |

## 前期工作定位

**前期工作 1：How to Compress Long-Context Code? An Exploratory Study**  
- 名称：How to Compress Long-Context Code? An Exploratory Study  
- 类型：从标题判断更像“探索性研究（exploratory study）”，可能偏评测/分析而非提出全新算法（需以正文为准）  
- 研究对象：长上下文代码任务中的“上下文压缩/选择/管理”策略与其对任务效果的影响（推断）  
- 核心贡献：更可能是厘清不同压缩策略在代码任务上的收益与失败模式、给出压缩—效果 trade-off 的观察结论（推断）  
- 与当前毕设关系：属于“研究基础/桥梁”——为“在 issue resolution 场景下做成本优化与上下文工程”提供经验结论、基线选择依据与评价维度  
- 最适合融入哪一章：更适合放在 chap03 的“长上下文代码理解与上下文压缩”以及“成本优化与 agent overhead”两节作为已有工作基础和动机来源  
- 可引用性说明：本次调研未能在公开一手索引（论文官方页/会议论文集页/预印本页）中检索到与该标题精确匹配的可引用条目；因此上述定位仅能基于标题语义做“保守推断”，不宜直接写入正文作为事实陈述（除非补充论文 PDF 或正式链接）。

**前期工作 2：OmniGIRL /（可能对应）多语言多模态 issue resolution 基准扩展**  
- 名称：OmniGIRL: A Multilingual and Multimodal Benchmark for GitHub Issue Resolution  
- 类型：Benchmark/数据集（issue resolution 评测基准）  
- 研究对象：多语言（Python/Java/JavaScript/TypeScript）、多领域与多模态（含图）issue resolution 任务分布与现有模型/系统表现 citeturn18view3turn13search9  
- 核心贡献：构造并发布更贴近真实生态分布的 issue resolution 基准，揭示现有系统在多语言与含图场景中的明显短板，并做失败原因分析 citeturn18view3  
- 与当前毕设关系：提供“任务场景基础”与“更真实的外部评测集”，可作为本文方法与成本优化策略的压力测试与泛化评估基准  
- 最适合融入哪一章：适合放在 chap03 的“仓库级任务与 GitHub issue resolution”作为任务演进与数据集版图的一部分；在方法与实验章中可作为扩展实验/外部验证，但其自身更偏背景与研究基础（而非本文核心算法贡献）。