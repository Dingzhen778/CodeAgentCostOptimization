from __future__ import annotations

import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger

from src.compression.context_compressor import (
    FunctionLevelTrimmer,
    TokenBudgetTrimmer,
    TopKFileSelector,
)
from src.compression.llmlingua_adapter import LLMLinguaConfig, LLMLinguaRanker


STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "when", "where",
    "while", "have", "has", "had", "been", "will", "would", "should", "could",
    "issue", "error", "errors", "problem", "statement", "fails", "failure",
    "after", "before", "about", "there", "their", "them", "than", "then",
    "fix", "bug", "code", "file", "files", "function", "class", "method",
}


@dataclass
class TaskContextConfig:
    method: str = "none"
    top_k_files: int = 4
    token_budget: int = 2500
    max_candidate_files: int = 24
    snippet_lines: int = 220
    enable_function_trim: bool = False
    include_skill_scaffold: bool = False
    include_pruning_hints: bool = False
    include_skill_memory: bool = False
    skill_file: str = "skills.md"
    llmlingua_model_name: str = "deepseek-ai/deepseek-coder-1.3b-base"
    llmlingua_device_map: str = "cpu"


class TaskContextBuilder:
    def __init__(self, config: Optional[TaskContextConfig] = None):
        self.config = config or TaskContextConfig()
        self._selector = TopKFileSelector(top_k=self.config.top_k_files)
        self._trimmer = FunctionLevelTrimmer()
        self._budget = TokenBudgetTrimmer(token_budget=self.config.token_budget)
        self._llmlingua = None
        if self.config.method in {"llmlingua_original", "hybrid_llmlingua"}:
            self._llmlingua = LLMLinguaRanker.shared(
                LLMLinguaConfig(
                    model_name=self.config.llmlingua_model_name,
                    device_map=self.config.llmlingua_device_map,
                    top_k=self.config.top_k_files,
                )
            )

    @classmethod
    def from_runner_config(cls, config: dict) -> "TaskContextBuilder":
        method_cfg = config.get("method", {})
        compression_cfg = config.get("compression", {})
        pruning_cfg = config.get("pruning", {})
        method_name = method_cfg.get("name", compression_cfg.get("strategy", "none"))

        if method_name == "hybrid":
            enable_function_trim = True
            include_skill_scaffold = True
            include_pruning_hints = True
        else:
            enable_function_trim = method_cfg.get("enable_function_trim", method_name in {"rag_function", "llmlingua_proxy", "llmlingua_original", "hybrid_llmlingua"})
            include_skill_scaffold = method_cfg.get("include_skill_scaffold", method_name in {"skill_abstraction", "hybrid"})
            include_pruning_hints = method_cfg.get("include_pruning_hints", method_name in {"pruning_budget", "hybrid"} or pruning_cfg.get("enable_dedup", False))
        include_skill_memory = method_cfg.get("include_skill_memory", method_name in {"skill_memory_md"})

        return cls(
            TaskContextConfig(
                method=method_name,
                top_k_files=int(method_cfg.get("top_k_files", compression_cfg.get("top_k_files", 4))),
                token_budget=int(method_cfg.get("token_budget", compression_cfg.get("token_budget", 2500))),
                max_candidate_files=int(method_cfg.get("max_candidate_files", 24)),
                snippet_lines=int(method_cfg.get("snippet_lines", 220)),
                enable_function_trim=enable_function_trim,
                include_skill_scaffold=include_skill_scaffold,
                include_pruning_hints=include_pruning_hints,
                include_skill_memory=include_skill_memory,
                skill_file=method_cfg.get("skill_file", "skills.md"),
                llmlingua_model_name=method_cfg.get("llmlingua_model_name", "deepseek-ai/deepseek-coder-1.3b-base"),
                llmlingua_device_map=method_cfg.get("llmlingua_device_map", "cpu"),
            )
        )

    def build_task(self, *, instance: dict, image_name: str, base_task: str) -> str:
        method = self.config.method
        if method in {"none", "vanilla"}:
            return base_task

        repo_context = ""
        if method in {"rag_topk", "rag_function", "llmlingua_proxy", "llmlingua_original", "skill_abstraction", "skill_memory_md", "hybrid", "hybrid_llmlingua"}:
            repo_context = self._build_repo_context(
                image_name=image_name,
                query=base_task,
                method=method,
            )

        sections: list[str] = [base_task.strip()]

        if self.config.include_skill_scaffold:
            sections.append(
                "\nStructured workflow:\n"
                "1. Reproduce or understand the issue briefly.\n"
                "2. Narrow to 1-3 candidate files.\n"
                "3. Locate the exact function or block to edit.\n"
                "4. Make the smallest patch that fixes the issue.\n"
                "5. Verify with a focused check.\n"
                "6. Submit the final patch only after verification.\n"
            )

        if self.config.include_pruning_hints:
            sections.append(
                "\nEfficiency hints:\n"
                "- Prefer `rg` before large file reads.\n"
                "- Avoid re-reading the same file unless you have new evidence.\n"
                "- Once you have a likely target file, stop broad search and focus.\n"
                "- Prefer focused snippets over whole-file dumps.\n"
            )

        if self.config.include_skill_memory:
            skill_memory = self._load_skill_memory()
            if skill_memory:
                sections.append(
                    "\nTransferable skill memory (reusable heuristics, not ground truth):\n"
                    f"{skill_memory}"
                )

        if repo_context:
            sections.append(repo_context)

        sections.append(
            "\nThe additional context above is only a starting point. You must still verify the code in the repository and submit the final patch using the normal mini-swe-agent submission flow."
        )
        return "\n\n".join(sections)

    def _build_repo_context(self, *, image_name: str, query: str, method: str) -> str:
        candidates = self._collect_candidate_files(image_name=image_name, query=query)
        if not candidates:
            return ""

        selected = self._selector.select(query, candidates)
        if method in {"llmlingua_original", "hybrid_llmlingua"} and self._llmlingua:
            selected = self._llmlingua.rank_files(query=query, files=selected)
        if self.config.enable_function_trim:
            selected = {
                path: self._trimmer.trim(content, query) or content
                for path, content in selected.items()
            }

        if method in {"llmlingua_proxy", "hybrid", "hybrid_llmlingua"}:
            selected = self._budget.trim(selected, query)

        if not selected:
            return ""

        blocks = ["Repository hints (auto-generated, may be incomplete):"]
        for path, content in selected.items():
            blocks.append(f"\n[Candidate File] {path}\n```text\n{content.strip()}\n```")
        return "\n".join(blocks)

    def _load_skill_memory(self) -> str:
        skill_path = Path(self.config.skill_file)
        if not skill_path.is_absolute():
            skill_path = Path(__file__).resolve().parents[2] / skill_path
        try:
            content = skill_path.read_text()
        except OSError:
            return ""
        return content.strip()

    def _collect_candidate_files(self, *, image_name: str, query: str) -> dict[str, str]:
        terms = _extract_query_terms(query)
        if not terms:
            return {}

        pattern = "|".join(re.escape(term) for term in terms[:8])
        find_cmd = (
            "cd /testbed && "
            f"rg -l -i -m 1 {shlex.quote(pattern)} . "
            "--glob '!*.json' --glob '!*.md' --glob '!*.txt' "
            f"| head -n {self.config.max_candidate_files}"
        )
        result = _docker_capture(image_name=image_name, command=find_cmd, timeout=90)
        if not result:
            return {}

        files: dict[str, str] = {}
        for rel_path in [line.strip() for line in result.splitlines() if line.strip()]:
            snippet = _docker_capture(
                image_name=image_name,
                command=f"cd /testbed && sed -n '1,{self.config.snippet_lines}p' {shlex.quote(rel_path)}",
                timeout=60,
            )
            if snippet:
                files[rel_path] = snippet
        return files


def _extract_query_terms(text: str) -> list[str]:
    raw_terms = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text.lower())
    scored: list[str] = []
    seen: set[str] = set()
    for token in raw_terms:
        if token in STOPWORDS:
            continue
        if token in seen:
            continue
        seen.add(token)
        scored.append(token)
    return scored[:12]


def _docker_capture(*, image_name: str, command: str, timeout: int) -> str:
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "bash", image_name, "-lc", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        logger.debug(f"Task context docker capture failed for {image_name}: {exc}")
        return ""

    if result.returncode != 0:
        return ""
    return result.stdout.strip()
