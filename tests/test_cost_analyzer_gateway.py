import json

from src.analysis.cost_analyzer import CostAnalyzer


def test_load_all_prefers_gateway_summary(tmp_path):
    experiments_dir = tmp_path / "experiments"
    exp_dir = experiments_dir / "baseline_vanilla"
    instance_dir = exp_dir / "inst-1"
    instance_dir.mkdir(parents=True)

    (instance_dir / "summary.json").write_text(json.dumps({
        "instance_id": "inst-1",
        "success": True,
        "runtime": 5.0,
        "total_tokens": 999,
        "input_tokens": 900,
        "output_tokens": 99,
        "total_steps": 2,
        "total_calls": 2,
    }))
    (exp_dir / "gateway_instance_summary.json").write_text(json.dumps([
        {
            "instance_id": "inst-1",
            "experiment": "baseline_vanilla",
            "strategy": "vanilla",
            "total_calls": 3,
            "input_tokens": 1200,
            "output_tokens": 200,
            "total_tokens": 1400,
            "total_latency": 4.0,
            "tool_breakdown": {"default": {"calls": 3, "tokens": 1400}},
        }
    ]))

    analyzer = CostAnalyzer(experiments_dir)
    df = analyzer.load_all()

    assert df.iloc[0]["total_tokens"] == 1400
    assert df.iloc[0]["token_source"] == "gateway"


def test_cost_breakdown_prefers_gateway_summary(tmp_path):
    experiments_dir = tmp_path / "experiments"
    exp_dir = experiments_dir / "exp3_hybrid"
    exp_dir.mkdir(parents=True)
    (exp_dir / "gateway_instance_summary.json").write_text(json.dumps([
        {
            "instance_id": "inst-1",
            "experiment": "exp3_hybrid",
            "strategy": "hybrid",
            "tool_breakdown": {
                "search": {"calls": 2, "tokens": 300},
                "edit": {"calls": 1, "tokens": 700},
            },
        }
    ]))

    analyzer = CostAnalyzer(experiments_dir)
    breakdown = analyzer.cost_breakdown("exp3_hybrid")

    assert list(breakdown["tool"]) == ["edit", "search"]
    assert int(breakdown.iloc[0]["total_tokens"]) == 700


def test_cost_breakdown_uses_global_gateway_log_as_fallback(tmp_path):
    experiments_dir = tmp_path / "experiments"
    exp_dir = experiments_dir / "exp4_routing"
    instance_dir = exp_dir / "inst-2"
    instance_dir.mkdir(parents=True)
    (instance_dir / "summary.json").write_text(json.dumps({
        "instance_id": "inst-2",
        "success": False,
        "runtime": 3.0,
    }))

    gateway_log_dir = tmp_path / "logs" / "gateway"
    gateway_log_dir.mkdir(parents=True)
    (gateway_log_dir / "gateway_token_log.jsonl").write_text(
        json.dumps({
            "instance_id": "inst-2",
            "experiment": "exp4_routing",
            "strategy": "routing",
            "tool": "read_file",
            "total_tokens": 123,
        }) + "\n"
    )

    analyzer = CostAnalyzer(experiments_dir)
    breakdown = analyzer.cost_breakdown("exp4_routing")

    assert len(breakdown) == 1
    assert breakdown.iloc[0]["tool"] == "read_file"
    assert int(breakdown.iloc[0]["total_tokens"]) == 123
