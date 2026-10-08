# Pulse — Claude Code Context

Pulse is **Module 1** of a 3-module personal AI system built by an AI/ML Engineer.
Its purpose: deliver a daily digest of what matters across research, tooling, and the broader AI ecosystem — fully automated, no manual curation needed at runtime.

**Module Roadmap (for orientation only — focus is Module 1):**
- Module 1 → Pulse (this project)
- Module 2 → Second Brain (RAG over personal notes/learnings)
- Module 3 → Workflow Automation Agent (depends on Module 2 memory layer)

See [README.md](README.md) for setup, running and deployment.

---

## What Pulse Does

A LangGraph pipeline. Given a set of **topic profiles** (`src/config/profiles.py`), it:
1. Ingests data from five source types (last 24 hours, capped per source type)
2. Deduplicates all ingested items in a single pass (by URL)
3. Summarizes by source type (Gemini)
4. Merges into a markdown digest
5. Emails the digest via Resend (`src/runner.py`)

It runs once daily as a Render cron job. There is **no retry logic** — pull limit is the quality gate.

---

## Stack

| Layer | Choice |
|---|---|
| Language | Python 3.13+, managed with `uv` |
| Agent Framework | LangGraph |
| LLM Provider | Google Gemini via `google.genai` + `langchain_google_genai` (default `gemini-2.5-flash`) |
| HTTP Client | `httpx` |
| Feed Parsing | `feedparser` |
| HTML Parsing | `BeautifulSoup` (`trafilatura` is also a dependency) |
| Content Hashing | `hashlib` (SHA-256) |
| Research Papers | `arxiv` lib + HuggingFace papers RSS |
| News | DuckDuckGo news via `ddgs` (no API key) |
| Email | Resend |

---

## Project Structure

```
Pulse/
├── CLAUDE.md, README.md
├── pyproject.toml, uv.lock
├── render.yaml                       # Cron: 04:00 UTC, `uv run python -m src.runner`
├── docs/                             # RULE.md (coding rules), AGENTIC_SYSTEM_TEMPLATE.md (generic template)
├── pulse/state/
│   ├── github_readme_hashes.json     # SHA-256 hashes for README change detection
│   └── docs_hashes.json              # SHA-256 hashes for docs change detection
├── tests/                            # unit/, integration/, e2e/ (empty) + ad-hoc tool scripts
└── src/
    ├── runner.py                     # Entry point: invoke graph, email digest
    ├── graph.py                      # Graph assembly, exports `pulse_graph`
    ├── agents/
    │   ├── base_node.py              # BaseNode (holds AIService)
    │   ├── ingestion_nodes.py        # IngestionNode: one method per source type
    │   ├── dedup_node.py
    │   ├── summarization_node.py     # SummarizationNode: one method per source type
    │   └── merge_digest_node.py
    ├── tools/                        # github_search_tool, doc_search_tool, research_search_tool,
    │                                 # news_tool, blog_tool
    ├── schemas/
    │   ├── RawItem.py                # RawItem (tool output)
    │   ├── state.py                  # AgentState, IngestedItem, SummaryItem
    │   └── topic_profile.py          # TopicProfile, SourceConfig
    ├── config/
    │   ├── settings.py               # Settings (env), TOP_N_BY_SOURCE, LOOKBACK_HOURS
    │   └── profiles.py               # TOPIC_PROFILES
    ├── prompts/templates.py          # Summarization prompts
    └── services/                     # AIService.py (Gemini), email_service.py (Resend)
```

`src/main.py`, root `main.py`, `Dockerfile`, `docker-compose.yml` and `src/services/base_service.py` are leftovers from an earlier FastAPI scaffold. `src/main.py` imports a non-existent `src.api`. Do not build on them.

---

## Core Types

**Tools return `RawItem`; nodes convert to `IngestedItem`.** Each is defined once; import, do not redefine.

`src/schemas/RawItem.py` — `TypedDict` returned by every tool:
```python
class RawItem(TypedDict):
    title: str
    url: str
    source: str | None
    source_type: str        # "github_release" | "docs" | "research_paper" | "news" | "blog"
    excerpt: str
    published_at: str       # ISO 8601, UTC
    content_hash: str | None
    full_content: str | None
```

`src/schemas/state.py` — Pydantic models:
```python
class IngestedItem(BaseModel):
    title: str; url: str; source_type: str
    source_name: str                    # e.g. domain, repo owner, "arxiv"
    source_rank: Optional[int] = None   # news/blog only
    topic: str; excerpt: str; published_at: str

class SummaryItem(BaseModel):
    source_type: str; summary_text: str; item_count: int

class AgentState(BaseModel):
    topic_profiles: list[TopicProfile]
    raw_items: Annotated[list[IngestedItem], operator.add]   # fan-in from ingestion
    deduped_items: list[IngestedItem]
    summaries: Annotated[list[SummaryItem], operator.add]    # fan-in from summarize
    final_digest: str
    errors: Annotated[list[str], operator.add]               # non-fatal
```

