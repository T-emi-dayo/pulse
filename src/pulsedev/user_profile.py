"""Versioned knowledge profile and deterministic evidence-backed updates."""

import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def _stable_id(kind: str, value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", _normalise(value).lower()).strip("-")[:28] or "item"
    digest = hashlib.sha256(f"{kind}:{_normalise(value)}".encode("utf-8")).hexdigest()[:12]
    return f"{slug}-{digest}"


def _as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value:
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None
    return None


def _min_date(values: list[date | None]) -> date | None:
    present = [value for value in values if value is not None]
    return min(present) if present else None


def _max_date(values: list[date | None]) -> date | None:
    present = [value for value in values if value is not None]
    return max(present) if present else None


class ProfileItem(BaseModel):
    """One named learning topic in a profile section."""

    id: str = Field(description="Stable, code-assigned identifier for this profile item. Never generated or changed by the language model.")
    name: str = Field(description="Short topic label; it does not imply demonstrated proficiency.")
    first_seen: date | None = Field(default=None, description="Earliest completion date among linked evidence, assigned by code. Null when no reliable date is known.")
    last_seen: date | None = Field(default=None, description="Latest completion date among linked evidence, assigned by code. Null when no reliable date is known.")
    evidence_ids: list[str] = Field(default_factory=list, description="Identifiers of completed picks supporting this item. These refer to existing pick IDs.")
    merged_into: str | None = Field(default=None, description="Stable ID of the surviving item if this item was merged. The historical item and its dates remain available.")


class ProfileSection(BaseModel):
    """A user-profile category containing stable knowledge items."""

    id: str = Field(description="Stable, code-assigned identifier for this section.")
    name: str = Field(description="Human-readable category name, such as Knowledge areas, Strengths, or Interests.")
    items: list[ProfileItem] = Field(default_factory=list, description="Knowledge items in this category, including archived merged items for identifier and date continuity.")


class LearningEvidence(BaseModel):
    """A completed weekly pick and its local proof reference."""

    pick_id: str = Field(description="Stable ID of the completed learning pick in the learning repository.")
    title: str = Field(description="Title of the completed learning pick.")
    covered_ideas: list[str] = Field(default_factory=list, description="Core questions or ideas recorded in the completed pick's notes.")
    takeaway: str = Field(default="", description="Learner-written takeaway recorded when the pick was completed.")
    rating: int | None = Field(default=None, ge=1, le=5, description="Optional learner rating from 1 to 5.")
    proof_path: str = Field(description="Repository-relative path to the pick and its evidence.")
    completed_at: date | None = Field(default=None, description="Date resolved by code from pick metadata, or the first date code observed the pick as done. Null stays unknown for legacy evidence; never supplied by an LLM.")

    @model_validator(mode="before")
    @classmethod
    def empty_legacy_date_is_unknown(cls, value: Any) -> Any:
        if isinstance(value, dict):
            value = dict(value)
            value["completed_at"] = _as_date(value.get("completed_at"))
        return value


class ProfileChange(BaseModel):
    """Audit record for a profile organization decision."""

    type: str = Field(description="Profile operation proposed by the model and applied by code.")
    section_id: str = Field(description="Stable ID of the profile section changed.")
    item_ids: list[str] = Field(description="Stable profile item IDs affected by the operation, resolved by code.")
    source_pick_ids: list[str] = Field(description="Completed pick IDs that support this change.")
    reasoning: str = Field(description="Model-provided explanation for how the change organizes topic labels using completed pick titles.")
    changed_at: date = Field(description="Date the change was applied, assigned by code.")


class UserProfile(BaseModel):
    """Durable, evidence-linked model of the learner's current knowledge."""

    version: int = Field(default=2, description="Profile data format version. Version 2 stores knowledge as sections and stable items.")
    updated_at: str = Field(default="", description="UTC timestamp assigned by code when the profile is synchronized.")
    summary: str = Field(description="Learner-authored long-term development direction.")
    knowledge_notes: str = Field(default="", description="Learner-authored context needed to interpret the profile, kept concise.")
    sections: list[ProfileSection] = Field(default_factory=list, description="Knowledge categories and their stable, date-resolved items.")
    evidence: list[LearningEvidence] = Field(default_factory=list, description="Completed picks and proof references synchronized from the learning repository.")
    profile_changes: list[ProfileChange] = Field(default_factory=list, description="Audit trail of model-proposed profile organization changes. Excluded from picker context to prevent context growth.")
    processed_evidence_ids: list[str] = Field(default_factory=list, description="Completed pick IDs already considered for profile organization, maintained by code to avoid repeatedly asking the LLM to process the same evidence.")

    @model_validator(mode="before")
    @classmethod
    def upgrade_legacy_sections(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        legacy = {
            "known_areas": "Knowledge areas",
            "strengths": "Strengths",
            "interests": "Interests",
            "development_areas": "Growth areas",
            "preferences": "Learning preferences",
        }
        if "sections" not in data:
            sections = []
            for key, label in legacy.items():
                values = data.pop(key, []) or []
                section_id = _stable_id("section", label)
                items = []
                for entry in values:
                    item = entry if isinstance(entry, dict) else {"name": str(entry)}
                    name = str(item.get("name") or item.get("label") or "").strip()
                    if not name:
                        continue
                    items.append({
                        "id": item.get("id") or _stable_id(section_id, name),
                        "name": name,
                        "first_seen": item.get("first_seen"),
                        "last_seen": item.get("last_seen"),
                        "evidence_ids": item.get("evidence_ids", []),
                        "merged_into": item.get("merged_into"),
                    })
                sections.append({"id": section_id, "name": label, "items": items})
            data["sections"] = sections
        elif isinstance(data["sections"], dict):
            sections = []
            for name, values in data["sections"].items():
                section_id = _stable_id("section", name)
                items = []
                for entry in values or []:
                    item = entry if isinstance(entry, dict) else {"name": str(entry)}
                    item_name = str(item.get("name") or item.get("label") or "").strip()
                    if item_name:
                        items.append({
                            "id": item.get("id") or _stable_id(section_id, item_name),
                            "name": item_name,
                            "first_seen": item.get("first_seen"),
                            "last_seen": item.get("last_seen"),
                            "evidence_ids": item.get("evidence_ids", []),
                            "merged_into": item.get("merged_into"),
                        })
                sections.append({"id": section_id, "name": name, "items": items})
            data["sections"] = sections
        data["version"] = 2
        if "processed_evidence_ids" not in data:
            data["processed_evidence_ids"] = [
                item.get("pick_id") for item in data.get("evidence", []) if item.get("pick_id")
            ]
        data.setdefault("profile_changes", [])
        return data


def make_profile_section(name: str, items: list[str] | None = None) -> ProfileSection:
    """Create a section and stable items without inventing dates."""
    section_id = _stable_id("section", name)
    return ProfileSection(
        id=section_id,
        name=name,
        items=[
            ProfileItem(id=_stable_id(section_id, item), name=item)
            for item in dict.fromkeys(value.strip() for value in (items or []) if value.strip())
        ],
    )


def section_items(profile: UserProfile, name: str) -> list[ProfileItem]:
    section = next((item for item in profile.sections if _normalise(item.name) == _normalise(name)), None)
    return [item for item in section.items if item.merged_into is None] if section else []


def read_profile(path: Path) -> UserProfile:
    return UserProfile.model_validate_json(path.read_text(encoding="utf-8"))


def write_profile(path: Path, profile: UserProfile) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sync_completed_evidence(profile: UserProfile, picks: list[dict]) -> UserProfile:
    evidence_by_id = {entry.pick_id: index for index, entry in enumerate(profile.evidence)}
    for pick in picks:
        if pick.get("status") != "done":
            continue
        body = pick.get("body", "")
        section = re.search(r"(?ms)^## Core ideas\s*\n(.*?)(?=^## |\Z)", body)
        ideas = re.findall(r"(?m)^\s*[-*]\s+(.+?)\s*$", section.group(1)) if section else []
        previous = profile.evidence[evidence_by_id[pick["id"]]] if pick["id"] in evidence_by_id else None
        resolved_date = _as_date(pick.get("completed_at")) or (previous.completed_at if previous else None)
        if resolved_date is None and previous is None:
            resolved_date = datetime.now(timezone.utc).date()
        evidence = LearningEvidence(
            pick_id=pick["id"], title=pick["title"], covered_ideas=ideas,
            takeaway=str(pick.get("takeaway") or ""), rating=pick.get("rating"),
            proof_path=f"picks/{pick['id']}",
            completed_at=resolved_date,
        )
        if pick["id"] in evidence_by_id:
            profile.evidence[evidence_by_id[pick["id"]]] = evidence
        else:
            evidence_by_id[pick["id"]] = len(profile.evidence)
            profile.evidence.append(evidence)
    profile.updated_at = datetime.now(timezone.utc).isoformat()
    return profile


def pending_profile_evidence(profile: UserProfile) -> list[LearningEvidence]:
    """Return a bounded oldest-first batch of unprocessed profile evidence."""
    processed = set(profile.processed_evidence_ids)
    pending = [entry for entry in profile.evidence if entry.pick_id not in processed]
    pending.sort(key=lambda entry: (entry.completed_at or date.min, entry.pick_id))
    return pending[:5]


def apply_profile_additions(
    profile: UserProfile,
    additions: list[dict],
    pending: list[LearningEvidence],
) -> UserProfile:
    """Apply model-proposed operations while code owns IDs, dates, and merges."""
    from src.pulsedev.schemas import ProfileAddition

    evidence_by_id = {entry.pick_id: entry for entry in pending}
    for raw in additions:
        addition = raw if isinstance(raw, ProfileAddition) else ProfileAddition.model_validate(raw)
        source_ids = list(dict.fromkeys(addition.source_pick_ids))
        if not source_ids or any(source_id not in evidence_by_id for source_id in source_ids):
            raise ValueError("Profile addition references evidence outside the pending completed picks")
        evidence = [evidence_by_id[source_id] for source_id in source_ids]
        evidence_dates = [item.completed_at for item in evidence]
        affected_ids: list[str] = []

        if addition.type == "create_section":
            section_name = addition.new_section_name or ""
            section_id = _stable_id("section", section_name)
            section = next((item for item in profile.sections if item.id == section_id), None)
            if section is None:
                section = make_profile_section(section_name)
                profile.sections.append(section)
        else:
            section = next((item for item in profile.sections if item.id == addition.section_id), None)
            if section is None:
                raise ValueError(f"Unknown profile section ID: {addition.section_id}")

        active_items = [item for item in section.items if item.merged_into is None]
        targets = [item for item in active_items if item.id in addition.target_item_ids]
        if len(targets) != len(addition.target_item_ids):
            raise ValueError("Profile addition references missing or already-merged item IDs")

        if addition.type == "merge_items":
            canonical = min(targets, key=lambda item: (item.first_seen or date.max, item.id))
            all_evidence = list(dict.fromkeys(
                [source_id for item in targets for source_id in item.evidence_ids] + source_ids
            ))
            all_dates = evidence_dates + [item.first_seen for item in targets] + [item.last_seen for item in targets]
            canonical.name = addition.item_name
            canonical.first_seen = _min_date(all_dates)
            canonical.last_seen = _max_date(all_dates)
            canonical.evidence_ids = all_evidence
            affected_ids = [item.id for item in targets]
            for item in targets:
                if item.id != canonical.id:
                    item.merged_into = canonical.id
        elif addition.type == "rename_item":
            item = targets[0]
            item.name = addition.item_name
            item.evidence_ids = list(dict.fromkeys(item.evidence_ids + source_ids))
            item.last_seen = _max_date([item.last_seen, *evidence_dates])
            affected_ids = [item.id]
        else:
            same_name = next((item for item in active_items if _normalise(item.name) == _normalise(addition.item_name)), None)
            if same_name:
                same_name.evidence_ids = list(dict.fromkeys(same_name.evidence_ids + source_ids))
                same_name.first_seen = _min_date([same_name.first_seen, *evidence_dates])
                same_name.last_seen = _max_date([same_name.last_seen, *evidence_dates])
                affected_ids = [same_name.id]
            else:
                item_id = _stable_id(section.id, addition.item_name)
                prior = next((item for item in section.items if item.id == item_id), None)
                if prior and prior.merged_into:
                    prior = next((item for item in section.items if item.id == prior.merged_into), prior)
                    prior.evidence_ids = list(dict.fromkeys(prior.evidence_ids + source_ids))
                    prior.last_seen = _max_date([prior.last_seen, *evidence_dates])
                    affected_ids = [prior.id]
                elif prior is None:
                    section.items.append(ProfileItem(
                        id=item_id, name=addition.item_name,
                        first_seen=_min_date(evidence_dates), last_seen=_max_date(evidence_dates),
                        evidence_ids=source_ids,
                    ))
                    affected_ids = [item_id]

        profile.profile_changes.append(ProfileChange(
            type=addition.type,
            section_id=section.id,
            item_ids=affected_ids,
            source_pick_ids=source_ids,
            reasoning=addition.reasoning,
            changed_at=datetime.now(timezone.utc).date(),
        ))

    profile.processed_evidence_ids = list(dict.fromkeys(
        profile.processed_evidence_ids + [item.pick_id for item in pending]
    ))
    profile.updated_at = datetime.now(timezone.utc).isoformat()
    return profile
