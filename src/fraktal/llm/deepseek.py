"""DeepSeek API provider — primary Fraktál backend.

OpenAI-compatible client targeting DeepSeek V3 (chat) and R1 (reasoner).
Also works as a generic OpenAI-compatible provider for any endpoint.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from openai import OpenAI

from fraktal.config import BUILTIN_MODELS, FraktalConfig, ModelInfo, get_model_info
from fraktal.llm.base import LLMProvider, LLMResponse, Message, ToolCall, ToolSpec


class DeepSeekProvider(LLMProvider):
    """OpenAI-compatible provider targeting DeepSeek (or any compatible endpoint)."""

    def __init__(
        self,
        model_id: str = "deepseek-chat",
        api_key: str | None = None,
        config: FraktalConfig | None = None,
        base_url: str | None = None,
    ):
        self.config = config or FraktalConfig.load()
        self.model_info = get_model_info(model_id)
        self.model_id = model_id

        # API key resolution
        self._api_key = api_key or self.config.api_key
        if not self._api_key and model_id.startswith("deepseek"):
            self._api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not self._api_key and model_id == "grok-4.5":
            self._api_key = os.environ.get("GROK_4_5_API_KEY", "")

        self._base_url = base_url or self.model_info.base_url

        self._client = OpenAI(
            api_key=self._api_key or "sk-placeholder",
            base_url=self._base_url,
            timeout=httpx.Timeout(300.0, connect=10.0),
            max_retries=2,
        )

    @property
    def context_window(self) -> int:
        return self.model_info.context_window

    def _tools_to_openai(self, tools: list[ToolSpec] | None) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def _messages_to_openai(
        self,
        messages: list[Message],
        system: str | None = None,
    ) -> list[dict[str, Any]]:
        msgs: list[dict[str, Any]] = []
        if system:
            msgs.append({"role": "system", "content": system})
        for m in messages:
            entry: dict[str, Any] = {"role": m.role}
            if m.content is not None:
                entry["content"] = m.content
            if m.tool_call_id is not None:
                entry["tool_call_id"] = m.tool_call_id
            if m.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": str(tc.arguments),  # will be JSON string
                        },
                    }
                    for tc in m.tool_calls
                ]
            msgs.append(entry)
        return msgs

    def chat(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        msgs = self._messages_to_openai(messages, system=system)

        params: dict[str, Any] = {
            "model": self.model_info.model,
            "messages": msgs,
            "temperature": temperature,
        }

        if max_tokens:
            params["max_tokens"] = max_tokens
        else:
            params["max_tokens"] = self.model_info.max_completion_tokens

        openai_tools = self._tools_to_openai(tools)
        if openai_tools:
            params["tools"] = openai_tools
            params["tool_choice"] = "auto"

        # DeepSeek-specific reasoning effort
        if self.model_info.supports_reasoning_effort and self.model_info.reasoning_effort:
            params["reasoning_effort"] = self.model_info.reasoning_effort

        params.update(kwargs)

        resp = self._client.chat.completions.create(**params)
        choice = resp.choices[0]
        msg = choice.message

        tool_calls: list[ToolCall] = []
        if msg.tool_calls:
            import json
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))

        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage=resp.usage.model_dump() if resp.usage else None,
        )

    def check_connection(self) -> dict[str, Any]:
        start = time.time()
        try:
            resp = self.chat(
                [Message(role="user", content="ping")],
                max_tokens=5,
                temperature=0,
            )
            elapsed = time.time() - start
            return {
                "ok": True,
                "model": self.model_info.name,
                "latency_ms": round(elapsed * 1000),
                "usage": resp.usage,
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "latency_ms": round((time.time() - start) * 1000),
            }
