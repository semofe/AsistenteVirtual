"""
orchestrator.py
------------------
El punto de unión de todo el sistema: toma un mensaje del usuario, arma el
contexto (personalidad + datos del usuario + RAG + sliding window), se lo
pasa al IAProvider activo, y si el modelo pide ejecutar herramientas
(crear archivo, abrir app, etc.), las ejecuta con el ToolRegistry y le
devuelve el resultado al modelo para que complete su respuesta.

Esta es la pieza que faltaba conectar: antes cada componente (provider,
memoria, acciones) se probaba por separado; Asistente es lo que los hace
funcionar juntos como una conversación real.
"""

from typing import Optional

from actions.tool_registry import ToolRegistry, crear_registro_por_defecto
from core.ia_provider import IAProvider
from core.memory.context_builder import ContextBuilder
from core.memory.rag import RAGMemory
from core.memory.sliding_window import SlidingWindow
from core.provider_factory import get_provider
from core.user_data import UserDataManager


class Asistente:
    def __init__(
        self,
        provider: Optional[IAProvider] = None,
        context_builder: Optional[ContextBuilder] = None,
        tool_registry: Optional[ToolRegistry] = None,
        max_iteraciones_tools: int = 3,
    ) -> None:
        self.provider = provider if provider is not None else get_provider()

        if context_builder is not None:
            self.context_builder = context_builder
        else:
            user_data = UserDataManager()
            self.context_builder = ContextBuilder(
                rag=RAGMemory(),
                sliding_window=SlidingWindow(),
                user_data=user_data,
            )

        self.tool_registry = tool_registry if tool_registry is not None else crear_registro_por_defecto(
            self.context_builder.user_data
        )
        self.max_iteraciones_tools = max_iteraciones_tools

    def procesar_mensaje(self, mensaje_usuario: str) -> str:
        """
        Procesa un mensaje del usuario de principio a fin: arma el contexto,
        llama al modelo, ejecuta las tools que pida (si las hay) y devuelve
        la respuesta final en texto.
        """
        mensaje_sistema, contexto_reciente = self.context_builder.construir(mensaje_usuario)
        contexto = [{"role": "system", "content": mensaje_sistema}] + contexto_reciente
        tools_schema = self.tool_registry.esquema_para_provider()

        resultado = self.provider.generate(prompt=mensaje_usuario, context=contexto, tools=tools_schema)

        # Si el modelo pidió ejecutar herramientas, las corremos y le
        # devolvemos el resultado para que complete su respuesta. Se limita
        # a max_iteraciones_tools para evitar loops infinitos si el modelo
        # insiste en pedir tools sin nunca cerrar con una respuesta de texto.
        iteraciones = 0
        while resultado.tool_calls and iteraciones < self.max_iteraciones_tools:
            resultados_texto = []
            for tool_call in resultado.tool_calls:
                salida = self.tool_registry.ejecutar(tool_call.name, tool_call.arguments)
                resultados_texto.append(f"[{tool_call.name}] -> {salida}")

            contexto.append({"role": "assistant", "content": resultado.text or "(solicitando herramientas)"})
            contexto.append({
                "role": "user",
                "content": "Resultado de las herramientas ejecutadas:\n" + "\n".join(resultados_texto),
            })

            resultado = self.provider.generate(
                prompt="Continúa la respuesta considerando el resultado anterior.",
                context=contexto,
                tools=tools_schema,
            )
            iteraciones += 1

        respuesta_final = resultado.text
        self.context_builder.registrar_intercambio(mensaje_usuario, respuesta_final)
        return respuesta_final


def iniciar_chat_consola() -> None:
    """Loop interactivo simple por consola, para probar el asistente completo."""
    asistente = Asistente()
    print(f"Nix listo (proveedor: {asistente.provider}). Escribe 'salir' para terminar.\n")

    while True:
        try:
            mensaje = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if not mensaje:
            continue
        if mensaje.lower() in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            break

        try:
            respuesta = asistente.procesar_mensaje(mensaje)
        except RuntimeError as e:
            print(f"[Error] {e}")
            continue

        print(f"Nix: {respuesta}\n")


if __name__ == "__main__":
    iniciar_chat_consola()