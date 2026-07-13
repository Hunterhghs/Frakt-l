"""Fraktál CLI — unified command-line interface.

Usage:
    fraktal build "Add rate limiting to the API"     # Full pipeline
    fraktal plan "Design a caching layer"            # Read-only exploration
    fraktal design "Rate limiting middleware"         # Design doc loop
    fraktal implement "Add JWT refresh"               # Code → review → fix
    fraktal review [target]                           # Review changes
    fraktal run "Find all TODOs"                      # Single agent run
    fraktal mcp --workspace .                         # MCP server
    fraktal health                                    # API check
    fraktal setup                                     # Init config
    fraktal agents|personas|skills|playbooks|prompts  # List resources
    fraktal memory search|recent                      # Inspect memory
    fraktal tools --workspace .                       # List tools
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from fraktal import __version__
from fraktal.config import BUILTIN_MODELS, FraktalConfig, get_model_info
from fraktal.llm.registry import create_provider
from fraktal.agents import (
    AgentRunner,
    list_agents,
    list_personas,
    list_roles,
)
from fraktal.agents.orchestrator import Orchestrator
from fraktal.playbooks import list_playbooks, load_playbook
from fraktal.prompts import AGENT_ROLES, load_prompt
from fraktal.tools.base import default_registry

console = Console()


# ── Helpers ─────────────────────────────────────────────────────────────────

def _load_config(
    workspace: str | None = None,
    model: str | None = None,
    provider: str | None = None,
) -> FraktalConfig:
    """Load config with CLI overrides."""
    overrides = {}
    if model:
        overrides["model"] = model
    if provider:
        overrides["provider"] = provider
    return FraktalConfig.load(workspace=workspace, **overrides)


def _get_model_id(ctx: click.Context) -> str | None:
    """Extract model from Click context chain."""
    # Walk up through parent contexts
    current = ctx
    while current is not None:
        obj = current.ensure_object(dict)
        if obj.get("model"):
            return obj["model"]
        current = current.parent
    return None


# ── CLI Group ───────────────────────────────────────────────────────────────

@click.group()
@click.version_option(__version__, prog_name="fraktal")
@click.option("--model", "-m", default=None, help="Model to use (deepseek-chat, deepseek-reasoner, grok-4.5).")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output.")
@click.pass_context
def main(ctx, model, verbose):
    """Fraktál — Fable 5 × Grok 4.5 Hybrid AI Coding Agent.

    High-performance multi-agent orchestration powered by DeepSeek API.
    Combines Fable 5 reasoning with Grok Build pipeline for specialized outputs.

    \b
    Quick start:
      fraktal setup               # Initialize config
      fraktal health              # Check API connectivity
      fraktal build "your task"   # Full pipeline: plan → design → implement → review
    """
    ctx.ensure_object(dict)
    ctx.obj["model"] = model
    ctx.obj["verbose"] = verbose


# ── Setup ───────────────────────────────────────────────────────────────────

@main.command()
def setup():
    """Initialize Fraktál configuration."""
    config_dir = Path.home() / ".fraktal"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / "config.toml"
    if not config_path.exists():
        config_path.write_text(
            "[fraktal]\n"
            'provider = "deepseek"\n'
            'model = "deepseek-chat"\n'
            'reasoning_model = "deepseek-reasoner"\n'
        )

    console.print(Panel.fit(
        "[bold green]✓[/] Fraktál initialized!\n\n"
        "Set your DeepSeek API key:\n"
        "  [bold]export DEEPSEEK_API_KEY='sk-your-key-here'[/]\n\n"
        "Quick test:\n"
        "  [bold]fraktal health[/]\n\n"
        f"Config: {config_path}\n"
        f"Models: {', '.join(BUILTIN_MODELS)}",
        title="Fraktál Setup",
        border_style="green",
    ))


# ── Health ──────────────────────────────────────────────────────────────────

@main.command()
@click.argument("model_id", required=False)
@click.pass_context
def health(ctx, model_id: Optional[str] = None):
    """Check API connectivity and model health."""
    model_id = model_id or _get_model_id(ctx) or "deepseek-chat"
    info = get_model_info(model_id)
    cfg = _load_config(model=model_id)

    console.print(f"Checking [bold cyan]{info.name}[/] ({info.model})...")

    try:
        provider = create_provider(cfg, model=model_id)
        result = provider.check_connection()
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/]")
        sys.exit(1)

    if result["ok"]:
        console.print(f"[green]✓[/] Connected to [bold]{result.get('model', info.name)}[/] "
                      f"in {result['latency_ms']}ms")
        if result.get("usage"):
            console.print(f"  Tokens used: {result['usage']}")
    else:
        console.print(f"[red]✗ Failed: {result.get('error', 'Unknown error')}[/]")


# ── Models ──────────────────────────────────────────────────────────────────

@main.command()
def models():
    """List available models."""
    table = Table(title="Available Models")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Context", justify="right")
    table.add_column("Reasoning", justify="center")
    table.add_column("Description")

    for mid, info in BUILTIN_MODELS.items():
        reasoning = "✓" if info.supports_reasoning_effort else "—"
        table.add_row(
            mid, info.name, f"{info.context_window:,}", reasoning,
            info.description[:80],
        )

    console.print(table)


# ── Agents, Personas, Roles ─────────────────────────────────────────────────

@main.command()
def agents():
    """List available agents."""
    table = Table(title="Available Agents")
    table.add_column("Name", style="bold cyan")
    table.add_column("Permission", style="yellow")
    table.add_column("Description")

    for name in list_agents():
        from fraktal.agents import load_agent
        agent = load_agent(name)
        table.add_row(agent.name, agent.permission_mode, agent.description[:100])

    console.print(table)


@main.command()
def personas():
    """List available personas."""
    table = Table(title="Available Personas")
    table.add_column("Name", style="bold green")
    table.add_column("Capability", style="yellow")
    table.add_column("Description")

    for name in list_personas():
        from fraktal.agents import load_persona
        persona = load_persona(name)
        table.add_row(persona.name, persona.default_capability_mode, persona.description[:100])

    console.print(table)


@main.command()
def roles():
    """List available roles."""
    table = Table(title="Available Roles")
    table.add_column("Name", style="bold magenta")
    table.add_column("Capability", style="yellow")
    table.add_column("Description")

    for name in list_roles():
        from fraktal.agents import load_role
        role = load_role(name)
        table.add_row(role.name, role.default_capability_mode, role.description[:100])

    console.print(table)


# ── Skills ──────────────────────────────────────────────────────────────────

@main.command()
def skills():
    """List available skill pipelines."""
    skills_dir = Path(__file__).parent / "skills"
    table = Table(title="Available Skills")
    table.add_column("Name", style="bold blue")
    table.add_column("Description")

    for skill_dir in sorted(skills_dir.iterdir()):
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                desc = ""
                for line in skill_md.read_text().split("\n"):
                    if line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip()
                        break
                table.add_row(skill_dir.name, desc[:100])

    console.print(table)


# ── Playbooks ───────────────────────────────────────────────────────────────

@main.command()
@click.argument("topic", required=False)
def playbooks(topic: Optional[str] = None):
    """List playbooks or show a specific one."""
    if topic:
        console.print(Panel(
            Markdown(load_playbook(topic)),
            title=f"Playbook: {topic}",
            border_style="green",
        ))
    else:
        table = Table(title="Domain Playbooks")
        table.add_column("Topic", style="bold green")
        for t in list_playbooks():
            table.add_row(t)
        console.print(table)
        console.print("\n[dim]Use: fraktal playbooks <topic> to view a specific playbook.[/]")


# ── Prompts ─────────────────────────────────────────────────────────────────

@main.command()
@click.argument("role", required=False)
def prompts(role: Optional[str] = None):
    """List roles or show a specific system prompt."""
    if role:
        if role not in AGENT_ROLES:
            console.print(f"[red]Unknown role: {role}[/]")
            console.print(f"Available: {', '.join(AGENT_ROLES)}")
            sys.exit(1)
        console.print(Panel(
            load_prompt(role),
            title=f"Prompt: {role}",
            border_style="yellow",
        ))
    else:
        table = Table(title="System Prompts")
        table.add_column("Role", style="bold yellow")
        for r in AGENT_ROLES:
            table.add_row(r)
        console.print(table)
        console.print("\n[dim]Use: fraktal prompts <role> to view a specific prompt.[/]")


# ── Tools ───────────────────────────────────────────────────────────────────

@main.command()
@click.option("--workspace", "-w", default=".", help="Workspace directory.")
def tools(workspace: str):
    """List available tools and their schemas."""
    registry = default_registry(Path(workspace).resolve())
    for spec in registry.specs():
        func = spec["function"]
        params = ", ".join(func.get("parameters", {}).get("properties", {}))
        console.print(f"[bold]{func['name']}[/]({params})")
        console.print(f"    {func['description']}\n")


# ── Memory ──────────────────────────────────────────────────────────────────

@main.group()
def memory():
    """Inspect long-term memory."""


@memory.command()
@click.option("--workspace", "-w", default=".", help="Workspace directory.")
@click.option("--limit", "-n", default=10, help="Max entries.")
def recent(workspace: str, limit: int):
    """Show recent memory entries."""
    from fraktal.memory import create_memory
    cfg = _load_config(workspace=workspace)
    mem = create_memory(cfg.memory_backend, cfg.memory_path)
    entries = mem.recent(limit=limit)
    if not entries:
        console.print("(no memories)")
        return
    for e in entries:
        console.print(f"[dim]{e.timestamp:.0f}[/] [{e.category}] {e.content[:120]}  [dim](id={e.id})[/]")


@memory.command()
@click.argument("query", required=True)
@click.option("--workspace", "-w", default=".", help="Workspace directory.")
@click.option("--limit", "-n", default=10, help="Max entries.")
def search(query: str, workspace: str, limit: int):
    """Search memory for a query."""
    from fraktal.memory import create_memory
    cfg = _load_config(workspace=workspace)
    mem = create_memory(cfg.memory_backend, cfg.memory_path)
    entries = mem.search(query, limit=limit)
    if not entries:
        console.print(f"No memories matching '[bold]{query}[/]'.")
        return
    for e in entries:
        console.print(f"[dim]{e.timestamp:.0f}[/] [{e.category}] {e.content[:120]}  [dim](id={e.id})[/]")


# ── Run ─────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("prompt", required=True)
@click.option("--agent", "-a", default="general-purpose", help="Agent to use.")
@click.option("--persona", "-p", default=None, help="Persona to inject.")
@click.option("--role", "-r", default=None, help="Role to apply.")
@click.option("--max-turns", default=30, help="Max conversation turns.")
@click.option("--workspace", "-w", default=".", help="Workspace directory.")
@click.pass_context
def run(ctx, prompt, agent, persona, role, max_turns, workspace):
    """Run a single agent with an optional persona."""
    model = _get_model_id(ctx)
    cfg = _load_config(workspace=workspace, model=model)
    runner = AgentRunner(
        agent_name=agent,
        persona_name=persona,
        role_name=role,
        model_id=model or cfg.model,
        config=cfg,
        cwd=cfg.workspace,
    )

    label = f"[bold]{agent}[/]"
    if persona:
        label += f" as [bold]{persona}[/]"
    console.print(f"[dim]Running {label}...[/]")

    result = runner.run(prompt, max_turns=max_turns)
    console.print(Markdown(result["final_message"]))
    console.print(f"\n[dim]{result['turns']} turns, {result['tool_calls']} tool calls[/]")


# ── Plan ────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("description", required=True)
@click.option("--workspace", "-w", default=".", help="Workspace directory.")
@click.pass_context
def plan(ctx, description, workspace):
    """Design an implementation plan (read-only exploration)."""
    model = _get_model_id(ctx)
    cfg = _load_config(workspace=workspace, model=model)
    orch = Orchestrator(config=cfg)

    console.print(f"[bold blue]Plan Skill[/]: {description}")
    result = orch.run_task(f"Design an implementation plan for: {description}")

    console.print(Panel(
        Markdown(result.output[:1500] + ("..." if len(result.output) > 1500 else "")),
        title="Implementation Plan",
        border_style="blue",
    ))
    console.print(f"[dim]{result.iterations} iterations, {result.tool_calls} tool calls[/]")


# ── Design ──────────────────────────────────────────────────────────────────

@main.command()
@click.argument("description", required=True)
@click.option("--output", "-o", default=None, help="Output directory.")
@click.option("--workspace", "-w", default=".", help="Workspace directory.")
@click.pass_context
def design(ctx, description, output, workspace):
    """Run the design skill (write → review → revise loop)."""
    model = _get_model_id(ctx)
    cfg = _load_config(workspace=workspace, model=model)
    out_dir = Path(output) if output else cfg.workspace
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold blue]Design Skill[/]: {description}")

    orch = Orchestrator(config=cfg)
    design_prompt = f"""Run the design skill for: {description}

