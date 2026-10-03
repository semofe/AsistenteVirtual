"""
context_builder.py
---------------------
Punto de unión entre las tres fuentes de "contexto" del asistente:

1. Personalidad (persona.txt)          -> quién es el asistente
2. RAG (memoria de largo plazo)        -> qué sabe sobre el usuario / el pasado
3. Sliding Window (memoria reciente)   -> de qué se habló hace un momento

El resultado es lo que se le pasa a IAProvider.generate() como `context`,
más un mensaje de sistema con persona + recuerdos relevantes.
"""

from pathlib import Path

from core.memory.rag import RAGMemory
from core.memory.sliding_window import SlidingWindow
from core.user_data import UserDataManager

DEFAULT_PERSONA_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "persona.txt"


class ContextBuilder:
    def __init__(
        self,
        rag: RAGMemory,
        sliding_window: SlidingWindow,
        user_data: UserDataManager | None = None,
        persona_path: Path = DEFAULT_PERSONA_PATH,
    ) -> None:
        self.rag = rag
        self.sliding_window = sliding_window
        self.user_data = user_data if user_data is not None else UserDataManager()
        self.persona_path = persona_path

    def _leer_persona(self) -> str:
        """
        Se lee del disco en cada llamada (no se cachea) para que si el
        usuario edita persona.txt en caliente, el cambio se note sin
        reiniciar el asistente.
        """
        if not self.persona_path.exists():
            return "Eres un asistente virtual servicial."
        return self.persona_path.read_text(encoding="utf-8").strip()

    def construir(self, mensaje_usuario: str, k_recuerdos: int = 3) -> tuple[str, list[dict]]:
        """
        Devuelve (mensaje_sistema, contexto_reciente) listos para pasar a
        IAProvider.generate(prompt=mensaje_usuario, context=contexto_reciente).

        El mensaje_sistema se puede anteponer como primer elemento del
        contexto (role="system") o concatenarse al prompt, según lo que
        soporte cada proveedor.
        """
        persona = self._leer_persona()
        datos_usuario = self.user_data.resumen_para_contexto()
        recuerdos = self.rag.recuperar(mensaje_usuario, k=k_recuerdos)
        contexto_reciente = self.sliding_window.obtener_contexto()

        bloques = [
            f"# Personalidad\n{persona}",
            f"# Datos del usuario\n{datos_usuario}",
        ]

        if recuerdos:
            recuerdos_texto = "\n".join(f"- {r}" for r in recuerdos)
            bloques.append(f"# Recuerdos relevantes sobre el usuario\n{recuerdos_texto}")

        mensaje_sistema = "\n\n".join(bloques)
        return mensaje_sistema, contexto_reciente

    def registrar_intercambio(self, mensaje_usuario: str, respuesta_asistente: str) -> None:
        """
        Actualiza la ventana deslizante tras cada turno. Guardar en el RAG
        es una decisión aparte (no todo intercambio merece quedar en
        memoria a largo plazo) -- eso se hace explícitamente llamando a
        rag.agregar_memoria() cuando se detecta un dato clave.
        """
        self.sliding_window.agregar_intercambio(mensaje_usuario, respuesta_asistente)