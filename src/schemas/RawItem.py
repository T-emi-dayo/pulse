from typing import TypedDict


class RawItem(TypedDict):
    """Single source of truth for raw items returned by all ingestion tools."""
    title: str
    url: str
    source: str | None
    source_type: str        # "github_release" | "docs" | "research_paper" | "news" | "blog"
    excerpt: str
    published_at: str       # ISO 8601, UTC
    content_hash: str | None
    full_content: str | None