Output the design document to: {out_dir / 'DESIGN.md'}
Write a summary to: {out_dir / 'DESIGN_SUMMARY.md'}

Follow the design-doc-writer persona. Be thorough and specific.
Include file paths, function names, and code snippets where relevant.
After writing, self-review for completeness, feasibility, and risk."""

    result = orch.run_task(design_prompt)
    console.print(f"[green]✓[/] Design complete after {result.iterations} iterations")
    for artifact in [out_dir / "DESIGN.md", out_dir / "DESIGN_SUMMARY.md"]:
        if artifact.exists():
            console.print(f"  [dim]{artifact}[/]")


# ── Implement ───────────────────────────────────────────────────────────────

@main.command()
@click.argument("description", required=True)
@click.option("--effort", "-e", type=click.Choice(["low", "medium", "high"]), default="medium",
              help="Review thoroughness.")
@click.option("--output", "-o", default=None, help="Output directory.")
@click.option("--workspace", "-w", default=".", help="Workspace directory.")
@click.pass_context
def implement(ctx, description, effort, output, workspace):
    """Run the implement skill (code → review → fix loop)."""
    model = _get_model_id(ctx)
    cfg = _load_config(workspace=workspace, model=model)
    out_dir = Path(output) if output else cfg.workspace
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold green]Implement Skill[/] ({effort} effort): {description}")

    orch = Orchestrator(config=cfg)
    impl_prompt = f"""Implement the following with {effort} effort: {description}

