"""
Token 使用量记录器
追踪每次 LLM 调用的 token 消耗，支持按 instance / step / tool 分组统计

每次 API 调用生成一条 UsageRecord，写入 request_log.jsonl
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class UsageRecord:
    """单次 LLM 调用的 token 用量记录"""
    instance_id: str
    step: int
    tool: str                        # 当前触发调用的工具名（read_file / search / edit …）
    model: str                       # 实际使用的模型
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency: float                   # 请求耗时（秒）
    timestamp: float = field(default_factory=time.time)
    experiment: str = "default"      # 实验名，用于跨实验对比
    strategy: str = "vanilla"        # 优化策略标签
    extra: dict = field(default_factory=dict)  # 可扩展字段

    def to_dict(self) -> dict:
        return asdict(self)


class TokenLogger:
    """
    线程安全的 token 日志记录器

    用法：
        logger = TokenLogger(log_dir="logs/run_001", instance_id="django__django-12345")
        logger.log(step=3, tool="read_file", model="deepseek-chat",
                   input_tokens=1200, output_tokens=200, latency=1.2)
        summary = logger.summary()
    """

    def __init__(
        self,
        log_dir: str | Path,
        instance_id: str,
        experiment: str = "default",
        strategy: str = "vanilla",
    ):
        self.log_dir = Path(log_dir)
        self.instance_id = instance_id
        self.experiment = experiment
        self.strategy = strategy

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self.log_dir / "request_log.jsonl"
        self._records: list[UsageRecord] = []

    # ------------------------------------------------------------------
    # 记录接口
    # ------------------------------------------------------------------

    def log(
        self,
        step: int,
        tool: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency: float,
        extra: Optional[dict] = None,
    ) -> UsageRecord:
        record = UsageRecord(
            instance_id=self.instance_id,
            step=step,
            tool=tool,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency=latency,
            experiment=self.experiment,
            strategy=self.strategy,
            extra=extra or {},
        )
        self._records.append(record)
        with self._log_file.open("a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")
        return record

    # ------------------------------------------------------------------
    # 统计接口
    # ------------------------------------------------------------------

    def summary(self) -> dict:
        """返回当前 instance 的汇总统计"""
        if not self._records:
            return {}
        total_input = sum(r.input_tokens for r in self._records)
        total_output = sum(r.output_tokens for r in self._records)
        tool_breakdown = {}
        for r in self._records:
            if r.tool not in tool_breakdown:
                tool_breakdown[r.tool] = {"calls": 0, "tokens": 0}
            tool_breakdown[r.tool]["calls"] += 1
            tool_breakdown[r.tool]["tokens"] += r.total_tokens

        return {
            "instance_id": self.instance_id,
            "experiment": self.experiment,
            "strategy": self.strategy,
            "total_steps": max(r.step for r in self._records),
            "total_calls": len(self._records),
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "avg_tokens_per_step": (total_input + total_output) / max(1, len(self._records)),
            "total_latency": sum(r.latency for r in self._records),
            "tool_breakdown": tool_breakdown,
        }

    def save_summary(self, success: Optional[bool] = None) -> Path:
        """将 summary 写入 summary.json"""
        data = self.summary()
        if success is not None:
            data["success"] = success
        out = self.log_dir / "summary.json"
        with out.open("w") as f:
            json.dump(data, f, indent=2)
        return out
