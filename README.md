# Fraktál — Fable 5 × Grok 4.5 Hybrid

<div align="center">

**High-performance multi-agent AI coding agent powered by DeepSeek API**

*Combines Fable 5's reasoning architecture with Grok 4.5's build pipeline for specialized outputs — websites, dashboards, reports, and more.*

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![DeepSeek](https://img.shields.io/badge/powered_by-DeepSeek_API-536DFE.svg)](https://deepseek.com)

</div>

---

## What is Fraktál?

**Fraktál** is a hybrid AI coding agent that merges two powerful paradigms:

- **Fable 5** — Elite reasoning discipline: hypothesis-driven thinking, evidence-based claims, adversarial self-verification, multi-provider LLM orchestration, persistent memory, MCP server, and domain playbooks.
- **Grok 4.5 Build** — Battle-tested multi-agent pipeline: `plan → design → implement → review` with agent/persona/role/skill architecture.

The result: **high-performance reasoning at low cost** (DeepSeek API), designed for Reasonix but applicable everywhere. Fraktál produces specialized, professional-grade outputs — interactive dashboards, polished websites, data-rich reports, and more.

## Architecture

```
fraktal/
├── src/fraktal/
│   ├── cli.py                    # Unified CLI (Click + Rich)
│   ├── config.py                 # Multi-provider config + model catalog
│   ├── llm/                      # LLM providers (DeepSeek, OpenAI, Anthropic)
│   │   ├── base.py               # Abstract provider interface
│   │   ├── deepseek.py           # DeepSeek client (primary)
│   │   └── registry.py           # Provider factory
│   ├── agents/                   # Agent system
│   │   ├── base.py               # Abstract Agent with tool loop
│   │   ├── runner.py             # AgentRunner (Agent + Persona + Role)
│   │   ├── orchestrator.py       # Top-level orchestrator
│   │   ├── subagents.py          # Architect, Coder, Verifier, Reporter
│   │   ├── definitions/          # Agent .md files (3)
│   │   ├── personas/             # Persona .toml files (8)
│   │   └── roles/                # Role .toml files (9)
│   ├── skills/                   # Grok Build pipeline skills
│   │   ├── plan/SKILL.md         # Read-only architecture exploration
│   │   ├── design/SKILL.md       # Write → review → revise loop
│   │   ├── implement/SKILL.md    # Code → review → fix loop
│   │   ├── review/SKILL.md       # Diff/branch/PR review
│   │   └── build/SKILL.md        # Full pipeline orchestration
│   ├── tools/                    # Tool suite (8 tools)
│   │   ├── base.py               # Tool, ToolRegistry, ToolResult
│   │   ├── filesystem.py         # Read, write, list files
│   │   ├── terminal.py           # Shell command execution
│   │   ├── search.py             # Regex code search
│   │   └── hheuristics.py        # H Heuristics domain tools
│   ├── memory/                   # Persistent memory (SQLite + JSON)
│   ├── playbooks/                # Domain playbooks (7)
│   ├── prompts/                  # System prompts (5 roles)
│   └── mcp/                      # MCP server for Reasonix interop
├── scripts/install.sh            # One-line installer
├── fraktal.toml                  # Workspace config
└── pyproject.toml
```

## How It Works

### The Build Pipeline

```
$ fraktal build "Add rate limiting to the API"

Phase 1: Plan        → Architect explores codebase, produces step-by-step plan
Phase 2: Design      → Design-doc-writer writes DESIGN.md
                     → Design-doc-reviewer audits it
                     → Writer revises until 0 open issues
Phase 3: Implement   → Coder writes code matching existing patterns
                     → Verifier checks for correctness
                     → Coder fixes issues
                     → Loop until clean
Phase 4: Review      → Final review against the diff (security audit on high effort)
```

### Agent System

| Sub-Agent | Access | Best For |
|-----------|--------|----------|
| **Architect** | Read-only | Codebase exploration, implementation planning |
| **Coder** | Full R/W | Writing code, fixing bugs, implementing features |
| **Verifier** | Read + Execute | Running tests, linting, correctness checks |
| **Reporter** | Read + Write docs | READMEs, summaries, architecture docs |

### Personas (8)

| Persona | Mode | Use For |
|---------|------|---------|
| `plan` | read-only | Architecture design, implementation planning |
| `implementer` | all | Writing code, fixing bugs |
| `reviewer` | read-only | Code review (5 axes) |
| `design-doc-writer` | all | Technical design documents |
| `design-doc-reviewer` | read-only | Design document auditing |
| `security-auditor` | read-only | Security vulnerability scanning |
| `researcher` | read-only | Deep codebase exploration |
| `test-writer` | all | Unit/integration test writing |

## Quick Start

### 1. Install

```bash
git clone https://github.com/Hunterhghs/Frakt-l.git
cd Frakt-l
bash scripts/install.sh
```

Or:

```bash
pip install -e .
```

### 2. Configure

```bash
# Set your DeepSeek API key
export DEEPSEEK_API_KEY="sk-your-key-here"

# Initialize config
fraktal setup
```

### 3. Verify

```bash
fraktal health
fraktal models
```

## Usage

### Full Build Pipeline

```bash
fraktal build --effort high "Add multi-tenant support to the platform"
fraktal build --skip-design "Fix the pagination bug"
```

### Individual Phases

```bash
# Plan (read-only exploration)
fraktal plan "Design a Redis caching layer"

# Design (write → review → revise)
fraktal design "Rate limiting middleware for FastAPI"

# Implement (code → review → fix)
fraktal implement --effort high "Add JWT refresh token rotation"

# Review
fraktal review                  # local uncommitted changes
fraktal review branch:feature-x # branch diff
fraktal review pr:42            # GitHub PR (requires gh CLI)
```

### Single Agent Run

```bash
fraktal run "Find all TODO comments in this codebase"
fraktal run --agent explore "What auth pattern does this project use?"
fraktal run --persona reviewer "Review the auth module"
fraktal run --model deepseek-reasoner --persona security-auditor "Audit the payment flow"
```

### Inspect & Debug

```bash
fraktal agents           # List agents
fraktal personas         # List personas
fraktal skills           # List skills
fraktal playbooks        # List domain playbooks
fraktal playbooks dashboard  # Show dashboard standards
fraktal prompts          # List system prompts
fraktal tools            # List tool schemas
fraktal memory recent    # Recent memories
fraktal memory search "auth"  # Search memories
```

### MCP Server

```bash
fraktal mcp --workspace /path/to/project
# Exposes all Fraktál tools to Reasonix and other MCP-compatible agents
```

## Models

| ID | Model | Context | Reasoning | Use Case |
|----|-------|---------|-----------|----------|
| `deepseek-chat` | DeepSeek V3 | 128K | — | General coding, fast iteration |
| `deepseek-reasoner` | DeepSeek R1 | 128K | ✓ | Complex architecture, debugging |
| `grok-4.5` | Grok 4.5 | 500K | ✓ | Original Grok passthrough |

Switch models with `--model` / `-m`:

```bash
fraktal --model deepseek-reasoner implement "Debug the race condition"
```

## Domain Playbooks

Fraktál includes 7 domain playbooks for specialized outputs:

| Playbook | What It Covers |
|----------|---------------|
| `dashboard` | KPI cards, interactive filters, dark mode, accessibility |
| `report` | Executive summary, methodology, data-backed claims, PDF-ready |
| `website` | Hero section, responsive design, WCAG 2.1 AA, SEO |
| `dataset` | Clean CSV/Parquet, data dictionary, reproducible pipeline |
| `research` | Research question, lit review, reproducible methods |
| `presentation` | One idea per slide, consistent branding, readable charts |
| `infographic` | Visual hierarchy, colorblind-safe, 300 DPI print-ready |

The Orchestrator consults playbooks before delegating work — ensuring every output meets H Heuristics quality standards.

## Configuration

Workspace config at `fraktal.toml`:

```toml
[fraktal]
provider = "deepseek"
model = "deepseek-chat"
reasoning_model = "deepseek-reasoner"
max_iterations = 40
max_delegations = 12
memory_backend = "sqlite"
default_effort = "medium"
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key (required) |
| `GROK_4_5_API_KEY` | Grok API key (for passthrough) |
| `ANTHROPIC_API_KEY` | Anthropic API key (for Claude models) |
| `OPENAI_API_KEY` | OpenAI API key (for GPT models) |
| `FRAKTAL_PROVIDER` | Override provider |
| `FRAKTAL_MODEL` | Override model |
| `FRAKTAL_BASE_URL` | Override base URL |

## Why DeepSeek?

- **Cost**: ~10-20x cheaper than frontier models for equivalent quality
- **Speed**: Fast inference with 128K context
- **Reasoning**: R1 model provides chain-of-thought for complex tasks
- **OpenAI-compatible**: Drop-in API compatibility — no lock-in
- **High performance, low cost**: The core Fraktál thesis

## Comparison

| Feature | Fable 5 | Grok Hybrid | **Fraktál** |
|---------|---------|-------------|-------------|
| LLM Backend | Multi-provider | DeepSeek + Grok | **DeepSeek-first, multi-provider** |
| Agent Model | Orchestrator + sub-agents | Agent/Persona/Role | **Both — unified** |
| Pipeline | Domain playbooks | plan → design → implement → review | **Grok Build + playbooks** |
| Tools | Rich suite (8+) | 5 basic tools | **Full suite + H Heuristics** |
| Memory | SQLite/JSON | — | **SQLite/JSON persistent** |
| MCP Server | ✓ | — | **✓ (Reasonix-native)** |
| CLI | `fable` | `grok-hybrid` | **`fraktal` (Click + Rich)** |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/

# Type check
mypy src/fraktal/
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

**Hunter Hughes** — H Heuristics  
[GitHub](https://github.com/Hunterhghs) · [Substack](https://hheuristics.substack.com)

---

<div align="center">
<sub>Fable 5 reasoning × Grok 4.5 pipeline × DeepSeek API. Built for Reasonix.</sub>
</div>
