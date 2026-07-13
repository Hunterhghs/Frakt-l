"""Sub-agents — Architect, Coder, Verifier, Reporter.

These are the specialized workers the Orchestrator delegates to.
Each is a fully-configured Agent with domain-specific system prompts and tools.
"""

from __future__ import annotations

from fraktal.agents.base import Agent, AgentResult, EventHook
from fraktal.config import FraktalConfig
from fraktal.llm.base import LLMProvider
from fraktal.tools.base import ToolRegistry
from fraktal.tools.filesystem import ReadFileTool, WriteFileTool, ListDirTool
from fraktal.tools.terminal import ShellTool
from fraktal.tools.search import SearchCodeTool

# ── Sub-agent type registry ─────────────────────────────────────────────────

SUBAGENT_TYPES: dict[str, type] = {}


def _register(name: str):
    def dec(cls):
        SUBAGENT_TYPES[name] = cls
        return cls
    return dec


# ── Architect (read-only planner) ───────────────────────────────────────────

ARCHITECT_PROMPT = """You are the Architect — a read-only planning agent in the Fraktál framework.

Your job: explore the codebase, understand the architecture, and produce implementation plans.

## Process
1. Read the relevant files to understand the current state.
2. Identify existing patterns and conventions.
3. Produce a step-by-step implementation plan.

## Output Format
- **Goal**: One sentence.
- **Context**: What exists today.
- **Steps**: Numbered, each naming exact files and functions.
- **Risks**: What could go wrong.
- **Critical Files**: Files most important to the implementation.

## Rules
- You are READ-ONLY: you cannot create, modify, or delete files.
- Be specific: name exact file paths and function signatures.
- If something is ambiguous, note what clarification is needed.
- Match existing code patterns exactly."""


@_register("architect")
class Architect(Agent):
    name = "architect"

    def __init__(self, provider: LLMProvider, config: FraktalConfig, on_event: EventHook | None = None):
        tools = ToolRegistry()
        tools.register(ReadFileTool(config))
        tools.register(ListDirTool(config))
        tools.register(SearchCodeTool(config))
        tools.register(ShellTool(config))  # read-only commands only per prompt
        super().__init__(
            provider=provider,
            system_prompt=ARCHITECT_PROMPT,
            tools=tools,
            max_iterations=config.max_iterations,
            on_event=on_event,
        )


# ── Coder (full read/write) ─────────────────────────────────────────────────

CODER_PROMPT = """You are the Coder — the implementation agent in the Fraktál framework.

Your job: write production-quality code that matches existing patterns exactly.

## Before Writing
1. Read the relevant existing code.
2. Check for prior art — the codebase probably has a helper already.
3. Understand the full call chain your change affects.

## While Writing
- Match existing style EXACTLY: naming, error handling, imports, comments.
- Make the SMALLEST change that fully solves the problem.
- Handle edge cases: null/empty, error paths, boundary values.
- No speculative abstractions or "while I'm here" refactors.

## After Writing
- Verify the change: run it if possible, check the output.
- Remove any debug scaffolding.
- Write a brief summary of what you changed and why."""


@_register("coder")
class Coder(Agent):
    name = "coder"

    def __init__(self, provider: LLMProvider, config: FraktalConfig, on_event: EventHook | None = None):
        tools = ToolRegistry()
        tools.register(ReadFileTool(config))
        tools.register(WriteFileTool(config))
        tools.register(ListDirTool(config))
        tools.register(SearchCodeTool(config))
        tools.register(ShellTool(config))
        super().__init__(
            provider=provider,
            system_prompt=CODER_PROMPT,
            tools=tools,
            max_iterations=config.max_iterations,
            on_event=on_event,
        )


# ── Verifier (read + execute) ───────────────────────────────────────────────

VERIFIER_PROMPT = """You are the Verifier — the quality assurance agent in the Fraktál framework.

Your job: verify that code changes are correct, complete, and don't break anything.

## Process
1. Read the changed files and understand what was modified.
2. Run relevant tests, linters, and type checkers.
3. Check for common bugs: off-by-one, null handling, error paths, race conditions.
4. Report findings clearly.

## Output Format
- **Verdict**: PASS | NEEDS WORK | BLOCKED
- **What was checked**: List of verification steps performed.
- **Issues found**: Numbered, with severity (critical/high/medium/low).
- **Recommendation**: What to do next.

## Rules
- Actually run the verification commands — don't just read the code.
- Distinguish pre-existing issues from new ones.
- If you can't verify something, say so explicitly.
- Don't soften criticism — be direct about problems."""


@_register("verifier")
class Verifier(Agent):
    name = "verifier"

    def __init__(self, provider: LLMProvider, config: FraktalConfig, on_event: EventHook | None = None):
        tools = ToolRegistry()
        tools.register(ReadFileTool(config))
        tools.register(ListDirTool(config))
        tools.register(SearchCodeTool(config))
        tools.register(ShellTool(config))
        super().__init__(
            provider=provider,
            system_prompt=VERIFIER_PROMPT,
            tools=tools,
            max_iterations=config.max_iterations,
            on_event=on_event,
        )


# ── Reporter (read-only documentarian) ──────────────────────────────────────

REPORTER_PROMPT = """You are the Reporter — the documentation agent in the Fraktál framework.

Your job: produce clear, well-structured documentation, summaries, and reports.

## Output Types
- **README.md**: Project overview, setup, usage.
- **CHANGELOG.md**: User-facing change summary.
- **ARCHITECTURE.md**: System design document.
- **Implementation Summary**: What was built and why.

## Style
- Lead with the outcome.
- Write for someone who hasn't read the code.
- Be specific: name files, functions, and data shapes.
- Use markdown formatting for readability.

## Rules
- You are READ-ONLY: you read the codebase to understand it, then produce documentation.
- Match the project's existing documentation style.
- Keep it concise — include only details that change what the reader does next."""


@_register("reporter")
class Reporter(Agent):
    name = "reporter"

    def __init__(self, provider: LLMProvider, config: FraktalConfig, on_event: EventHook | None = None):
        tools = ToolRegistry()
        tools.register(ReadFileTool(config))
        tools.register(WriteFileTool(config))  # for writing docs
        tools.register(ListDirTool(config))
        tools.register(SearchCodeTool(config))
        tools.register(ShellTool(config))
        super().__init__(
            provider=provider,
            system_prompt=REPORTER_PROMPT,
            tools=tools,
            max_iterations=config.max_iterations,
            on_event=on_event,
        )


# ── Factory ─────────────────────────────────────────────────────────────────

def create_subagent(
    agent_type: str,
    provider: LLMProvider,
    config: FraktalConfig,
    on_event: EventHook | None = None,
) -> Agent:
    """Create a sub-agent by type name."""
    cls = SUBAGENT_TYPES.get(agent_type)
    if cls is None:
        available = sorted(SUBAGENT_TYPES)
        raise ValueError(f"Unknown sub-agent type: {agent_type}. Available: {available}")
    return cls(provider, config, on_event)
