"""Orchestrator — the top-level Fraktál agent.

The Orchestrator plans tasks and delegates to specialized sub-agents
(Architect, Coder, Verifier, Reporter). It never edits files directly —
all real work flows through sub-agents.

Tools available to the Orchestrator:
- delegate: spawn a sub-agent on an objective
- playbook: fetch domain guidance for a deliverable type
- remember / recall: persistent memory across sessions
"""

from __future__ import annotations

from typing import Any

from fraktal.agents.base import Agent, AgentResult, EventHook
from fraktal.agents.subagents import SUBAGENT_TYPES, create_subagent
from fraktal.config import FraktalConfig
from fraktal.llm.base import LLMProvider
from fraktal.llm.registry import create_provider
from fraktal.tools.base import Tool, ToolRegistry, ToolResult


# ── Orchestrator System Prompt ──────────────────────────────────────────────

ORCHESTRATOR_PROMPT = """You are the Fraktál Orchestrator — the top-level AI coding agent in the
Fraktál framework (Fable 5 × Grok 4.5 hybrid, powered by DeepSeek).

## Your Role
Plan complex tasks and delegate execution to specialized sub-agents.
You never edit files directly — you delegate to the Coder for implementation,
the Architect for planning, the Verifier for quality checks, and the
Reporter for documentation.

## Available Sub-Agents
- **architect**: Read-only codebase exploration → step-by-step implementation plan.
- **coder**: Full read/write — implements features and fixes bugs.
- **verifier**: Read + execute — runs tests, lints, checks for correctness.
- **reporter**: Read + write docs — produces READMEs, summaries, reports.

## Workflow
1. **Understand** the task and check memory for relevant context.
2. **Plan**: delegate to the architect for a plan if the task is complex.
3. **Implement**: delegate implementation steps to the coder.
4. **Verify**: delegate verification to the verifier.
5. **Report**: summarize results. Remember key decisions for future sessions.

## Rules
- Delegate one self-contained objective at a time.
- Include all necessary context in the delegation objective.
- Verify after implementation before declaring success.
- Use the playbook tool for domain-specific guidance (dashboards, reports, websites).
- Be thorough but efficient — don't over-plan simple tasks."""


# ── Orchestrator Tools ──────────────────────────────────────────────────────

class DelegateTool(Tool):
    """Spawn a sub-agent on a self-contained objective."""

    name = "delegate"
    description = (
        "Delegate a self-contained objective to a specialized sub-agent and "
        "get its final report back. Sub-agents do not share your conversation "
        "history, so include ALL necessary context in the objective."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "agent": {
                "type": "string",
                "enum": sorted(SUBAGENT_TYPES),
                "description": "Which sub-agent: architect (plan), coder (implement), verifier (check), reporter (document).",
            },
            "objective": {
                "type": "string",
                "description": "Complete, self-contained objective with all needed context.",
            },
        },
        "required": ["agent", "objective"],
    }

    def __init__(
        self,
        provider: LLMProvider,
        config: FraktalConfig,
        on_event: EventHook | None = None,
        max_delegations: int = 12,
    ):
        self.provider = provider
        self.config = config
        self.on_event = on_event
        self.max_delegations = max_delegations
        self.delegations = 0

    def execute(self, agent: str, objective: str) -> ToolResult:
        if self.delegations >= self.max_delegations:
            return ToolResult(
                output=f"Delegation budget exhausted ({self.max_delegations}). Summarize and finish.",
                success=False,
            )
        self.delegations += 1

        if self.on_event:
            self.on_event("orchestrator", "delegate", f"{agent}: {objective[:80]}...")

        sub = create_subagent(agent, self.provider, self.config, self.on_event)
        result = sub.run(objective)

        status = "completed" if result.success else "stopped early"
        return ToolResult(
            output=f"[{agent} {status} after {result.iterations} iteration(s)]\n\n{result.output}",
            success=result.success,
        )


class PlaybookTool(Tool):
    """Fetch domain guidance for a deliverable type."""

    name = "playbook"
    description = (
        "Fetch Fraktál's playbook for a type of deliverable: standards, "
        "structure, and quality gates. Consult before delegating work on "
        "dashboards, reports, websites, research, or data analysis."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Deliverable type: dashboard, report, website, dataset, research, presentation, infographic.",
            },
        },
        "required": ["topic"],
    }

    def execute(self, topic: str) -> ToolResult:
        from fraktal.playbooks import load_playbook
        return ToolResult(output=load_playbook(topic))


class RememberTool(Tool):
    """Save a fact to long-term memory."""

    name = "remember"
    description = "Save an important fact, decision, or task summary to long-term memory."

    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "What to remember."},
            "category": {
                "type": "string",
                "description": "note, decision, task, or project-fact. Default: note.",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional tags.",
            },
        },
        "required": ["content"],
    }

    def __init__(self, memory) -> None:
        self.memory = memory

    def execute(self, content: str, category: str = "note", tags: list | None = None) -> ToolResult:
        entry_id = self.memory.remember(content, category=category, tags=tags or [])
        return ToolResult(output=f"Remembered (id={entry_id}).")


class RecallTool(Tool):
    """Search long-term memory."""

    name = "recall"
    description = "Search long-term memory for facts and decisions from previous sessions."

    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Keywords to search for."},
            "limit": {"type": "integer", "description": "Max results (default 5)."},
        },
        "required": ["query"],
    }

    def __init__(self, memory) -> None:
        self.memory = memory

    def execute(self, query: str, limit: int = 5) -> ToolResult:
        entries = self.memory.search(query, limit=limit)
        if not entries:
            return ToolResult(output="No matching memories.")
        lines = [f"- [{e.category}] {e.content} (id={e.id})" for e in entries]
        return ToolResult(output="\n".join(lines))


# ── Orchestrator ────────────────────────────────────────────────────────────

class Orchestrator(Agent):
    """Top-level Fraktál agent: plan, delegate, verify, remember."""

    name = "orchestrator"

    def __init__(
        self,
        config: FraktalConfig | None = None,
        provider: LLMProvider | None = None,
        on_event: EventHook | None = None,
    ):
        self.config = config or FraktalConfig.load()
        provider = provider or create_provider(self.config)

        # Memory
        from fraktal.memory import create_memory
        self.memory = create_memory(self.config.memory_backend, self.config.memory_path)

        # Build tool registry
        tools = ToolRegistry()
        tools.register(DelegateTool(
            provider, self.config, on_event,
            max_delegations=self.config.max_delegations,
        ))
        tools.register(PlaybookTool())
        tools.register(RememberTool(self.memory))
        tools.register(RecallTool(self.memory))

        super().__init__(
            provider=provider,
            system_prompt=ORCHESTRATOR_PROMPT,
            tools=tools,
            max_iterations=self.config.max_iterations,
            on_event=on_event,
        )

    def run_task(self, task: str) -> AgentResult:
        """Run a task with recent memory injected as context."""
        recent = self.memory.recent(limit=5)
        context = None
        if recent:
            context = "Relevant memory from previous sessions:\n" + "\n".join(
                f"- [{e.category}] {e.content}" for e in recent
            )

        if self.on_event:
            self.on_event("orchestrator", "start", task[:120])

        result = self.run(task, context=context)

        if result.success:
            summary = result.output[:500]
            self.memory.remember(
                f"Task: {task[:200]} — Outcome: {summary}",
                category="task",
            )

        if self.on_event:
            self.on_event("orchestrator", "finish", "success" if result.success else "incomplete")

        return result
