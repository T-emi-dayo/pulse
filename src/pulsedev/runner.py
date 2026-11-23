"""Weekly PulseDev entry point. Run with ``python -m src.pulsedev.runner``."""

import logging
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import resend

from src.config.settings import settings
from src.pulsedev.digests import read_weekly_digests, week_window
from src.pulsedev.learning_repo import LearningRepo
from src.pulsedev.picker import build_picker_prompt, choose_pick
from src.pulsedev.status_policy import apply_weekly_policy, build_carry_over_note
from src.pulsedev.user_profile import apply_profile_additions, pending_profile_evidence
from src.utils.redaction import redact_secrets

logger = logging.getLogger("pulse.pulsedev")
ROOT = Path(__file__).resolve().parents[2]


def _notify(pick_path: Path, title: str, week: str) -> None:
    required = [settings.RESEND_API_KEY, settings.DIGEST_FROM_EMAIL, settings.DIGEST_TO_EMAIL]
    if not all(required):
        raise RuntimeError("Email not configured for PulseDev; set the existing Resend email settings.")
    resend.api_key = settings.RESEND_API_KEY
    body = pick_path.read_text(encoding="utf-8")
    resend.Emails.send({
        "from": settings.DIGEST_FROM_EMAIL,
        "to": [settings.DIGEST_TO_EMAIL],
        "subject": f"PulseDev — {week}: {title}",
        "text": body + f"\n\n---\nPulseDev weekly run: {week}.\n",
    })


def _deferred_topics(picks: list[dict], today: date) -> list[dict]:
    deferred = []
    for pick in picks:
        if pick["status"] not in {"skipped", "lapsed"} or not pick.get("proposed_at"):
            continue
        proposed = date.fromisoformat(str(pick["proposed_at"])[:10])
        avoid_until = proposed + timedelta(weeks=3)
        if today <= avoid_until:
            deferred.append({
                "title": pick["title"],
                "reason": pick.get("skip_reason", "previously lapsed"),
                "avoid_until": avoid_until.isoformat(),
            })
    return deferred


def main() -> None:
    today = datetime.now(timezone.utc).date()
    start, end, week = week_window(today)
    run_path = ROOT / "data" / "runs" / f"pulsedev-{week}.json"
    run_path.parent.mkdir(parents=True, exist_ok=True)
    report = {"run_key": week, "started_at": datetime.now(timezone.utc).isoformat(), "status": "failed"}
    if run_path.exists():
        try:
            previous = json.loads(run_path.read_text(encoding="utf-8"))
            if previous.get("status") == "success":
                logger.info("PulseDev run %s already completed; skipping duplicate.", week)
                return
        except (OSError, json.JSONDecodeError):
            pass

    try:
        digests = read_weekly_digests(ROOT / "data" / "digests", start, end)
        if not digests:
            raise RuntimeError(f"No saved Pulse digests found for {start} through {end}.")
        with LearningRepo() as repo:
            picks = repo.picks()
            decision = apply_weekly_policy(picks, today)
            picks = repo.picks()
            profile = repo.sync_profile(picks)
            if decision["action"] == "create":
                pending_evidence = pending_profile_evidence(profile)
                prompt = build_picker_prompt(
                    digests, profile, _deferred_topics(picks, today),
                    decision.get("lower_friction", False),
                    pending_evidence=pending_evidence,
                )
                proposal = choose_pick(prompt)
                profile = apply_profile_additions(
                    profile, proposal.get("profile_additions", []), pending_evidence,
                )
                repo.save_profile(profile)
                pick_id = repo.create_pick(proposal, week)
                repo.save_index()
                repo.push_changes(f"PulseDev: propose {pick_id}")
                pick_path = repo.path / "picks" / pick_id / "pick.md"
                title = proposal["candidates"][proposal["selected_index"]]["title"]
                _notify(pick_path, title, week)
                report.update(
                    status="success", pick_id=pick_id, action="created",
                    candidates=proposal["candidates"], selected_index=proposal["selected_index"],
                    selected_pick=proposal["selected_pick"],
                    selection_reason=proposal["selection_reason"],
                )
            elif decision["action"] in {"resend", "carry"}:
                pick = decision["pick"]
                if decision["action"] == "carry":
                    repo.update_pick_body(pick, build_carry_over_note(pick, week))
                repo.save_index()
                repo.push_changes(f"PulseDev: review {pick['id']} for {week}")
                pick_path = pick["path"]
                _notify(pick_path, pick["title"], week)
                report.update(status="success", pick_id=pick["id"], action=decision["action"])
            else:
                raise RuntimeError(f"Unsupported status-policy action: {decision['action']}")
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        run_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        logger.error("PulseDev run failed: %s", redact_secrets(exc))
        report.update(status="failed", error=redact_secrets(exc), finished_at=datetime.now(timezone.utc).isoformat())
        run_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
