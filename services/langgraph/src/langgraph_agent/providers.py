"""Provider clients used by the LangGraph agent."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class ProviderError(RuntimeError):
    """Raised when a provider cannot satisfy a generation request."""


@dataclass
class ProviderResponse:
    """Container for model generation results."""

    content: str
    metadata: dict[str, Any]


class BaseProvider:
    """Base class for providers."""

    name: str

    async def __call__(self, prompt: str, tools: list[str]) -> str:
        response = await self.generate(prompt, tools)
        return response.content

    async def generate(self, prompt: str, tools: list[str]) -> ProviderResponse:  # pragma: no cover - interface contract
        raise NotImplementedError


class StubProvider(BaseProvider):
    """Provider used when upstream services are not available."""

    def __init__(self, name: str, reason: str | None = None) -> None:
        self.name = name
        self._reason = reason or "stubbed provider"

    async def generate(self, prompt: str, tools: list[str]) -> ProviderResponse:
        tool_hint = f" Tools considered: {', '.join(tools)}." if tools else ""
        message = f"{self.name.title()} stub response for: {prompt[:200]} ({self._reason}).{tool_hint}"
        return ProviderResponse(content=message, metadata={"provider": self.name, "stub": True})


class OpenAIChatProvider(BaseProvider):
    """HTTP client that calls OpenAI's chat completions API."""

    def __init__(self, api_key: str | None, base_url: str, model: str) -> None:
        self.name = "openai"
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        if not self._api_key:
            self._stub = StubProvider(self.name, reason="missing API key")
        else:
            self._stub = None

    async def generate(self, prompt: str, tools: list[str]) -> ProviderResponse:
        if not self._api_key:
            return await self._stub.generate(prompt, tools)  # type: ignore[union-attr]

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{self._base_url}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - depends on network
            raise ProviderError(f"OpenAI request failed: {exc}") from exc

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ProviderResponse(content=content or "", metadata={"provider": self.name, "raw": data})


class OllamaChatProvider(BaseProvider):
    """HTTP client that calls Ollama's generate endpoint."""

    def __init__(self, base_url: str, model: str) -> None:
        self.name = "ollama"
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def generate(self, prompt: str, tools: list[str]) -> ProviderResponse:
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{self._base_url}/api/generate", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - depends on network
            raise ProviderError(f"Ollama request failed: {exc}") from exc

        data = response.json()
        content = data.get("response", "")
        return ProviderResponse(content=content or "", metadata={"provider": self.name, "raw": data})
