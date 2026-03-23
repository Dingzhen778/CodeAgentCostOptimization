"""
LLM Gateway FastAPI Server

作为本地 OpenAI-compatible 代理服务器启动，
Claude Code / mini-swe-agent 可以将 OPENAI_BASE_URL 指向此服务。

启动方式：
    python -m src.gateway.server --config configs/gateway.yaml

或：
    uvicorn src.gateway.server:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import json
import time
from typing import Any

import httpx
import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger
from pathlib import Path

app = FastAPI(title="LLM Cost Gateway", version="0.1.0")

# 全局配置（由 --config 加载）
_config: dict = {}
_token_log_file: Path | None = None


# -----------------------------------------------------------------------
# 路由：OpenAI-compatible /v1/chat/completions
# -----------------------------------------------------------------------

@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    body = await request.json()
    model: str = body.get("model", _config.get("default_model", "deepseek-chat"))

    # 解析 tool 类型（从请求 headers 或 body 中的自定义字段）
    tool_hint: str = request.headers.get("X-Tool-Hint", "default")

    # 路由到目标模型
    routing: dict = _config.get("routing", {})
    target_model = routing.get(tool_hint, routing.get("default", model))

    # 构造转发请求
    upstream_url = _config.get("upstream_url", "https://api.deepseek.com/v1")
    upstream_key = _config.get("upstream_key", "")

    body["model"] = target_model

    t0 = time.monotonic()
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            resp = await client.post(
                f"{upstream_url}/chat/completions",
                json=body,
                headers={
                    "Authorization": f"Bearer {upstream_key}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))

    latency = time.monotonic() - t0
    data = resp.json()

    # 记录 token 用量
    usage = data.get("usage", {})
    _log_usage(
        model=target_model,
        tool=tool_hint,
        input_tokens=usage.get("prompt_tokens", 0),
        output_tokens=usage.get("completion_tokens", 0),
        latency=latency,
    )

    return JSONResponse(content=data)


# -----------------------------------------------------------------------
# Token 日志
# -----------------------------------------------------------------------

def _log_usage(model: str, tool: str, input_tokens: int, output_tokens: int, latency: float):
    record = {
        "ts": time.time(),
        "model": model,
        "tool": tool,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "latency": round(latency, 3),
    }
    logger.info(f"[token] {json.dumps(record)}")
    if _token_log_file:
        with _token_log_file.open("a") as f:
            f.write(json.dumps(record) + "\n")


# -----------------------------------------------------------------------
# 健康检查
# -----------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "config": _config.get("default_model", "unknown")}


# -----------------------------------------------------------------------
# CLI 入口
# -----------------------------------------------------------------------

def main():
    import argparse
    global _config, _token_log_file

    parser = argparse.ArgumentParser(description="LLM Cost Gateway Server")
    parser.add_argument("--config", default="configs/gateway.yaml")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    with open(args.config) as f:
        _config = yaml.safe_load(f)

    log_dir = Path(_config.get("log_dir", "logs/gateway"))
    log_dir.mkdir(parents=True, exist_ok=True)
    _token_log_file = log_dir / "gateway_token_log.jsonl"

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
