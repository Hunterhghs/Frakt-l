"""Agent system — definition loaders, AgentRunner, and abstract Agent base.

Merges Grok Build's Agent/Persona/Role definition system with
Fable 5's abstract Agent and tool-execution loop.
"""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from fraktal.config import FraktalConfig
from fraktal.llm.base import LLMProvider, Message, ToolCall, ToolSpec
from fraktal.llm.registry import create_provider


# ── Definition parsers ──────────────────────────────────────────────────────

@dataclass
class AgentDefinition:
    name: str
    description: str
    prompt_mode: str = "full"
    model: str = "inherit"
    permission_mode: str = "default"
    agents_md: bool = True
    body: str = ""

    @classmethod
    def from_markdown(cls, path: Path) -> "AgentDefinition":
        text = path.read_text()
        frontmatter: dict[str, str] = {}
        body = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, _, val = line.partition(":")
                        frontmatter[key.strip()] = val.strip()
                body = parts[2].strip()
        return cls(
            name=frontmatter.get("name", path.stem),
            description=frontmatter.get("description", ""),
            prompt_mode=frontmatter.get("prompt_mode", "full"),
            model=frontmatter.get("model", "inherit"),
            permission_mode=frontmatter.get("permission_mode", "default"),
            agents_md=frontmatter.get("agents_md", "true").lower() == "true",
            body=body,
        )


@dataclass
class PersonaDefinition:
    name: str
    description: str
    instructions: str
    default_fork_context: bool = True
    reasoning_effort: str | None = None
    default_capability_mode: str = "all"
    inputs: list[dict] = field(default_factory=list)
    outputs: list[dict] = field(default_factory=list)

    @classmethod
    def from_toml(cls, path: Path) -> "PersonaDefinition":
        data = tomllib.loads(path.read_text())
        return cls(
            name=path.stem,
            description=data.get("description", ""),
            instructions=data.get("instructions", ""),
            default_fork_context=data.get("default_fork_context", True),
            reasoning_effort=data.get("reasoning_effort"),
            default_capability_mode=data.get("default_capability_mode", "all"),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
        )


@dataclass
class RoleDefinition:
    name: str
    description: str
    default_capability_mode: str = "read-only"
    reasoning_effort: str | None = None
    default_fork_context: bool = True

    @classmethod
    def from_toml(cls, path: Path) -> "RoleDefinition":
        data = tomllib.loads(path.read_text())
        return cls(
            name=path.stem,
            description=data.get("description", ""),
            default_capability_mode=data.get("default_capability_mode", "read-only"),
            reasoning_effort=data.get("reasoning_effort"),
            default_fork_context=data.get("default_fork_context", True),
        )


# ── Bundled resource loaders ────────────────────────────────────────────────

def _bundled_dir() -> Path:
    return Path(__file__).parent


def load_agent(name: str) -> AgentDefinition:
    path = _bundled_dir() / "definitions" / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Agent not found: {name} (looked in {path})")
    return AgentDefinition.from_markdown(path)


def load_persona(name: str) -> PersonaDefinition:
    path = _bundled_dir() / "personas" / f"{name}.toml"
    if not path.exists():
        raise FileNotFoundError(f"Persona not found: {name}")
    return PersonaDefinition.from_toml(path)


def load_role(name: str) -> RoleDefinition:
    path = _bundled_dir() / "roles" / f"{name}.toml"
    if not path.exists():
        raise FileNotFoundError(f"Role not found: {name}")
    return RoleDefinition.from_toml(path)


def list_agents() -> list[str]:
    d = _bundled_dir() / "definitions"
    return sorted([p.stem for p in d.glob("*.md")])


def list_personas() -> list[str]:
    d = _bundled_dir() / "personas"
    return sorted([p.stem for p in d.glob("*.toml")])


def list_roles() -> list[str]:
    d = _bundled_dir() / "roles"
    return sorted([p.stem for p in d.glob("*.toml")])


# ── Tool schemas (for OpenAI-compatible function calling) ────────────────────

SHELL_TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Execute a shell command and return its output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run."},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)."},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its contents with line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "offset": {"type": "integer", "description": "Line offset (0-based)."},
                    "limit": {"type": "integer", "description": "Max lines to return."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates parent directories as needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "content": {"type": "string", "description": "Content to write."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search for a regex pattern in source files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern to search."},
                    "path": {"type": "string", "description": "Directory or file to search (default: workspace)."},
                    "file_types": {"type": "string", "description": "Comma-separated extensions (default: py,js,ts,tsx,md,toml,json,yaml,yml)."},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List directory contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path."},
                },
                "required": ["path"],
            },
        },
    },
]


# ── Agent Runner ─────────────────────────────────────────────────────────────

EventHook = Callable[[str, str, str], None]


