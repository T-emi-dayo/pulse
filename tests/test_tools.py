"""
Tool test runner for Pulse ingestion tools.

Goals:
    1. Verify each tool is functioning and returning data
    2. Inspect the raw response structure of each tool
    3. Identify schema inconsistencies ahead of normalization

Usage:
    Run all tools:
        python -m tests.test_tools

    Run a specific tool:
        python -m tests.test_tools github_releases
        python -m tests.test_tools github_readmes
        python -m tests.test_tools docs
        python -m tests.test_tools arxiv
        python -m tests.test_tools huggingface
        python -m tests.test_tools news
        python -m tests.test_tools blogs
"""

import sys
import json
from pprint import pformat

from src.config.settings import settings
from src.tools.github_search_tool import fetch_github_releases, fetch_github_readmes
from src.tools.doc_search_tool import fetch_docs
from src.tools.research_search_tool import fetch_arxiv_papers, fetch_huggingface_papers
from src.tools.news_tool import fetch_news
from src.tools.blog_tool import fetch_blogs


# ── Test inputs ───────────────────────────────────────────────────────────────

GITHUB_REPOS = [
    "langchain-ai/langgraph",
    "anthropics/anthropic-sdk-python",
    "openai/openai-python",
    "microsoft/autogen",
]

DOC_URLS = [
    "https://python.langchain.com/docs/introduction/",
    "https://docs.anthropic.com/en/docs/overview",
]

RESEARCH_KEYWORDS = ["LLM agents", "reasoning", "retrieval augmented generation"]

NEWS_KEYWORDS = [""]

BLOG_FEED_URLS = [
    "https://huggingface.co/blog/feed.xml",
    "https://blog.langchain.dev/rss/",
]
BLOG_KEYWORDS = ["agent", "LLM", "fine-tuning", "RAG"]


# ── Display helpers ───────────────────────────────────────────────────────────

DIVIDER = "=" * 72
SUBDIV  = "-" * 72


def _print_header(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def _print_result(items: list, tool_name: str) -> None:
    print(f"\n[{tool_name}] returned {len(items)} item(s)")

    if not items:
        print("  ⚠  No items returned — check inputs or 24h window.")
        return

    print(f"\n{'FIRST ITEM — full structure':^72}")
    print(SUBDIV)
    first = items[0]
    # Print as clean JSON-like output so every field is visible
    for key, value in first.items():
        if isinstance(value, str) and len(value) > 120:
            display = value[:120] + "…"
        else:
            display = value
        print(f"  {key:<16}: {display!r}")

    if len(items) > 1:
        print(f"\n{'ALL ITEMS — titles':^72}")
        print(SUBDIV)
        for i, item in enumerate(items, 1):
            published = item.get("published_at", "unknown date")
            print(f"  [{i:02d}] {item['title'][:70]}")
            print(f"        published_at : {published}")
            print(f"        url          : {item['url'][:80]}")
            print()


# ── Individual tool tests ─────────────────────────────────────────────────────

def test_github_releases() -> None:
    _print_header("TOOL: fetch_github_releases")
    print(f"  Repos : {GITHUB_REPOS}")
    print()

    try:
        items = fetch_github_releases(GITHUB_REPOS)
        _print_result(items, "fetch_github_releases")
    except Exception as e:
        print(f"  ✗ EXCEPTION: {e}")


def test_github_readmes() -> None:
    _print_header("TOOL: fetch_github_readmes")
    print(f"  Repos : {GITHUB_REPOS}")
    print()

    try:
        items = fetch_github_readmes(GITHUB_REPOS)
        _print_result(items, "fetch_github_readmes")
    except Exception as e:
        print(f"  ✗ EXCEPTION: {e}")


def test_docs() -> None:
    _print_header("TOOL: fetch_docs")
    print(f"  URLs  : {DOC_URLS}")
    print()

    try:
        items = fetch_docs(DOC_URLS)
        _print_result(items, "fetch_docs")
    except Exception as e:
        print(f"  ✗ EXCEPTION: {e}")


def test_arxiv() -> None:
    _print_header("TOOL: fetch_arxiv_papers")
    print(f"  Keywords : {RESEARCH_KEYWORDS}")
    print()

    try:
        items = fetch_arxiv_papers(RESEARCH_KEYWORDS, max_results=5)
        _print_result(items, "fetch_arxiv_papers")
    except Exception as e:
        print(f"  ✗ EXCEPTION: {e}")


def test_huggingface() -> None:
    _print_header("TOOL: fetch_huggingface_papers")
    print(f"  Keywords : {RESEARCH_KEYWORDS}")
    print()

    try:
        items = fetch_huggingface_papers(RESEARCH_KEYWORDS)
        _print_result(items, "fetch_huggingface_papers")
    except Exception as e:
        print(f"  ✗ EXCEPTION: {e}")


def test_news() -> None:
    _print_header("TOOL: fetch_news")
    print(f"  Keywords : {NEWS_KEYWORDS}")
    print(f"  API key  : {'SET' if settings.NEWS_API_KEY else 'MISSING — set NEWS_API_KEY in .env'}")
    print()

    if not settings.NEWS_API_KEY:
        print("  ⚠  Skipping — NEWS_API_KEY not configured.")
        return

    try:
        items = fetch_news(NEWS_KEYWORDS, api_key=settings.NEWS_API_KEY, page_size=5)
        _print_result(items, "fetch_news")
    except Exception as e:
        print(f"  ✗ EXCEPTION: {e}")


def test_blogs() -> None:
    _print_header("TOOL: fetch_blogs")
    print(f"  Feed URLs : {BLOG_FEED_URLS}")
    print(f"  Keywords  : {BLOG_KEYWORDS}")
    print()

    try:
        items = fetch_blogs(BLOG_FEED_URLS, BLOG_KEYWORDS)
        _print_result(items, "fetch_blogs")
    except Exception as e:
        print(f"  ✗ EXCEPTION: {e}")


# ── Registry & runner ─────────────────────────────────────────────────────────

TESTS = {
    "github_releases" : test_github_releases,
    "github_readmes"  : test_github_readmes,
    "docs"            : test_docs,
    "arxiv"           : test_arxiv,
    "huggingface"     : test_huggingface,
    "news"            : test_news,
    "blogs"           : test_blogs,
}


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target == "all":
        print("\n🔍 Running all tool tests...\n")
        for name, fn in TESTS.items():
            fn()
    elif target in TESTS:
        TESTS[target]()
    else:
        print(f"Unknown tool '{target}'. Available: {', '.join(TESTS)} or 'all'")
        sys.exit(1)

    print(f"\n{DIVIDER}")
    print("  Done.")
    print(DIVIDER)


if __name__ == "__main__":
    main()
