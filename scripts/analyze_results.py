#!/usr/bin/env python3
"""
analyze_results.py

分析实验结果，生成对比图表

用法：
    python scripts/analyze_results.py --exp-dir experiments/ --output figures/
    python scripts/analyze_results.py --exp-dir experiments/ --experiment exp3_hybrid
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.analysis.cost_analyzer import CostAnalyzer
from src.analysis.plotter import ExperimentPlotter


def main():
    parser = argparse.ArgumentParser(description="Analyze cost optimization experiment results")
    parser.add_argument("--exp-dir", default="experiments", help="实验目录")
    parser.add_argument("--output", default="figures", help="图表输出目录")
    parser.add_argument("--experiment", default=None, help="只分析某个特定实验的 breakdown")
    args = parser.parse_args()

    analyzer = CostAnalyzer(args.exp_dir)
    plotter = ExperimentPlotter(args.output)

    # 加载所有实验数据
    logger.info("Loading experiment data...")
    df = analyzer.load_all()

    if df.empty:
        logger.warning("No experiment data found. Run some experiments first.")
        return

    # 汇总表
    summary = analyzer.summary_table()
    logger.info("\n" + summary.to_string(index=False))

    # Pareto 曲线
    pareto_data = analyzer.pareto_data()
    plotter.plot_pareto(pareto_data)

    # 对比柱状图
    plotter.plot_comparison_bar(summary)

    # Token Breakdown（针对特定实验）
    if args.experiment:
        bd = analyzer.cost_breakdown(args.experiment)
        if not bd.empty:
            plotter.plot_token_breakdown(bd, experiment=args.experiment)
        else:
            logger.warning(f"No breakdown data for {args.experiment}")
    else:
        # 对所有实验生成 breakdown
        for exp in summary["experiment"]:
            bd = analyzer.cost_breakdown(exp)
            if not bd.empty:
                plotter.plot_token_breakdown(bd, experiment=exp)

    logger.info(f"\nAll figures saved to: {args.output}/")


if __name__ == "__main__":
    main()
