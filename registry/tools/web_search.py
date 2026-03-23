"""Web Search — simulates a web search engine returning relevant results."""

from __future__ import annotations

import hashlib

from registry.models import ToolParameter, ToolSchema, ToolVersion

SCHEMA = ToolSchema(
    name="web_search",
    display_name="Web Search",
    description=(
        "Performs a simulated web search and returns a ranked list of results "
        "including titles, snippets, and URLs. Useful for answering factual "
        "questions, finding documentation, researching topics, or discovering "
        "recent news and articles on any subject."
    ),
    category="data",
    tags=["search", "arama", "web", "google", "internet", "research"],
    parameters=[
        ToolParameter(name="query", type="string", description="Search query string"),
        ToolParameter(name="num_results", type="number", description="Number of results to return (1-10)", required=False),
        ToolParameter(name="language", type="string", description="Result language: 'en' or 'tr'", required=False),
    ],
    version=ToolVersion(major=1, minor=2, patch=0),
    examples=[
        "Search for 'LangGraph agent tutorial'.",
        "'Python asyncio best practices' konusunu araştır.",
        "Find recent articles about transformer architecture improvements.",
    ],
    callable_template="result = web_search(query='{query}')",
)

_MOCK_DOMAINS = [
    "docs.example.com",
    "blog.techworld.io",
    "stackoverflow.com",
    "medium.com",
    "dev.to",
    "github.com",
    "arxiv.org",
    "wikipedia.org",
]


def execute(params: dict) -> dict:
    """Return deterministic-ish mock search results based on the query."""
    query = params.get("query", "")
    num_results = int(params.get("num_results", 5))
    language = params.get("language", "en")

    results = []
    for i in range(min(num_results, 10)):
        seed = hashlib.md5(f"{query}-{i}".encode()).hexdigest()[:8]  # noqa: S324
        domain = _MOCK_DOMAINS[i % len(_MOCK_DOMAINS)]
        results.append(
            {
                "position": i + 1,
                "title": f"{query.title()} — Result {i + 1}",
                "url": f"https://{domain}/article/{seed}",
                "snippet": f"Comprehensive guide about {query}. This article covers key concepts, best practices, and practical examples.",
            }
        )

    return {"query": query, "language": language, "total_results": len(results), "results": results}
