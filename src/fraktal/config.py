"""Unified configuration for Fraktál — merges Fable 5 multi-provider config
with Grok Build's model catalog.

Resolution order (later overrides earlier):
1. Built-in defaults
2. ``fraktal.toml`` in workspace root
3. Environment variables (``FRAKTAL_*`` + provider API keys)
4. Explicit keyword overrides
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Model Catalog ────────────────────────────────────────────────────────────

@dataclass
class ModelInfo:
    """One model entry in the catalog."""
    id: str
    model: str
    name: str
    description: str
    base_url: str
    api_backend: str = "chat"
    context_window: int = 128000
    max_completion_tokens: int = 8192
    reasoning_effort: str | None = None
    supports_reasoning_effort: bool = False
    agent_type: str = "fraktal-plan"
    hidden: bool = False

    @property
    def api_key_env(self) -> str:
        return f"{self.id.upper().replace('-', '_')}_API_KEY"


# Built-in models — DeepSeek first, plus Grok passthrough
BUILTIN_MODELS: dict[str, ModelInfo] = {
    "deepseek-chat": ModelInfo(
        id="deepseek-chat",
        model="deepseek-chat",
        name="DeepSeek V3",
        description="DeepSeek's latest chat model — fast, affordable, general-purpose coding",
        base_url="https://api.deepseek.com/v1",
        api_backend="chat",
        context_window=128000,
        max_completion_tokens=8192,
        agent_type="fraktal-plan",
    ),
    "deepseek-reasoner": ModelInfo(
        id="deepseek-reasoner",
        model="deepseek-reasoner",
        name="DeepSeek R1",
        description="DeepSeek's reasoning model — chain-of-thought for complex architecture and debugging",
        base_url="https://api.deepseek.com/v1",
        api_backend="chat",
        context_window=128000,
        max_completion_tokens=8192,
        reasoning_effort="high",
        supports_reasoning_effort=True,
        agent_type="fraktal-plan",
    ),
    "grok-4.5": ModelInfo(
        id="grok-4.5",
        model="grok-4.5",
        name="Grok 4.5",
        description="xAI Grok 4.5 — frontier reasoning, 500K context (original Grok Build passthrough)",
        base_url="https://cli-chat-proxy.grok.com/v1",
        api_backend="chat",
        context_window=500000,
        max_completion_tokens=32768,
        reasoning_effort="high",
        supports_reasoning_effort=True,
        agent_type="fraktal-plan",
    ),
}


# ── Config ───────────────────────────────────────────────────────────────────

@dataclass
class FraktalConfig:
    """Runtime configuration for Fraktál agents, providers, and storage."""

    # LLM provider
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    reasoning_model: str = "deepseek-reasoner"
    api_key: str | None = None
    base_url: str | None = None
    max_tokens: int = 8192
    temperature: float = 0.2

    # Agent behaviour
    max_iterations: int = 40
    max_delegations: int = 12
    command_timeout: int = 120

    # Skill defaults
    default_effort: str = "medium"      # low | medium | high
    max_review_rounds: int = 6

    # Workspace
    workspace: Path = field(default_factory=Path.cwd)

    # Memory
    memory_backend: str = "sqlite"
    memory_path: Path | None = None

    # MCP
    mcp_enabled: bool = True

    # Misc
    verbose: bool = False
    fork_context: bool = True

    def __post_init__(self) -> None:
        self.workspace = Path(self.workspace).resolve()
        if self.memory_path is None:
            self.memory_path = self.workspace / ".fraktal" / "memory"
        self.memory_path = Path(self.memory_path)

    @classmethod
    def load(
        cls,
        workspace: str | Path | None = None,
        **overrides: Any,
    ) -> "FraktalConfig":
        """Load config from fraktal.toml + environment, with keyword overrides."""
        ws = Path(workspace).resolve() if workspace else Path.cwd()
        data: dict[str, Any] = {}

        # 1. fraktal.toml
        toml_path = ws / "fraktal.toml"
        if toml_path.exists():
            with open(toml_path, "rb") as f:
                raw = tomllib.load(f)
            data.update(raw.get("fraktal", raw))

        # 2. Environment variables
        env_map = {
            "provider": "FRAKTAL_PROVIDER",
            "model": "FRAKTAL_MODEL",
            "reasoning_model": "FRAKTAL_REASONING_MODEL",
            "base_url": "FRAKTAL_BASE_URL",
            "max_tokens": "FRAKTAL_MAX_TOKENS",
            "temperature": "FRAKTAL_TEMPERATURE",
            "memory_backend": "FRAKTAL_MEMORY_BACKEND",
            "mcp_enabled": "FRAKTAL_MCP_ENABLED",
            "verbose": "FRAKTAL_VERBOSE",
        }
        for key, env in env_map.items():
            val = os.environ.get(env)
            if val is not None:
                data[key] = val

        data["workspace"] = ws
        data.update({k: v for k, v in overrides.items() if v is not None})

        # Build instance (only fields that exist on the dataclass)
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        cfg = cls(**{k: v for k, v in data.items() if k in valid_fields})

        # Coerce types from env strings
        cfg.max_tokens = int(cfg.max_tokens)
        cfg.temperature = float(cfg.temperature)
        cfg.max_iterations = int(cfg.max_iterations)
        cfg.max_delegations = int(cfg.max_delegations)
        cfg.command_timeout = int(cfg.command_timeout)
        cfg.max_review_rounds = int(cfg.max_review_rounds)
        if isinstance(cfg.mcp_enabled, str):
            cfg.mcp_enabled = cfg.mcp_enabled.lower() in ("true", "1", "yes")
        if isinstance(cfg.verbose, str):
            cfg.verbose = cfg.verbose.lower() in ("true", "1", "yes")
        if isinstance(cfg.fork_context, str):
            cfg.fork_context = cfg.fork_context.lower() in ("true", "1", "yes")

        # Resolve API key
        if cfg.api_key is None:
            cfg.api_key = resolve_api_key(cfg.provider)

        return cfg


def resolve_api_key(provider: str) -> str | None:
    """Find an API key for the given provider from the environment."""
    candidates: dict[str, list[str]] = {
        "anthropic": ["FRAKTAL_API_KEY", "ANTHROPIC_API_KEY"],
        "openai": ["FRAKTAL_API_KEY", "OPENAI_API_KEY"],
        "deepseek": ["FRAKTAL_API_KEY", "DEEPSEEK_API_KEY"],
        "grok": ["FRAKTAL_API_KEY", "GROK_4_5_API_KEY"],
        "openai-compatible": ["FRAKTAL_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"],
        "ollama": [],
        "lmstudio": [],
    }
    for env in candidates.get(provider, ["FRAKTAL_API_KEY"]):
        val = os.environ.get(env)
        if val and val.strip():
            return val.strip()
    return None


def get_model_info(model_id: str) -> ModelInfo:
    """Look up a model in the built-in catalog."""
    info = BUILTIN_MODELS.get(model_id)
    if info is None:
        available = ", ".join(BUILTIN_MODELS)
        raise ValueError(f"Unknown model '{model_id}'. Available: {available}")
    return info
