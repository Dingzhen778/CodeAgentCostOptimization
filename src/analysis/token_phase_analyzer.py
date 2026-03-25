from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


SEARCH_PATTERNS = (
    r"\brg\b",
    r"\bgrep\b",
    r"\bfind\b",
    r"\bls\b",
    r"\bgit grep\b",
    r"\bglob\b",
)

READ_PATTERNS = (
    r"\bcat\b",
    r"\bsed\s+-n\b",
    r"\bhead\b",
    r"\btail\b",
    r"\bnl\b",
    r"\bawk\b",
)

EDIT_PATTERNS = (
    r"apply_patch",
    r"\bsed\s+-i\b",
    r"\bperl\s+-0pi\b",
    r"\bpython\b.*write_text",
    r"\bpython\b.*open\(.*[\"']w",
    r"\becho\b.*>\s*[^>]",
    r"\btee\b",
)

VERIFY_PATTERNS = (
    r"\bpytest\b",
    r"\bpy\.test\b",
    r"\btox\b",
    r"\bunittest\b",
    r"\bmanage\.py test\b",
    r"\bpython\b.*-m pytest\b",
    r"\bpython\b.*- <<",
)

SUBMIT_PATTERNS = (
    r"COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT",
    r"\bpatch\.txt\b",
    r"\bgit diff\b",
)


def _matches_any(command: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, command) for pattern in patterns)


def classify_command(command: str, step_index: int) -> str:
    command = command.strip()
    if not command:
        return "other"
    if _matches_any(command, SUBMIT_PATTERNS):
        return "submit"
    if _matches_any(command, VERIFY_PATTERNS):
        return "verify"
    if _matches_any(command, EDIT_PATTERNS):
        return "edit"
    if _matches_any(command, READ_PATTERNS):
        return "read"
    if _matches_any(command, SEARCH_PATTERNS):
        return "search"
    if step_index <= 2:
        return "bootstrap"
    return "other"


def _phase_group(phase: str) -> str:
    if phase in {"bootstrap", "search", "read"}:
        return "understand"
    if phase == "edit":
        return "implement"
    if phase in {"verify", "submit"}:
        return "validate"
    return "other"


def extract_step_rows(trajectory_path: Path) -> list[dict]:
    data = json.loads(trajectory_path.read_text())
    rows: list[dict] = []
    step_index = 0
    for message in data.get("messages", []):
        if message.get("role") != "assistant":
            continue
        response = message.get("extra", {}).get("response", {})
        usage = response.get("usage") or {}
        if not usage:
            continue
        step_index += 1
        actions = message.get("extra", {}).get("actions") or []
        command = actions[0]["command"] if actions else ""
        phase = classify_command(command, step_index)
        rows.append(
            {
                "step_index": step_index,
                "phase": phase,
                "phase_group": _phase_group(phase),
                "command": command,
                "input_tokens": usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0,
                "output_tokens": usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0,
                "total_tokens": usage.get("total_tokens", 0)
                or ((usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0) + (usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)),
            }
        )
    return rows


def summarize_instance(instance_dir: Path) -> dict:
    traj_path = instance_dir / "trajectory.json"
    if not traj_path.exists():
        return {}

    rows = extract_step_rows(traj_path)
    result_path = instance_dir / "result.json"
    result = json.loads(result_path.read_text()) if result_path.exists() else {}

    by_phase: dict[str, dict[str, float]] = defaultdict(lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
    by_group: dict[str, dict[str, float]] = defaultdict(lambda: {"calls": 0, "total_tokens": 0})
    for row in rows:
        phase_stats = by_phase[row["phase"]]
        phase_stats["calls"] += 1
        phase_stats["input_tokens"] += row["input_tokens"]
        phase_stats["output_tokens"] += row["output_tokens"]
        phase_stats["total_tokens"] += row["total_tokens"]
        group_stats = by_group[row["phase_group"]]
        group_stats["calls"] += 1
        group_stats["total_tokens"] += row["total_tokens"]

    total_tokens = sum(row["total_tokens"] for row in rows)
    phase_percentages = {
        phase: round(stats["total_tokens"] / total_tokens, 4) if total_tokens else 0.0
        for phase, stats in by_phase.items()
    }
    return {
        "instance_id": instance_dir.name,
        "success": bool(result.get("success")),
        "runtime": result.get("runtime"),
        "api_calls": len(rows),
        "trajectory_total_tokens": total_tokens,
        "result_total_tokens": result.get("total_tokens"),
        "phase_breakdown": dict(by_phase),
        "phase_percentages": phase_percentages,
        "phase_group_breakdown": dict(by_group),
        "phase_sequence": [row["phase"] for row in rows],
        "top_phases": Counter(row["phase"] for row in rows).most_common(),
    }


def summarize_experiment(experiment_dir: Path) -> dict:
    instances = []
    for instance_dir in sorted(experiment_dir.iterdir()):
        if not instance_dir.is_dir():
            continue
        summary = summarize_instance(instance_dir)
        if summary:
            instances.append(summary)

    phase_totals: dict[str, dict[str, float]] = defaultdict(lambda: {"calls": 0, "total_tokens": 0})
    group_totals: dict[str, dict[str, float]] = defaultdict(lambda: {"calls": 0, "total_tokens": 0})
    for inst in instances:
        for phase, stats in inst["phase_breakdown"].items():
            phase_totals[phase]["calls"] += stats["calls"]
            phase_totals[phase]["total_tokens"] += stats["total_tokens"]
        for group, stats in inst["phase_group_breakdown"].items():
            group_totals[group]["calls"] += stats["calls"]
            group_totals[group]["total_tokens"] += stats["total_tokens"]

    total_tokens = sum(inst["trajectory_total_tokens"] for inst in instances)
    success_instances = [inst for inst in instances if inst["success"]]
    failed_instances = [inst for inst in instances if not inst["success"]]

    def _avg_phase_share(items: list[dict]) -> dict[str, float]:
        if not items:
            return {}
        phase_names = sorted({phase for inst in items for phase in inst["phase_breakdown"].keys()})
        out = {}
        for phase in phase_names:
            out[phase] = round(
                sum(inst["phase_breakdown"].get(phase, {}).get("total_tokens", 0) for inst in items)
                / max(1, sum(inst["trajectory_total_tokens"] for inst in items)),
                4,
            )
        return out

    return {
        "experiment": experiment_dir.name,
        "instances": len(instances),
        "resolved": sum(1 for inst in instances if inst["success"]),
        "resolve_rate": round(sum(1 for inst in instances if inst["success"]) / len(instances), 4) if instances else 0.0,
        "trajectory_total_tokens": total_tokens,
        "phase_totals": dict(phase_totals),
        "phase_percentages": {
            phase: round(stats["total_tokens"] / total_tokens, 4) if total_tokens else 0.0
            for phase, stats in phase_totals.items()
        },
        "phase_group_totals": dict(group_totals),
        "phase_group_percentages": {
            group: round(stats["total_tokens"] / total_tokens, 4) if total_tokens else 0.0
            for group, stats in group_totals.items()
        },
        "success_phase_percentages": _avg_phase_share(success_instances),
        "failure_phase_percentages": _avg_phase_share(failed_instances),
        "instance_summaries": instances,
    }
