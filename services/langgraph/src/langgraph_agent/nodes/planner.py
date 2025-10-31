"""Planner node determines the execution strategy."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..routing import ModelRouter
from .input_parser import AgentTask


@dataclass
class PlanStep:
    """Single step in an execution plan."""

    description: str
    provider: str
    tools: List[str]


@dataclass
class ExecutionPlan:
    """Plan built by the planner node."""

    steps: List[PlanStep]

    @property
    def primary_provider(self) -> str:
        return self.steps[0].provider if self.steps else "openai"


class PlannerNode:
    """Create execution plan based on task context and registry data."""

    def __init__(self, router: ModelRouter, available_tools: list[str] | None = None) -> None:
        self._router = router
        self._available_tools = available_tools or []

    def plan(self, task: AgentTask) -> ExecutionPlan:
        provider = self._router.select_provider(task.latest_user_message)
        tools = self._suggest_tools(task.latest_user_message)
        step = PlanStep(description="Generate assistant response", provider=provider, tools=tools)
        return ExecutionPlan(steps=[step])

    def _suggest_tools(self, user_message: str) -> List[str]:
        if not self._available_tools:
            return []
        lowered = user_message.lower()
        if "search" in lowered:
            return [tool for tool in self._available_tools if "search" in tool]
        if "knowledge" in lowered or "document" in lowered:
            return [tool for tool in self._available_tools if "knowledge" in tool]
        return self._available_tools[:1]
