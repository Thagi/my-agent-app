# LibreChat LangGraph Agent Platform

## Overview
This repository defines an agentic application that exposes LibreChat as the primary user interface while delegating orchestration to a LangGraph-based autonomous agent. The agent connects to Model Context Protocol (MCP) servers, including flows published from n8n, and dynamically chooses the best capability to execute each user task.

## Key Components
- **LibreChat** – Chat UI deployed via Podman and configured to route requests to the LangGraph agent service.
- **LangGraph Agent Service** – Python service that implements the agent, tool registry, and model selection logic. It supports both OpenAI-hosted models and locally hosted alternatives such as Ollama's `gpt-oss:20b`.
- **MCP Tooling** – Collection of MCP servers (built-in services, bespoke integrations, and n8n-exported workflows) that expose structured tools to the agent.
- **n8n Automation** – Workflow automation platform used to build reusable capabilities. Selected workflows are packaged and served as MCP endpoints.
- **MongoDB** – Backing data store for LibreChat user accounts, conversations, and configuration state.
- **Model Backends** – OpenAI models (default) and Ollama models (optional) accessed through a model router. Additional providers can be added with minimal configuration updates.
- **Podman Compose Stack** – Containerized deployment ensuring each service runs in an isolated pod with persistent volumes for stateful components.

## Repository Layout
```
.
├── README.md        # This document
├── AGENTS.md        # Contribution and coding-agent instructions
├── PLANS.md         # High-level implementation plan for the platform
├── podman-compose.yml
├── config/
│   └── librechat.json
├── mcp/
│   └── registry/
│       └── registry.yaml
└── services/
    └── langgraph/
        ├── AGENTS.md
        ├── pyproject.toml
        ├── Dockerfile
        ├── src/langgraph_agent/
        ├── tests/
        └── mcp_registry/
```

The LangGraph agent service currently ships with a FastAPI-based endpoint that mirrors OpenAI's chat completions API. It loads MCP registry metadata from `mcp/registry/registry.yaml`, selects a model provider using the built-in router, and prefers real OpenAI or Ollama calls when credentials are present. When upstream models are unavailable, the service gracefully falls back to deterministic stub responses so the UI remains responsive during development.

## Prerequisites
- Podman **4.4+**
- podman-compose **1.0+**
- Access to an OpenAI API key (if using OpenAI models)
- Local Ollama instance with `gpt-oss:20b` pulled (optional fallback)
- Node.js **18+** (for building LibreChat assets if customization is required)

## Configuration
1. Copy `.env.example` (to be provided with the implementation) to `.env` and set the following variables:
   - `OPENAI_API_KEY` – API key used by the agent when delegating to OpenAI models.
   - `OPENAI_BASE_URL` – Override for the OpenAI REST endpoint (defaults to `https://api.openai.com/v1`).
   - `OPENAI_CHAT_MODEL` – Chat completion model identifier (defaults to `gpt-4o-mini`).
   - `OLLAMA_BASE_URL` – HTTP endpoint for the local Ollama server (defaults to `http://host.containers.internal:11434`).
   - `OLLAMA_MODEL` – Ollama model tag to request during inference (defaults to `gpt-oss:20b`).
   - `LANGGRAPH_MODEL_ROUTER` – Preferred model selection strategy (e.g., `openai`, `ollama`, or `auto`).
   - `LIBRECHAT_CONFIG_PATH` – Path to LibreChat configuration JSON.
   - `N8N_ENCRYPTION_KEY` – Persistent key required by n8n for encrypted credentials.
   - `MONGO_URI` – Connection string for LibreChat's MongoDB instance (defaults to `mongodb://mongo:27017/librechat`).

2. Optional: Add secrets required by n8n workflows (third-party API keys, webhook URLs) to `secrets/*.env` files and reference them from workflow nodes.

## Persistent volumes
To prevent data loss when the Podman stack shuts down, the compose file defines the following named volumes:
- `librechat-data` → `/app/data`
- `langgraph-state` → `/app/state`
- `n8n-data` → `/home/node/.n8n`
- `ollama-models` → `/root/.ollama`
- `redis-data` → `/data`
- `mongo-data` → `/data/db`

Check `podman-compose.yml` for exact mapping names. Ensure the host directories exist before starting the stack if you convert the named volumes to bind mounts.

## Running the Stack
1. Copy `.env.example` to `.env` and adjust secrets before starting the stack.
2. Build custom images if needed (e.g., the LangGraph agent service):
   ```bash
   podman-compose build
   ```
3. Start all services:
   ```bash
   podman-compose up -d
   ```
4. Access LibreChat at `http://localhost:3080` (default port). The LangGraph agent service exposes an internal HTTP endpoint consumed by LibreChat.
5. Access n8n at `http://localhost:5678` to manage workflows and publish MCP-compatible APIs.
6. Inspect MongoDB data by running `podman exec -it librechat-mongo mongosh` or by temporarily attaching a MongoDB client container to the podman network (the database is not exposed on the host by default).
7. To view logs:
   ```bash
   podman-compose logs -f
   ```

### Running the LangGraph agent locally

To iterate on the agent service without containers, install dependencies with [uv](https://github.com/astral-sh/uv) or pip:

```bash
cd services/langgraph
uv pip install --all-extras .
uvicorn langgraph_agent.main:app --reload
```

Execute the unit tests from the same directory:

```bash
pytest
```

## n8n Workflow Publication as MCP Servers
1. Design workflows in the n8n UI and test them using built-in tools.
2. Export workflows and place them under `workflows/` with metadata describing the MCP interface (action names, parameters, etc.).
3. The LangGraph agent service will include a discovery process that loads available MCP descriptors and registers them as tools. n8n workflows exposed via MCP should implement idempotent operations and return structured JSON responses.

## Agent Orchestration
- The LangGraph agent will maintain a tool registry combining:
  - Built-in capabilities (search, retrieval, calculators).
  - MCP servers (including n8n-derived tools).
  - Direct integrations (e.g., REST APIs wrapped as MCP servers).
- The agent leverages LangGraph nodes for planning, execution, and validation. When a task arrives from LibreChat, it selects a model and sequence of tools using available metadata and cost heuristics.
- State, conversation history, and execution traces are persisted in the agent volume for auditing and resumption.

## Extending Models
Add new models by updating the model router configuration. Each entry should include provider name, base URL, authentication token, and supported modalities. The router will surface the configuration to LangGraph, allowing runtime selection without code changes.

## Development Workflow
1. Implement features on dedicated branches.
2. Update `PLANS.md` with new tasks or architectural decisions when expanding the stack.
3. Document service-specific instructions in nested `AGENTS.md` files placed beside the relevant code.
4. Run unit/integration tests for the LangGraph agent service (to be added under `services/langgraph/tests/`).

## Troubleshooting
- **LibreChat cannot reach the agent service** – Verify the service URL configured in LibreChat matches the podman network alias.
- **n8n credentials lost** – Confirm the n8n volume is mounted and the `N8N_ENCRYPTION_KEY` is unchanged.
- **Ollama model not found** – Run `ollama pull gpt-oss:20b` on the host or in the Ollama container.
- **MCP tool not registered** – Check that the MCP server is reachable and conforms to the protocol schema expected by the LangGraph tool loader.

## Roadmap
- Automate MCP discovery from n8n via WebSocket events.
- Provide example LangGraph graphs for typical automations (summarization, data enrichment, workflow chaining).
- Add CI pipeline that lints the Python agent and validates compose definitions.

## License
To be determined. Update this section before public release.
