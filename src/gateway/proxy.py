"""
LLM Gateway 中转层

将 Claude Code / mini-swe-agent 发出的 OpenAI-compatible 请求
路由到廉价 API（DeepSeek / Qwen / OpenRouter 等），并自动记录 token 用量。

设计原则：
  - 对 Agent 侧完全透明（OpenAI API 兼容）
  - 支持 per-request 模型路由（根据 tool 类型路由不同模型）
  - 每次请求写入 TokenLogger
"""
from __future__ import annotations

import time
from typing import Any, Optional

import httpx
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion

from src.gateway.token_logger import TokenLogger


# -----------------------------------------------------------------------
# 模型路由表（可在 configs/gateway.yaml 中覆盖）
# -----------------------------------------------------------------------
DEFAULT_ROUTING: dict[str, str] = {
    # tool_name -> model_id
    "default":      "deepseek-chat",
    "read_file":    "deepseek-chat",
    "search":       "deepseek-chat",
    "bash":         "deepseek-chat",
    "edit":         "deepseek-chat",      # 可换成更强的模型
    "write_file":   "deepseek-chat",
}


class LLMGateway:
    """
    同步 LLM Gateway

    用法：
        gw = LLMGateway(
            base_url="https://your-proxy/v1",
            api_key="sk-xxx",
            token_logger=logger,
        )
        response = gw.chat(messages, tool="read_file", step=3)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        token_logger: Optional[TokenLogger] = None,
        routing: Optional[dict[str, str]] = None,
        default_model: str = "deepseek-chat",
        timeout: float = 120.0,
    ):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
        )
        self.token_logger = token_logger
        self.routing = routing or DEFAULT_ROUTING
        self.default_model = default_model

    # ------------------------------------------------------------------
    # 核心接口
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        tool: str = "default",
        step: int = 0,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        """发送 chat completion 请求并记录 token"""
        chosen_model = model or self.routing.get(tool, self.routing.get("default", self.default_model))

        t0 = time.monotonic()
        response: ChatCompletion = self.client.chat.completions.create(
            model=chosen_model,
            messages=messages,
            **kwargs,
        )
        latency = time.monotonic() - t0

        # 记录 token 用量
        if self.token_logger and response.usage:
            self.token_logger.log(
                step=step,
                tool=tool,
                model=chosen_model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                latency=latency,
            )

        return response

    # ------------------------------------------------------------------
    # 工厂方法：从配置文件构建
    # ------------------------------------------------------------------

    @classmethod
    def from_config(cls, config: dict, token_logger: Optional[TokenLogger] = None) -> "LLMGateway":
        return cls(
            base_url=config["base_url"],
            api_key=config["api_key"],
            token_logger=token_logger,
            routing=config.get("routing", DEFAULT_ROUTING),
            default_model=config.get("default_model", "deepseek-chat"),
            timeout=config.get("timeout", 120.0),
        )


class AsyncLLMGateway:
    """
    异步版本 LLM Gateway（用于并发跑多个 instance）
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        token_logger: Optional[TokenLogger] = None,
        routing: Optional[dict[str, str]] = None,
        default_model: str = "deepseek-chat",
        timeout: float = 120.0,
    ):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
        )
        self.token_logger = token_logger
        self.routing = routing or DEFAULT_ROUTING
        self.default_model = default_model

    async def chat(
        self,
        messages: list[dict],
        tool: str = "default",
        step: int = 0,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        chosen_model = model or self.routing.get(tool, self.routing.get("default", self.default_model))

        t0 = time.monotonic()
        response: ChatCompletion = await self.client.chat.completions.create(
            model=chosen_model,
            messages=messages,
            **kwargs,
        )
        latency = time.monotonic() - t0

        if self.token_logger and response.usage:
            self.token_logger.log(
                step=step,
                tool=tool,
                model=chosen_model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                latency=latency,
            )

        return response
