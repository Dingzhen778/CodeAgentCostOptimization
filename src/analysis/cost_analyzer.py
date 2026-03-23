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
