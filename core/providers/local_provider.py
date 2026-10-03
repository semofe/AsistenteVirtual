"""
local_provider.py
--------------------
Implementación de IAProvider para un modelo corriendo localmente vía Ollama
(https://ollama.com). No requiere API key ni conexión a internet, siempre que
el servidor de Ollama esté corriendo (por defecto en http://localhost:11434).
"""

from typing import Any, Optional

import requests

from core.ia_provider import IAProvider, GenerationResult, ToolCall


class LocalProvider(IAProvider):
    def __init__(
        self,
        model_name: str = "llama3.1",
        host: str = "http://localhost:11434",
        **kwargs: Any,
    ) -> None:
        super().__init__(model_name, **kwargs)
        self.host = host.rstrip("/")

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=2)
            return resp.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def supports_function_calling(self) -> bool:
        # Algunos modelos locales (ej. llama3.1, qwen2.5) sí soportan tools
        # vía Ollama, pero no todos. Se deja en False por defecto y se puede
        # activar por configuración si el modelo elegido lo soporta.
        return self.config.get("supports_tools", False)

    def generate(
        self,
        prompt: str,
        context: Optional[list[dict[str, str]]] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> GenerationResult:
        if not self.is_available():
            raise RuntimeError(
                f"No se pudo conectar con Ollama en {self.host}. "
                "Verifica que el servicio esté corriendo (`ollama serve`)."
            )

        context = context or []
        messages = list(context) + [{"role": "user", "content": prompt}]

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
        }

        if tools and self.supports_function_calling():
            payload["tools"] = self._translate_tools(tools)

        response = requests.post(f"{self.host}/api/chat", json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()

        message = data.get("message", {})
        text = message.get("content", "")
        tool_calls: list[ToolCall] = []

        for tc in message.get("tool_calls", []):
            fn = tc.get("function", {})
            tool_calls.append(ToolCall(name=fn.get("name", ""), arguments=fn.get("arguments", {})))

        return GenerationResult(text=text, tool_calls=tool_calls, raw_response=data)

    @staticmethod
    def _translate_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Ollama usa el mismo esquema de tools que OpenAI."""
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