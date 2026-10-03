"""
vector_store.py
------------------
Almacén simple de vectores + metadatos, persistido en un archivo JSON.
No requiere FAISS ni Chroma: para el volumen de datos de un asistente
personal (miles de recuerdos, no millones), una búsqueda lineal con
similitud coseno es más que suficiente y mucho más fácil de mantener.

Si en el futuro el corpus crece demasiado, esta clase se puede reemplazar
por una que use FAISS/Chroma sin cambiar la interfaz pública (add / search).
"""

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Documento:
    id: str
    texto: str
    vector: list[float]
    metadata: dict = field(default_factory=dict)


class VectorStore:
    def __init__(self, ruta_persistencia: str = "config/memoria_rag.json") -> None:
        self.ruta = Path(ruta_persistencia)
        self._documentos: list[Documento] = []
        self._cargar()

    def _cargar(self) -> None:
        if self.ruta.exists():
            with open(self.ruta, encoding="utf-8") as f:
                data = json.load(f)
            self._documentos = [Documento(**d) for d in data]

    def _guardar(self) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump([d.__dict__ for d in self._documentos], f, ensure_ascii=False, indent=2)

    def add(self, texto: str, vector: np.ndarray, metadata: dict | None = None) -> str:
        doc = Documento(
            id=str(uuid.uuid4()),
            texto=texto,
            vector=vector.tolist(),
            metadata=metadata or {},
        )
        self._documentos.append(doc)
        self._guardar()
        return doc.id

    def search(self, query_vector: np.ndarray, k: int = 3) -> list[tuple[Documento, float]]:
        """Devuelve los k documentos más similares al vector de consulta."""
        if not self._documentos:
            return []

        resultados = []
        for doc in self._documentos:
            sim = self._cosine(query_vector, np.array(doc.vector))
            resultados.append((doc, sim))

        resultados.sort(key=lambda x: x[1], reverse=True)
        return resultados[:k]

    def all_texts(self) -> list[str]:
        """Útil para reajustar (fit) embedders como TF-IDF con todo el corpus."""
        return [d.texto for d in self._documentos]

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        if a.shape != b.shape:
            # Puede pasar si el embedder (ej. TF-IDF) cambió su vocabulario
            # entre que se guardó el documento y ahora. En ese caso, se
            # considera no comparable.
            return -1.0
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def __len__(self) -> int:
        return len(self._documentos)