Write a summary of what you implemented to: {out_dir / 'IMPLEMENT_SUMMARY.md'}

Rules:
- Read existing code before writing.
- Follow existing patterns exactly.
- Make the smallest change that solves the problem.
- Don't add features that weren't asked for.
- After implementing, review your own changes for issues."""

    result = orch.run_task(impl_prompt)
    console.print(f"[green]✓[/] Implementation complete after {result.iterations} iterations")
    for artifact in [out_dir / "IMPLEMENT_SUMMARY.md"]:
        if artifact.exists():
            console.print(f"  [dim]{artifact}[/]")


# ── Review ──────────────────────────────────────────────────────────────────

@main.command()
@click.argument("target", required=False, default="local")
@click.option("--workspace", "-w", default=".", help="Workspace directory.")
@click.pass_context
def review(ctx, target, workspace):
    """Review code changes (local, branch:<name>, or pr:<number>)."""
    model = _get_model_id(ctx)
    cfg = _load_config(workspace=workspace, model=model)
    out_dir = cfg.workspace / ".fraktal"
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold yellow]Review Skill[/]: {target}")

    # Get diff
    if target == "local" or not target:
        diff_cmd = ["git", "diff", "HEAD"]
    elif target.startswith("branch:"):
        branch = target.split(":", 1)[1]
        diff_cmd = ["git", "diff", f"main...{branch}"]
    elif target.startswith("pr:"):
        pr_num = target.split(":", 1)[1]
        diff_cmd = ["gh", "pr", "diff", pr_num]
    else:
        diff_cmd = ["git", "diff", "HEAD"]

    try:
        diff_result = subprocess.run(
            diff_cmd,
            capture_output=True, text=True, timeout=30, cwd=str(cfg.workspace),
        )
        diff_text = diff_result.stdout or "(no changes)"
    except Exception as e:
        console.print(f"[red]✗ Failed to get diff: {e}[/]")
        sys.exit(1)

    review_path = out_dir / "REVIEW.md"
    summary_path = out_dir / "REVIEW_SUMMARY.md"

    orch = Orchestrator(config=cfg)
    review_prompt = f"""Review the following code changes.

