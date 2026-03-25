from __future__ import annotations

import os
import re
from typing import Any

_ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::-(.*?))?\}")


def _expand_env_string(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        default = match.group(2)
        return os.environ.get(name, default if default is not None else match.group(0))

    return _ENV_PATTERN.sub(repl, value)


def resolve_env_placeholders(value: Any) -> Any:
    """Recursively expand ${VAR} placeholders inside config values."""
    if isinstance(value, dict):
        return {k: resolve_env_placeholders(v) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_env_placeholders(v) for v in value]
    if isinstance(value, str):
        return _expand_env_string(value)
    return value
