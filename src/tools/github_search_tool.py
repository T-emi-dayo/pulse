import hashlib
import json
import feedparser
import httpx
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.types import RawItem


HASH_STORE_PATH = Path("pulse/state/github_readme_hashes.json")
CUTOFF_HOURS = 24


def _get_cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=CUTOFF_HOURS)


# ── Hash store helpers ────────────────────────────────────────────────────────

def _load_hash_store() -> dict:
    if HASH_STORE_PATH.exists():
        with open(HASH_STORE_PATH, "r") as f:
            return json.load(f)
    return {}


def _save_hash_store(store: dict) -> None:
    HASH_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HASH_STORE_PATH, "w") as f:
        json.dump(store, f, indent=2)


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ── GitHub Releases ───────────────────────────────────────────────────────────

def fetch_github_releases(repos: list[str]) -> list[RawItem]:
    """
    Fetches new releases from GitHub .atom RSS feeds for a list of repos.

    Args:
        repos: List of repo slugs in "owner/repo" format.
               e.g. ["langchain-ai/langchain", "openai/openai-python"]

    Returns:
        List of RawItem dicts for releases published within the last 24h.
    """
    cutoff = _get_cutoff()
    items: list[RawItem] = []

    for repo in repos:
        url = f"https://github.com/{repo}/releases.atom"
        feed = feedparser.parse(url)

        if feed.bozo:
            print(f"[github_releases] Failed to parse feed for {repo}: {feed.bozo_exception}")
            continue

        for entry in feed.entries:
            # FeedParserDict provides automatic fallbacks via keymap
            # Try to access published first, falls back through keymap hierarchy
            try:
                time_tuple = entry.get("published_parsed")
                if not time_tuple:
                    time_tuple = entry.get("updated_parsed")
                if not time_tuple:
                    # Last resort: try other possible keys
                    time_tuple = entry.get("modified_parsed") or entry.get("date_parsed")

                if time_tuple:
                    published = datetime(*time_tuple[:6], tzinfo=timezone.utc)
                else:
                    published = datetime.now(timezone.utc)
            except (TypeError, KeyError, AttributeError) as e:
                print(f"[github_releases] Failed to parse date for {repo} entry: {e}")
                published = datetime.now(timezone.utc)

            if published < cutoff:
                break  # releases.atom is date-ordered, safe to break

            # entry.content[0].value contains the release notes HTML
            raw_content = entry.get("content", [{}])[0].get("value", "") or entry.get("summary", "")

            items.append(
                RawItem(
                    title=f"[{repo}] {entry.title.strip()}",
                    url=entry.link,
                    source_type="github_release",
                    excerpt=raw_content[:500],
                    published_at=published.isoformat(),
                    content_hash=None,
                    full_content=raw_content or None,
                )
            )

    return items


# ── GitHub README ─────────────────────────────────────────────────────────────

def _fetch_readme_content(repo: str) -> str | None:
    """
    Fetches raw README content. Tries `main` branch first, falls back to `master`.
    """
    for branch in ("main", "master"):
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/README.md"
        try:
            response = httpx.get(url, timeout=10, follow_redirects=True)
            if response.status_code == 200:
                return response.text
        except httpx.RequestError as e:
            print(f"[github_readme] Request error for {repo} ({branch}): {e}")

    print(f"[github_readme] README not found for {repo} on main or master.")
    return None


def fetch_github_readmes(repos: list[str]) -> list[RawItem]:
    """
    Checks README content for a list of repos. Emits a RawItem only if the
    README has changed since the last run (based on SHA-256 hash).

    Args:
        repos: List of repo slugs in "owner/repo" format.

    Returns:
        List of RawItem dicts for repos whose README has changed.
    """
    store = _load_hash_store()
    items: list[RawItem] = []
    now = datetime.now(timezone.utc).isoformat()

    for repo in repos:
        content = _fetch_readme_content(repo)
        if content is None:
            continue

        new_hash = _hash_content(content)
        existing = store.get(repo, {})
        old_hash = existing.get("hash")

        if old_hash == new_hash:
            # No change — update last_checked timestamp only
            store[repo]["last_checked"] = now
            continue

        # README changed (or first time seeing this repo)
        change_label = "Updated" if old_hash else "First seen"
        items.append(
            RawItem(
                title=f"[{repo}] README {change_label}",
                url=f"https://github.com/{repo}#readme",
                source_type="github_readme",
                excerpt=content[:500],
                published_at=now,
                content_hash=new_hash,
                full_content=content,
            )
        )

        store[repo] = {
            "hash": new_hash,
            "last_checked": now,
        }

    _save_hash_store(store)
    return items


# ── Combined entry point ──────────────────────────────────────────────────────

def fetch_github(repos: list[str]) -> list[RawItem]:
    """
    Runs both release and README checks for the given repos and returns
    a combined list of RawItems.

    Args:
        repos: List of repo slugs in "owner/repo" format.
    """
    release_items = fetch_github_releases(repos)
    readme_items = fetch_github_readmes(repos)
    return release_items + readme_items