# Pulse — Claude Code Context

Pulse is **Module 1** of a 3-module personal AI system built by an AI/ML Engineer.
Its purpose: deliver a daily digest of what matters across research, tooling, and the broader AI ecosystem — fully automated, no manual curation needed at runtime.

**Module Roadmap (for orientation only — focus is Module 1):**
- Module 1 → Pulse (this project, active build)
- Module 2 → Second Brain (RAG over personal notes/learnings)
- Module 3 → Workflow Automation Agent (depends on Module 2 memory layer)

---

## What Pulse Does

Pulse runs as a LangGraph agentic pipeline. Given a set of **topic profiles**, it:
1. Ingests data from monitored and searched sources (last 24 hours, capped per source type)
2. Deduplicates all ingested items in a single pass
3. Summarizes by source type
4. Merges into a final structured digest

It is designed to run once daily. There is **no retry logic** — pull limit is the quality gate.

---

## Stack

| Layer | Choice |
|---|---|
| Language | Python |
| Agent Framework | LangGraph |
| LLM Provider | Google Gemini via `google.genai` + `langchain_google_genai` |
| HTTP Client | `httpx` |
| Feed Parsing | `feedparser` |
| HTML Parsing | `BeautifulSoup` |
| Content Hashing | `hashlib` (SHA-256) |
| Research Papers | `arxiv` lib + HuggingFace RSS |
| News | NewsCatcherAPI |

---

## Project Structure

```
pulse/
├── CLAUDE.md
├── pulse/
│   ├── __init__.py
│   ├── types.py            # Shared types — single source of truth (RawItem lives here)
│   ├── config.py           # Constants: TOP_N per source, time windows, API keys
│   ├── state.py            # AgentState definition
│   ├── graph.py            # LangGraph graph assembly
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── github_release.py   # GitHub .atom RSS via feedparser
│   │   ├── docs.py             # BeautifulSoup + httpx + SHA-256 hashing
│   │   ├── research_paper.py   # arxiv lib + HuggingFace RSS
│   │   ├── news.py             # NewsCatcherAPI
│   │   └── blog.py             # feedparser + ranked RSS
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── ingestion/
│   │   │   ├── github_release_node.py
│   │   │   ├── docs_node.py
│   │   │   ├── research_paper_node.py
│   │   │   ├── news_node.py
│   │   │   └── blog_node.py
│   │   ├── dedup_node.py
│   │   ├── summarize/
│   │   │   ├── research_papers_node.py
│   │   │   ├── github_releases_node.py
│   │   │   ├── docs_node.py
│   │   │   ├── news_node.py
│   │   │   └── blogs_node.py
│   │   └── merge_digest_node.py
│   └── state/
│       ├── github_readme_hashes.json   # Persisted SHA-256 hashes for README change detection
│       └── docs_hashes.json            # Persisted SHA-256 hashes for docs change detection
```

---

## Core Types (`pulse/types.py`)

**This is the single source of truth. Do not redefine `RawItem` elsewhere.**

```python
from typing import Literal
from dataclasses import dataclass, field
from datetime import datetime

SourceType = Literal["github_release", "docs", "research_paper", "news", "blog"]

@dataclass
class RawItem:
    id: str                         # Unique identifier (URL or generated hash)
    source_type: SourceType
    title: str
    url: str
    content: str                    # Raw text / summary / changelog
    published_at: datetime
    topic: str                      # Which topic profile this came from
    metadata: dict = field(default_factory=dict)  # Source-specific extras
```

---

## AgentState (`pulse/state.py`)

```python
from typing import Annotated
from langgraph.graph import MessagesState
import operator

class AgentState(MessagesState):
    topic_profiles: list[dict]                          # Input: list of TopicProfile dicts
    raw_items: Annotated[list[RawItem], operator.add]   # Fan-in from all ingestion nodes
    deduped_items: list[RawItem]                        # Output of dedup node
    summaries: Annotated[list[dict], operator.add]      # Fan-in from all summarize nodes
    final_digest: str                                   # Output of merge_digest node
    errors: Annotated[list[str], operator.add]          # Accumulated errors, non-fatal
```

---

## Topic Profile Schema

```python
{
    "topic": str,           # e.g. "LLM Agents"
    "priority": int,        # 1 (highest) to 3 (lowest)
    "sources": [
        {
            "source_type": SourceType,
            "keywords": list[str],
            "urls": list[str],          # For docs/blogs
            "repos": list[str],         # For github_release — "owner/repo"
            "watchlist": list[str],     # For research_paper — arXiv categories or author IDs
        }
    ]
}
```

---

## Source Type Classification

### Monitored Sources (no LLM, pure code)
These use a curation list as the quality gate. No query generation.

| Source Type | Tool | Mechanism |
|---|---|---|
| `github_release` | `github_release.py` | GitHub `.atom` RSS via feedparser |
| `docs` | `docs.py` | httpx + BeautifulSoup + SHA-256 content hashing |
| `research_paper` | `research_paper.py` | `arxiv` lib + HuggingFace RSS |

