#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml
from loguru import logger


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.scripts.run_experiment import load_swebench_instances


METHOD_MATRIX = [
    {
        "experiment": "subset_baseline_raw",
        "strategy": "baseline_raw",
        "method": {"name": "none"},
        "agent": {"max_steps": 60},
    },
    {
        "experiment": "subset_rag_topk",
        "strategy": "rag_topk",
        "method": {"name": "rag_topk", "top_k_files": 4, "snippet_lines": 220},
        "agent": {"max_steps": 60},
    },
    {
        "experiment": "subset_rag_function",
        "strategy": "rag_function",
        "method": {"name": "rag_function", "top_k_files": 4, "snippet_lines": 220, "enable_function_trim": True},
        "agent": {"max_steps": 60},
    },
    {
        "experiment": "subset_llmlingua_original",
        "strategy": "llmlingua_original",
        "method": {
            "name": "llmlingua_original",
            "top_k_files": 4,
            "snippet_lines": 220,
            "enable_function_trim": True,
            "llmlingua_model_name": "deepseek-ai/deepseek-coder-1.3b-base",
            "llmlingua_device_map": "cpu",
        },
        "agent": {"max_steps": 60},
    },
    {
        "experiment": "subset_pruning_budget",
        "strategy": "pruning_budget",
        "method": {"name": "pruning_budget", "include_pruning_hints": True},
        "agent": {"max_steps": 40},
    },
    {
        "experiment": "subset_skill_abstraction",
        "strategy": "skill_abstraction",
        "method": {"name": "skill_abstraction", "top_k_files": 4, "snippet_lines": 220, "include_skill_scaffold": True},
        "agent": {"max_steps": 60},
    },
    {
        "experiment": "subset_skill_memory_md",
        "strategy": "skill_memory_md",
        "method": {
            "name": "skill_memory_md",
            "top_k_files": 4,
            "snippet_lines": 220,
            "include_skill_memory": True,
            "skill_file": "skills.md",
        },
        "agent": {"max_steps": 60},
    },
    {
        "experiment": "subset_hybrid",
        "strategy": "hybrid",
        "method": {"name": "hybrid", "top_k_files": 4, "snippet_lines": 220, "enable_function_trim": True, "token_budget": 2500},
        "agent": {"max_steps": 40},
    },
    {
        "experiment": "subset_hybrid_llmlingua",
        "strategy": "hybrid_llmlingua",
        "method": {
            "name": "hybrid_llmlingua",
            "top_k_files": 4,
            "snippet_lines": 220,
            "enable_function_trim": True,
            "token_budget": 2500,
            "llmlingua_model_name": "deepseek-ai/deepseek-coder-1.3b-base",
            "llmlingua_device_map": "cpu",
        },
        "agent": {"max_steps": 40},
    },
]


def _write_config(output_root: Path, base_cfg: dict, method_cfg: dict) -> Path:
    config = json.loads(json.dumps(base_cfg))
    config["experiment"] = method_cfg["experiment"]
    config["strategy"] = method_cfg["strategy"]
    config["output_dir"] = str(output_root / method_cfg["experiment"])
    config["agent"]["max_steps"] = int(base_cfg["agent"]["max_steps"])
    config["method"] = method_cfg["method"]
    config_path = output_root / "configs" / f"{method_cfg['experiment']}.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    return config_path


def _write_instance_file(output_root: Path, instances: list[dict]) -> Path:
    path = output_root / "subset_instances.json"
    path.write_text(json.dumps(instances, indent=2))
    return path


def _build_base_config(args: argparse.Namespace) -> dict:
    return {
        "experiment": "placeholder",
        "strategy": "placeholder",
        "agent": {
            "type": "mini-swe-agent",
            "max_steps": args.max_steps,
        },
        "gateway": {
            "base_url": args.base_url,
            "api_key": args.api_key,
            "default_model": args.model,
        },
        "output_dir": "experiments/placeholder",
    }


def _summarize(output_root: Path) -> None:
    rows = []
    for method in METHOD_MATRIX:
        summary_path = output_root / method["experiment"] / "experiment_summary.json"
        if not summary_path.exists():
            continue
        data = json.loads(summary_path.read_text())
        rows.append(
            {
                "experiment": data["experiment"],
                "strategy": data["strategy"],
                "n_instances": data["n_instances"],
                "pass_rate": data["pass_rate"],
                "avg_total_tokens": data["avg_total_tokens"],
            }
        )

    (output_root / "matrix_summary.json").write_text(json.dumps(rows, indent=2))
    if rows:
        header = "experiment,strategy,n_instances,pass_rate,avg_total_tokens\n"
        lines = [
            f"{row['experiment']},{row['strategy']},{row['n_instances']},{row['pass_rate']:.4f},{row['avg_total_tokens']:.2f}"
            for row in rows
        ]
        (output_root / "matrix_summary.csv").write_text(header + "\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a subset-method matrix for SWE-bench.")
    parser.add_argument("--split", default="verified", choices=["lite", "full", "verified"])
    parser.add_argument("--instances", type=int, default=12, help="How many SWE-bench instances to run.")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--max-steps", type=int, default=60)
    parser.add_argument("--output-root", default="experiments/subset_method_matrix")
    parser.add_argument("--instance-file", help="Optional JSON file with explicit instance list.")
    parser.add_argument("--mock", action="store_true", help="Use mock runner instead of real API calls.")
    parser.add_argument(
        "--methods",
        nargs="*",
        help="Optional subset of strategy names to run, e.g. baseline_raw rag_topk llmlingua_original.",
    )
    args = parser.parse_args()

    output_root = ROOT / args.output_root
    output_root.mkdir(parents=True, exist_ok=True)

    if args.instance_file:
        instances = json.loads(Path(args.instance_file).read_text())
    else:
        instances = load_swebench_instances(split=args.split, n=args.instances)

    instance_file = _write_instance_file(output_root, instances)
    base_cfg = _build_base_config(args)

    methods_to_run = METHOD_MATRIX
    if args.methods:
        wanted = set(args.methods)
        methods_to_run = [m for m in METHOD_MATRIX if m["strategy"] in wanted]
        missing = wanted - {m["strategy"] for m in methods_to_run}
        if missing:
            raise SystemExit(f"Unknown methods requested: {sorted(missing)}")

    for method in methods_to_run:
        config_path = _write_config(output_root, base_cfg, method)
        cmd = [
            sys.executable,
            str(ROOT / "src" / "scripts" / "run_experiment.py"),
            "--config",
            str(config_path),
            "--split",
            args.split,
            "--workers",
            str(args.workers),
            "--instance-file",
            str(instance_file),
        ]
        if args.mock:
            cmd.append("--mock")
        logger.info(f"Running {method['experiment']}")
        subprocess.run(cmd, check=False)

    _summarize(output_root)
    logger.info(f"Subset method matrix written to {output_root}")


if __name__ == "__main__":
    main()
