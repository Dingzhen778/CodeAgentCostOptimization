import json
from pathlib import Path

from src.agent.runner import AgentRunner


def test_load_gateway_summary_filters_current_run(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    log_dir = project_root / "logs" / "gateway"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "gateway_token_log.jsonl"

    original = log_file.read_text() if log_file.exists() else None
    try:
        records = [
            {
                "ts": 100.0,
                "instance_id": "inst-1",
                "experiment": "exp-a",
                "strategy": "vanilla",
                "tool": "default",
                "input_tokens": 10,
                "output_tokens": 2,
                "total_tokens": 12,
                "latency": 1.0,
            },
            {
                "ts": 201.0,
                "instance_id": "inst-1",
                "experiment": "exp-a",
                "strategy": "vanilla",
                "tool": "edit",
                "input_tokens": 20,
                "output_tokens": 5,
                "total_tokens": 25,
                "latency": 2.0,
            },
            {
                "ts": 202.0,
                "instance_id": "inst-1",
                "experiment": "exp-a",
                "strategy": "vanilla",
                "tool": "default",
                "input_tokens": 8,
                "output_tokens": 1,
                "total_tokens": 9,
                "latency": 0.5,
            },
            {
                "ts": 203.0,
                "instance_id": "inst-1",
                "experiment": "exp-b",
                "strategy": "vanilla",
                "tool": "default",
                "input_tokens": 99,
                "output_tokens": 1,
                "total_tokens": 100,
                "latency": 9.0,
            },
        ]
        log_file.write_text("".join(json.dumps(r) + "\n" for r in records))

        runner = AgentRunner(
            {
                "experiment": "exp-a",
                "strategy": "vanilla",
                "output_dir": str(tmp_path / "out"),
            }
        )

        summary = runner._load_gateway_summary(instance_id="inst-1", started_at=200.0)

        assert summary["total_calls"] == 2
        assert summary["input_tokens"] == 28
        assert summary["output_tokens"] == 6
        assert summary["total_tokens"] == 34
        assert summary["tool_breakdown"]["edit"]["tokens"] == 25
        assert summary["tool_breakdown"]["default"]["calls"] == 1
    finally:
        if original is None:
            log_file.unlink(missing_ok=True)
        else:
            log_file.write_text(original)
