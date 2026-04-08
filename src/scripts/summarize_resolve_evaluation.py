#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_eval_report(report_path: Path) -> dict:
    data = json.loads(report_path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Unexpected report format: {report_path}")
    return data


def summarize(report_path: Path, total_instances: int) -> dict:
    report = load_eval_report(report_path)
    resolved = 0
    completed = 0
    for instance_id, payload in report.items():
        if not isinstance(payload, dict):
            continue
        completed += 1
        resolved += int(bool(payload.get("resolved")))
    return {
        "report_path": str(report_path),
        "completed_instances": completed,
        "resolved_instances": resolved,
        "resolved_rate_on_completed": (resolved / completed) if completed else 0.0,
        "resolved_rate_on_total": (resolved / total_instances) if total_instances else 0.0,
        "total_instances": total_instances,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize SWE-bench harness report.json")
    parser.add_argument("--report", required=True, help="Path to harness report.json")
    parser.add_argument(
        "--total-instances",
        type=int,
        required=True,
        help="Denominator for total resolved rate",
    )
    parser.add_argument("--output", default=None, help="Optional output JSON path")
    args = parser.parse_args()

    summary = summarize(Path(args.report), args.total_instances)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, indent=2))
        print(f"Wrote summary to {output}")
    else:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
