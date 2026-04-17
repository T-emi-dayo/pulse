import logging
from datetime import datetime, timezone

import resend

from src.config.settings import settings
from src.schemas.state import SummaryItem, IngestedItem

logger = logging.getLogger(__name__)

_SOURCE_ORDER = ["research_paper", "github_release", "docs", "news", "blog"]

_SOURCE_META: dict[str, dict] = {
    "research_paper": {"label": "Research Papers",       "icon": "🔬", "color": "#7c3aed"},
    "github_release": {"label": "GitHub Releases",       "icon": "⚙️",  "color": "#0ea5e9"},
    "docs":           {"label": "Documentation Updates", "icon": "📄", "color": "#10b981"},
    "news":           {"label": "News",                  "icon": "📰", "color": "#f59e0b"},
    "blog":           {"label": "Blog Posts",            "icon": "✍️",  "color": "#ec4899"},
}


# ── HTML builder ──────────────────────────────────────────────────────────────

def _build_html(
    summaries: list[SummaryItem],
    deduped_items: list[IngestedItem],
    errors: list[str],
    date_str: str,
) -> str:
    total_items = len(deduped_items)
    by_source: dict[str, SummaryItem] = {s.source_type: s for s in summaries}

    active_source_types = [st for st in _SOURCE_ORDER if st in by_source]
    active_labels = " &middot; ".join(
        _SOURCE_META[st]["label"] for st in active_source_types
    )
    stats_line = f"{total_items} items &middot; {len(active_source_types)} source type{'s' if len(active_source_types) != 1 else ''} &middot; {active_labels}"

    # ── Content sections ───────────────────────────────────────────────────────
    sections_html = ""
    first_section = True

    for source_type in _SOURCE_ORDER:
        summary = by_source.get(source_type)
        if not summary:
            continue

        meta = _SOURCE_META[source_type]
        item_word = "item" if summary.item_count == 1 else "items"
        body_html = summary.summary_text.strip().replace("\n", "<br>")

        if not first_section:
            sections_html += """
                <tr>
                  <td style="padding: 4px 40px 0;">
                    <div style="border-top: 1px solid #e2e8f0;"></div>
                  </td>
                </tr>"""
        first_section = False

        sections_html += f"""
                <tr>
                  <td style="padding: 28px 40px 6px;">
                    <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                      <tr>
                        <td>
                          <div style="font-size: 11px; font-weight: 700; color: {meta['color']};
                                      text-transform: uppercase; letter-spacing: 1.5px;">
                            {meta['icon']}&nbsp;&nbsp;{meta['label']}
                          </div>
                        </td>
                        <td align="right">
                          <div style="font-size: 11px; color: #94a3b8;">
                            {summary.item_count} {item_word}
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 8px 40px 0;">
                    <div style="font-size: 14px; color: #1e293b; line-height: 1.75;">
                      {body_html}
                    </div>
                  </td>
                </tr>"""

    # ── Errors section (if any) ────────────────────────────────────────────────
    errors_html = ""
    if errors:
        error_rows = "".join(
            f"<li style='margin-bottom:3px; font-size:12px; color:#78350f;'>{e}</li>"
            for e in errors
        )
        errors_html = f"""
                <tr>
                  <td style="padding: 20px 40px 0;">
                    <div style="background:#fef9c3; border:1px solid #fde68a; border-radius:6px; padding:14px 18px;">
                      <div style="font-size:12px; font-weight:700; color:#92400e; margin-bottom:8px;">
                        ⚠️ {len(errors)} ingestion error{'s' if len(errors) != 1 else ''} — results may be partial
                      </div>
                      <ul style="margin:0; padding-left:16px;">
                        {error_rows}
                      </ul>
                    </div>
                  </td>
                </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>Pulse AI Digest &mdash; {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
         style="background:#f1f5f9;padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" role="presentation"
               style="max-width:600px;width:100%;">

          <!-- Header --------------------------------------------------------->
          <tr>
            <td style="background:#0f172a;border-radius:12px 12px 0 0;padding:28px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td>
                    <div style="font-size:22px;font-weight:800;color:#f8fafc;
                                letter-spacing:-0.5px;line-height:1;">
                      ⚡ PULSE
                    </div>
                    <div style="font-size:12px;color:#64748b;margin-top:5px;letter-spacing:0.3px;">
                      Daily AI Intelligence Digest
                    </div>
                  </td>
                  <td align="right" valign="middle">
                    <div style="font-size:13px;font-weight:500;color:#94a3b8;">
                      {date_str}
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Stats bar ------------------------------------------------------->
          <tr>
            <td style="background:#1e293b;padding:11px 40px;">
              <div style="font-size:11px;color:#94a3b8;letter-spacing:0.3px;">
                📊&nbsp;&nbsp;{stats_line}
              </div>
            </td>
          </tr>

          <!-- Content --------------------------------------------------------->
          <tr>
            <td style="background:#ffffff;padding-bottom:28px;">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                {sections_html}
                {errors_html}
              </table>
            </td>
          </tr>

          <!-- Footer ---------------------------------------------------------->
          <tr>
            <td style="background:#f8fafc;border-top:1px solid #e2e8f0;
                        border-radius:0 0 12px 12px;padding:16px 40px;">
              <div style="font-size:11px;color:#b0b8c8;text-align:center;letter-spacing:0.2px;">
                Generated by <strong style="color:#94a3b8;">Pulse</strong>
                &middot; {date_str} UTC
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>"""


# ── Public entry point ────────────────────────────────────────────────────────

def send_digest(result: dict) -> None:
    """
    Sends the daily Pulse digest via Resend.

    Args:
        result: The full dict returned by pulse_graph.invoke(). Must contain
                'summaries', 'deduped_items', 'errors', and 'final_digest'.

    Raises:
        RuntimeError: If email env vars are not configured.
        Exception: Propagates Resend API errors.
    """
    if not all([settings.RESEND_API_KEY, settings.DIGEST_FROM_EMAIL, settings.DIGEST_TO_EMAIL]):
        raise RuntimeError(
            "Email not configured — set RESEND_API_KEY, DIGEST_FROM_EMAIL, "
            "and DIGEST_TO_EMAIL in your environment."
        )

    summaries: list[SummaryItem] = result.get("summaries", [])
    deduped_items: list[IngestedItem] = result.get("deduped_items", [])
    errors: list[str] = result.get("errors", [])
    plain_text: str = result.get("final_digest", "")

    resend.api_key = settings.RESEND_API_KEY

    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    subject = f"⚡ Pulse — {date_str}"

    html_body = _build_html(summaries, deduped_items, errors, date_str)

    params: resend.Emails.SendParams = {
        "from": settings.DIGEST_FROM_EMAIL,
        "to": [settings.DIGEST_TO_EMAIL],
        "subject": subject,
        "html": html_body,
        "text": plain_text,
    }

    response = resend.Emails.send(params)
    logger.info(f"Digest email sent — id={response.get('id', 'unknown')}")
