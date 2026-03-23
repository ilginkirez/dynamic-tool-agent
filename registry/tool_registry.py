"""Tool Registry — central catalogue for all available tools."""

from __future__ import annotations

import warnings

from .models import ToolSchema


class ToolRegistry:
    """In-memory registry that stores and queries tool schemas."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSchema] = {}

    # ── mutations ──────────────────────────────────────────────

    def register(self, tool: ToolSchema) -> None:
        """Register a tool. Emits a warning if the tool is deprecated."""
        if tool.deprecated:
            msg = f"Tool '{tool.name}' is deprecated."
            if tool.replaced_by:
                msg += f" Use '{tool.replaced_by}' instead."
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
        self._tools[tool.name] = tool

    # ── queries ────────────────────────────────────────────────

    def get(self, name: str) -> ToolSchema | None:
        """Return a single tool by its unique name, or None."""
        return self._tools.get(name)

    def list_all(self) -> list[ToolSchema]:
        """Return every registered tool."""
        return list(self._tools.values())

    def list_by_category(self, category: str) -> list[ToolSchema]:
        """Return tools that belong to the given category."""
        return [t for t in self._tools.values() if t.category == category]

    def search_by_tags(self, tags: list[str]) -> list[ToolSchema]:
        """Return tools whose tag list intersects with the supplied tags."""
        tag_set = set(tags)
        return [t for t in self._tools.values() if tag_set & set(t.tags)]

    # ── export ─────────────────────────────────────────────────

    def to_index_documents(self) -> list[dict]:
        """
        Produce a list of dicts ready to be upserted into ChromaDB.

        Each dict has:
          - id: tool name
          - document: concatenation of description, tags, and examples
          - metadata: name, category, tags (comma-separated), deprecated flag
        """
        docs: list[dict] = []
        for tool in self._tools.values():
            document = (
                tool.description
                + " "
                + " ".join(tool.tags)
                + " "
                + " ".join(tool.examples)
            )
            docs.append(
                {
                    "id": tool.name,
                    "document": document,
                    "metadata": {
                        "name": tool.name,
                        "category": tool.category,
                        "tags": ",".join(tool.tags),
                        "deprecated": tool.deprecated,
                    },
                }
            )
        return docs
