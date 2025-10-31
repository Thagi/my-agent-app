FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY mcp_registry ./registry

RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache .

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "langgraph_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
