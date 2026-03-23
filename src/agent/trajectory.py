"""
轨迹（Trajectory）数据结构

记录 Agent 每一步的动作、输入、输出，用于：
  1. 事后分析（cost breakdown）
  2. Trajectory Pruning（实时剪枝）
  3. 可视化回放
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class TrajectoryStep:
    """Agent 的单步动作记录"""
    step: int
    action: str                    # 工具名：read_file / search / bash / edit …
    target: str                    # 操作对象：文件路径 / 搜索词 …
    input_content: str = ""        # 传给工具的完整内容（可能很长）
    output_content: str = ""       # 工具返回结果（截断后）
    input_tokens: int = 0          # 此步骤 input token
    output_tokens: int = 0
    latency: float = 0.0
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        # 截断长字段，避免 jsonl 过大
        d["input_content"] = d["input_content"][:500] if d["input_content"] else ""
        d["output_content"] = d["output_content"][:500] if d["output_content"] else ""
        return d


class Trajectory:
    """
    完整轨迹容器

    用法：
        traj = Trajectory(instance_id="django__django-12345", log_dir="logs/run_001")
        traj.add(step=1, action="search", target="login function")
        ...
        traj.save()
    """

    def __init__(self, instance_id: str, log_dir: str | Path):
        self.instance_id = instance_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._steps: list[TrajectoryStep] = []
        self._traj_file = self.log_dir / "trajectory.jsonl"

    def add(
        self,
        step: int,
        action: str,
        target: str,
        input_content: str = "",
        output_content: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency: float = 0.0,
        **metadata: Any,
    ) -> TrajectoryStep:
        ts = TrajectoryStep(
            step=step,
            action=action,
            target=target,
            input_content=input_content,
            output_content=output_content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency=latency,
            metadata=metadata,
        )
        self._steps.append(ts)
        with self._traj_file.open("a") as f:
            f.write(json.dumps(ts.to_dict()) + "\n")
        return ts

    # ------------------------------------------------------------------
    # 统计 / 查询接口
    # ------------------------------------------------------------------

    def steps(self) -> list[TrajectoryStep]:
        return list(self._steps)

    def action_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for s in self._steps:
            counts[s.action] = counts.get(s.action, 0) + 1
        return counts

    def unique_targets(self, action: Optional[str] = None) -> set[str]:
        """返回访问过的唯一 target（用于去重剪枝）"""
        return {
            s.target
            for s in self._steps
            if action is None or s.action == action
        }

    def total_tokens(self) -> int:
        return sum(s.input_tokens + s.output_tokens for s in self._steps)

    def save(self) -> Path:
        """（已实时写入，此方法备用）"""
        return self._traj_file
