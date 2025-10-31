"""Input parsing node for LangGraph agent."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class ChatMessage:
    """Normalized chat message."""

    role: str
    content: str


@dataclass
class AgentTask:
    """Normalized representation of a LibreChat request."""

    messages: List[ChatMessage]

    @property
    def latest_user_message(self) -> str:
        for message in reversed(self.messages):
            if message.role == "user":
                return message.content
        return ""


class InputParserNode:
    """Transforms raw payloads into agent tasks."""

    def parse(self, messages: Iterable[dict[str, str]]) -> AgentTask:
        normalized = [ChatMessage(role=msg.get("role", "user"), content=msg.get("content", "")) for msg in messages]
        return AgentTask(messages=normalized)
