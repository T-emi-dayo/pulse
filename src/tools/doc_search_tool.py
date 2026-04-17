import hashlib
import json
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pathlib import Path

from src.types import RawItem


HASH_STORE_PATH = Path("pulse/state/docs_hashes.json")

# Tried in order — first match wins
CONTENT_SELECTORS = ["main", "article", "[role='main']", "div.content", "div.docs-content", "body"]

# Tags to strip before extraction — these change often and carry no useful info
NOISE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]


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


# ── Content extraction ────────────────────────────────────────────────────────

def _extract_content(html: str) -> tuple[str, str]:
    """
    Extracts (title, body_text) from raw HTML.
    Strips noise tags first, then tries semantic selectors in priority order.
    Hashes the body text (not raw HTML) to avoid false positives from
    superficial markup changes.

    Returns:
        (page_title, extracted_text)
    """
    soup = BeautifulSoup(html, "html.parser")

    # Extract page title before stripping anything
    page_title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled"

    # Strip noise tags in-place
    for tag in soup(NOISE_TAGS):
        tag.decompose()

    # Try content selectors in priority order
    content_el = None
    for selector in CONTENT_SELECTORS:
        content_el = soup.select_one(selector)
        if content_el:
            break

    raw_text = content_el.get_text(separator=" ", strip=True) if content_el else ""

    # Collapse whitespace
    content_text = " ".join(raw_text.split())

    return page_title, content_text


# ── Docs fetcher ──────────────────────────────────────────────────────────────

def _fetch_page(url: str) -> str | None:
    """Fetches raw HTML for a URL. Returns None on failure."""
    try:
        response = httpx.get(
            url,
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; PulseBot/1.0)"},
        )
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as e:
        print(f"[docs] HTTP error for {url}: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"[docs] Request error for {url}: {e}")
    return None


def fetch_docs(urls: list[str]) -> list[RawItem]:
    """
    Checks a list of documentation URLs for content changes.
    Emits a RawItem only if the page content has changed since the last run.

    Uses semantic HTML extraction + SHA-256 hashing on extracted text
    (not raw HTML) to avoid false positives from superficial markup changes.

    Args:
        urls: List of documentation page URLs to monitor.

    Returns:
        List of RawItem dicts for pages whose content has changed.
    """
    store = _load_hash_store()
    items: list[RawItem] = []
    now = datetime.now(timezone.utc).isoformat()

    for url in urls:
        html = _fetch_page(url)
        if html is None:
            continue

        page_title, content_text = _extract_content(html)

        if not content_text:
            print(f"[docs] No extractable content found for {url}, skipping.")
            continue

        new_hash = _hash_content(content_text)
        existing = store.get(url, {})
        old_hash = existing.get("hash")

        if old_hash == new_hash:
            store[url]["last_checked"] = now
            continue

        change_label = "Updated" if old_hash else "First seen"
        items.append(
            RawItem(
                title=f"{page_title} [{change_label}]",
                url=url,
                source_type="docs",
                excerpt=content_text[:500],
                published_at=now,
                content_hash=new_hash,
                full_content=content_text,
            )
        )

        store[url] = {
            "hash": new_hash,
            "last_checked": now,
        }

    _save_hash_store(store)
    return items