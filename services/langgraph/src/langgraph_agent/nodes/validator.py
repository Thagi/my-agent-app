"""Validator node ensures outputs satisfy basic expectations."""
from __future__ import annotations

from dataclasses import dataclass

from .input_parser import AgentTask
from .executor import ExecutionResult


@dataclass
class ValidationResult:
    """Result of output validation."""

    is_valid: bool
    message: str


class ValidatorNode:
    """Performs lightweight validation of execution results."""

    def validate(self, task: AgentTask, result: ExecutionResult) -> ValidationResult:
        if not result.content.strip():
            return ValidationResult(is_valid=False, message="Empty response generated")
        if "sorry" in result.content.lower() and "cannot" in result.content.lower():
            suggestion = "Consider rephrasing the request or trying a different tool."
            return ValidationResult(is_valid=False, message=suggestion)
        return ValidationResult(is_valid=True, message="ok")
