"""
test_memoria.py
------------------
Prueba manual del sistema de memoria (Sliding Window + RAG) sin necesidad
de un IAProvider real. Simula que el usuario cuenta datos clave, y luego
verifica que al preguntar algo relacionado, el RAG los recupera.

Ejecutar: python test_memoria.py
"""

from core.memory.rag import RAGMemory
from core.memory.sliding_window import SlidingWindow
from core.memory.context_builder import ContextBuilder
from core.memory.vector_store import VectorStore
from core.user_data import UserDataManager


def main() -> None:
    # Usamos un archivo de memoria temporal para no ensuciar el real
    store = VectorStore(ruta_persistencia="config/memoria_rag_test.json")
    rag = RAGMemory(vector_store=store)
    ventana = SlidingWindow(max_turnos=6)
    user_data = UserDataManager()
    builder = ContextBuilder(rag=rag, sliding_window=ventana, user_data=user_data)

    print("== Guardando datos clave del usuario en el RAG ==")
    rag.agregar_memoria("El usuario se llama Sergio y estudia ingeniería de software.")
    rag.agregar_memoria("A Sergio le gusta el modding y la traducción de videojuegos.")
    rag.agregar_memoria("Sergio prefiere que el asistente responda de forma directa y breve.")

    print("== Simulando un intercambio reciente ==")
    builder.registrar_intercambio("Hola Nix", "Hola Sergio, ¿en qué te ayudo hoy?")

    consulta = "¿Qué sabe Sergio sobre modding?"
    print(f"\n== Consulta: {consulta} ==")
    mensaje_sistema, contexto_reciente = builder.construir(consulta)

    print("\n--- Mensaje de sistema generado ---")
    print(mensaje_sistema)

    print("\n--- Contexto reciente (sliding window) ---")
    for turno in contexto_reciente:
        print(f"[{turno['role']}] {turno['content']}")


if __name__ == "__main__":
    main()