"""MCP registry loader."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_registry(path: Path) -> dict[str, Any]:
    """Load MCP registry metadata from YAML file."""

    if not path.exists():
        return {"servers": []}
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content) or {}
    servers = data.get("servers", [])
    tool_names: list[str] = []
    for server in servers:
        for action in server.get("actions", []):
            tool_names.append(f"{server.get('name')}.{action.get('name')}")
    return {"servers": servers, "tool_names": tool_names}
