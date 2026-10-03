"""
rag.py
--------
RAGMemory es la pieza que le da al asistente "memoria a largo plazo":
guarda fragmentos de conversación o datos clave del usuario, y luego
recupera los más relevantes para la pregunta actual.

Nota de diseño sobre TF-IDF: como el vocabulario del vectorizador cambia
cada vez que se agrega texto nuevo, RAGMemory reajusta (re-fit) el embedder
sobre todo el corpus y re-calcula los vectores existentes cada vez que se
agrega un recuerdo nuevo. Para un asistente personal (cientos/miles de
recuerdos) esto es instantáneo; si el corpus creciera mucho, ahí sí
conviene migrar a SentenceTransformerEmbedder (que no tiene este problema
porque no depende de un vocabulario que cambia).
"""

from core.memory.embedder import Embedder, TfidfEmbedder
from core.memory.vector_store import VectorStore, Documento


class RAGMemory:
    def __init__(
        self,
        embedder: Embedder | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.embedder = embedder if embedder is not None else TfidfEmbedder()
        self.store = vector_store if vector_store is not None else VectorStore()

        # Si ya había datos guardados de una sesión anterior, ajustamos
        # el embedder a ese corpus para que los vectores sean comparables.
        textos_previos = self.store.all_texts()
        if textos_previos:
            self.embedder.fit(textos_previos)

    def agregar_memoria(self, texto: str, metadata: dict | None = None) -> str:
        """Guarda un nuevo recuerdo (dato clave del usuario, hecho relevante, etc)."""
        textos_previos = self.store.all_texts()
        corpus_completo = textos_previos + [texto]

        # Reajustamos el vocabulario TF-IDF con el corpus completo...
        self.embedder.fit(corpus_completo)

        # ...y si el embedder es TF-IDF, sus vectores viejos quedaron
        # desactualizados: los recalculamos para mantener consistencia.
        if isinstance(self.embedder, TfidfEmbedder) and textos_previos:
            self._reindexar(textos_previos)

        vector = self.embedder.encode(texto)
        return self.store.add(texto, vector, metadata)

    def _reindexar(self, textos_previos: list[str]) -> None:
        """Recalcula los vectores de los documentos ya existentes."""
        nuevos_vectores = self.embedder.encode_many(textos_previos)
        for doc, vector in zip(self.store._documentos, nuevos_vectores):
            doc.vector = vector.tolist()
        self.store._guardar()

    def recuperar(self, consulta: str, k: int = 3, umbral_minimo: float = 0.05) -> list[str]:
        """
        Devuelve los k recuerdos más relevantes para la consulta actual.
        Descarta resultados por debajo de umbral_minimo para no meter
        "ruido" en el prompt cuando no hay nada realmente relacionado.
        """
        if len(self.store) == 0:
            return []

        query_vector = self.embedder.encode(consulta)
        resultados = self.store.search(query_vector, k=k)

        return [doc.texto for doc, score in resultados if score >= umbral_minimo]

    def recuperar_con_metadata(self, consulta: str, k: int = 3) -> list[Documento]:
        """Igual que recuperar(), pero devuelve el documento completo con su metadata."""
        if len(self.store) == 0:
            return []
        query_vector = self.embedder.encode(consulta)
        return [doc for doc, _ in self.store.search(query_vector, k=k)]