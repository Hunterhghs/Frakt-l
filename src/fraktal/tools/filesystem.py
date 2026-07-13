"""Filesystem tools — read, write, list files."""

from pathlib import Path

from fraktal.config import FraktalConfig
from fraktal.tools.base import Tool, ToolResult


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read a file and return its contents with line numbers."

    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file."},
            "offset": {"type": "integer", "description": "Line offset (0-based, default 0)."},
            "limit": {"type": "integer", "description": "Max lines to return (default all)."},
        },
        "required": ["path"],
    }

    def __init__(self, config: FraktalConfig):
        self.workspace = config.workspace

    def execute(self, path: str, offset: int = 0, limit: int | None = None) -> ToolResult:
        try:
            p = Path(path)
            if not p.is_absolute():
                p = self.workspace / p
            content = p.read_text()
            lines = content.split("\n")
            if limit is None:
                limit = len(lines)
            selected = lines[offset : offset + limit]
            formatted = "\n".join(
                f"{i + offset + 1:4}→{line}" for i, line in enumerate(selected)
            )
            return ToolResult(output=formatted)
        except FileNotFoundError:
            return ToolResult(output=f"File not found: {path}", success=False)
        except Exception as e:
            return ToolResult(output=f"Error reading {path}: {e}", success=False)


class WriteFileTool(Tool):
    name = "write_file"
    description = "Write content to a file. Creates parent directories as needed."

    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file."},
            "content": {"type": "string", "description": "Content to write."},
        },
        "required": ["path", "content"],
    }

    def __init__(self, config: FraktalConfig):
        self.workspace = config.workspace

    def execute(self, path: str, content: str) -> ToolResult:
        try:
            p = Path(path)
            if not p.is_absolute():
                p = self.workspace / p
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return ToolResult(output=f"Wrote {len(content)} bytes to {p}")
        except Exception as e:
            return ToolResult(output=f"Error writing {path}: {e}", success=False)


class ListDirTool(Tool):
    name = "list_dir"
    description = "List directory contents."

    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path."},
        },
        "required": ["path"],
    }

    def __init__(self, config: FraktalConfig):
        self.workspace = config.workspace

    def execute(self, path: str) -> ToolResult:
        try:
            p = Path(path)
            if not p.is_absolute():
                p = self.workspace / p
            items = []
            for child in sorted(p.iterdir()):
                suffix = "/" if child.is_dir() else f"  ({child.stat().st_size} bytes)"
                items.append(f"  {child.name}{suffix}")
            return ToolResult(output="\n".join(items) or "(empty)")
        except FileNotFoundError:
            return ToolResult(output=f"Directory not found: {path}", success=False)
        except Exception as e:
            return ToolResult(output=f"Error listing {path}: {e}", success=False)
