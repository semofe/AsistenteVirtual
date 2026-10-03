"""
openai_provider.py
--------------------
Implementación de IAProvider usando la API de OpenAI (chat.completions).
"""

import json
import os
from typing import Any, Optional

from core.ia_provider import IAProvider, GenerationResult, ToolCall


class OpenAIProvider(IAProvider):
    def __init__(self, model_name: str = "gpt-4o-mini", **kwargs: Any) -> None:
        super().__init__(model_name, **kwargs)
        self._client = None
        self._api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI  # pip install openai

            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def is_available(self) -> bool:
        return bool(self._api_key)

    def supports_function_calling(self) -> bool:
        return True

    def generate(
        self,
        prompt: str,
        context: Optional[list[dict[str, str]]] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> GenerationResult:
        if not self.is_available():
            raise RuntimeError(
                "OpenAIProvider no tiene configurada OPENAI_API_KEY. "
                "Defínela como variable de entorno o en settings.json."
            )

        client = self._get_client()
        context = context or []

        messages = list(context) + [{"role": "user", "content": prompt}]
        openai_tools = self._translate_tools(tools) if tools else None

        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=openai_tools,
        )

        choice = response.choices[0].message
        text = choice.content or ""
        tool_calls: list[ToolCall] = []

        if choice.tool_calls:
            for tc in choice.tool_calls:
                tool_calls.append(
                    ToolCall(
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments or "{}"),
                    )
                )

        return GenerationResult(text=text, tool_calls=tool_calls, raw_response=response)

    @staticmethod
    def _translate_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convierte el esquema genérico de tools al formato esperado por OpenAI."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {}),
                },
            }
            for t in tools
        ]