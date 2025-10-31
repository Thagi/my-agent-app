# LangGraph Service Coding Guidelines

This document applies to all files within `services/langgraph/`.

- Prefer FastAPI for HTTP endpoints and keep route handlers lean. Place orchestration logic in dedicated modules under `src/langgraph_agent/`.
- Use Pydantic models for request/response validation and dataclasses for internal state when appropriate.
- Keep functions pure where possible to simplify testing.
- Provide unit tests for new behavior under `services/langgraph/tests/`.
- Structure new LangGraph nodes inside `src/langgraph_agent/nodes/`.
