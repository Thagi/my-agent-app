"""FastAPI entrypoint for the LangGraph agent service."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import get_settings
from .nodes.executor import ExecutionResult, ExecutorNode
from .nodes.input_parser import InputParserNode
from .nodes.planner import PlannerNode
from .nodes.validator import ValidatorNode
from .providers import OllamaChatProvider, OpenAIChatProvider, ProviderError, StubProvider
from .registry import load_registry
from .routing import ModelRouter


class ChatMessagePayload(BaseModel):
    role: Literal["system", "user", "assistant", "tool"] = "user"
    content: str


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessagePayload]
    stream: bool | None = False


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessagePayload
    finish_reason: Literal["stop", "length", "tool_calls"] = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    created: int
    model: str
    provider: str
    tool_calls: list[str] = Field(default_factory=list)
    choices: list[ChatCompletionChoice]


def create_app() -> FastAPI:
    settings = get_settings()
    registry = load_registry(settings.mcp_registry_path)

    providers = {
        "openai": OpenAIChatProvider(settings.openai_api_key, settings.openai_base_url, settings.openai_chat_model),
        "ollama": OllamaChatProvider(settings.ollama_base_url, settings.ollama_model),
    }
    if settings.fallback_provider not in providers:
        providers[settings.fallback_provider] = StubProvider(settings.fallback_provider, reason="configured fallback")
    if settings.default_provider not in providers:
        providers[settings.default_provider] = StubProvider(settings.default_provider, reason="configured default")
    router = ModelRouter(providers, settings.default_provider, settings.fallback_provider)

    input_parser = InputParserNode()
    planner = PlannerNode(router, registry.get("tool_names", []))
    executor = ExecutorNode(router)
    validator = ValidatorNode()

    app = FastAPI(title="LangGraph Agent Service")

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {"status": "ok", "provider": settings.default_provider}

    @app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
    async def chat_completions(payload: ChatCompletionRequest) -> ChatCompletionResponse:
        if not payload.messages:
            raise HTTPException(status_code=400, detail="messages cannot be empty")

        task = input_parser.parse(msg.model_dump() for msg in payload.messages)
        plan = planner.plan(task)
        try:
            result = await executor.execute(plan, task)
        except ProviderError as exc:
            if plan.primary_provider != router.fallback_provider:
                result = await executor.execute(plan, task, provider_override=router.fallback_provider)
            else:
                offline_provider = StubProvider("offline", reason=str(exc))
                content = await offline_provider(task.latest_user_message, [])
                result = ExecutionResult(content=content, provider="offline", tool_calls=[])

        validation = validator.validate(task, result)

        if not validation.is_valid:
            try:
                result = await executor.execute(plan, task, provider_override=router.fallback_provider)
            except ProviderError as exc:
                offline_provider = StubProvider("offline", reason=str(exc))
                content = await offline_provider(task.latest_user_message, [])
                result = ExecutionResult(content=content, provider="offline", tool_calls=[])
            validation = validator.validate(task, result)

        if not validation.is_valid:
            raise HTTPException(status_code=502, detail=validation.message)

        response_message = ChatMessagePayload(role="assistant", content=result.content)
        choice = ChatCompletionChoice(index=0, message=response_message)
        response = ChatCompletionResponse(
            id=str(uuid4()),
            created=int(datetime.utcnow().timestamp()),
            model=payload.model or plan.primary_provider,
            provider=result.provider,
            tool_calls=result.tool_calls,
            choices=[choice],
        )
        return response

    return app


app = create_app()