Output detailed findings to: {review_path}
Write a brief summary to: {summary_path}

## Diff
```diff
{diff_text[:8000]}
```

Review for: correctness, security, performance, style, architecture.
Use the reviewer persona output format (Issue N, Severity, Category, Description, Recommendation, Status).
Be specific: cite file:line for each finding."""

    result = orch.run_task(review_prompt)

    if review_path.exists():
        console.print(f"[green]✓[/] Review complete")
        console.print(f"  [dim]{review_path}[/]")
        console.print(f"  [dim]{summary_path}[/]")
        # Show summary
        preview = review_path.read_text()[:500]
        console.print(Panel(preview, title="Review Preview", border_style="yellow"))
    else:
        console.print(f"[yellow]![/] Review produced no output file")


# ── Build ───────────────────────────────────────────────────────────────────

@main.command()
@click.argument("description", required=True)
@click.option("--effort", "-e", type=click.Choice(["low", "medium", "high"]), default="medium")
@click.option("--skip-design", is_flag=True, help="Skip the design phase.")
@click.option("--workspace", "-w", default=".", help="Workspace directory.")
@click.pass_context
def build(ctx, description, effort, skip_design, workspace):
    """Run the full build pipeline: plan → design → implement → review.

    This is the flagship Fraktál command — the complete Grok Build workflow
    powered by Fable 5's reasoning and DeepSeek's API.
    """
    model = _get_model_id(ctx)
    cfg = _load_config(workspace=workspace, model=model)

    console.print(Panel.fit(
        f"[bold]Fraktál Build Pipeline[/]\n"
        f"Task: {description}\n"
        f"Effort: {effort}\n"
        f"Model: {model or cfg.model}\n"
        f"Workspace: {cfg.workspace}",
        border_style="cyan",
    ))

    orch = Orchestrator(config=cfg)

    # Phase 1: Plan
    console.print("\n[bold blue]━ Phase 1/4: Plan[/]")
    plan_result = orch.run_task(
        f"Design a step-by-step implementation plan for: {description}\n\n"
        "Be specific: name exact files, functions, and changes. "
        "Explore the codebase first. Output a plan the Coder can execute directly."
    )
    console.print(Panel(
        Markdown(plan_result.output[:800] + ("..." if len(plan_result.output) > 800 else "")),
        title="Plan",
        border_style="blue",
    ))

    if not skip_design:
        # Phase 2: Design
        console.print("\n[bold blue]━ Phase 2/4: Design[/]")
        design_result = orch.run_task(
            f"Write a design document for: {description}\n\n"
            "Output to DESIGN.md and DESIGN_SUMMARY.md in the workspace root. "
            "Follow the design-doc-writer persona. Include architecture, data flow, "
            "tradeoffs, implementation steps, and risks."
        )
        console.print(f"[green]✓[/] Design: {design_result.iterations} iterations")

    # Phase 3: Implement
    console.print(f"\n[bold green]━ Phase 3/4: Implement ({effort} effort)[/]")
    impl_result = orch.run_task(
        f"Implement the following with {effort} effort: {description}\n\n"
        "Write a summary to IMPLEMENT_SUMMARY.md. "
        "Read existing code before writing. Match patterns exactly. "
        "Make the smallest change that solves the problem."
    )
    console.print(f"[green]✓[/] Implement: {impl_result.iterations} iterations")

    # Phase 4: Review
    console.print("\n[bold yellow]━ Phase 4/4: Review[/]")
    review_result = orch.run_task(
        "Review the current git diff for correctness, security, performance, style, "
        "and architecture. Output findings to .fraktal/REVIEW.md and a summary to "
        ".fraktal/REVIEW_SUMMARY.md. Be specific with file:line citations."
    )
    console.print(f"[green]✓[/] Review: {review_result.iterations} iterations")

    console.print(Panel.fit(
        "[bold green]Build pipeline complete![/]\n\n"
        f"Phases: plan → {'design → ' if not skip_design else ''}implement → review\n"
        f"Total iterations: {plan_result.iterations + design_result.iterations if not skip_design else 0 + impl_result.iterations + review_result.iterations}",
        border_style="green",
    ))


# ── MCP ─────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--workspace", "-w", default=".", help="Workspace to sandbox tools to.")
def mcp(workspace: str):
    """Start the MCP server (stdio) for Reasonix and other agents."""
    from fraktal.mcp import run_mcp_server
    cfg = _load_config(workspace=workspace)
    console.print(f"[dim]Starting Fraktál MCP server (workspace: {cfg.workspace})...[/]", file=sys.stderr)
    run_mcp_server(cfg)


# ── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
