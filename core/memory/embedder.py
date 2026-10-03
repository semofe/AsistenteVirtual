"""
embedder.py
-------------
Interfaz para convertir texto en vectores numéricos (embeddings), usados
por el sistema RAG para medir similitud semántica.

Se incluye una implementación por defecto basada en TF-IDF (rápida, sin
dependencias pesadas, sin conexión a internet), pero está pensada para
poder cambiarse por embeddings más potentes (ej. sentence-transformers)
sin tocar el resto del sistema -- solo se implementa Embedder y se
registra en la config, igual que con IAProvider.
"""

from abc import ABC, abstractmethod

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Embedder(ABC):
    @abstractmethod
    def fit(self, textos: list[str]) -> None:
        """Ajusta el vectorizador/modelo al corpus actual (si aplica)."""
        raise NotImplementedError

    @abstractmethod
    def encode(self, texto: str) -> np.ndarray:
        """Convierte un texto en un vector."""
        raise NotImplementedError

    @abstractmethod
    def encode_many(self, textos: list[str]) -> np.ndarray:
        """Convierte varios textos en una matriz de vectores."""
        raise NotImplementedError

    @staticmethod
    def similitud(a: np.ndarray, b: np.ndarray) -> float:
        """Similitud coseno entre dos vectores."""
        a = a.reshape(1, -1)
        b = b.reshape(1, -1)
        return float(cosine_similarity(a, b)[0][0])


class TfidfEmbedder(Embedder):
    """
    Embedder simple basado en TF-IDF. Ideal para empezar: no requiere
    descargar ningún modelo ni tener GPU. Es la misma técnica que ya usas
    en tu módulo de detección de patrones (ml_patrones.py), así que se
    mantiene consistencia dentro del proyecto.

    Limitación: solo capta similitud léxica (palabras en común), no
    significado profundo. Para eso, ver SentenceTransformerEmbedder abajo.
    """

    def __init__(self) -> None:
        self._vectorizer = TfidfVectorizer()
        self._fitted = False

    def fit(self, textos: list[str]) -> None:
        if not textos:
            return
        self._vectorizer.fit(textos)
        self._fitted = True

    def encode(self, texto: str) -> np.ndarray:
        if not self._fitted:
            # Si aún no hay corpus, ajustamos sobre la marcha con este único texto
            self.fit([texto])
        return self._vectorizer.transform([texto]).toarray()[0]

    def encode_many(self, textos: list[str]) -> np.ndarray:
        if not self._fitted:
            self.fit(textos)
        return self._vectorizer.transform(textos).toarray()


class SentenceTransformerEmbedder(Embedder):
    """
    Alternativa más potente (similitud semántica real, no solo léxica).
    Requiere: pip install sentence-transformers

    Para activarla, solo cambia en settings.json el embedder usado por
    RAGMemory -- no hay que tocar rag.py ni vector_store.py.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # pip install sentence-transformers

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def fit(self, textos: list[str]) -> None:
        # No hace falta "entrenar": el modelo ya viene preentrenado.
        pass

    def encode(self, texto: str) -> np.ndarray:
        return self._get_model().encode(texto)

    def encode_many(self, textos: list[str]) -> np.ndarray:
        return self._get_model().encode(textos)