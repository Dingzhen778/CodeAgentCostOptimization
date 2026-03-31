#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.analysis.token_phase_analyzer import summarize_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze token usage by agent work phase")
    parser.add_argument("experiment_dirs", nargs="+", help="Experiment directories to analyze")
    parser.add_argument("--output", help="Optional JSON file path")
    args = parser.parse_args()

    summaries = [summarize_experiment(Path(exp_dir)) for exp_dir in args.experiment_dirs]
    payload = {"experiments": summaries}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
