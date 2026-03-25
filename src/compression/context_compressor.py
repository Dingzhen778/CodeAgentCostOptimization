"""
Context Compression 模块

实现多种上下文压缩策略，减少传给 LLM 的 input token：

1. TopKFileSelector   — 基于 BM25 / embedding 相关性选 top-k 文件
2. FunctionLevelTrimmer — 只保留相关函数，过滤无关代码块
3. TokenBudgetTrimmer  — 超过 token 预算时截断，保留最相关内容
4. ContextCompressor   — 组合以上三种（Hybrid）
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import tiktoken


# -----------------------------------------------------------------------
# 配置
# -----------------------------------------------------------------------

@dataclass
class CompressionConfig:
    """压缩策略配置"""
    strategy: str = "hybrid"            # none | topk | function | budget | hybrid
    top_k_files: int = 5                # TopK 文件数
    token_budget: int = 8000            # 单次请求最大 input token
    embedding_model: str = "bge-small-en"  # 用于相关性计算的 embedding 模型
    tokenizer: str = "cl100k_base"      # tiktoken tokenizer
    keep_imports: bool = True           # 压缩时是否保留 import 语句
    keep_class_signatures: bool = True  # 是否保留类签名


# -----------------------------------------------------------------------
# Token 计数工具
# -----------------------------------------------------------------------

def count_tokens(text: str, tokenizer: str = "cl100k_base") -> int:
    enc = tiktoken.get_encoding(tokenizer)
    return len(enc.encode(text, disallowed_special=()))


# -----------------------------------------------------------------------
# 1. Top-K File Selector（基于 BM25 关键词匹配）
# -----------------------------------------------------------------------

class TopKFileSelector:
    """
    从仓库文件列表中选取与问题最相关的 top-k 文件。
    使用 BM25（不需要 GPU），可替换为 embedding 相似度。
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    def select(self, query: str, files: dict[str, str]) -> dict[str, str]:
        """
        Args:
            query: issue / bug 描述文本
            files: {file_path: file_content}
        Returns:
            top-k 相关文件的字典
        """
        if len(files) <= self.top_k:
            return files

        scores = self._bm25_score(query, files)
        top_paths = sorted(scores, key=scores.get, reverse=True)[: self.top_k]
        return {p: files[p] for p in top_paths}

    @staticmethod
    def _bm25_score(query: str, files: dict[str, str]) -> dict[str, float]:
        """简化版 BM25（不依赖外部库）"""
        query_terms = re.findall(r"\w+", query.lower())
        scores: dict[str, float] = {}
        for path, content in files.items():
            words = re.findall(r"\w+", content.lower())
            word_freq = {}
            for w in words:
                word_freq[w] = word_freq.get(w, 0) + 1
            score = sum(word_freq.get(t, 0) for t in query_terms)
            # 路径匹配加权
            path_lower = path.lower()
            path_score = sum(2 for t in query_terms if t in path_lower)
            scores[path] = score + path_score
        return scores


# -----------------------------------------------------------------------
# 2. Function-Level Trimmer
# -----------------------------------------------------------------------

class FunctionLevelTrimmer:
    """
    在文件内部，只保留与 query 相关的函数/类，过滤无关代码块。
    减少单个文件的 token 数。
    """

    def __init__(self, keep_imports: bool = True, keep_class_signatures: bool = True):
        self.keep_imports = keep_imports
        self.keep_class_signatures = keep_class_signatures

    def trim(self, content: str, query: str) -> str:
        """返回压缩后的文件内容"""
        lines = content.split("\n")
        blocks = self._split_into_blocks(lines)
        query_terms = self._expand_terms(query)

        kept: list[str] = []
        for block_type, block_lines in blocks:
            if block_type == "import" and self.keep_imports:
                kept.extend(block_lines)
            elif block_type == "class_sig" and self.keep_class_signatures:
                kept.extend(block_lines)
            elif block_type in ("function", "class", "top_level"):
                block_text = "\n".join(block_lines)
                if self._is_relevant_block(block_text, query_terms):
                    kept.extend(block_lines)
            # 无关代码块：丢弃

        return "\n".join(kept)

    @classmethod
    def _expand_terms(cls, text: str) -> set[str]:
        terms: set[str] = set()
        for token in re.findall(r"\w+", text.lower()):
            if not token:
                continue
            terms.add(token)
            for part in cls._split_identifier(token):
                if part:
                    terms.add(part)
        return terms

    @staticmethod
    def _split_identifier(token: str) -> list[str]:
        parts = re.split(r"[_\W]+", token)
        expanded: list[str] = []
        for part in parts:
            if not part:
                continue
            camel_parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|\d+", part)
            if camel_parts:
                expanded.extend(p.lower() for p in camel_parts if p)
            else:
                expanded.append(part.lower())
        return expanded

    @classmethod
    def _is_relevant_block(cls, block_text: str, query_terms: set[str]) -> bool:
        block_lower = block_text.lower()
        block_terms = cls._expand_terms(block_text)
        if query_terms & block_terms:
            return True

        # Fallback to substring / prefix matching for cases like:
        # "login authentication bug" -> "def login_user" / "authenticate(...)"
        for query_term in query_terms:
            if len(query_term) < 4:
                continue
            if query_term in block_lower:
                return True
            for block_term in block_terms:
                if len(block_term) < 4:
                    continue
                if query_term.startswith(block_term) or block_term.startswith(query_term):
                    return True
        return False

    @staticmethod
    def _split_into_blocks(lines: list[str]) -> list[tuple[str, list[str]]]:
        """将文件按顶层 def/class 切割成块"""
        blocks: list[tuple[str, list[str]]] = []
        current_type = "top_level"
        current: list[str] = []

        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                if current:
                    blocks.append((current_type, current))
                current_type = "import"
                current = [line]
            elif re.match(r"^def |^async def ", stripped):
                if current:
                    blocks.append((current_type, current))
                current_type = "function"
                current = [line]
            elif re.match(r"^class ", stripped):
                if current:
                    blocks.append((current_type, current))
                current_type = "class"
                current = [line]
            else:
                if current_type == "import" and not (stripped.startswith("import ") or stripped.startswith("from ")):
                    blocks.append((current_type, current))
                    current_type = "top_level"
                    current = [line]
                else:
                    current.append(line)

        if current:
            blocks.append((current_type, current))
        return blocks