class AgentRunner:
    """Runs an agent with a given persona and model, handling tool calls.

    This is the core execution engine — it loads an AgentDefinition,
    injects a PersonaDefinition for behaviour, and runs the tool-use
    loop against the LLM provider.
    """

    def __init__(
        self,
        agent_name: str = "general-purpose",
        persona_name: str | None = None,
        role_name: str | None = None,
        model_id: str | None = None,
        config: FraktalConfig | None = None,
        cwd: Path | None = None,
        on_event: EventHook | None = None,
    ):
        self.config = config or FraktalConfig.load()
        self.cwd = cwd or self.config.workspace
        self.on_event = on_event

        self.agent = load_agent(agent_name)
        self.persona = load_persona(persona_name) if persona_name else None
        self.role = load_role(role_name) if role_name else None

        # Model resolution
        model_id = model_id or self.config.model
        self.provider = create_provider(self.config, model=model_id)
        self.model_id = model_id

        # Build system prompt
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        parts: list[str] = []
        if self.persona:
            parts.append(self.persona.instructions)
        elif self.role:
            parts.append(f"You are a {self.role.description}.")
        parts.append(self.agent.body)

        if self.agent.permission_mode == "plan":
            parts.append(
                "\n=== READ-ONLY MODE ===\n"
                "You have NO file editing tools. Do not create, modify, or delete files.\n"
                "Use run_shell only for read-only commands (ls, git status, git log, git diff, find, cat, head, tail)."
            )

        parts.append(f"\nWorkspace: {self.cwd}")
        return "\n\n".join(parts)

    def _execute_tool(self, name: str, args: dict) -> str:
        """Execute a tool call and return the result string."""
        if name == "run_shell":
            timeout = args.get("timeout", 60)
            try:
                result = subprocess.run(
                    args["command"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(self.cwd),
                )
                out = result.stdout
                if result.stderr:
                    out += f"\n[stderr]\n{result.stderr}"
                if result.returncode != 0:
                    out += f"\n[exit code: {result.returncode}]"
                return out[:10000]
            except subprocess.TimeoutExpired:
                return f"Command timed out after {timeout}s"
            except Exception as e:
                return f"Error: {e}"

        elif name == "read_file":
            try:
                p = Path(args["path"])
                if not p.is_absolute():
                    p = self.cwd / p
                content = p.read_text()
                lines = content.split("\n")
                offset = int(args.get("offset", 0))
                limit = int(args.get("limit", len(lines)))
                selected = lines[offset : offset + limit]
                return "\n".join(f"{i + offset + 1:4}→{line}" for i, line in enumerate(selected))
            except Exception as e:
                return f"Error reading file: {e}"

        elif name == "write_file":
            try:
                p = Path(args["path"])
                if not p.is_absolute():
                    p = self.cwd / p
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(args["content"])
                return f"Wrote {len(args['content'])} bytes to {p}"
            except Exception as e:
                return f"Error writing file: {e}"

        elif name == "search_code":
            try:
                pattern = args["pattern"]
                search_path = self.cwd / args.get("path", ".")
                file_types = args.get("file_types", "py,js,ts,tsx,md,toml,json,yaml,yml")
                includes = []
                for ext in file_types.split(","):
                    includes.extend(["--include", f"*.{ext.strip()}"])
                result = subprocess.run(
                    ["grep", "-rn", *includes, pattern, str(search_path)],
                    capture_output=True, text=True, timeout=30, cwd=str(self.cwd),
                )
                return result.stdout[:8000] or "No matches found."
            except Exception as e:
                return f"Error searching: {e}"

        elif name == "list_dir":
            try:
                p = Path(args["path"])
                if not p.is_absolute():
                    p = self.cwd / p
                items = []
                for child in sorted(p.iterdir()):
                    suffix = "/" if child.is_dir() else f"  ({child.stat().st_size} bytes)"
                    items.append(f"  {child.name}{suffix}")
                return "\n".join(items) or "(empty)"
            except Exception as e:
                return f"Error listing directory: {e}"

        return f"Unknown tool: {name}"

    def run(self, prompt: str, max_turns: int = 30) -> dict[str, Any]:
        """Run the agent loop. Returns final summary dict."""
        messages: list[Message] = [Message(role="user", content=prompt)]
        turn = 0
        tool_calls_made = 0
        last_content = ""

        while turn < max_turns:
            turn += 1

            if self.on_event:
                self.on_event(self.agent.name, "think", f"turn {turn}/{max_turns}")

            resp = self.provider.chat(
                messages=messages,
                system=self.system_prompt,
                tools=[
                    ToolSpec(
                        name=t["function"]["name"],
                        description=t["function"]["description"],
                        parameters=t["function"]["parameters"],
                    )
                    for t in SHELL_TOOLS_SCHEMA
                ] if self.agent.permission_mode != "plan" else None,
                temperature=0.3,
            )

            if resp.content:
                last_content = resp.content
                messages.append(Message(role="assistant", content=resp.content))

            if resp.tool_calls:
                for tc in resp.tool_calls:
                    tool_calls_made += 1
                    if self.on_event:
                        self.on_event(self.agent.name, "tool", tc.name)
                    result = self._execute_tool(tc.name, tc.arguments)
                    messages.append(Message(
                        role="tool",
                        content=result,
                        tool_call_id=tc.id,
                    ))
                continue  # loop for tool results

            # No tool calls — agent is done
            break

        return {
            "turns": turn,
            "tool_calls": tool_calls_made,
            "final_message": last_content or "(no content)",
            "finish_reason": resp.finish_reason if resp else "stop",
            "usage": resp.usage if resp else None,
        }
