"""VectorStore — ChromaDB wrapper for tool similarity search."""

from __future__ import annotations

import os

import chromadb
from dotenv import load_dotenv

from .embedder import Embedder

load_dotenv()


class VectorStore:
    """Manages a ChromaDB collection of tool embeddings for semantic search."""

    def __init__(self) -> None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(name="tools")
        self._embedder = Embedder()

    # ── indexing ───────────────────────────────────────────────

    def index_tools(self, documents: list[dict]) -> None:
        """
        Index tool documents into ChromaDB.

        Accepts the output of ``ToolRegistry.to_index_documents()``.
        If the collection already contains data it is cleared first so
        the index always reflects the current tool registry state.

        Each dict is expected to have:
          - id: str
          - document: str
          - metadata: dict
        """
        # Clear existing data if collection is not empty
        if self._collection.count() > 0:
            existing_ids = self._collection.get()["ids"]
            if existing_ids:
                self._collection.delete(ids=existing_ids)

        ids = [doc["id"] for doc in documents]
        texts = [doc["document"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]

        embeddings = self._embedder.embed_batch(texts)

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    # ── querying ───────────────────────────────────────────────

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        """
        Perform a semantic similarity search against the indexed tools.

        Returns a list of dicts, each containing:
          - tool_name: str
          - category: str
          - tags: list[str]
          - distance: float
          - deprecated: bool
        """
        query_embedding = self._embedder.embed(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        hits: list[dict] = []
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for i, tool_id in enumerate(ids):
            meta = metadatas[i] if i < len(metadatas) else {}
            hits.append(
                {
                    "tool_name": meta.get("name", tool_id),
                    "category": meta.get("category", ""),
                    "tags": meta.get("tags", "").split(",") if meta.get("tags") else [],
                    "distance": distances[i] if i < len(distances) else 0.0,
                    "deprecated": bool(meta.get("deprecated", False)),
                }
            )

        return hits
