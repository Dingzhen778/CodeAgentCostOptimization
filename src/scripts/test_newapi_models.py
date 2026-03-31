#!/usr/bin/env python3
"""
test_newapi_models.py

列出 New API 可用模型，或对指定模型发起最小 chat completion 验证。

用法：
    python scripts/test_newapi_models.py --list
    python scripts/test_newapi_models.py --filter deepseek glm kimi
    python scripts/test_newapi_models.py --models deepseek-v3.2 glm-4.7 kimi-k2.5
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))


DEFAULT_BASE_URL = "https://newapi.deepwisdom.ai/v1"
DEFAULT_MODELS = ["deepseek-v3.2", "glm-4.7", "kimi-k2.5"]


def pick_temperature(model: str, default_temperature: float) -> float:
    if "kimi-k2.5" in model.lower():
        return 1.0
    return default_temperature


def list_models(base_url: str, api_key: str) -> list[str]:
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        response = client.get(
            f"{base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        response.raise_for_status()
    return [item["id"] for item in response.json().get("data", [])]


def test_models(base_url: str, api_key: str, models: list[str], prompt: str, max_tokens: int, temperature: float):
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=60.0)
    for model in models:
        chosen_temperature = pick_temperature(model, temperature)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=chosen_temperature,
                max_tokens=max_tokens,
            )
            message = response.choices[0].message if response.choices else None
            usage = getattr(response, "usage", None)
            print(json.dumps({
                "model": model,
                "ok": True,
                "temperature": chosen_temperature,
                "text": getattr(message, "content", None),
                "reasoning_content": getattr(message, "reasoning_content", None),
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
            }, ensure_ascii=False))
        except Exception as exc:
            print(json.dumps({
                "model": model,
                "ok": False,
                "temperature": chosen_temperature,
                "error": type(exc).__name__,
                "detail": str(exc),
            }, ensure_ascii=False))


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="List or test New API models")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key-env", default="NEW_API_KEY")
    parser.add_argument("--list", action="store_true", help="只列出可用模型")
    parser.add_argument("--filter", nargs="*", default=[], help="只显示包含这些关键字的模型")
    parser.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    parser.add_argument("--prompt", default="Reply with exactly: OK")
    parser.add_argument("--max-tokens", type=int, default=32)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(f"Missing env var: {args.api_key_env}")

    models = list_models(args.base_url, api_key)
    if args.list:
        for model in models:
            if args.filter and not any(keyword.lower() in model.lower() for keyword in args.filter):
                continue
            print(model)
        return

    test_models(
        base_url=args.base_url,
        api_key=api_key,
        models=args.models,
        prompt=args.prompt,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )


if __name__ == "__main__":
    main()
