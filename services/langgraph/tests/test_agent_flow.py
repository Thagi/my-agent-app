from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from langgraph_agent.main import app
from langgraph_agent.nodes.input_parser import InputParserNode
from langgraph_agent.routing import ModelRouter


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_input_parser_returns_agent_task() -> None:
    parser = InputParserNode()
    task = parser.parse([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ])
    assert task.latest_user_message == "Hello"


async def _stub_handler(prompt: str, tools: list[str]) -> str:
    return prompt


def test_model_router_selects_fallback_for_offline_keyword() -> None:
    router = ModelRouter({"openai": _stub_handler, "ollama": _stub_handler}, "openai", "ollama")
    provider = router.select_provider("Use offline local model")
    assert provider == "ollama"


@pytest.mark.asyncio
async def test_model_router_generate_falls_back_on_error() -> None:
    async def _failing_handler(prompt: str, tools: list[str]) -> str:
        raise RuntimeError("network down")

    router = ModelRouter({"openai": _failing_handler, "ollama": _stub_handler}, "openai", "ollama")
    result = await router.generate("openai", "Hello", tools=["demo.tool"])
    assert result.provider == "ollama"
    assert result.content == "Hello"


def test_chat_completion_endpoint_returns_response(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "Plan a day trip to Kyoto"},
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["choices"][0]["message"]["role"] == "assistant"
    assert "stub response" in payload["choices"][0]["message"]["content"].lower()
