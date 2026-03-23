"""
实验结果可视化

生成论文核心图：
1. Pareto 曲线（Cost vs Pass Rate）
2. Token 成本分布（Breakdown）
3. 实验对比柱状图
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

# 论文风格
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "figure.dpi": 150,
})

COLORS = sns.color_palette("tab10")

EXPERIMENT_LABELS = {
    "baseline_vanilla":      "Vanilla (No Opt.)",
    "baseline_small_model":  "Small Model Only",
    "exp1_compression":      "Context Compression",
    "exp2_pruning":          "Trajectory Pruning",
    "exp3_hybrid":           "Hybrid (Ours)",
    "exp4_routing":          "Model Routing",
}


class ExperimentPlotter:
    """
    用法：
        plotter = ExperimentPlotter(output_dir="figures/")
        plotter.plot_pareto(summary_df)
        plotter.plot_token_breakdown(breakdown_df, experiment="exp3_hybrid")
        plotter.plot_comparison_bar(summary_df)
    """

    def __init__(self, output_dir: str | Path = "figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Pareto 曲线（核心图）
    # ------------------------------------------------------------------

    def plot_pareto(
        self,
        df: pd.DataFrame,
        save_name: str = "pareto_curve.pdf",
        highlight: Optional[str] = "exp3_hybrid",
    ):
        """
        x 轴：平均 token 成本
        y 轴：Pass Rate
        """
        fig, ax = plt.subplots(figsize=(7, 5))

        for i, row in df.iterrows():
            exp = row["experiment"]
            label = EXPERIMENT_LABELS.get(exp, exp)
            color = COLORS[i % len(COLORS)]
            marker = "*" if exp == highlight else "o"
            size = 200 if exp == highlight else 100
            ax.scatter(
                row["avg_total_tokens"] / 1000,
                row["pass_rate"] * 100,
                s=size,
                c=[color],
                marker=marker,
                label=label,
                zorder=3,
            )

        ax.set_xlabel("Average Token Cost (K tokens / instance)")
        ax.set_ylabel("Pass Rate (%)")
        ax.set_title("Cost–Performance Pareto Curve on SWE-bench")
        ax.legend(loc="lower right", fontsize=9)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax.grid(True, alpha=0.3)
        ax.set_xlim(left=0)
        ax.set_ylim(0, 55)

        # 标注"我们的方法"
        if highlight and highlight in df["experiment"].values:
            h_row = df[df["experiment"] == highlight].iloc[0]
            ax.annotate(
                "Ours",
                xy=(h_row["avg_total_tokens"] / 1000, h_row["pass_rate"] * 100),
                xytext=(10, -20),
                textcoords="offset points",
                fontsize=9,
                color="red",
                arrowprops=dict(arrowstyle="->", color="red"),
            )

        plt.tight_layout()
        out = self.output_dir / save_name
        plt.savefig(out, bbox_inches="tight")
        plt.close()
        print(f"Saved: {out}")
        return out

    # ------------------------------------------------------------------
    # 2. Token 成本分布（Breakdown 饼图 / 柱状图）
    # ------------------------------------------------------------------

    def plot_token_breakdown(
        self,
        breakdown_df: pd.DataFrame,
        experiment: str = "baseline_vanilla",
        save_name: Optional[str] = None,
    ):
        if breakdown_df.empty:
            print("No data to plot.")
            return

        save_name = save_name or f"token_breakdown_{experiment}.pdf"
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # 左：饼图
        ax1.pie(
            breakdown_df["total_tokens"],
            labels=breakdown_df["tool"],
            autopct="%1.1f%%",
            colors=COLORS[: len(breakdown_df)],
            startangle=90,
        )
        ax1.set_title(f"Token Distribution by Tool\n({EXPERIMENT_LABELS.get(experiment, experiment)})")

        # 右：横向柱状图
        sns.barplot(
            data=breakdown_df,
            y="tool",
            x="total_tokens",
            palette="tab10",
            ax=ax2,
        )
        ax2.set_xlabel("Total Tokens")
        ax2.set_ylabel("Tool")
        ax2.set_title("Token Cost per Tool")
        ax2.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))

        plt.tight_layout()
        out = self.output_dir / save_name
        plt.savefig(out, bbox_inches="tight")
        plt.close()
        print(f"Saved: {out}")
        return out

    # ------------------------------------------------------------------
    # 3. 对比柱状图（Token 节省 vs Pass Rate）
    # ------------------------------------------------------------------

    def plot_comparison_bar(
        self,
        df: pd.DataFrame,
        save_name: str = "comparison_bar.pdf",
    ):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        labels = [EXPERIMENT_LABELS.get(e, e) for e in df["experiment"]]
        x = np.arange(len(labels))
        width = 0.6

        # 左：平均 token
        bars = ax1.bar(x, df["avg_total_tokens"] / 1000, width, color=COLORS[: len(df)])
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
        ax1.set_ylabel("Avg Tokens (K)")
        ax1.set_title("Token Cost Comparison")
        ax1.bar_label(bars, fmt="%.0fK", fontsize=8, padding=2)

        # 右：Pass Rate
        bars2 = ax2.bar(x, df["pass_rate"] * 100, width, color=COLORS[: len(df)])
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
        ax2.set_ylabel("Pass Rate (%)")
        ax2.set_title("Pass Rate Comparison")
        ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax2.bar_label(bars2, fmt="%.1f%%", fontsize=8, padding=2)
        ax2.set_ylim(0, 55)

        plt.tight_layout()
        out = self.output_dir / save_name
        plt.savefig(out, bbox_inches="tight")
        plt.close()
        print(f"Saved: {out}")
        return out
