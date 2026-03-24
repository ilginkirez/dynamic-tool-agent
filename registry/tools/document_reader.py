"""Document Reader — simulates reading and summarising content from a URL."""

from __future__ import annotations

import hashlib

from registry.models import ToolParameter, ToolSchema, ToolVersion

SCHEMA = ToolSchema(
    name="document_reader",
    display_name="Document Reader",
    description=(
        "Reads and extracts text content from a given URL, supporting web pages, "
        "PDFs, and plain-text documents. Returns the document title, a brief "
        "summary, word count, and extracted key points. Useful for research, "
        "content curation, and automated information gathering."
    ),
    category="utility",
    tags=["document", "belge", "reader", "url", "pdf", "read", "extract", "okuma", "özetle", "makale"],
    parameters=[
        ToolParameter(name="url", type="string", description="URL of the document to read"),
        ToolParameter(name="summarize", type="boolean", description="Whether to return a summary", required=False),
    ],
    version=ToolVersion(major=1, minor=0, patch=0),
    examples=[
        "Read and summarize the article at https://example.com/blog/ai-agents.",
        "Bu PDF'nin içeriğini oku: https://arxiv.org/pdf/2305.12345",
        "Extract key points from the LangChain documentation page.",
    ],
    callable_template="result = document_reader(url='{url}')",
)


def execute(params: dict) -> dict:
    """Return mock document content based on URL."""
    url = params.get("url", "https://example.com")
    summarize = params.get("summarize", True)

    # Deterministic mock based on URL
    url_hash = hashlib.md5(url.encode()).hexdigest()[:6]  # noqa: S324
    word_count = int(url_hash[:4], 16) % 5000 + 500

    result: dict = {
        "url": url,
        "title": f"Document from {url.split('/')[2] if '/' in url else url}",
        "word_count": word_count,
        "language": "en",
        "key_points": [
            "The document discusses modern approaches to the topic.",
            "Several case studies and benchmarks are presented.",
            "Key recommendations are provided for practitioners.",
        ],
        "success": True,
    }

    if summarize:
        result["summary"] = (
            f"This document ({word_count} words) provides a comprehensive overview "
            "of the topic, covering theoretical foundations and practical applications. "
            "It concludes with actionable recommendations for implementation."
        )

    return result
