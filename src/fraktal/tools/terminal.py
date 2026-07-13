"""Terminal tool — execute shell commands."""

import subprocess

from fraktal.config import FraktalConfig
from fraktal.tools.base import Tool, ToolResult


class ShellTool(Tool):
    name = "run_shell"
    description = "Execute a shell command and return its output."

    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command to run."},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)."},
        },
        "required": ["command"],
    }

    def __init__(self, config: FraktalConfig):
        self.workspace = config.workspace
        self.default_timeout = config.command_timeout

    def execute(self, command: str, timeout: int | None = None) -> ToolResult:
        timeout = timeout or self.default_timeout
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace),
            )
            out = result.stdout
            if result.stderr:
                out += f"\n[stderr]\n{result.stderr}"
            if result.returncode != 0:
                out += f"\n[exit code: {result.returncode}]"
            return ToolResult(
                output=out[:10000],
                success=result.returncode == 0,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(output=f"Command timed out after {timeout}s", success=False)
        except Exception as e:
            return ToolResult(output=f"Error: {e}", success=False)
