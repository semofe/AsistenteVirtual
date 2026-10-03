"""
ia_provider.py
----------------
Define el contrato (interfaz) que debe cumplir cualquier proveedor de modelo
de lenguaje, ya sea en la nube (Gemini, OpenAI) o local (Ollama, llama.cpp, etc).

Gracias a esta abstracción, el resto del sistema (memoria, RAG, ejecución de
herramientas) nunca necesita saber qué proveedor está usando realmente.
Cambiar de proveedor es tan simple como cambiar un valor en settings.json.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolCall:
    """Representa una petición del modelo para ejecutar una función/tool."""
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """
    Resultado normalizado de una generación, sin importar el proveedor.
    Así el resto del código siempre trabaja con la misma forma de dato.
    """
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw_response: Any = None  # por si se necesita depurar la respuesta original


class IAProvider(ABC):
    """
    Contrato base para cualquier proveedor de modelo de lenguaje.

    Todo proveedor concreto (GeminiProvider, OpenAIProvider, LocalProvider...)
    debe heredar de esta clase e implementar sus métodos abstractos.
    """

    def __init__(self, model_name: str, **kwargs: Any) -> None:
        self.model_name = model_name
        self.config = kwargs

    @abstractmethod
    def generate(
        self,
        prompt: str,
        context: Optional[list[dict[str, str]]] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> GenerationResult:
        """
        Genera una respuesta a partir de un prompt y un contexto de conversación.

        Args:
            prompt: mensaje actual del usuario.
            context: lista de mensajes previos, formato [{"role": ..., "content": ...}].
            tools: definición de herramientas disponibles (function calling),
                   en un formato genérico que cada proveedor traduce a su propio esquema.

        Returns:
            GenerationResult con el texto de respuesta y, si aplica, las tool_calls
            que el modelo solicitó ejecutar.
        """
        raise NotImplementedError

    @abstractmethod
    def supports_function_calling(self) -> bool:
        """Indica si este proveedor puede invocar herramientas (tools)."""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica que el proveedor esté listo para usarse
        (API key configurada, servidor local corriendo, etc).
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model_name}>"