`src/schemas/topic_profile.py`:
```python
class SourceConfig(TypedDict):
    source_type: str
    keywords: list[str]     # news/blog/research queries
    urls: list[str]         # docs pages, blog feeds
    repos: list[str]        # github_release: "owner/repo"
    watchlist: list[str]    # research_paper: arXiv categories
class TopicProfile(TypedDict):
    topic: str
    priority: int           # 1 (highest) to 3 (lowest)
    sources: list[SourceConfig]
```

---

## Source Types

| Source Type | Tool | Mechanism |
|---|---|---|
| `github_release` | `fetch_github` | GitHub `.atom` via feedparser, plus README hash diff |
| `docs` | `fetch_docs` | httpx + BeautifulSoup + SHA-256 hash diff; only changed pages emit items |
| `research_paper` | `fetch_research_papers` | `arxiv` + HuggingFace RSS, de-duplicated by URL |
| `news` | `fetch_news` | `ddgs` news search; keywords joined into one OR query |
| `blog` | `fetch_blogs` | feedparser over profile URLs, falling back to `DEFAULT_FEEDS` |

All ingestion is pure code. No LLM is used before summarization.

---

## Ingestion Node Contract

`IngestionNode` has one method per source type (`ingest_github_releases`, `ingest_docs`, `ingest_research_papers`, `ingest_news`, `ingest_blogs`). Each:

1. Collects the profiles' source configs for its own `source_type` (`_extract_profiles`)
2. Calls its tool, then caps with `TOP_N_BY_SOURCE[source_type]`. GitHub also filters to `LOOKBACK_HOURS`; the tools apply a 24h cutoff themselves.
3. Converts `RawItem` to `IngestedItem` (`source_name`, `source_rank` for news/blog)
4. On exception, appends `"[ingest_x] <msg>"` to a local `errors` list and continues
5. Returns `{"raw_items": items, "errors": errors}`

No retries. Errors are non-fatal.

---

## Graph Topology (`src/graph.py`)

```
START ──> 5 ingest nodes (parallel) ──> dedup ──> 5 summarize nodes (parallel) ──> merge_digest ──> END
```

- Dedup: by URL, first-seen order, over merged `raw_items`.
- Each summarize node filters `deduped_items` by its `source_type`, calls Gemini with the prompt from `src/prompts/templates.py`, and returns a `SummaryItem`. No items means no summary; an LLM failure appends an error.
- `merge_digest` (no LLM) orders sections: research papers, GitHub releases, docs, news, blogs, then lists errors.
- Summaries are per source type across all topics, not per topic.

---

## Config

`src/config/settings.py`:
- `Settings` (pydantic-settings, reads `.env`): `GEMINI_API_KEY`, `RESEND_API_KEY`, `DIGEST_FROM_EMAIL`, `DIGEST_TO_EMAIL`, `BASE_MODEL`, `INGESTION_MODEL`, `SUMMARIZATION_MODEL`
- `TOP_N_BY_SOURCE = {github_release: 10, docs: 10, research_paper: 5, news: 20, blog: 10}`
- `LOOKBACK_HOURS = 24`

`NEWS_API_KEY` / `SERP_API_KEY` exist in settings but are unused.

---

## Persistent State

| File | Purpose |
|---|---|
| `pulse/state/github_readme_hashes.json` | SHA-256 of GitHub READMEs — diff detection |
| `pulse/state/docs_hashes.json` | SHA-256 of doc pages — diff detection |

Paths are relative to the working directory, so run from the repo root. They are rewritten on every run and show as modified in git.

---

## Build Status

All pipeline components are built: tools, ingestion, dedup, summarization, merge, graph, runner, email delivery and the Render cron config.

Remaining:
- Tests (`tests/unit`, `integration`, `e2e` are empty)
- Remove the leftover FastAPI scaffold (`src/main.py`, `main.py`, `Dockerfile`, `docker-compose.yml`, `base_service.py`) or point it at `src.runner`
- Hash stores need persistent storage on Render (ephemeral disk resets them)

## Open Decisions (do not assume defaults — ask first)

- **Research watchlist definition** — currently arXiv categories; author IDs not supported
- **Summarize prompt design** — current prompts are one paragraph per source type
- **Final digest schema** — currently markdown sections per source type
- **`TOP_N_BY_SOURCE` values** — provisional, tune after first runs

---

## Key Conventions

- Follow [docs/RULE.md](docs/RULE.md): iterate on existing code, stay in scope, keep files short, comment only the why
- All datetimes are **UTC-aware** (`datetime.now(timezone.utc)`)
- Errors are **non-fatal** and accumulate in `AgentState.errors`
- No LLM calls in ingestion nodes — LLM calls happen only in summarization nodes
- Run commands from the repo root with `uv run`
