# Pulse

Pulse is **Module 1** of a 3-module personal AI system. It builds a daily digest of what matters across AI research, tooling, and the wider ecosystem, then emails it. Once configured, it runs with no manual curation.

| Module | Name | Status |
|---|---|---|
| 1 | Pulse (this repo) | Active |
| 2 | Second Brain (RAG over personal notes) | Planned |
| 3 | Workflow Automation Agent | Planned |

## How it works

Pulse is a [LangGraph](https://langchain-ai.github.io/langgraph/) pipeline. It runs once a day, with no retry logic. The per-source pull limit is the quality gate.

```
START ─┬─> ingest_github_releases ─┐
       ├─> ingest_docs            ─┤
       ├─> ingest_research_papers ─┼─> dedup ─┬─> summarize_github_releases ─┐
       ├─> ingest_news            ─┤          ├─> summarize_docs            ─┤
       └─> ingest_blogs           ─┘          ├─> summarize_research_papers ─┼─> merge_digest ─> END
                                              ├─> summarize_news            ─┤
                                              └─> summarize_blogs           ─┘
```

1. **Ingest**: five nodes run in parallel. Each pulls items from the last 24 hours (`LOOKBACK_HOURS`) and caps them per source type (`TOP_N_BY_SOURCE`). Ingestion makes no LLM calls.
2. **Dedup**: one pass over all ingested items, by URL, keeping first-seen order.
3. **Summarize**: five nodes run in parallel, one per source type. Each sends its batch to Gemini with a source-specific prompt.
4. **Merge**: assembles the summaries into a markdown digest. No LLM call.
5. **Deliver**: `src/runner.py` emails the digest through Resend as HTML with a plain-text fallback.

Errors are non-fatal. Each node appends to `errors` and returns whatever it collected, and the digest lists the errors at the end.

### Sources

| Source type | Tool | Mechanism |
|---|---|---|
| `github_release` | `src/tools/github_search_tool.py` | GitHub `.atom` feeds via `feedparser`, plus README change detection (SHA-256) |
| `docs` | `src/tools/doc_search_tool.py` | `httpx` + `BeautifulSoup`, SHA-256 hash diff; only changed pages produce an item |
| `research_paper` | `src/tools/research_search_tool.py` | `arxiv` library + HuggingFace papers RSS, de-duplicated by URL |
| `news` | `src/tools/news_tool.py` | DuckDuckGo news search via `ddgs` (no API key) |
| `blog` | `src/tools/blog_tool.py` | `feedparser` over RSS feeds, with default feeds when a profile has none |

Hashes for change detection are persisted in `pulse/state/docs_hashes.json` and `pulse/state/github_readme_hashes.json`.

## Project structure

```
Pulse/
├── pyproject.toml, uv.lock       # Dependencies (managed with uv)
├── render.yaml                   # Render cron job (daily at 04:00 UTC)
├── Dockerfile, docker-compose.yml
├── .env.example
├── CLAUDE.md                     # Context for Claude Code
├── docs/                         # Design notes and project rules
├── pulse/state/                  # Persisted SHA-256 hash stores (JSON)
├── tests/                        # unit/, integration/, e2e/ and tool scripts
└── src/
    ├── runner.py                 # Entry point: run graph, email digest
    ├── graph.py                  # LangGraph assembly (pulse_graph)
    ├── agents/                   # Graph nodes
    │   ├── base_node.py
    │   ├── ingestion_nodes.py
    │   ├── dedup_node.py
    │   ├── summarization_node.py
    │   └── merge_digest_node.py
    ├── tools/                    # One fetcher per source type
    ├── schemas/                  # AgentState, RawItem, TopicProfile
    ├── config/
    │   ├── settings.py           # Env settings, TOP_N_BY_SOURCE, LOOKBACK_HOURS
    │   └── profiles.py           # TOPIC_PROFILES: what to track
    ├── prompts/templates.py      # Summarization prompts
    └── services/                 # AIService (Gemini), email_service (Resend)
```

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env     # then fill in the values below
```

### Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Summarization via Google Gemini |
| `RESEND_API_KEY` | Yes | Sending the digest email |
| `DIGEST_FROM_EMAIL` | Yes | Sender; the address must be verified in Resend |
| `DIGEST_TO_EMAIL` | Yes | Recipient |
| `BASE_MODEL`, `SUMMARIZATION_MODEL`, `INGESTION_MODEL` | No | Gemini model names (default `gemini-2.5-flash`) |

`.env.example` also contains template entries (LLM provider, vector DB, Redis, `NEWS_API_KEY`) that Pulse does not currently read.

## Running

```bash
uv run python -m src.runner
```

This runs the full pipeline and sends the email. It exits non-zero if the graph fails, no digest is produced, or email is not configured.

To run only the graph and print the digest:

```python
from src.graph import pulse_graph
from src.config.profiles import TOPIC_PROFILES

result = pulse_graph.invoke({"topic_profiles": TOPIC_PROFILES})
print(result["final_digest"])
```

## Configuration

**Topic profiles** (`src/config/profiles.py`) define what Pulse tracks. Current topics, by priority:

1. LLM Agents & Frameworks (1)
2. Foundation Models & Research (1)
3. MLOps & AI Infrastructure (2)
4. Open Source Models & Fine-tuning (2)
5. AI Safety & Evaluation (3)

Each profile lists sources, and each source has the fields `source_type`, `keywords`, `urls`, `repos` (`owner/repo`), and `watchlist` (arXiv categories).

**Caps** (`src/config/settings.py`): `TOP_N_BY_SOURCE` is currently github_release 10, docs 10, research_paper 5, news 20, blog 10. The values are provisional and will be tuned after the first runs. `LOOKBACK_HOURS` is 24.

**Prompts** live in `src/prompts/templates.py`.

## Deployment

Pulse deploys as a Render cron job (`render.yaml`):

- Schedule: `0 4 * * *` (04:00 UTC, 05:00 WAT)
- Build: `pip install uv && uv sync --frozen`
- Start: `uv run python -m src.runner`
- Set `GEMINI_API_KEY`, `RESEND_API_KEY`, `DIGEST_FROM_EMAIL` and `DIGEST_TO_EMAIL` in the Render dashboard.

The hash stores in `pulse/state/` are files on disk. On an ephemeral filesystem they reset between runs, so every docs page and README looks "changed" again.

## Known issues

- `src/main.py`, `main.py`, the `Dockerfile` and `docker-compose.yml` still describe an earlier FastAPI scaffold. `src/main.py` imports `src.api`, which does not exist, so the container commands will not start. Use `src.runner` instead.
- The `Dockerfile` uses Python 3.11, but `pyproject.toml` requires 3.13.
- `src/agents/dedup_node.py` dedups by URL only.

## Tests

```bash
uv run pytest
```

## License

[Add your license here]
