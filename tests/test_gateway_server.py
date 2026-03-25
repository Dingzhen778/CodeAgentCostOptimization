from src.gateway import server


def test_resolve_target_model_prefers_explicit_request_model():
    original_config = server._config
    try:
        server._config = {
            "default_model": "deepseek-v3.2",
            "routing": {
                "default": "deepseek-v3.2",
                "edit": "glm-4.7",
            },
        }

        target = server._resolve_target_model({"model": "openai/glm-4.7"}, "default")

        assert target == "openai/glm-4.7"
    finally:
        server._config = original_config


def test_resolve_target_model_uses_routing_when_request_model_missing():
    original_config = server._config
    try:
        server._config = {
            "default_model": "deepseek-v3.2",
            "routing": {
                "default": "deepseek-v3.2",
                "edit": "glm-4.7",
            },
        }

        target = server._resolve_target_model({}, "edit")

        assert target == "glm-4.7"
    finally:
        server._config = original_config
