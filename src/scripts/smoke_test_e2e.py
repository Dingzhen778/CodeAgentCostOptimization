#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".venv" / "bin" / "python"


def wait_for_health(port: int, timeout: float = 20.0) -> dict:
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            response = httpx.get(f"http://127.0.0.1:{port}/health", timeout=2.0)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"gateway health check failed: {last_error}")


def run_direct_chat(port: int) -> dict:
    payload = {
        "model": "deepseek-v3.2",
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
        "temperature": 0,
        "max_tokens": 16,
    }
    response = httpx.post(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        json=payload,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def run_minisweagent(port: int, traj_path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["MSWEA_CONFIGURED"] = "true"
    env["OPENAI_API_KEY"] = "smoke-test"
    cmd = [
        str(PYTHON),
        "-m",
        "minisweagent.run.mini",
        "-m",
        "openai/deepseek-v3.2",
        "-t",
        "Run the command printf OK and then finish by issuing echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT exactly.",
        "-y",
        "--exit-immediately",
        "-o",
        str(traj_path),
        "-c",
        "mini.yaml",
        "-c",
        f"model.model_kwargs.api_base=http://127.0.0.1:{port}/v1",
        "-c",
        "model.cost_tracking=ignore_errors",
    ]
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def load_traj_summary(traj_path: Path) -> dict:
    data = json.loads(traj_path.read_text())
    return {
        "exit_status": data.get("info", {}).get("exit_status"),
        "api_calls": data.get("info", {}).get("model_stats", {}).get("api_calls"),
        "submission": data.get("info", {}).get("submission"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="End-to-end smoke test: gateway + New API + mini-swe-agent")
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument("--traj-path", default="/tmp/mswea_smoke.traj.json")
    args = parser.parse_args()

    traj_path = Path(args.traj_path)
    if traj_path.exists():
        traj_path.unlink()

    server_cmd = [
        str(PYTHON),
        "-m",
        "src.gateway.server",
        "--config",
        "configs/gateway.yaml",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port),
    ]

    server = subprocess.Popen(
        server_cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=os.setsid,
    )

    try:
        health = wait_for_health(args.port)
        direct = run_direct_chat(args.port)
        agent = run_minisweagent(args.port, traj_path)
        if agent.returncode != 0:
            raise RuntimeError(f"mini-swe-agent exited with {agent.returncode}\n{agent.stdout}\n{agent.stderr}")
        if not traj_path.exists():
            raise RuntimeError("trajectory file was not created")
        summary = load_traj_summary(traj_path)
        print(json.dumps({
            "health": health,
            "direct_model": direct.get("model"),
            "direct_text": direct.get("choices", [{}])[0].get("message", {}).get("content"),
            "traj_path": str(traj_path),
            "agent_summary": summary,
        }, ensure_ascii=False, indent=2))
        return 0
    finally:
        try:
            os.killpg(os.getpgid(server.pid), signal.SIGTERM)
        except Exception:
            pass
        try:
            server.wait(timeout=10)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
