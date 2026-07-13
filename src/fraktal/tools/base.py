"""Tool base classes — Tool, ToolRegistry, ToolResult."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    output: str
    success: bool = True
    artifacts: list[str] = field(default_factory=list)


class Tool:
    """Abstract tool with JSON Schema parameters."""

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def specs(self) -> list[dict[str, Any]]:
        """Return tool specs in OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]


def default_registry(workspace_path: str) -> ToolRegistry:
    """Build a default tool registry for a workspace."""
    from fraktal.config import FraktalConfig
    from fraktal.tools.filesystem import ReadFileTool, WriteFileTool, ListDirTool
    from fraktal.tools.terminal import ShellTool
    from fraktal.tools.search import SearchCodeTool

    config = FraktalConfig(workspace=workspace_path)
    registry = ToolRegistry()
    registry.register(ReadFileTool(config))
    registry.register(WriteFileTool(config))
    registry.register(ListDirTool(config))
    registry.register(SearchCodeTool(config))
    registry.register(ShellTool(config))
    return registry
