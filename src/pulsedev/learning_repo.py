import json
import logging
import os
import re
import subprocess
import tempfile
import base64
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from src.config.settings import settings
from src.pulsedev.user_profile import (
    UserProfile,
    make_profile_section,
    read_profile,
    sync_completed_evidence,
    write_profile,
)

logger = logging.getLogger(__name__)
_STATUSES = {"proposed", "in_progress", "done", "skipped", "lapsed"}


def _parse_pick(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Missing YAML frontmatter: {path}")
    _, frontmatter, body = text.split("---", 2)
    fields = yaml.safe_load(frontmatter) or {}
    if fields.get("status") not in _STATUSES:
        raise ValueError(f"Invalid status in {path}")
    if not fields.get("id") or not fields.get("title") or not fields.get("proposed_at"):
        raise ValueError(f"Pick needs id, title, and proposed_at fields: {path}")
    if isinstance(fields.get("proposed_at"), (date, datetime)):
        fields["proposed_at"] = fields["proposed_at"].isoformat()
    fields["body"] = body
    fields["path"] = path
    return fields


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, text=True,
        capture_output=True, encoding="utf-8",
    ).stdout.strip()


class LearningRepo:
    def __init__(self) -> None:
        self.name = settings.LEARNING_REPO.strip()
        self.token = settings.LEARNING_REPO_TOKEN.strip()
        if not self.name or not self.token:
            raise RuntimeError("Set LEARNING_REPO and LEARNING_REPO_TOKEN to enable PulseDev.")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.name):
            raise RuntimeError("LEARNING_REPO must use the owner/repository format.")
        self._url = f"https://github.com/{self.name}.git"

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(prefix="pulse-learning-")
        self.path = Path(self._temp.name) / "learning-log"
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
        auth = base64.b64encode(f"x-access-token:{self.token}".encode()).decode()
        env["GIT_CONFIG_VALUE_0"] = f"AUTHORIZATION: basic {auth}"
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", self._url, str(self.path)],
                check=True, text=True, capture_output=True, env=env,
            )
        except Exception:
            self._temp.cleanup()
            raise
        self._git_env = env
        _git(self.path, "config", "user.name", "PulseDev")
        _git(self.path, "config", "user.email", "pulsedev@users.noreply.github.com")
        if not _git(self.path, "branch", "--show-current"):
            _git(self.path, "checkout", "-b", settings.LEARNING_REPO_BRANCH)
        self._needs_bootstrap = False
        if not (self.path / "_template").is_dir():
            import shutil
            source = Path(__file__).resolve().parents[2] / "templates" / "learning-log"
            for item in source.rglob("*"):
                relative = item.relative_to(source)
                target = self.path / relative
                if item.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                elif not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
            (self.path / "picks").mkdir(exist_ok=True)
            self._needs_bootstrap = True
        return self

    def __exit__(self, exc_type, exc, tb):
        self._temp.cleanup()

    def picks(self) -> list[dict]:
        return [_parse_pick(path) for path in sorted(self.path.glob("picks/*/pick.md"))]

    def sync_profile(self, picks: list[dict]) -> UserProfile:
        profile_path = self.path / "profile.json"
        if profile_path.exists():
            profile = read_profile(profile_path)
        else:
            profile = UserProfile(
                summary=settings.LEARNING_ANCHOR,
                knowledge_notes=settings.LEARNING_PROFILE,
                sections=[
                    make_profile_section("Knowledge areas", ["LLM and agentic systems"]),
                    make_profile_section("Strengths", ["LLM and agentic systems"]),
                    make_profile_section("Interests", ["Useful personal tools and workflows"]),
                    make_profile_section("Growth areas", ["Backend", "Deployment", "Mathematics", "Theory and foundations"]),
                    make_profile_section("Learning preferences", ["Weekly scope", "Mix of practical and abstract work", "Flexible deliverables"]),
                ],
            )
        profile = sync_completed_evidence(profile, picks)
        write_profile(profile_path, profile)
        return profile

    def save_profile(self, profile: UserProfile) -> None:
        write_profile(self.path / "profile.json", profile)

    def create_pick(self, proposal: dict, week: str) -> str:
        selected = proposal["candidates"][proposal["selected_index"]]
        details = proposal["selected_pick"]
        slug = re.sub(r"[^a-z0-9]+", "-", selected["title"].lower()).strip("-")[:50]
        pick_id = f"{week}-{slug}"
        target = self.path / "picks" / pick_id
        if target.exists():
            return pick_id
        template = self.path / "_template"
        if not template.is_dir():
            raise RuntimeError("Learning repo is missing its _template/ directory.")
        import shutil
        shutil.copytree(template, target)
        fields = {
            "id": pick_id, "title": selected["title"], "status": "proposed",
            "proposed_at": datetime.now(timezone.utc).date().isoformat(),
            "rating": None,
        }
        fields["first_step"] = details["first_step"]
        core_ideas = "\n".join(f"- {idea}" for idea in details["core_ideas"])
        content = (
            "---\n" + yaml.safe_dump(fields, sort_keys=False, allow_unicode=True)
            + "---\n\n## Why now\n\n" + selected["rationale"]
            + "\n\n## Outcome\n\n" + details["outcome"]
            + "\n\n## Selection rationale\n\n" + proposal["selection_reason"]
            + "\n\n## Core ideas\n\n" + core_ideas + "\n\n## First steps\n\n"
            + "1. " + details["first_step"] + "\n"
        )
        (target / "pick.md").write_text(content, encoding="utf-8")
        notes = target / "notes.md"
        note_questions = "\n\n".join(f"### {idea}\n\nWrite your explanation here." for idea in details["core_ideas"])
        notes.write_text(
            "# Learning notes\n\nAnswer each question in your own words.\n\n## Core ideas\n\n"
            + note_questions
            + "\n\n## Takeaway\n\nWhat changed in your understanding?\n",
            encoding="utf-8",
        )
        return pick_id

    def save_index(self) -> None:
        entries = []
        for pick in self.picks():
            entries.append({key: pick.get(key) for key in (
                "id", "title", "status", "rating", "proposed_at", "first_step",
            )})
        (self.path / "index.json").write_text(
            json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    def update_pick_body(self, pick: dict, addition: str) -> None:
        pick["body"] += addition
        fields = {key: value for key, value in pick.items() if key not in {"body", "path"}}
        pick["path"].write_text(
            "---\n" + yaml.safe_dump(fields, sort_keys=False, allow_unicode=True)
            + "---" + pick["body"], encoding="utf-8",
        )

    def push_changes(self, message: str) -> bool:
        _git(self.path, "add", "picks", "index.json", "profile.json")
        if self._needs_bootstrap:
            _git(self.path, "add", "_template", ".github", "README.md")
        changed = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=self.path).returncode != 0
        if not changed:
            return False
        _git(self.path, "commit", "-m", message)
        branch = _git(self.path, "branch", "--show-current")
        try:
            subprocess.run(
                ["git", "push", "--set-upstream", "origin", branch], cwd=self.path, check=True,
                capture_output=True, text=True, env=self._git_env,
            )
        except subprocess.CalledProcessError as exc:
            try:
                subprocess.run(
                    ["git", "pull", "--rebase", "origin", branch], cwd=self.path, check=True,
                    capture_output=True, text=True, env=self._git_env,
                )
                subprocess.run(
                    ["git", "push", "--set-upstream", "origin", branch], cwd=self.path, check=True,
                    capture_output=True, text=True, env=self._git_env,
                )
            except subprocess.CalledProcessError as retry_exc:
                logger.error("Learning repo push failed: %s", retry_exc.stderr[-1500:])
                raise RuntimeError("Could not push to the learning repo; check token access and retry.") from exc
        return True
