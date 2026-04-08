#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_instance_ids(instance_file: Path | None) -> set[str] | None:
    if instance_file is None:
        return None
    data = json.loads(instance_file.read_text())
    if isinstance(data, list):
        ids = set()
        for item in data:
            if isinstance(item, str):
                ids.add(item)
            elif isinstance(item, dict) and "instance_id" in item:
                ids.add(item["instance_id"])
        return ids
    raise ValueError(f"Unsupported instance file format: {instance_file}")


def iter_instance_dirs(method_dir: Path):
    for path in sorted(method_dir.iterdir()):
        if path.is_dir():
            yield path


def build_predictions(
    method_dir: Path,
    model_name: str,
    instance_ids: set[str] | None,
    include_empty: bool,
) -> list[dict]:
    predictions = []
    for inst_dir in iter_instance_dirs(method_dir):
        instance_id = inst_dir.name
        if instance_ids is not None and instance_id not in instance_ids:
            continue
        patch_path = inst_dir / "patch.diff"
        patch = patch_path.read_text() if patch_path.exists() else ""
        if not include_empty and not patch.strip():
            continue
        predictions.append(
            {
                "instance_id": instance_id,
                "model_name_or_path": model_name,
                "model_patch": patch,
            }
        )
    return predictions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build SWE-bench harness predictions.json from experiment outputs."
    )
    parser.add_argument("--method-dir", required=True, help="Path to one method directory")
    parser.add_argument("--output", required=True, help="Output predictions JSON path")
    parser.add_argument(
        "--model-name",
        default="mini-swe-agent",
        help="Value for model_name_or_path in predictions.json",
    )
    parser.add_argument(
        "--instance-file",
        default=None,
        help="Optional JSON file containing target instance ids",
    )
    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Include empty patch entries as empty model_patch strings",
    )
    args = parser.parse_args()

    method_dir = Path(args.method_dir)
    output = Path(args.output)
    instance_ids = load_instance_ids(Path(args.instance_file)) if args.instance_file else None
    predictions = build_predictions(
        method_dir=method_dir,
        model_name=args.model_name,
        instance_ids=instance_ids,
        include_empty=args.include_empty,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(predictions, indent=2))
    print(f"Wrote {len(predictions)} predictions to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
