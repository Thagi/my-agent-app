# Repository Coding Instructions

This document applies to the entire repository. Add additional `AGENTS.md` files in subdirectories whenever more specific guidance is required.

## Commit & PR Guidelines
- Write descriptive commit messages summarizing the change (e.g., `docs: add podman-compose deployment guide`).
- Keep documentation and infrastructure updates separate from application code changes when possible.
- After completing local testing, update the PR description to reflect the cumulative impact of the change.

## Documentation Standards
- Prefer [CommonMark](https://spec.commonmark.org/) compliant Markdown.
- Use sentence case for headings (e.g., `## Running the stack`).
- Wrap lines at ~100 characters to improve readability in diffs.
- Include code blocks for commands and configuration snippets using fenced Markdown with language hints.

## Development Conventions
- When adding code:
  - Organize services under `services/<service-name>/`.
  - Place infrastructure artifacts under `compose/` or `infrastructure/`.
  - Provide unit tests alongside Python modules under `tests/` using `pytest`.
  - Document service-specific instructions in a colocated `AGENTS.md`.
- Ensure Podman Compose files define named volumes for stateful services and document them in the README.

## Planning Artifacts
- Keep `PLANS.md` current with the high-level implementation roadmap.
- For significant changes, describe context, goals, and step-by-step actions in the plan before starting work.
