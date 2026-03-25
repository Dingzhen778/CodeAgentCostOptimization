#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx
from swebench.harness.utils import load_swebench_dataset

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent.runner import AgentRunner


ROOT = Path(__file__).resolve().parent.parent


def build_image_name(instance_id: str) -> str:
    docker_compatible = instance_id.replace("__", "_1776_").lower()
    return f"docker.io/swebench/sweb.eval.x86_64.{docker_compatible}:latest"


def wait_for_health(port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            response = httpx.get(f"http://127.0.0.1:{port}/health", timeout=2.0)
            response.raise_for_status()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"gateway health check failed: {last_error}")


def start_gateway(port: int, log_file: Path) -> subprocess.Popen[str]:
    server_cmd = [
        str(ROOT / ".venv" / "bin" / "python"),
        "-m",
        "src.gateway.server",
        "--config",
        "configs/gateway.yaml",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    log_handle = log_file.open("w")
    return subprocess.Popen(
        server_cmd,
        cwd=ROOT,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=None,
    )


def stop_gateway(proc: subprocess.Popen[str]) -> None:
    try:
        proc.send_signal(signal.SIGTERM)
    except Exception:
        pass
    try:
        proc.wait(timeout=10)
    except Exception:
        pass


def run_batch(
    experiment: str,
    model_name: str,
    instances: list[dict],
    port: int,
    max_steps: int,
    output_root: Path,
) -> dict:
    log_file = output_root / f"{experiment}_gateway.log"
    gateway = start_gateway(port=port, log_file=log_file)
    try:
        wait_for_health(port)
        runner = AgentRunner(
            {
                "experiment": experiment,
                "strategy": "verified_model_sweep",
                "agent": {"type": "mini-swe-agent", "max_steps": max_steps},
                "gateway": {
                    "base_url": f"http://127.0.0.1:{port}/v1",
                    "api_key": "issue-run",
                    "default_model": model_name,
                },
                "output_dir": str(output_root / experiment),
            }
        )

        results = []
        for inst in instances:
            issue = inst.get("problem_statement", "")
            instance = {
                "instance_id": inst["instance_id"],
                "image_name": build_image_name(inst["instance_id"]),
                "problem_statement": issue,
            }
            result = runner.run(instance)
            results.append(result.to_dict())

        summary = {
            "experiment": experiment,
            "model": model_name,
            "instances_requested": len(instances),
            "instances_completed": len(results),
            "resolved_instances": sum(1 for r in results if r.get("success")),
            "resolve_rate": sum(1 for r in results if r.get("success")) / max(1, len(results)),
            "avg_total_tokens": sum(r.get("total_tokens", 0) for r in results) / max(1, len(results)),
            "results": results,
        }
        (output_root / experiment / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2)
        )
        return summary
    finally:
        stop_gateway(gateway)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run verified instances across one or more models with no overlap")
    parser.add_argument("--per-model", type=int, default=50)
    parser.add_argument("--max-steps", type=int, default=60)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--output-dir", default="experiments/verified_model_sweep_150")
    parser.add_argument(
        "--batch",
        choices=["all", "dpsk", "glm", "minimax"],
        default="all",
        help="Run all model batches or a single named batch.",
    )
    args = parser.parse_args()

    all_models = [
        ("verified_dpsk_50", "deepseek-v3.2", 18090),
        ("verified_glm_50", "glm-4.7", 18091),
        ("verified_minimax_50", "MiniMax-M2.7", 18092),
    ]
    batch_map = {
        "dpsk": [all_models[0]],
        "glm": [all_models[1]],
        "minimax": [all_models[2]],
        "all": all_models,
    }
    models = batch_map[args.batch]

    dataset = load_swebench_dataset("princeton-nlp/SWE-bench_Verified")
    total_needed = args.per_model * len(all_models)
    selected = dataset[args.start_index : args.start_index + total_needed]
    if len(selected) < total_needed:
        raise SystemExit(f"Need {total_needed} verified instances, only found {len(selected)} from start index {args.start_index}")

    output_root = ROOT / args.output_dir
    output_root.mkdir(parents=True, exist_ok=True)

    final_summary = {
        "meta": {
            "dataset": "SWE-bench_Verified",
            "per_model": args.per_model,
            "max_steps": args.max_steps,
            "start_index": args.start_index,
            "batch": args.batch,
        },
        "batches": [],
    }

    index_map = {name: idx for idx, (name, _, _) in enumerate(all_models)}
    for experiment, model_name, port in models:
        i = index_map[experiment]
        lo = i * args.per_model
        hi = (i + 1) * args.per_model
        batch_instances = selected[lo:hi]
        summary = run_batch(
            experiment=experiment,
            model_name=model_name,
            instances=batch_instances,
            port=port,
            max_steps=args.max_steps,
            output_root=output_root,
        )
        final_summary["batches"].append(summary)
        (output_root / "master_summary.json").write_text(
            json.dumps(final_summary, ensure_ascii=False, indent=2)
        )

    print(json.dumps(final_summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
