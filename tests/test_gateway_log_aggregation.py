from scripts.aggregate_gateway_logs import aggregate


def test_aggregate_gateway_records_by_instance():
    records = [
        {
            "instance_id": "inst-1",
            "experiment": "exp",
            "strategy": "vanilla",
            "tool": "default",
            "input_tokens": 10,
            "output_tokens": 2,
            "total_tokens": 12,
            "latency": 1.0,
        },
        {
            "instance_id": "inst-1",
            "experiment": "exp",
            "strategy": "vanilla",
            "tool": "edit",
            "input_tokens": 20,
            "output_tokens": 5,
            "total_tokens": 25,
            "latency": 2.0,
        },
        {
            "instance_id": "inst-2",
            "experiment": "exp",
            "strategy": "hybrid",
            "tool": "default",
            "input_tokens": 8,
            "output_tokens": 1,
            "total_tokens": 9,
            "latency": 0.5,
        },
    ]

    summary = aggregate(records)

    assert len(summary) == 2
    assert summary[0]["instance_id"] == "inst-1"
    assert summary[0]["total_tokens"] == 37
    assert summary[0]["tool_breakdown"]["edit"]["tokens"] == 25
