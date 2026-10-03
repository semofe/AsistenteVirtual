"""
gemini_provider.py
-------------------
Implementación de IAProvider usando el SDK oficial actual de Google:
`google-genai` (pip install google-genai).

Nota: el paquete viejo `google-generativeai` fue descontinuado por Google
en 2026 -- si ves ese nombre en tutoriales antiguos, ya no se debe usar.
"""

import os
from typing import Any, Optional

from core.ia_provider import IAProvider, GenerationResult, ToolCall

# Mapeo de roles genéricos (los que usa el resto del sistema) a los que
# espera la API de Gemini, que usa "model" en vez de "assistant".
_ROL_A_GEMINI = {"user": "user", "assistant": "model"}


class GeminiProvider(IAProvider):
    def __init__(self, model_name: str = "gemini-2.5-flash", **kwargs: Any) -> None:
        super().__init__(model_name, **kwargs)
        self._client = None
        self._api_key = kwargs.get("api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def _get_client(self):
        """Carga el SDK de forma perezosa, solo cuando realmente se necesita."""
        if self._client is None:
            from google import genai  # pip install google-genai

            self._client = genai.Client(api_key=self._api_key)
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
                "GeminiProvider no tiene configurada GEMINI_API_KEY. "
                "Defínela como variable de entorno o en settings.json."
            )

        from google.genai import types

        client = self._get_client()
        context = context or []

        # Gemini no acepta role="system" dentro de contents -- ese tipo de
        # mensaje se pasa aparte, como system_instruction. Lo separamos del
        # resto del historial antes de traducir roles.
        mensajes_sistema = [m["content"] for m in context if m["role"] == "system"]
        turnos_conversacion = [m for m in context if m["role"] != "system"]

        contents = [
            types.Content(
                role=_ROL_A_GEMINI.get(m["role"], "user"),
                parts=[types.Part.from_text(text=m["content"])],
            )
            for m in turnos_conversacion
        ]
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        config_kwargs: dict[str, Any] = {
            # Desactivamos AFC explícitamente: las tools se ejecutan a mano
            # con ToolRegistry, no queremos que el SDK intente invocarlas
            # por su cuenta (eso es lo que generaba el warning).
            "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
        }
        if mensajes_sistema:
            config_kwargs["system_instruction"] = "\n\n".join(mensajes_sistema)
        if tools:
            config_kwargs["tools"] = [self._translate_tools(tools)]

        response = client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        texto = response.text or ""
        tool_calls: list[ToolCall] = []

        if response.function_calls:
            for fc in response.function_calls:
                tool_calls.append(ToolCall(name=fc.name, arguments=dict(fc.args or {})))

        return GenerationResult(text=texto, tool_calls=tool_calls, raw_response=response)

    @staticmethod
    def _translate_tools(tools: list[dict[str, Any]]):
        """Convierte el esquema genérico de tools al formato esperado por Gemini."""
        from google.genai import types

        declaraciones = [
            types.FunctionDeclaration(
                name=t["name"],
                description=t.get("description", ""),
                parameters_json_schema=t.get("parameters", {}),
            )
            for t in tools
        ]
        return types.Tool(function_declarations=declaraciones)