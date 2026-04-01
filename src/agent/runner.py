"""
Agent Runner

将 SWE-bench instance 交给 mini-swe-agent（或 Claude Code）运行，
同时注入 LLM Gateway 和 Token Logger。

使用方式：
    runner = AgentRunner.from_config("configs/experiments/baseline_vanilla.yaml")
    result = runner.run(instance)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from loguru import logger

from src.agent.task_context import TaskContextBuilder
from src.gateway.token_logger import TokenLogger
from src.agent.trajectory import Trajectory
from src.config_utils import resolve_env_placeholders


class InstanceResult:
    """单个 SWE-bench instance 的运行结果"""

    def __init__(
        self,
        instance_id: str,
        success: bool,
        patch: str,
        token_summary: dict,
        runtime: float,
        log_dir: Path,
    ):
        self.instance_id = instance_id
        self.success = success
        self.patch = patch
        self.token_summary = token_summary
        self.runtime = runtime
        self.log_dir = log_dir

    def to_dict(self) -> dict:
        return {
            "instance_id": self.instance_id,
            "success": self.success,
            "runtime": round(self.runtime, 2),
            **self.token_summary,
        }

    def save(self):
        out = self.log_dir / "result.json"
        with out.open("w") as f:
            json.dump(self.to_dict(), f, indent=2)

        if self.patch:
            patch_file = self.log_dir / "patch.diff"
            patch_file.write_text(self.patch)

        logger.info(f"[{self.instance_id}] success={self.success} "
                    f"tokens={self.token_summary.get('total_tokens', '?')} "
                    f"runtime={self.runtime:.1f}s")


class AgentRunner:
    """
    封装 mini-swe-agent 运行逻辑，注入自定义 LLM Gateway。

    config 示例（configs/experiments/baseline_vanilla.yaml）：
        experiment: baseline_vanilla
        strategy: vanilla
        agent:
          type: mini-swe-agent        # 或 claude-code
          max_steps: 30
        gateway:
          base_url: http://localhost:8080/v1
          api_key: ${OPENAI_API_KEY}
          default_model: deepseek-chat
        output_dir: experiments/baseline_vanilla
    """

    def __init__(self, config: dict):
        self.config = config
        self.experiment = config.get("experiment", "default")
        self.strategy = config.get("strategy", "vanilla")
        self.output_dir = Path(config.get("output_dir", "experiments/default"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.task_context_builder = TaskContextBuilder.from_runner_config(config)

        # Gateway 配置
        self.gateway_config = config.get("gateway", {})

    @classmethod
    def from_config(cls, config_path: str | Path) -> "AgentRunner":
        load_dotenv()
        with open(config_path) as f:
            config = resolve_env_placeholders(yaml.safe_load(f))
        return cls(config)

    # ------------------------------------------------------------------
    # 核心接口
    # ------------------------------------------------------------------

    def run(self, instance: dict) -> InstanceResult:
        """运行单个 SWE-bench instance"""
        instance_id = instance["instance_id"]
        log_dir = self.output_dir / instance_id
        log_dir.mkdir(parents=True, exist_ok=True)

        token_logger = TokenLogger(
            log_dir=log_dir,
            instance_id=instance_id,
            experiment=self.experiment,
            strategy=self.strategy,
        )
        trajectory = Trajectory(instance_id=instance_id, log_dir=log_dir)

        wall_t0 = time.time()
        t0 = time.monotonic()
        try:
            patch, success = self._run_agent(instance, token_logger, trajectory, log_dir)
        except Exception as e:
            logger.error(f"[{instance_id}] Agent failed: {e}")
            patch, success = "", False

        runtime = time.monotonic() - t0
        summary = token_logger.save_summary(success=success)
        token_summary = token_logger.summary()
        if not token_summary:
            token_summary = self._load_gateway_summary(instance_id=instance_id, started_at=wall_t0)
        token_summary["success"] = success

        result = InstanceResult(
            instance_id=instance_id,
            success=success,
            patch=patch,
            token_summary=token_summary,
            runtime=runtime,
            log_dir=log_dir,
        )
        result.save()
        return result

    def _run_agent(
        self,
        instance: dict,
        token_logger: TokenLogger,
        trajectory: Trajectory,
        log_dir: Path,
    ) -> tuple[str, bool]:
        """
        调用 mini-swe-agent。
        通过设置环境变量 OPENAI_BASE_URL 指向本地 Gateway，实现 token 追踪。

        若你使用 Claude Code，可在此处调用 `claude` CLI 并解析输出。
        """
        agent_type = self.config.get("agent", {}).get("type", "mini-swe-agent")

        if agent_type == "mini-swe-agent":
            return self._run_mini_swe_agent(instance, log_dir)
        elif agent_type == "mock":
            return self._run_mock(instance, token_logger, trajectory)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    def _run_mini_swe_agent(self, instance: dict, log_dir: Path) -> tuple[str, bool]:
        """通过 subprocess 调用 mini-swe-agent 的 SWE-bench Docker 路径。"""
        env = os.environ.copy()
        env.setdefault("MSWEA_CONFIGURED", "true")
        env.setdefault("MSWEA_COST_TRACKING", "ignore_errors")
        gw = self.gateway_config
        if gw.get("api_key"):
            env["OPENAI_API_KEY"] = gw["api_key"]
        if gw.get("base_url"):
            api_base = gw["base_url"]
        else:
            api_base = ""

        traj_file = log_dir / "trajectory.json"
        swebench_config = (
            Path(__file__).resolve().parents[2]
            / "mini-swe-agent"
            / "src"
            / "minisweagent"
            / "config"
            / "benchmarks"
            / "swebench.yaml"
        )
        extra_headers = {
            "X-Instance-Id": instance["instance_id"],
            "X-Experiment-Name": self.experiment,
            "X-Strategy-Name": self.strategy,
        }
        image_name = self._get_swebench_image_name(instance)
        base_task = instance.get("problem_statement") or f"Investigate instance {instance['instance_id']}."
        task = self.task_context_builder.build_task(
            instance=instance,
            image_name=image_name,
            base_task=base_task,
        )
        model_name = gw.get("default_model", "deepseek-v3.2")
        if api_base:
            model_name = self._normalize_openai_model_name(model_name)
        cmd = [
            sys.executable,
            "-m",
            "minisweagent.run.mini",
            "-m",
            model_name,
            "-t",
            task,
            "-y",
            "--exit-immediately",
            "-o",
            str(traj_file),
            "-c",
            str(swebench_config),
            "-c",
            f"agent.step_limit={self.config.get('agent', {}).get('max_steps', 30)}",
            "-c",
            "environment.environment_class=docker",
            "-c",
            f"environment.image={image_name}",
        ]
        if api_base:
            cmd.extend(["-c", f"model.model_kwargs.api_base={api_base}"])
        cmd.extend(["-c", f"model.model_kwargs.extra_headers={json.dumps(extra_headers)}"])
        cmd.extend(["-c", "model.cost_tracking=ignore_errors"])

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=600)
        patch = self._extract_submission_patch(traj_file)
        success = result.returncode == 0 and bool(patch)
        return patch, success

    @staticmethod
    def _normalize_openai_model_name(model_name: str) -> str:
        known_prefixes = (
            "openai/",
            "anthropic/",
            "bedrock/",
            "vertex_ai/",
            "gemini/",
            "azure/",
            "huggingface/",
            "ollama/",
            "deepseek/",
            "openrouter/",
        )
        if model_name.startswith(known_prefixes):
            return model_name
        return f"openai/{model_name}"

    def _load_gateway_summary(self, instance_id: str, started_at: float) -> dict:
        """从全局 gateway 日志回填当前 instance 的 token 汇总。"""
        log_file = Path(__file__).resolve().parents[2] / "logs" / "gateway" / "gateway_token_log.jsonl"
        if not log_file.exists():
            return {}

        total_input = 0
        total_output = 0
        total_latency = 0.0
        total_calls = 0
        tool_breakdown: dict[str, dict[str, int]] = {}

        with log_file.open() as f:
            for line in f:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if record.get("ts", 0) < started_at:
                    continue
                if record.get("instance_id") != instance_id:
                    continue
                if record.get("experiment") != self.experiment:
                    continue
                if record.get("strategy") != self.strategy:
                    continue

                total_calls += 1
                total_input += record.get("input_tokens", 0)
                total_output += record.get("output_tokens", 0)
                total_latency += record.get("latency", 0.0)

                tool = record.get("tool", "default")
                if tool not in tool_breakdown:
                    tool_breakdown[tool] = {"calls": 0, "tokens": 0}
                tool_breakdown[tool]["calls"] += 1
                tool_breakdown[tool]["tokens"] += record.get("total_tokens", 0)

        if total_calls == 0:
            return {}

        total_tokens = total_input + total_output
        return {
            "instance_id": instance_id,
            "experiment": self.experiment,
            "strategy": self.strategy,
            "total_calls": total_calls,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_tokens,
            "avg_tokens_per_step": total_tokens / total_calls,
            "total_latency": total_latency,
            "tool_breakdown": tool_breakdown,
        }

    @staticmethod
    def _get_swebench_image_name(instance: dict) -> str:
        image_name = instance.get("image_name") or instance.get("docker_image")
        if image_name:
            return image_name

        iid = instance["instance_id"]
        docker_compatible = iid.replace("__", "_1776_")
        return f"docker.io/swebench/sweb.eval.x86_64.{docker_compatible}:latest".lower()

    @staticmethod
    def _extract_submission_patch(traj_file: Path) -> str:
        if not traj_file.exists():
            return ""
        try:
            data = json.loads(traj_file.read_text())
        except json.JSONDecodeError:
            return ""
        return data.get("info", {}).get("submission", "") or ""

    def _run_mock(self, instance: dict, token_logger: TokenLogger, trajectory: Trajectory) -> tuple[str, bool]:
        """
        Mock Agent（用于本地调试，不需要真实 SWE-bench 环境）
        模拟一个 5 步的 agent 流程，写入假 token 数据
        """
        import random
        steps = [
            ("search", "bug report keywords", 800, 150),
            ("read_file", "src/main.py", 2000, 100),
            ("read_file", "src/utils.py", 1500, 80),
            ("bash", "run tests", 300, 200),
            ("edit", "src/main.py", 1800, 400),
        ]
        for i, (action, target, inp, out) in enumerate(steps, 1):
            token_logger.log(
                step=i, tool=action, model="mock-model",
                input_tokens=inp + random.randint(-100, 100),
                output_tokens=out + random.randint(-20, 20),
                latency=random.uniform(0.5, 2.0),
            )
            trajectory.add(step=i, action=action, target=target,
                           input_tokens=inp, output_tokens=out)

        mock_patch = f"--- a/src/main.py\n+++ b/src/main.py\n@@ -10,1 +10,1 @@\n-bug\n+fix\n"
        success = random.random() > 0.3
        return mock_patch, success
