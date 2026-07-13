"""Abstract Agent base class — the core agent loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from fraktal.llm.base import LLMProvider, LLMResponse, Message, ToolCall, ToolSpec
from fraktal.tools.base import Tool, ToolRegistry, ToolResult


EventHook = Callable[[str, str, str], None]


@dataclass
class AgentResult:
    success: bool
    output: str
    iterations: int
    tool_calls: int = 0
    usage: dict[str, int] | None = None


class Agent:
    """Abstract agent: a system prompt + tools + LLM provider.

    Subclasses define the system prompt, tools, and any pre/post processing.
    The `run()` method executes the tool-use loop.
    """

    name: str = "agent"

    def __init__(
        self,
        provider: LLMProvider,
        system_prompt: str,
        tools: ToolRegistry | None = None,
        max_iterations: int = 40,
        on_event: EventHook | None = None,
    ):
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools or ToolRegistry()
        self.max_iterations = max_iterations
        self.on_event = on_event

    def _tools_as_specs(self) -> list[ToolSpec]:
        specs: list[ToolSpec] = []
        for tool in self.tools.list_tools():
            specs.append(ToolSpec(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
            ))
        return specs

    def _execute_tool(self, name: str, args: dict) -> str:
        tool = self.tools.get(name)
        if tool is None:
            return f"Unknown tool: {name}"
        try:
            result = tool.execute(**args)
            return result.output
        except Exception as e:
            return f"Tool error ({name}): {e}"

    def run(self, task: str, context: str | None = None) -> AgentResult:
        """Execute the agent loop on a task. Returns AgentResult."""
        user_message = task
        if context:
            user_message = f"{context}\n\n---\n\n{task}"

        messages: list[Message] = [Message(role="user", content=user_message)]
        iterations = 0
        tool_calls_made = 0
        last_content = ""
        last_usage = None

        while iterations < self.max_iterations:
            iterations += 1

            if self.on_event:
                self.on_event(self.name, "think", f"iteration {iterations}/{self.max_iterations}")

            resp = self.provider.chat(
                messages=messages,
                system=self.system_prompt,
                tools=self._tools_as_specs() or None,
                temperature=0.3,
            )
            last_usage = resp.usage

            if resp.content:
                last_content = resp.content
                messages.append(Message(role="assistant", content=resp.content))

            if resp.tool_calls:
                for tc in resp.tool_calls:
                    tool_calls_made += 1
                    if self.on_event:
                        self.on_event(self.name, "tool", tc.name)
                    result = self._execute_tool(tc.name, tc.arguments)
                    messages.append(Message(
                        role="tool",
                        content=result,
                        tool_call_id=tc.id,
                    ))
                continue

            # No tool calls — agent finished
            break

        success = iterations < self.max_iterations or bool(last_content)
        return AgentResult(
            success=success,
            output=last_content or "(no output)",
            iterations=iterations,
            tool_calls=tool_calls_made,
            usage=last_usage,
        )
