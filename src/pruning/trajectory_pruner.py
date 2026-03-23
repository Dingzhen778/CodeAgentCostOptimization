"""
Trajectory Pruning 模块

在 Agent 运行过程中，实时拦截并剪枝冗余动作，减少步骤数和 token 消耗：

1. DeduplicationPruner  — 去重：若文件已读过，跳过重复 read
2. StepLimitPruner      — 步骤上限：超过 max_steps 时强制停止
3. SearchLimitPruner    — Search 调用上限
4. EarlyStopPruner      — 检测到 patch 已生成时提前退出
5. TrajectoryPruner     — 组合以上策略
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PruningDecision(Enum):
    ALLOW = "allow"         # 允许执行
    SKIP = "skip"           # 跳过（返回缓存或空结果）
    STOP = "stop"           # 停止整个 agent


@dataclass
class PruningConfig:
    """剪枝策略配置"""
    enable_dedup: bool = True           # 去重相同文件读取
    enable_step_limit: bool = True
    max_steps: int = 30
    enable_search_limit: bool = True
    max_search_calls: int = 10          # 最多搜索次数
    enable_early_stop: bool = True      # 检测 patch 生成后提前退出
    token_step_budget: Optional[int] = None  # 单步 token 上限（None=不限）


@dataclass
class ActionContext:
    """当前 Agent 准备执行的动作上下文"""
    step: int
    action: str           # read_file / search / bash / edit / write_file
    target: str           # 文件路径 / 搜索词
    content: str = ""     # 将要传入的内容（用于 token 预估）


# -----------------------------------------------------------------------
# 各独立剪枝器
# -----------------------------------------------------------------------

class DeduplicationPruner:
    """
    去重剪枝：记录已读文件，阻止重复 read_file 调用
    """

    def __init__(self):
        self._seen: dict[str, set[str]] = {}   # action -> set of targets

    def decide(self, ctx: ActionContext) -> PruningDecision:
        if ctx.action not in ("read_file", "search"):
            return PruningDecision.ALLOW

        if ctx.action not in self._seen:
            self._seen[ctx.action] = set()

        if ctx.target in self._seen[ctx.action]:
            return PruningDecision.SKIP

        self._seen[ctx.action].add(ctx.target)
        return PruningDecision.ALLOW

    @property
    def stats(self) -> dict:
        return {k: len(v) for k, v in self._seen.items()}


class StepLimitPruner:
    """步骤数上限"""

    def __init__(self, max_steps: int = 30):
        self.max_steps = max_steps

    def decide(self, ctx: ActionContext) -> PruningDecision:
        if ctx.step >= self.max_steps:
            return PruningDecision.STOP
        return PruningDecision.ALLOW


class SearchLimitPruner:
    """搜索调用次数上限"""

    def __init__(self, max_search_calls: int = 10):
        self.max_search_calls = max_search_calls
        self._count = 0

    def decide(self, ctx: ActionContext) -> PruningDecision:
        if ctx.action != "search":
            return PruningDecision.ALLOW
        if self._count >= self.max_search_calls:
            return PruningDecision.STOP
        self._count += 1
        return PruningDecision.ALLOW

    @property
    def search_count(self) -> int:
        return self._count


class EarlyStopPruner:
    """
    检测 patch 已生成（edit/write_file 已调用）时，
    如果后续只有 bash 测试，可以提前退出
    """

    def __init__(self):
        self._patch_generated = False
        self._test_count = 0

    def notify_action_result(self, action: str, result: str):
        """在动作执行后调用，更新状态"""
        if action in ("edit", "write_file"):
            self._patch_generated = True
        if action == "bash" and self._patch_generated:
            self._test_count += 1

    def decide(self, ctx: ActionContext) -> PruningDecision:
        # patch 生成后允许最多 2 次 bash 测试，之后停止
        if self._patch_generated and ctx.action == "bash" and self._test_count >= 2:
            return PruningDecision.STOP
        return PruningDecision.ALLOW


# -----------------------------------------------------------------------
# 组合剪枝器
# -----------------------------------------------------------------------

class TrajectoryPruner:
    """
    主剪枝控制器

    用法（在 Agent 每步之前调用）：
        pruner = TrajectoryPruner(PruningConfig(max_steps=25, max_search_calls=8))

        decision = pruner.before_action(ActionContext(step=5, action="read_file", target="utils.py"))
        if decision == PruningDecision.SKIP:
            # 返回缓存或空结果，不实际调用工具
            pass
        elif decision == PruningDecision.STOP:
            # 终止 agent
            break
    """

    def __init__(self, config: Optional[PruningConfig] = None):
        self.config = config or PruningConfig()
        self._pruners = []

        if self.config.enable_dedup:
            self._dedup = DeduplicationPruner()
            self._pruners.append(self._dedup)
        else:
            self._dedup = None

        if self.config.enable_step_limit:
            self._step_limit = StepLimitPruner(self.config.max_steps)
            self._pruners.append(self._step_limit)
        else:
            self._step_limit = None

        if self.config.enable_search_limit:
            self._search_limit = SearchLimitPruner(self.config.max_search_calls)
            self._pruners.append(self._search_limit)
        else:
            self._search_limit = None

        if self.config.enable_early_stop:
            self._early_stop = EarlyStopPruner()
            self._pruners.append(self._early_stop)
        else:
            self._early_stop = None

        self._pruning_log: list[dict] = []

    # ------------------------------------------------------------------
    # 核心接口
    # ------------------------------------------------------------------

    def before_action(self, ctx: ActionContext) -> PruningDecision:
        """在每个 Agent 动作执行前调用，返回是否允许/跳过/停止"""
        for pruner in self._pruners:
            decision = pruner.decide(ctx)
            if decision != PruningDecision.ALLOW:
                self._pruning_log.append({
                    "step": ctx.step,
                    "action": ctx.action,
                    "target": ctx.target,
                    "decision": decision.value,
                    "pruner": type(pruner).__name__,
                })
                return decision
        return PruningDecision.ALLOW

    def after_action(self, action: str, result: str):
        """在每个 Agent 动作执行后调用，更新内部状态"""
        if self._early_stop:
            self._early_stop.notify_action_result(action, result)

    # ------------------------------------------------------------------
    # 统计
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        s: dict = {
            "total_pruned": len(self._pruning_log),
            "pruning_log": self._pruning_log,
        }
        if self._dedup:
            s["dedup_unique_reads"] = self._dedup.stats
        if self._search_limit:
            s["search_calls"] = self._search_limit.search_count
        return s
