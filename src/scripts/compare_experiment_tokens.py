#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_results(exp_dir: Path) -> dict[str, dict]:
    out = {}
    for result_file in exp_dir.glob("*/result.json"):
        data = json.loads(result_file.read_text())
        out[data["instance_id"]] = data
    return out


def main():
    parser = argparse.ArgumentParser(description="Compare token usage across two experiment directories.")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    baseline = load_results(Path(args.baseline))
    candidate = load_results(Path(args.candidate))
    rows = []
    for instance_id in sorted(set(baseline) & set(candidate)):
        b = baseline[instance_id]
        c = candidate[instance_id]
        b_tokens = b.get("total_tokens", 0) or 0
        c_tokens = c.get("total_tokens", 0) or 0
        rows.append(
            {
                "instance_id": instance_id,
                "baseline_success": b.get("success", False),
                "candidate_success": c.get("success", False),
                "baseline_total_tokens": b_tokens,
                "candidate_total_tokens": c_tokens,
                "token_delta": c_tokens - b_tokens,
                "token_reduction_ratio": ((b_tokens - c_tokens) / b_tokens) if b_tokens else None,
            }
        )

    summary = {
        "baseline_dir": args.baseline,
        "candidate_dir": args.candidate,
        "instances_compared": len(rows),
        "baseline_avg_tokens": (sum(r["baseline_total_tokens"] for r in rows) / len(rows)) if rows else 0,
        "candidate_avg_tokens": (sum(r["candidate_total_tokens"] for r in rows) / len(rows)) if rows else 0,
        "avg_token_reduction_ratio": (
            sum(r["token_reduction_ratio"] for r in rows if r["token_reduction_ratio"] is not None) /
            max(1, sum(1 for r in rows if r["token_reduction_ratio"] is not None))
        ) if rows else 0,
        "rows": rows,
    }
    Path(args.output).write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
