"""
Fraktál — Fable 5 × Grok 4.5 Hybrid AI Coding Agent.

High-performance multi-agent orchestration powered by DeepSeek API.
Combines Fable 5's reasoning architecture with Grok 4.5's build pipeline
(plan → design → implement → review). Designed for Reasonix but
applicable everywhere.

Key capabilities:
- Multi-agent orchestration (Architect, Coder, Verifier, Reporter)
- Grok Build pipeline for code generation workflows
- Persistent memory across sessions (SQLite)
- MCP server for interop with any AI agent
- Domain playbooks for specialized outputs (websites, dashboards, reports)
- DeepSeek-first with multi-provider fallback
"""

__version__ = "0.1.0"
__author__ = "Hunter Hughes / H Heuristics"

from fraktal.config import FraktalConfig
from fraktal.agents.orchestrator import Orchestrator

__all__ = ["FraktalConfig", "Orchestrator", "__version__"]
