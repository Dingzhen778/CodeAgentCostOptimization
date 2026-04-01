#!/usr/bin/env python3
"""
run_experiment.py

运行单个或批量 SWE-bench 实验

用法：
    # Mock 模式（本地调试，不需要真实 API）
    python scripts/run_experiment.py \
        --config configs/experiments/baseline_vanilla.yaml \
        --mock --instances 10

    # 真实模式
    python scripts/run_experiment.py \
        --config configs/experiments/exp3_hybrid.yaml \
        --split lite \
        --instances 50 \
        --workers 4
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from loguru import logger
from tqdm import tqdm

# 项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.agent.runner import AgentRunner


def load_swebench_instances(split: str = "lite", n: int = None) -> list[dict]:
    """加载 SWE-bench 实例列表"""
    try:
        from swebench.harness.utils import load_swebench_dataset
        instances = load_swebench_dataset(f"princeton-nlp/SWE-bench_{split.capitalize()}")
        if n:
            instances = instances[:n]
        return instances
    except ImportError:
        logger.warning("swebench not installed, using mock instances")
        return _mock_instances(n or 5)


def load_instances_from_file(path: str | Path) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Instance file must contain a JSON list of SWE-bench instances.")
    return data


def _mock_instances(n: int) -> list[dict]:
    """生成 mock instances（用于本地调试）"""
    return [
        {
            "instance_id": f"django__django-{10000 + i}",
            "repo": "django/django",
            "problem_statement": f"Fix bug #{i} in the authentication module",
            "base_commit": "abc123",
        }
        for i in range(n)
    ]


def run_all(
    runner: AgentRunner,
    instances: list[dict],
    workers: int = 1,
) -> list[dict]:
    """并发运行所有 instances"""
    results = []

    if workers <= 1:
        for inst in tqdm(instances, desc=f"Running {runner.experiment}"):
            result = runner.run(inst)
            results.append(result.to_dict())
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(runner.run, inst): inst for inst in instances}
            for future in tqdm(as_completed(futures), total=len(futures), desc=f"Running {runner.experiment}"):
                try:
                    result = future.result()
                    results.append(result.to_dict())
                except Exception as e:
                    inst = futures[future]
                    logger.error(f"[{inst['instance_id']}] Failed: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Run SWE-bench cost optimization experiment")
    parser.add_argument("--config", required=True, help="实验配置文件路径")
    parser.add_argument("--split", default="lite", choices=["lite", "full", "verified"])
    parser.add_argument("--instances", type=int, default=None, help="运行前 N 个 instance（调试用）")
    parser.add_argument("--workers", type=int, default=1, help="并发 worker 数")
    parser.add_argument("--mock", action="store_true", help="使用 mock agent（不需要真实 API）")
    parser.add_argument("--instance-file", help="显式指定一个 JSON instance 列表文件")
    parser.add_argument("--instance-ids", nargs="*", help="只运行这些 instance_id")
    args = parser.parse_args()

    # 加载配置
    runner = AgentRunner.from_config(args.config)

    # 如果是 mock 模式，覆盖 agent type
    if args.mock:
        runner.config.setdefault("agent", {})["type"] = "mock"
        logger.info("Running in MOCK mode")

    # 加载 instances
    if args.instance_file:
        instances = load_instances_from_file(args.instance_file)
    elif args.mock:
        instances = _mock_instances(args.instances or 5)
    else:
        instances = load_swebench_instances(split=args.split, n=args.instances)

    if args.instance_ids:
        keep = set(args.instance_ids)
        instances = [inst for inst in instances if inst["instance_id"] in keep]

    logger.info(f"Experiment: {runner.experiment} | Instances: {len(instances)} | Workers: {args.workers}")

    # 运行
    results = run_all(runner, instances, workers=args.workers)

    # 汇总
    n_success = sum(1 for r in results if r.get("success"))
    total_tokens = sum(r.get("total_tokens", 0) for r in results)
    pass_rate = n_success / len(results) if results else 0

    logger.info(f"\n{'='*50}")
    logger.info(f"Experiment: {runner.experiment}")
    logger.info(f"Instances:  {len(results)}")
    logger.info(f"Pass Rate:  {pass_rate:.1%}")
    logger.info(f"Avg Tokens: {total_tokens / max(1, len(results)):,.0f}")
    logger.info(f"{'='*50}")

    _write_gateway_instance_summary(runner)

    # 写入实验汇总
    summary_out = Path(runner.output_dir) / "experiment_summary.json"
    with summary_out.open("w") as f:
        json.dump({
            "experiment": runner.experiment,
            "strategy": runner.strategy,
            "n_instances": len(results),
            "pass_rate": pass_rate,
            "avg_total_tokens": total_tokens / max(1, len(results)),
            "results": results,
        }, f, indent=2)
    logger.info(f"Summary saved to: {summary_out}")


def _write_gateway_instance_summary(runner: AgentRunner):
    """从全局 gateway log 聚合当前实验的实例级 token 汇总。"""
    script = Path(__file__).parent / "aggregate_gateway_logs.py"
    gateway_log = Path("logs/gateway/gateway_token_log.jsonl")
    if not gateway_log.exists():
        logger.warning("Gateway log not found, skipping gateway instance summary.")
        return

    output = Path(runner.output_dir) / "gateway_instance_summary.json"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--log-file",
            str(gateway_log),
            "--output",
            str(output),
            "--experiment",
            runner.experiment,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.warning(f"Failed to aggregate gateway logs: {result.stderr.strip()}")
        return
    logger.info(result.stdout.strip())


if __name__ == "__main__":
    main()
