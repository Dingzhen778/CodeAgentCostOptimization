from src.config_utils import resolve_env_placeholders


def test_resolve_env_placeholders(monkeypatch):
    monkeypatch.setenv("TEST_API_KEY", "secret-value")
    config = {
        "api_key": "${TEST_API_KEY}",
        "nested": {
            "items": ["x", "${TEST_API_KEY}"],
        },
    }

    resolved = resolve_env_placeholders(config)

    assert resolved["api_key"] == "secret-value"
    assert resolved["nested"]["items"][1] == "secret-value"


def test_resolve_env_placeholders_with_default(monkeypatch):
    monkeypatch.delenv("MISSING_MODEL", raising=False)
    config = {"model": "${MISSING_MODEL:-deepseek-v3.2}"}

    resolved = resolve_env_placeholders(config)

    assert resolved["model"] == "deepseek-v3.2"
