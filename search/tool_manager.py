"""ToolManager — hybrid search + LLM re-ranking + inertial scoring."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from registry.models import ToolSchema
from registry.tool_registry import ToolRegistry

from .vector_store import VectorStore

load_dotenv()

_STATS_PATH = Path("logs/tool_stats.json")


class ToolManager:
    """
    Orchestrates 3-stage hybrid tool discovery:

    1. Tag / keyword filtering
    2. Semantic similarity via ChromaDB
    3. Score merging with inertial boost + threshold cut-off

    Optionally re-ranks the shortlist with an LLM call.

    The inertial scoring is a pragmatic adaptation of the TIG
    (Tool Inertia Graph) paper's *inertial selection* principle:
    tools that historically succeed get a mild boost, but never
    enough to dominate the semantic signal.
    """

    def __init__(self, registry: ToolRegistry, vector_store: VectorStore) -> None:
        self.registry = registry
        self.vector_store = vector_store

        self.llm = ChatGroq(
            model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY", ""),
        )
        self.threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

        # ── TIG — usage statistics ─────────────────────────────
        self._usage_stats: dict[str, dict] = {}
        if _STATS_PATH.exists():
            try:
                self._usage_stats = json.loads(_STATS_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._usage_stats = {}

    # ── public API ─────────────────────────────────────────────

    def find_tools(self, user_query: str, top_k: int = 3) -> list[ToolSchema]:
        """
        3-stage hybrid search.

        Stage 1 — Tag / keyword filter:
            Compare query tokens against every tool's tags (case-insensitive
            substring match). Collect matching tool names in *keyword_matches*.

        Stage 2 — Semantic search:
            Run ``vector_store.search`` to get the nearest 10 tools by
            embedding distance. Convert ChromaDB L2 distance to a
            similarity score: ``semantic_score = 1 - distance``.
            Discard deprecated tools.

        Stage 3 — Score merging + threshold:
            For each candidate, compute:
                inertial  = _inertial_score(tool_name)
                combined  = semantic_score * inertial
                if tool in keyword_matches: combined *= 1.3
            Drop candidates below ``self.threshold``.
            Return the top-*k* ``ToolSchema`` objects.
        """

        # ── Stage 1: keyword / tag matching ────────────────────
        query_tokens = user_query.lower().split()
        keyword_matches: set[str] = set()

        for tool in self.registry.list_all():
            tool_tags_lower = [tag.lower() for tag in tool.tags]
            for token in query_tokens:
                # IMPORTANT: check 'tag in token' to support Turkish suffixes
                # e.g., if tag is 'pdf', it should match token 'pdf'in' or 'pdfi'
                if any(tag in token for tag in tool_tags_lower):
                    keyword_matches.add(tool.name)
                    break

        # ── Stage 2: semantic search ───────────────────────────
        semantic_results = self.vector_store.search(user_query, n_results=10)

        # ── Stage 3: score merging ─────────────────────────────
        scored: list[tuple[float, str]] = []

        for hit in semantic_results:
            tool_name: str = hit["tool_name"]

            # skip deprecated
            if hit.get("deprecated"):
                continue

            # Convert L2 distance (0-2) to cosine similarity (0-1)
            semantic_score = 1.0 - (hit["distance"] / 2.0)

            # inertial boost (TIG)
            inertial = self._inertial_score(tool_name)
            combined_score = semantic_score * inertial

            # keyword boost
            if tool_name in keyword_matches:
                combined_score *= 1.3

            if combined_score >= self.threshold:
                scored.append((combined_score, tool_name))

        # sort descending, take top_k
        scored.sort(key=lambda x: x[0], reverse=True)
        top_names = [name for _, name in scored[:top_k]]

        results: list[ToolSchema] = []
        for name in top_names:
            schema = self.registry.get(name)
            if schema is not None:
                results.append(schema)

        return results

    def rerank_with_llm(self, query: str, candidates: list[ToolSchema]) -> list[ToolSchema]:
        """
        Ask the LLM to pick the actually-relevant tools from *candidates*.

        Prompt template asks for a JSON list of tool names.
        Falls back to returning *candidates* unchanged on parse errors.
        """
        if not candidates:
            return []

        tool_descriptions = "\n".join(
            f"- {t.name}: {t.description}" for t in candidates
        )

        prompt = (
            f"Kullanıcı şunu istiyor: {query}\n\n"
            "Aşağıdaki tool'lardan hangisi/hangileri gerçekten bu işi yapabilir?\n"
            'Sadece uygun olanların isimlerini JSON listesi olarak döndür: ["tool_name1", ...]\n'
            "Eğer hiçbiri uygun değilse boş liste döndür: []\n\n"
            f"Mevcut tool'lar:\n{tool_descriptions}"
        )

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()

            # Extract JSON array from response (handle markdown fences)
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            selected_names: list[str] = json.loads(content)

            if not isinstance(selected_names, list):
                return candidates  # fallback on bad format

            name_set = set(selected_names)
            reranked = [t for t in candidates if t.name in name_set]
            
            # If the LLM explicitly returned an empty list, it means NO tool is suitable.
            # We MUST return [] here to drop the false positives, rather than falling back
            # to all candidates.
            return reranked

        except (json.JSONDecodeError, Exception):
            # Parse error or LLM call failure → return None to signal failure or candidates
            return candidates

    def search_and_rerank(self, user_query: str) -> list[ToolSchema]:
        """
        Full pipeline: ``find_tools`` → ``rerank_with_llm``.

        If ``find_tools`` returns nothing, short-circuits and returns ``[]``
        without making an LLM call.
        """
        candidates = self.find_tools(user_query)
        if not candidates:
            return []
        return self.rerank_with_llm(user_query, candidates)

    # ── TIG helpers ────────────────────────────────────────────

    def _inertial_score(self, tool_name: str) -> float:
        stats = self._usage_stats.get(tool_name)
        if not stats or stats.get("total", 0) == 0:
            return 1.0
        success_rate = stats["success"] / stats["total"]
        return 0.7 + (success_rate * 0.3)  # minimum 0.7, maksimum 1.0

    def update_stats(self, tool_name: str, success: bool) -> None:
        """
        Record a tool execution result and persist to disk.

        Called by the logger / agent after each tool invocation.
        """
        if tool_name not in self._usage_stats:
            self._usage_stats[tool_name] = {"success": 0, "fail": 0, "total": 0}

        entry = self._usage_stats[tool_name]
        entry["total"] += 1
        if success:
            entry["success"] += 1
        else:
            entry["fail"] += 1

        # Persist
        _STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _STATS_PATH.write_text(
            json.dumps(self._usage_stats, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
