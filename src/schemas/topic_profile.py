from typing import TypedDict, Optional

class SourceConfig(TypedDict):
    source_type: str          # "news" | "blog" | "github_release" | "research_paper" | "docs"
    keywords: list[str]       # for news/blogs — LLM uses these as anchors
    urls: list[str]           # for docs — specific pages to monitor
    repos: list[str]          # for github_release — e.g. ["langchain-ai/langgraph"]
    watchlist: list[str]      # for research_paper — authors, labs, or arxiv categories

class TopicProfile(TypedDict):
    topic: str                # e.g. "LLM Frameworks"
    priority: int             # 1 = highest — influences merge summarization ordering
    sources: list[SourceConfig]