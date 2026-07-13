"""Search tool — regex code search."""

import subprocess

from fraktal.config import FraktalConfig
from fraktal.tools.base import Tool, ToolResult


class SearchCodeTool(Tool):
    name = "search_code"
    description = "Search for a regex pattern in source files."

    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search for."},
            "path": {"type": "string", "description": "Directory or file to search (default: workspace root)."},
            "file_types": {
                "type": "string",
                "description": "Comma-separated file extensions (default: py,js,ts,tsx,md,toml,json,yaml,yml,html,css).",
            },
        },
        "required": ["pattern"],
    }

    DEFAULT_TYPES = "py,js,ts,tsx,md,toml,json,yaml,yml,html,css,svg"

    def __init__(self, config: FraktalConfig):
        self.workspace = config.workspace

    def execute(self, pattern: str, path: str = ".", file_types: str | None = None) -> ToolResult:
        try:
            search_path = self.workspace / path
            types = file_types or self.DEFAULT_TYPES
            includes = []
            for ext in types.split(","):
                includes.extend(["--include", f"*.{ext.strip()}"])
            result = subprocess.run(
                ["grep", "-rn", *includes, pattern, str(search_path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.workspace),
            )
            output = result.stdout[:8000]
            return ToolResult(output=output or "No matches found.")
        except Exception as e:
            return ToolResult(output=f"Error searching: {e}", success=False)
