from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from loguru import logger


LLMLINGUA_PARENT = Path("/home/azureuser/jrh/Code_compression_method/hard-compression")


@dataclass
class LLMLinguaConfig:
    model_name: str = "deepseek-ai/deepseek-coder-1.3b-base"
    device_map: str = "cpu"
    top_k: int = 4
    condition_in_question: str = "after"


class LLMLinguaRanker:
    _shared = None
    _shared_key = None

    def __init__(self, config: Optional[LLMLinguaConfig] = None):
        self.config = config or LLMLinguaConfig()
        self._compressor = None

    @classmethod
    def shared(cls, config: Optional[LLMLinguaConfig] = None) -> "LLMLinguaRanker":
        config = config or LLMLinguaConfig()
        key = (config.model_name, config.device_map, config.top_k, config.condition_in_question)
        if cls._shared is None or cls._shared_key != key:
            cls._shared = cls(config)
            cls._shared_key = key
        return cls._shared

    def rank_files(self, *, query: str, files: dict[str, str]) -> dict[str, str]:
        if len(files) <= self.config.top_k:
            return files

        compressor = self._get_compressor()
        cross_files = [
            SimpleNamespace(path=path, file_path=path, code_content=content)
            for path, content in files.items()
            if content.strip()
        ]
        if not cross_files:
            return {}

        ranked = compressor.select_cross_files(
            cross_files,
            question=query,
            condition_in_question=self.config.condition_in_question,
            topk=self.config.top_k,
        )
        result: dict[str, str] = {}
        for item in ranked:
            path = getattr(item, "path", None) or getattr(item, "file_path", None)
            if path in files:
                result[path] = files[path]
        return result or files

    def _get_compressor(self):
        if self._compressor is not None:
            return self._compressor

        if str(LLMLINGUA_PARENT) not in sys.path:
            sys.path.insert(0, str(LLMLINGUA_PARENT))

        from llmlingua.llmlingua_change import PromptCompressor

        logger.info(
            f"Loading LLMLingua PromptCompressor: model={self.config.model_name} device={self.config.device_map}"
        )
        self._compressor = PromptCompressor(
            model_name=self.config.model_name,
            device_map=self.config.device_map,
            use_llmlingua2=False,
        )
        return self._compressor
