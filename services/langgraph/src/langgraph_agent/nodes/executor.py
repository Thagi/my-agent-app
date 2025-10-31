"""Execution node interacts with external providers or MCP tools."""
from __future__ import annotations

from dataclasses import dataclass

from ..routing import GenerationResult, ModelRouter
from .input_parser import AgentTask
from .planner import ExecutionPlan


@dataclass
class ExecutionResult:
    """Result returned by the executor node."""

    content: str
    provider: str
    tool_calls: list[str]


class ExecutorNode:
    """Executes the planned steps using the model router."""

    def __init__(self, router: ModelRouter) -> None:
        self._router = router

    async def execute(self, plan: ExecutionPlan, task: AgentTask, provider_override: str | None = None) -> ExecutionResult:
        provider = provider_override or plan.primary_provider
        generation: GenerationResult = await self._router.generate(
            provider, task.latest_user_message, tools=self._extract_tools(plan)
        )
        return ExecutionResult(
            content=generation.content,
            provider=generation.provider,
            tool_calls=self._extract_tools(plan),
        )

    def _extract_tools(self, plan: ExecutionPlan) -> list[str]:
        tools: list[str] = []
        for step in plan.steps:
            tools.extend(step.tools)
        return tools
