import json

from src.analysis.token_phase_analyzer import classify_command, summarize_instance


def test_classify_command_by_work_type():
    assert classify_command("find /testbed -name '*.py'", 1) == "search"
    assert classify_command("sed -n '1,80p' foo.py", 3) == "read"
    assert classify_command("apply_patch <<'PATCH'", 4) == "edit"
    assert classify_command("pytest tests/test_x.py -q", 5) == "verify"
    assert classify_command("echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt", 6) == "submit"


def test_summarize_instance_groups_tokens_by_phase(tmp_path):
    instance_dir = tmp_path / "inst-1"
    instance_dir.mkdir()
    trajectory = {
        "info": {"model_stats": {"api_calls": 3}},
        "messages": [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "task"},
            {
                "role": "assistant",
                "content": "search",
                "extra": {
                    "actions": [{"command": "find /testbed -name '*.py'"}],
                    "response": {"usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12}},
                },
            },
            {"role": "tool", "content": "files"},
            {
                "role": "assistant",
                "content": "read",
                "extra": {
                    "actions": [{"command": "sed -n '1,80p' foo.py"}],
                    "response": {"usage": {"prompt_tokens": 20, "completion_tokens": 3, "total_tokens": 23}},
                },
            },
            {"role": "tool", "content": "code"},
            {
                "role": "assistant",
                "content": "verify",
                "extra": {
                    "actions": [{"command": "pytest tests/test_x.py -q"}],
                    "response": {"usage": {"prompt_tokens": 30, "completion_tokens": 4, "total_tokens": 34}},
                },
            },
        ],
    }
    (instance_dir / "trajectory.json").write_text(json.dumps(trajectory))
    (instance_dir / "result.json").write_text(json.dumps({"instance_id": "inst-1", "success": True, "runtime": 12.3, "total_tokens": 69}))

    summary = summarize_instance(instance_dir)

    assert summary["api_calls"] == 3
    assert summary["trajectory_total_tokens"] == 69
    assert summary["phase_breakdown"]["search"]["total_tokens"] == 12
    assert summary["phase_breakdown"]["read"]["total_tokens"] == 23
    assert summary["phase_breakdown"]["verify"]["total_tokens"] == 34
    assert summary["phase_group_breakdown"]["understand"]["total_tokens"] == 35
    assert summary["phase_group_breakdown"]["validate"]["total_tokens"] == 34