### Searched Sources (LLM with tools)
These use LLM for query generation. Source ranking applies here. Dedup handles overlap (no relevancy rubric).

| Source Type | Tool | Mechanism |
|---|---|---|
| `news` | `news.py` | NewsCatcherAPI |
| `blog` | `blog.py` | feedparser + ranked RSS feeds |

---

## Ingestion Node Contract

Every ingestion node must follow this pattern — no exceptions:

```python
from datetime import datetime, timedelta, timezone
from pulse.config import TOP_N_BY_SOURCE
from pulse.types import RawItem, SourceType

CUTOFF = datetime.now(timezone.utc) - timedelta(hours=24)

def run(state: AgentState) -> dict:
    items: list[RawItem] = []

    for profile in state["topic_profiles"]:
        for source in profile["sources"]:
            if source["source_type"] != "github_release":  # guard per node
                continue
            try:
                fetched = fetch_github_releases(source)             # call tool
                filtered = [i for i in fetched if i.published_at >= CUTOFF]  # 24hr window
                capped = filtered[:TOP_N_BY_SOURCE["github_release"]]         # flat cap
                items.extend(capped)
            except Exception as e:
                return {"raw_items": items, "errors": [str(e)]}

    return {"raw_items": items}
```

**Key rules:**
- Filter to last 24 hours first, then apply `TOP_N` cap
- Errors are non-fatal — append to `errors`, return partial `raw_items`
- No retry logic — pull limit is final
- Each node only handles its own `source_type`

---

## Graph Topology

```
[START]
   |
   └──> [ingest_github_releases]  ──┐
   └──> [ingest_docs]              ──┤
   └──> [ingest_research_papers]   ──┤──> [dedup_node]
   └──> [ingest_news]              ──┤         |
   └──> [ingest_blogs]             ──┘         |
                                          (fan-out)
                                    ┌──> [summarize_research_papers]  ──┐
                                    ├──> [summarize_github_releases]   ──┤
                                    ├──> [summarize_docs]              ──┤──> [merge_digest_node] ──> [END]
                                    ├──> [summarize_news]              ──┤
                                    └──> [summarize_blogs]             ──┘
```

**Fan-out after ingestion:** All 5 ingestion nodes run in parallel (LangGraph parallel edges).
**Dedup:** Runs once after all ingestion nodes complete, over the fully merged `raw_items`.
**Summarization:** Fan-out by source type after dedup. Each node filters `deduped_items` by its `source_type`.
**Merge:** Single node assembles `summaries` into `final_digest`.

---

## Summarization Design

**Strategy: Batched by source type → merge**

Each summarize node:
1. Filters `deduped_items` to its `source_type`
2. Sends the batch to the LLM with a source-type-aware prompt
3. Returns a structured summary dict appended to `summaries`

```python
# Summary unit written to AgentState["summaries"]
{
    "source_type": SourceType,
    "topic": str,
    "summary_text": str,
    "item_count": int,
}
```

`merge_digest_node` assembles all summary units into the final structured markdown digest.

---

## Config (`pulse/config.py`)

```python
TOP_N_BY_SOURCE = {
    "github_release": 10,
    "docs": 10,
    "research_paper": 5,
    "news": 20,
    "blog": 10,
}

LOOKBACK_HOURS = 24
```

Tune `TOP_N_BY_SOURCE` values as needed — research papers are capped lower intentionally (high signal, low volume).

---

## Persistent State Files

| File | Purpose |
|---|---|
| `pulse/state/github_readme_hashes.json` | SHA-256 hashes of GitHub READMEs — diff detection |
| `pulse/state/docs_hashes.json` | SHA-256 hashes of doc pages — diff detection |

The `docs` tool writes to these after each run. Only changed content produces a `RawItem`.

---

## Active Build Status

| Component | Status |
|---|---|
| `github_release` tool | ✅ Built |
| `docs` tool | ✅ Built |
| `research_paper` tool | ✅ Built |
| `news` tool | ✅ Built |
| `blog` tool | ✅ Built |
| `pulse/types.py` consolidation | ⏳ Pending (`RawItem` duplicated across tool files) |
| Ingestion nodes | ⏳ Next |
| Dedup node | ⏳ Pending |
| Summarization nodes | ⏳ Pending |
| Merge digest node | ⏳ Pending |
| Graph assembly | ⏳ Pending |

---

## Open Decisions (do not assume defaults — ask first)

- **Research watchlist definition** — arXiv categories, author IDs, or both?
- **Summarize node prompt design** — format and depth of per-source summaries
- **Final digest format** — structured markdown sections per source type (likely), exact schema TBD
- **`TOP_N_BY_SOURCE` values** — defaults in config are provisional, tune after first run

---

## Key Conventions

- `RawItem` is defined **only** in `pulse/types.py` — import from there everywhere
- All datetimes are **UTC-aware** (`datetime.now(timezone.utc)`)
- Errors are **non-fatal** and accumulate in `AgentState["errors"]`
- No LLM calls in ingestion nodes — pure data fetching only
- LLM calls happen only in: searched source query generation (news/blog) and summarization nodes
