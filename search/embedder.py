"""Embedder — generates vector embeddings using SentenceTransformers."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()


class Embedder:
    """Thin wrapper around a SentenceTransformer model for text embedding."""

    def __init__(self) -> None:
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self._model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        """Return the embedding vector for a single text string."""
        vector = self._model.encode(text)
        return vector.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a batch of text strings."""
        vectors = self._model.encode(texts)
        return [v.tolist() for v in vectors]
