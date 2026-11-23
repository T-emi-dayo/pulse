import re
from datetime import date, datetime, timezone

import yaml


def _write_pick(pick: dict, **updates) -> None:
    fields = {key: value for key, value in pick.items() if key not in {"body", "path"}}
    fields.update(updates)
    pick["path"].write_text(
        "---\n" + yaml.safe_dump(fields, sort_keys=False, allow_unicode=True)
        + "---" + pick["body"], encoding="utf-8",
    )
    pick.update(fields)


def apply_weekly_policy(picks: list[dict], today: date | None = None) -> dict:
    """Resolve the latest open pick. Returns a decision for the weekly runner."""
    today = today or datetime.now(timezone.utc).date()
    active = [p for p in picks if p["status"] in {"proposed", "in_progress"}]
    if not active:
        return {"action": "create"}
    latest = max(active, key=lambda p: str(p.get("proposed_at", "")))
    proposed_at = latest["proposed_at"]
    if isinstance(proposed_at, datetime):
        proposed_at = proposed_at.date()
    elif not isinstance(proposed_at, date):
        proposed_at = date.fromisoformat(str(proposed_at))
    elapsed = (today - proposed_at).days // 7

    if latest["status"] == "proposed":
        if elapsed < 2:
            return {"action": "resend", "pick": latest}
        _write_pick(latest, status="lapsed", lapsed_at=today.isoformat())
        return {"action": "create", "lower_friction": True}

    carries = int(latest.get("carry_count", 0))
    if carries < 1:
        _write_pick(latest, carry_count=carries + 1, last_carried_at=today.isoformat())
        return {"action": "carry", "pick": latest}
    _write_pick(latest, status="lapsed", lapsed_at=today.isoformat())
    return {"action": "create", "lower_friction": True}


def preview_weekly_policy(picks: list[dict], today: date | None = None) -> dict:
    """Predict the weekly action without editing any pick files."""
    today = today or datetime.now(timezone.utc).date()
    active = [pick for pick in picks if pick["status"] in {"proposed", "in_progress"}]
    if not active:
        return {"action": "create"}
    latest = max(active, key=lambda pick: str(pick.get("proposed_at", "")))
    proposed = latest.get("proposed_at", "")
    proposed_date = proposed.date() if isinstance(proposed, datetime) else (
        proposed if isinstance(proposed, date) else date.fromisoformat(str(proposed)[:10])
    )
    elapsed = (today - proposed_date).days // 7
    if latest["status"] == "proposed":
        return {"action": "resend"} if elapsed < 2 else {"action": "create", "lower_friction": True}
    return {"action": "carry"} if int(latest.get("carry_count", 0)) < 1 else {"action": "create", "lower_friction": True}


def build_carry_over_note(pick: dict, week: str) -> str:
    """Write a deterministic continuity note without asking an LLM to re-plan."""
    match = re.search(r"(?ms)^## First steps\s*\n(.*?)(?=^## |\Z)", pick.get("body", ""))
    first_step = next((line.strip() for line in (match.group(1).splitlines() if match else []) if line.strip()), "")
    continuation = (
        f"Continue from this recorded step: {first_step}"
        if first_step else "Continue with the first unresolved core idea and update the first step if your circumstances changed."
    )
    return (
        "\n\n## Weekly continuity\n\n"
        f"The status policy carried this pick into {week}. The original outcome and core ideas stay unchanged. "
        f"{continuation}\n"
    )
