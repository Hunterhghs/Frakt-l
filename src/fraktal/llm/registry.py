"""Provider registry — factory for creating LLM providers."""

from __future__ import annotations

from fraktal.config import FraktalConfig
from fraktal.llm.base import LLMProvider


def create_provider(
    config: FraktalConfig | None = None,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> LLMProvider:
    """Create an LLM provider from config or explicit arguments.

    Supported providers:
    - deepseek: DeepSeek API (V3, R1)
    - openai: OpenAI API (GPT-4o, etc.)
    - anthropic: Anthropic API (Claude)
    - openai-compatible: Any OpenAI-compatible endpoint
    - ollama: Local Ollama
    - lmstudio: Local LM Studio
    """
    cfg = config or FraktalConfig.load()
    p = provider or cfg.provider
    m = model or cfg.model

    if p in ("deepseek", "openai-compatible"):
        from fraktal.llm.deepseek import DeepSeekProvider
        return DeepSeekProvider(
            model_id=m,
            api_key=api_key or cfg.api_key,
            config=cfg,
            base_url=base_url or cfg.base_url,
        )

    if p == "openai":
        from fraktal.llm.deepseek import DeepSeekProvider
        return DeepSeekProvider(
            model_id=m,
            api_key=api_key or cfg.api_key,
            config=cfg,
            base_url=base_url or "https://api.openai.com/v1",
        )

    if p == "anthropic":
        raise NotImplementedError(
            "Anthropic provider requires the anthropic SDK. "
            "Install with: pip install anthropic"
        )

    if p in ("ollama", "lmstudio"):
        from fraktal.llm.deepseek import DeepSeekProvider
        default_urls = {
            "ollama": "http://localhost:11434/v1",
            "lmstudio": "http://localhost:1234/v1",
        }
        return DeepSeekProvider(
            model_id=m,
            api_key="not-needed",
            config=cfg,
            base_url=base_url or default_urls[p],
        )

    raise ValueError(
        f"Unknown provider: {p}. "
        f"Supported: deepseek, openai, anthropic, openai-compatible, ollama, lmstudio"
    )
