import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.config.profiles import TOPIC_PROFILES
from src.config.settings import settings
from src.pulsedev.user_profile import UserProfile

ROOT = Path(__file__).resolve().parents[2]
WEB = Path(__file__).resolve().parent
app = FastAPI(title="Pulse local dashboard", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")


def _json_files(folder: Path, prefix: str) -> list[dict]:
    rows = []
    if not folder.is_dir():
        return rows
    for path in sorted(folder.glob(f"{prefix}*.json"), reverse=True):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
            row["file"] = path.name
            rows.append(row)
        except (OSError, json.JSONDecodeError):
            continue
    return rows


def _read_picks(learning_path: Path) -> list[dict]:
    picks = []
    for path in sorted(learning_path.glob("picks/*/pick.md"), reverse=True):
        try:
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---\n"):
                continue
            _, raw, body = text.split("---", 2)
            fields = yaml.safe_load(raw) or {}
            picks.append({
                "id": fields.get("id", path.parent.name),
                "title": fields.get("title", path.parent.name),
                "status": fields.get("status", "unknown"),
                "rating": fields.get("rating"),
                "takeaway": fields.get("takeaway"),
                "first_step": fields.get("first_step"),
                "proposed_at": str(fields.get("proposed_at", "")),
                "proof_path": f"picks/{path.parent.name}",
                "body": body,
            })
        except (OSError, ValueError, yaml.YAMLError):
            continue
    return picks


def _read_digests() -> list[dict]:
    digests = []
    folder = ROOT / "data" / "digests"
    for path in folder.glob("pulse_digest_*.md"):
        match = re.fullmatch(r"pulse_digest_(\d{8}T\d{6}Z)", path.stem)
        if not match:
            continue
        try:
            sent_at = datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            content = path.read_text(encoding="utf-8")
        except (OSError, ValueError):
            continue
        inline_urls = list(dict.fromkeys(
            url.rstrip(".,;:") for url in re.findall(r"https?://[^\s<>\]\[)]+", content)
        ))
        source_path = path.with_name(f"{path.stem}.sources.json")
        try:
            saved_sources = json.loads(source_path.read_text(encoding="utf-8")) if source_path.exists() else []
        except (OSError, json.JSONDecodeError):
            saved_sources = []
        sources_by_url = {}
        for source in saved_sources:
            if not isinstance(source, dict):
                continue
            url = str(source.get("url", ""))
            parsed = urlsplit(url)
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                sources_by_url[url] = {**source, "url": url}
        for url in inline_urls:
            parsed = urlsplit(url)
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                sources_by_url.setdefault(url, {"url": url, "title": parsed.netloc, "source_name": parsed.netloc})
        digests.append({
            "file": path.name,
            "date": sent_at.date().isoformat(),
            "sent_at": sent_at.isoformat(),
            "content": content,
            "sources": list(sources_by_url.values()),
        })
    return sorted(digests, key=lambda item: item["sent_at"], reverse=True)


def dashboard_data() -> dict:
    learning_path = Path(settings.LEARNING_LOG_PATH).expanduser() if settings.LEARNING_LOG_PATH else None
    profile = None
    picks = []
    if learning_path and learning_path.is_dir():
        profile_file = learning_path / "profile.json"
        if profile_file.exists():
            try:
                profile_model = UserProfile.model_validate_json(profile_file.read_text(encoding="utf-8"))
                profile = profile_model.model_dump(mode="json")
                legacy_views = {
                    "knowledge areas": "known_areas",
                    "strengths": "strengths",
                    "interests": "interests",
                    "growth areas": "development_areas",
                    "learning preferences": "preferences",
                }
                for section in profile_model.sections:
                    field = legacy_views.get(section.name.casefold())
                    if field:
                        profile[field] = [item.name for item in section.items if item.merged_into is None]
            except (OSError, ValueError):
                profile = {"error": "profile.json could not be read"}
        picks = _read_picks(learning_path)

    digests = _read_digests()

    hashes = {}
    for name in ("docs_hashes.json", "github_readme_hashes.json"):
        path = ROOT / "pulse" / "state" / name
        try:
            hashes[name] = len(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError):
            hashes[name] = 0

    topics = [{"name": profile["topic"], "priority": profile["priority"]} for profile in TOPIC_PROFILES]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topics": topics,
        "models": {
            "base": settings.BASE_MODEL,
            "summarization": settings.SUMMARIZATION_MODEL,
            "picker": settings.INGESTION_MODEL,
        },
        "learning_log_path": str(learning_path) if learning_path else "",
        "profile": profile,
        "picks": picks,
        "digests": digests,
        "pulse_runs": _json_files(ROOT / "data" / "runs", "pulse-"),
        "pulsedev_runs": _json_files(ROOT / "data" / "runs", "pulsedev-"),
        "hash_counts": hashes,
    }


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(WEB / "index.html")


@app.get("/api/dashboard")
def get_dashboard() -> dict:
    return dashboard_data()


def main() -> None:
    import uvicorn
    print("Pulse dashboard: http://127.0.0.1:8765 (read-only, local only)")
    uvicorn.run("src.dashboard.app:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
