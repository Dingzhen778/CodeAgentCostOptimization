"""
实验结果分析器

从 experiments/ 目录读取多个实验的 summary.json，
生成对比表格和统计数据。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd


class CostAnalyzer:
    """
    加载多个实验结果，生成对比分析

    用法：
        analyzer = CostAnalyzer("experiments/")
        df = analyzer.load_all()
        print(analyzer.summary_table())
        analyzer.cost_breakdown("baseline_vanilla")
    """

    def __init__(self, experiments_dir: str | Path = "experiments"):
        self.experiments_dir = Path(experiments_dir)
        self.project_root = self.experiments_dir.parent
        self.gateway_log_dir = self.project_root / "logs" / "gateway"
        self._df: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    # 数据加载
    # ------------------------------------------------------------------

    def load_all(self) -> pd.DataFrame:
        """
        扫描所有实验目录，加载 summary.json，返回 DataFrame
        每行 = 一个 instance 的结果
        """
        records = []
        if not self.experiments_dir.exists():
            self._df = pd.DataFrame()
            return self._df

        gateway_rows = self._load_gateway_instance_rows()
        gateway_by_key = {
            (row["experiment"], row["instance_id"]): row for row in gateway_rows
        }

        for exp_dir in sorted(self.experiments_dir.iterdir()):
            if not exp_dir.is_dir():
                continue
            experiment = exp_dir.name
            for instance_dir in exp_dir.iterdir():
                summary_file = instance_dir / "summary.json"
                if summary_file.exists():
                    with summary_file.open() as f:
                        data = json.load(f)
                    data["experiment"] = experiment
                    gateway_row = gateway_by_key.get((experiment, data.get("instance_id", "")))
                    if gateway_row:
                        data.update({
                            "input_tokens": gateway_row.get("input_tokens", data.get("input_tokens")),
                            "output_tokens": gateway_row.get("output_tokens", data.get("output_tokens")),
                            "total_tokens": gateway_row.get("total_tokens", data.get("total_tokens")),
                            "total_calls": gateway_row.get("total_calls", data.get("total_calls")),
                            "total_latency": gateway_row.get("total_latency", data.get("total_latency")),
                            "tool_breakdown": gateway_row.get("tool_breakdown", data.get("tool_breakdown")),
                            "token_source": "gateway",
                        })
                    else:
                        data["token_source"] = "local"
                    records.append(data)

        self._df = pd.DataFrame(records)
        return self._df

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            self.load_all()
        return self._df

    # ------------------------------------------------------------------
    # 分析接口
    # ------------------------------------------------------------------

    def summary_table(self) -> pd.DataFrame:
        """按实验汇总：pass rate、平均 token、效率"""
        df = self.df
        grouped = df.groupby("experiment").agg(
            instances=("instance_id", "count"),
            pass_rate=("success", "mean"),
            avg_total_tokens=("total_tokens", "mean"),
            avg_input_tokens=("input_tokens", "mean"),
            avg_output_tokens=("output_tokens", "mean"),
            avg_steps=("total_steps", "mean"),
            avg_calls=("total_calls", "mean"),
            avg_runtime=("runtime", "mean"),
        ).reset_index()

        # 效率指标
        grouped["efficiency"] = (
            grouped["pass_rate"] / grouped["avg_total_tokens"] * 1e6
        ).round(4)

        # token 节省率（相对于 vanilla baseline）
        if "baseline_vanilla" in grouped["experiment"].values:
            baseline_tokens = grouped.loc[
                grouped["experiment"] == "baseline_vanilla", "avg_total_tokens"
            ].values[0]
            grouped["token_saving_pct"] = (
                (baseline_tokens - grouped["avg_total_tokens"]) / baseline_tokens * 100
            ).round(1)
        else:
            grouped["token_saving_pct"] = None

        return grouped.sort_values("avg_total_tokens")

    def cost_breakdown(self, experiment: str) -> pd.DataFrame:
        """分析单个实验的 tool-level token 分布"""
        gateway_breakdown = self._gateway_cost_breakdown(experiment)
        if not gateway_breakdown.empty:
            return gateway_breakdown

        df = self.df[self.df["experiment"] == experiment]
        if df.empty:
            return pd.DataFrame()

        # 从 request_log.jsonl 读取 tool-level 数据
        records = []
        for _, row in df.iterrows():
            instance_id = row.get("instance_id", "")
            log_file = (
                self.experiments_dir / experiment / instance_id / "request_log.jsonl"
            )
            if not log_file.exists():
                continue
            with log_file.open() as f:
                for line in f:
                    r = json.loads(line)
                    r["experiment"] = experiment
                    r["instance_id"] = instance_id
                    records.append(r)

        if not records:
            return pd.DataFrame()

        req_df = pd.DataFrame(records)
        return (
            req_df.groupby("tool")
            .agg(
                calls=("tool", "count"),
                total_tokens=("total_tokens", "sum"),
                avg_tokens=("total_tokens", "mean"),
            )
            .reset_index()
            .sort_values("total_tokens", ascending=False)
        )

    def pareto_data(self) -> pd.DataFrame:
        """返回用于绘制 Pareto 曲线的数据（cost vs pass rate）"""
        return self.summary_table()[
            ["experiment", "avg_total_tokens", "pass_rate", "efficiency"]
        ].copy()

    # ------------------------------------------------------------------
    # Gateway 优先加载
    # ------------------------------------------------------------------

    def _load_gateway_instance_rows(self) -> list[dict]:
        rows: list[dict] = []
        for exp_dir in sorted(self.experiments_dir.iterdir()):
            if not exp_dir.is_dir():
                continue
            summary_file = exp_dir / "gateway_instance_summary.json"
            if not summary_file.exists():
                continue
            with summary_file.open() as f:
                data = json.load(f)
            for row in data:
                row = dict(row)
                row.setdefault("experiment", exp_dir.name)
                rows.append(row)
        return rows

    def _gateway_cost_breakdown(self, experiment: str) -> pd.DataFrame:
        summary_file = self.experiments_dir / experiment / "gateway_instance_summary.json"
        if summary_file.exists():
            with summary_file.open() as f:
                rows = json.load(f)
        else:
            rows = self._load_gateway_breakdown_from_global_log(experiment)

        if not rows:
            return pd.DataFrame()

        totals: dict[str, dict[str, float]] = {}
        for row in rows:
            for tool, stats in row.get("tool_breakdown", {}).items():
                agg = totals.setdefault(tool, {"calls": 0, "total_tokens": 0})
                agg["calls"] += stats.get("calls", 0)
                agg["total_tokens"] += stats.get("tokens", 0)

        if not totals:
            return pd.DataFrame()

        breakdown = pd.DataFrame([
            {
                "tool": tool,
                "calls": stats["calls"],
                "total_tokens": stats["total_tokens"],
                "avg_tokens": stats["total_tokens"] / max(stats["calls"], 1),
            }
            for tool, stats in totals.items()
        ])
        return breakdown.sort_values("total_tokens", ascending=False)

    def _load_gateway_breakdown_from_global_log(self, experiment: str) -> list[dict]:
        log_file = self.gateway_log_dir / "gateway_token_log.jsonl"
        if not log_file.exists():
            return []

        grouped: dict[tuple[str, str, str], dict] = {}
        with log_file.open() as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("experiment") != experiment:
                    continue
                instance_id = record.get("instance_id", "")
                if not instance_id:
                    continue
                key = (
                    instance_id,
                    record.get("experiment", ""),
                    record.get("strategy", ""),
                )
                if key not in grouped:
                    grouped[key] = {
                        "instance_id": instance_id,
                        "experiment": record.get("experiment", ""),
                        "strategy": record.get("strategy", ""),
                        "tool_breakdown": {},
                    }
                tool = record.get("tool", "default")
                tb = grouped[key]["tool_breakdown"].setdefault(tool, {"calls": 0, "tokens": 0})
                tb["calls"] += 1
                tb["tokens"] += record.get("total_tokens", 0)
        return list(grouped.values())