# -----------------------------------------------------------------------
# 3. Token Budget Trimmer
# -----------------------------------------------------------------------

class TokenBudgetTrimmer:
    """
    当所有选中文件的 token 总量超过预算时，按相关性优先截断。
    """

    def __init__(self, token_budget: int = 8000, tokenizer: str = "cl100k_base"):
        self.token_budget = token_budget
        self.tokenizer = tokenizer

    def trim(self, files: dict[str, str], query: str) -> dict[str, str]:
        """
        Returns: 在 token budget 内的文件内容（可能截断）
        """
        result: dict[str, str] = {}
        used = 0

        # 按相关性排序（已由 TopKFileSelector 完成，这里按长度升序先填短文件）
        sorted_files = sorted(files.items(), key=lambda kv: count_tokens(kv[1], self.tokenizer))

        for path, content in sorted_files:
            tokens = count_tokens(content, self.tokenizer)
            remaining = self.token_budget - used
            if tokens <= remaining:
                result[path] = content
                used += tokens
            elif remaining > 200:
                # 截断到剩余预算
                enc = tiktoken.get_encoding(self.tokenizer)
                encoded = enc.encode(content, disallowed_special=())
                truncated = enc.decode(encoded[:remaining])
                result[path] = truncated + "\n# [TRUNCATED BY TOKEN BUDGET]"
                used += remaining
            # 否则跳过
            if used >= self.token_budget:
                break

        return result


# -----------------------------------------------------------------------
# 4. ContextCompressor（组合）
# -----------------------------------------------------------------------

class ContextCompressor:
    """
    主压缩器，组合 TopK + FunctionLevel + TokenBudget

    用法：
        compressor = ContextCompressor(CompressionConfig(strategy="hybrid", top_k_files=5))
        compressed = compressor.compress(query=issue_text, files=repo_files)
        context_str = compressor.to_prompt_string(compressed)
    """

    def __init__(self, config: Optional[CompressionConfig] = None):
        self.config = config or CompressionConfig()
        self._topk = TopKFileSelector(top_k=self.config.top_k_files)
        self._func_trim = FunctionLevelTrimmer(
            keep_imports=self.config.keep_imports,
            keep_class_signatures=self.config.keep_class_signatures,
        )
        self._budget = TokenBudgetTrimmer(
            token_budget=self.config.token_budget,
            tokenizer=self.config.tokenizer,
        )

    def compress(self, query: str, files: dict[str, str]) -> dict[str, str]:
        """
        完整压缩流程：
          1. TopK 文件选择
          2. 函数级剪枝
          3. Token Budget 截断
        """
        strategy = self.config.strategy

        if strategy == "none":
            return files

        # Step 1: TopK
        if strategy in ("topk", "hybrid"):
            files = self._topk.select(query, files)

        # Step 2: Function-level trimming
        if strategy in ("function", "hybrid"):
            files = {
                path: self._func_trim.trim(content, query)
                for path, content in files.items()
            }

        # Step 3: Token budget
        if strategy in ("budget", "hybrid"):
            files = self._budget.trim(files, query)

        return files

    @staticmethod
    def to_prompt_string(files: dict[str, str]) -> str:
        """将压缩后的文件字典转为 prompt 字符串"""
        parts = []
        for path, content in files.items():
            parts.append(f"### File: {path}\n```\n{content}\n```")
        return "\n\n".join(parts)

    def compression_ratio(self, original: dict[str, str], compressed: dict[str, str]) -> float:
        """计算压缩比（压缩后 token / 原始 token）"""
        orig_tokens = sum(count_tokens(c, self.config.tokenizer) for c in original.values())
        comp_tokens = sum(count_tokens(c, self.config.tokenizer) for c in compressed.values())
        if orig_tokens == 0:
            return 1.0
        return comp_tokens / orig_tokens
