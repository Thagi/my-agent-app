"""Model routing helpers."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Callable, Coroutine


logger = logging.getLogger(__name__)


ProviderHandler = Callable[[str, list[str]], Coroutine[None, None, str]]


@dataclass
class GenerationResult:
    """Represents the outcome of a provider generation call."""

    provider: str
    content: str


class ModelRouter:
    """Simple provider router that selects handlers based on heuristics."""

    def __init__(self, providers: dict[str, ProviderHandler], default_provider: str, fallback_provider: str) -> None:
        if default_provider not in providers:
            raise ValueError(f"Unknown default provider: {default_provider}")
        if fallback_provider not in providers:
            raise ValueError(f"Unknown fallback provider: {fallback_provider}")
        self._providers = providers
        self._default = default_provider
        self._fallback = fallback_provider

    def select_provider(self, user_message: str) -> str:
        lowered = user_message.lower()
        if any(keyword in lowered for keyword in ("offline", "local", "privacy")):
            return self._fallback
        if "image" in lowered or "vision" in lowered:
            return self._fallback
        return self._default

    @property
    def fallback_provider(self) -> str:
        return self._fallback

    async def generate(self, provider: str, prompt: str, tools: list[str] | None = None) -> GenerationResult:
        tools = tools or []
        handler = self._providers.get(provider)
        if handler is None:
            logger.warning("Unknown provider '%s'; using fallback '%s'", provider, self._fallback)
            handler = self._providers[self._fallback]
            provider = self._fallback

        try:
            content = await handler(prompt, tools)
            return GenerationResult(provider=provider, content=content)
        except Exception as exc:  # pragma: no cover - defensive path
            logger.warning("Provider '%s' failed: %s", provider, exc)
            if provider != self._fallback:
                fallback_handler = self._providers[self._fallback]
                fallback_content = await fallback_handler(prompt, tools)
                return GenerationResult(provider=self._fallback, content=fallback_content)
            raise
