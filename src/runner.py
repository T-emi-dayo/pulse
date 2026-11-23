"""
Pulse daily runner — entry point for the scheduled cron job.

Usage:
    uv run python -m src.runner
"""

import logging
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.graph import pulse_graph
from src.config.profiles import TOPIC_PROFILES
from src.services.email_service import send_digest
from src.utils.redaction import redact_secrets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("pulse.runner")
ROOT = Path(__file__).resolve().parents[1]


def _record_run(run_key: str, status: str, started: datetime, **details) -> None:
    path = ROOT / "data" / "runs" / f"pulse-{run_key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "run_key": run_key,
        "status": status,
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        **details,
    }
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    start = datetime.now(timezone.utc)
    run_key = start.strftime("%Y-%m-%d")
    run_record = ROOT / "data" / "runs" / f"pulse-{run_key}.json"
    if run_record.exists():
        try:
            previous = json.loads(run_record.read_text(encoding="utf-8"))
            if previous.get("status") in {"success", "degraded"}:
                logger.info("Pulse run %s already completed; skipping duplicate.", run_key)
                return
        except (OSError, json.JSONDecodeError):
            pass

    logger.info("Pulse run starting — %s", start.strftime("%Y-%m-%d %H:%M UTC"))

    try:
        result = pulse_graph.invoke({"topic_profiles": TOPIC_PROFILES})
    except Exception as exc:
        logger.error("Graph invocation failed: %s", redact_secrets(exc))
        _record_run(run_key, "failed", start, stage="graph", error=redact_secrets(exc))
        sys.exit(1)

    errors: list[str] = result.get("errors", [])
    digest: str = result.get("final_digest", "")

    if errors:
        logger.warning(f"{len(errors)} non-fatal error(s) during ingestion/summarization:")
        for err in errors:
            logger.warning("  %s", redact_secrets(err))
    errors = [redact_secrets(error) for error in errors]
    result["errors"] = errors

    if not digest:
        logger.error("No digest produced — nothing to send.")
        _record_run(run_key, "failed", start, stage="digest", error="No digest produced")
        sys.exit(1)

    health = f"Degraded: {len(errors)} source or processing issue(s)." if errors else "Success: all configured stages completed."
    result["final_digest"] = f"{redact_secrets(digest).rstrip()}\n\n---\n\nRun health: {health}\n"

    try:
        send_digest(result)
    except RuntimeError as exc:
        # Configuration error — log clearly and exit
        logger.error(str(exc))
        _record_run(run_key, "failed", start, stage="email", error=redact_secrets(exc))
        sys.exit(1)
    except Exception as exc:
        logger.error("Failed to send digest email: %s", redact_secrets(exc))
        _record_run(run_key, "failed", start, stage="email", error=redact_secrets(exc))
        sys.exit(1)

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    _record_run(
        run_key, "degraded" if errors else "success", start,
        elapsed_seconds=round(elapsed, 1), error_count=len(errors),
    )
    logger.info(f"Pulse run complete in {elapsed:.1f}s.")


if __name__ == "__main__":
    main()
