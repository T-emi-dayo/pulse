# Pulse

Pulse is an intelligent personal data gathering AI system. It builds a daily digest of what matters across AI research, tooling, and the wider ecosystem, then emails it. Once configured, it runs with no manual curation.

## How it works

Pulse is a [LangGraph](https://langchain-ai.github.io/langgraph/) pipeline. It runs once a day. The per-source pull limit is the quality gate.

```
START ─┬─> ingest_github_releases ─┐
       ├─> ingest_docs            ─┤
       ├─> ingest_research_papers ─┼─> dedup ─┬─> summarize_github_releases ─┐
       ├─> ingest_news            ─┤          ├─> summarize_docs            ─┤
       └─> ingest_blogs           ─┘          ├─> summarize_research_papers ─┼─> merge_digest ─> END
                                              ├─> summarize_news            ─┤
                                              └─> summarize_blogs           ─┘
```

1. **Ingest**: five nodes run in parallel. Each pulls items from the last 24 hours (`LOOKBACK_HOURS`), retries a failing fetch up to three times, and caps items per source type (`TOP_N_BY_SOURCE`). Ingestion makes no LLM calls.
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
├── .github/workflows/            # Daily Pulse and weekly PulseDev schedules
├── templates/learning-log/       # Bootstrap structure for the separate learning repo
├── Dockerfile, docker-compose.yml
├── .env.example
├── CLAUDE.md                     # Context for Claude Code
├── docs/                         # Design notes and project rules
├── pulse/state/                  # Persisted SHA-256 hash stores (JSON)
├── tests/                        # unit/, integration/, e2e/ and tool scripts
└── src/
    ├── runner.py                 # Entry point: run graph, email digest
    ├── pulsedev/                  # Weekly picker, user profile, status policy, and CLI
    ├── dashboard/                 # Local read-only dashboard
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
    ├── prompts/prompt.yaml      # All LLM prompt text
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
| `LEARNING_LOG_PATH` | No | Local learning-repo checkout for CLI previews and the dashboard |

`.env.example` also contains legacy template entries for the LLM provider, vector DB, and Redis that Pulse does not currently read. News ingestion uses DuckDuckGo through `ddgs`; it does not require `NEWS_API_KEY`.

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

**Prompts** live in the single catalog at `src/prompts/prompt.yaml`. Python loads and fills named entries from this file.

## GitHub Actions deployment

Pulse runs daily at 04:00 UTC through `.github/workflows/pulse-daily.yml`. It commits digest files, run records, and source hash state back to the Pulse repository. PulseDev runs separately at 06:00 UTC every Monday and reads the prior ISO week's saved digests.

Add these repository Actions secrets to Pulse:

| Secret | Used for |
|---|---|
| `GEMINI_API_KEY` | Daily summaries and weekly topic picker |
| `RESEND_API_KEY` | Digest and pick email |
| `DIGEST_FROM_EMAIL` | Verified Resend sender |
| `DIGEST_TO_EMAIL` | Recipient |
| `LEARNING_REPO_TOKEN` | Fine-grained GitHub token with contents read/write on the learning repo only |

Add these Actions variables to Pulse:

| Variable | Purpose |
|---|---|
| `LEARNING_REPO` | Learning repo in `owner/name` form |
| `LEARNING_REPO_BRANCH` | Optional; defaults to `main` |
| `LEARNING_ANCHOR` | Optional longer-term direction for picks; has a broad self-development default |
| `LEARNING_PROFILE` | Optional current strengths and areas of interest; has a broad default |

PulseDev bootstraps `_template/`, `picks/`, `profile.json`, `index.json`, and the validation workflow when the configured learning repo is empty or has no `_template/`. Existing files are preserved. The repo is expected to be private; do not put employer or client material in it.

The workflows open a GitHub issue if a run fails, so enable Actions to create issues in the Pulse repository. Allow Actions to write to the Pulse repository and ensure branch protection permits its artifact commits. Set the daily and weekly schedules in UTC as shown above; GitHub may start scheduled jobs later than the requested minute.

### User profile and proof links

`profile.json` in the learning repo is PulseDev's current user profile. Version 2 stores named sections with stable item IDs, first and last evidence dates, and source pick IDs. Version 1 flat lists migrate automatically; dates remain unknown until supported by completed work. The weekly picker may propose additions, renames, or merges based on newly completed picks. Python assigns IDs and resolves dates; merged items keep their IDs and point to the surviving item. The picker receives the active profile concepts and only the completion evidence it has not already processed, not the full evidence history.

The picker returns three lightweight title-and-rationale candidates, then provides a week-sized `outcome`, concrete `first_step`, and core questions only for the selected candidate. It does not choose learning sources. The weekly scope and carry-over policy are handled by code. Deliverable categories, free-form effort estimates, `builds_on`, and `produces` are not part of the pick schema.

### Preview PulseDev before deployment

Clone the learning repo locally, then point `LEARNING_LOG_PATH` in `.env` to that checkout. The CLI can collect your profile details in the terminal and inspect saved digests and picks:

```bash
uv run pulsedev profile-init --learning-log "path/to/learning-log"
uv run pulsedev preview --learning-log "path/to/learning-log" --dry-run
uv run pulsedev preview --learning-log "path/to/learning-log" --invoke
```

The dry run shows the exact prompt and predicts the weekly status-policy action without calling Gemini. `--invoke` asks Gemini for three lightweight candidates, selected-pick details, and optional profile topic-label changes based only on completed pick titles and status. Both preview modes avoid creating a pick, pushing to GitHub, or sending email. Digest selection is limited to the previous Monday-Sunday window; `--digest PATH` may be repeated only for files dated within that window. The profile wizard adds items to the named knowledge sections while preserving existing IDs and evidence dates.

After editing `profile.json` in your local learning-repo checkout, commit and push it so the scheduled Actions workflow sees the updated profile.

### Local dashboard

With `LEARNING_LOG_PATH` set, start the read-only dashboard:

```bash
uv run pulse-dashboard
```

Open `http://127.0.0.1:8765`. It shows your profile as an explorable topic graph with linked proof, digest dates on a calendar with searchable source links, Pulse run health, and PulseDev picks in month and week calendar views. New digest runs save a compact source catalog beside the existing Markdown digest so article links are available in the reader. It binds only to the local machine and does not edit either repository.

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
