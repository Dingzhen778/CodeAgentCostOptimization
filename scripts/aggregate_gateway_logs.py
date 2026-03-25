#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_records(log_file: Path) -> list[dict]:
    records = []
    with log_file.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def aggregate(records: list[dict], experiment: str | None = None) -> list[dict]:
    grouped: dict[tuple[str, str, str], dict] = {}
    tool_breakdowns: dict[tuple[str, str, str], dict[str, dict[str, float]]] = defaultdict(dict)

    for record in records:
        instance_id = record.get("instance_id", "")
        if not instance_id:
            continue
        if experiment and record.get("experiment") != experiment:
            continue
        key = (
            instance_id,
            record.get("experiment", ""),
            record.get("strategy", ""),
        )
        if key not in grouped:
            grouped[key] = {
                "instance_id": instance_id,
                "experiment": key[1],
                "strategy": key[2],
                "total_calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "total_latency": 0.0,
            }
        agg = grouped[key]
        agg["total_calls"] += 1
        agg["input_tokens"] += record.get("input_tokens", 0)
        agg["output_tokens"] += record.get("output_tokens", 0)
        agg["total_tokens"] += record.get("total_tokens", 0)
        agg["total_latency"] += record.get("latency", 0.0)

        tool = record.get("tool", "default")
        tb = tool_breakdowns[key].setdefault(tool, {"calls": 0, "tokens": 0})
        tb["calls"] += 1
        tb["tokens"] += record.get("total_tokens", 0)

    output = []
    for key, agg in grouped.items():
        agg["tool_breakdown"] = tool_breakdowns[key]
        output.append(agg)
    return sorted(output, key=lambda x: (x["experiment"], x["instance_id"]))


def main():
    parser = argparse.ArgumentParser(description="Aggregate gateway_token_log.jsonl by instance_id")
    parser.add_argument("--log-file", default="logs/gateway/gateway_token_log.jsonl")
    parser.add_argument("--output", default="logs/gateway/gateway_instance_summary.json")
    parser.add_argument("--experiment", default=None)
    args = parser.parse_args()

    records = load_records(Path(args.log_file))
    summary = aggregate(records, experiment=args.experiment)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote {len(summary)} instance summaries to {out}")


if __name__ == "__main__":
    sys.exit(main())
