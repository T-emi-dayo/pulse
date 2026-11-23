import json
import re
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {"proposed", "in_progress", "done", "skipped", "lapsed"}
errors = []
index = []


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    _, raw, body = text.split("---", 2)
    return yaml.safe_load(raw) or {}, body


for pick_path in sorted((ROOT / "picks").glob("*/pick.md")):
    folder = pick_path.parent
    try:
        fields, body = frontmatter(pick_path)
        if isinstance(fields.get("proposed_at"), (date, datetime)):
            fields["proposed_at"] = fields["proposed_at"].isoformat()
        if fields.get("status") not in REQUIRED:
            raise ValueError(f"{pick_path}: invalid status")
        if not fields.get("id") or not fields.get("title") or not fields.get("proposed_at"):
            raise ValueError(f"{pick_path}: id, title, and proposed_at are required")
        if fields["status"] == "skipped" and not fields.get("skip_reason"):
            raise ValueError(f"{pick_path}: skipped picks need a skip_reason")
        notes_path = folder / "notes.md"
        if not notes_path.is_file():
            raise ValueError(f"{folder}: missing notes.md")
        if fields["status"] == "done":
            if not isinstance(fields.get("rating"), int) or not 1 <= fields["rating"] <= 5:
                raise ValueError(f"{pick_path}: done picks need rating 1-5")
            if not fields.get("takeaway") or len(str(fields["takeaway"]).strip()) < 20:
                raise ValueError(f"{pick_path}: done picks need a written takeaway")
            ideas_section = re.search(r"(?ms)^## Core ideas\s*\n(.*?)(?=^## |\Z)", body)
            ideas = re.findall(r"(?m)^\s*[-*]\s+(.+?)\s*$", ideas_section.group(1)) if ideas_section else []
            notes = notes_path.read_text(encoding="utf-8")
            if not ideas:
                raise ValueError(f"{pick_path}: no core ideas listed")
            for idea in ideas:
                heading = re.search(rf"(?mi)^###\s+{re.escape(idea)}\s*$", notes)
                if not heading:
                    raise ValueError(f"{notes_path}: add a heading answering: {idea}")
                following = notes[heading.end():].split("\n### ", 1)[0]
                answer = re.sub(r"(?is)^\s*Write your explanation here\.?\s*", "", following).strip()
                if len(re.sub(r"\W", "", answer)) < 60:
                    raise ValueError(f"{notes_path}: answer core idea in your own words: {idea}")
            kind = str(fields.get("deliverable_type", "")).lower()
            if kind == "code":
                artifacts = [path for path in folder.rglob("*") if path.suffix in {".py", ".ipynb"}]
                if not artifacts or not (folder / "README.md").is_file():
                    raise ValueError(f"{folder}: Code picks need a script/notebook and README.md")
            if kind == "service":
                if not (folder / "README.md").is_file() or not any(folder.rglob("test_*.py")):
                    raise ValueError(f"{folder}: Service picks need README.md and an end-to-end test")
            if kind == "dev tool":
                if not (folder / "README.md").is_file() or not re.search(r"(?im)^#+\s*use on a real task\b", notes):
                    raise ValueError(f"{folder}: Dev tool picks need usage notes and a real-task use record")
            if kind == "experiment":
                for section in ("method", "results", "conclusion"):
                    if not re.search(rf"(?im)^#+\s*{section}\b", notes):
                        raise ValueError(f"{notes_path}: Experiment picks need a {section} section")
            if kind == "write-up" and not (folder / "writeup.md").is_file():
                raise ValueError(f"{folder}: Write-up picks need a reviewable writeup.md draft")
        index.append({key: fields.get(key) for key in (
            "id", "title", "status", "rating", "takeaway", "anchor", "proposed_at", "builds_on", "produces"
        )})
    except Exception as exc:
        errors.append(str(exc))

if errors:
    raise SystemExit("\n".join(errors))
(ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
