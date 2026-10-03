"""
sliding_window.py
--------------------
Mantiene los últimos N turnos de la conversación en memoria (RAM), para dar
coherencia inmediata a la charla sin necesidad de buscar en ningún índice.

Es deliberadamente simple: una cola de tamaño fijo. Todo lo que es "memoria
a largo plazo" (datos clave del usuario, hechos pasados) vive en el RAG
(ver rag.py), no aquí.
"""

from collections import deque
from dataclasses import dataclass


@dataclass
class Turno:
    role: str      # "user" | "assistant"
    content: str


class SlidingWindow:
    def __init__(self, max_turnos: int = 10) -> None:
        """
        Args:
            max_turnos: cuántos turnos (mensajes, no pares) se conservan.
                        10 turnos ~= 5 intercambios usuario/asistente.
        """
        self._buffer: deque[Turno] = deque(maxlen=max_turnos)

    def agregar(self, role: str, content: str) -> None:
        self._buffer.append(Turno(role=role, content=content))

    def agregar_intercambio(self, mensaje_usuario: str, respuesta_asistente: str) -> None:
        self.agregar("user", mensaje_usuario)
        self.agregar("assistant", respuesta_asistente)

    def obtener_contexto(self) -> list[dict[str, str]]:
        """Devuelve los turnos en el formato genérico que espera IAProvider.generate()."""
        return [{"role": t.role, "content": t.content} for t in self._buffer]

    def limpiar(self) -> None:
        self._buffer.clear()

    def __len__(self) -> int:
        return len(self._buffer)