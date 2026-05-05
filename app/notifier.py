"""
Discord webhook notifier.
Set DISCORD_WEBHOOK_URL in .env to enable.
Leave it blank to run silently (dashboard only).
"""
import httpx
from config import DISCORD_WEBHOOK_URL

_SENIORITY_LABELS = {
    "internship": "🎓 Internship",
    "new_grad":   "🎓 New Grad",
    "entry_level": "🟢 Entry Level",
    "junior":     "🟢 Junior",
    "senior+":    "🔴 Senior+",
    "unspecified": "⚪ Unspecified",
}

_SCORE_BAR_LEN = 10


def _score_bar(score: float) -> str:
    filled = round(score * _SCORE_BAR_LEN)
    return "█" * filled + "░" * (_SCORE_BAR_LEN - filled)


def _job_embed(job) -> dict:
    score = job.match_score
    company_name = job.company.name if job.company else "Unknown"
    seniority = _SENIORITY_LABELS.get(job.seniority, "⚪ Unspecified")
    color = int(0x57F287 if score >= 0.6 else 0xFEE75C if score >= 0.4 else 0xEB459E)

    return {
        "title": job.title,
        "url": job.url,
        "color": color,
        "fields": [
            {"name": "🏢 Company",  "value": company_name,                        "inline": True},
            {"name": "📍 Location", "value": job.location or "United States",     "inline": True},
            {"name": "🎯 Match",    "value": f"`{_score_bar(score)}` {round(score*100)}% — {job.matched_role}", "inline": False},
            {"name": "📋 Level",    "value": seniority,                           "inline": True},
        ],
        "footer": {"text": "Career Portal Monitor"},
    }


async def send_new_jobs(jobs: list) -> None:
    """Post one Discord message per new job. Batches into groups of 10 embeds."""
    if not DISCORD_WEBHOOK_URL or not jobs:
        return

    async with httpx.AsyncClient(timeout=15) as client:
        batch_size = 10
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i : i + batch_size]
            payload = {
                "content": f"**{len(batch)} new job match{'es' if len(batch) > 1 else ''}** found across your companies 🔍",
                "embeds": [_job_embed(j) for j in batch],
            }
            try:
                resp = await client.post(DISCORD_WEBHOOK_URL, json=payload)
                resp.raise_for_status()
            except Exception as e:
                print(f"[notifier] Discord send failed: {e}")


async def send_scrape_summary(total_new: int, companies_ok: int, companies_failed: int) -> None:
    """Post a brief run summary — only if there were failures or new jobs."""
    if not DISCORD_WEBHOOK_URL:
        return
    if total_new == 0 and companies_failed == 0:
        return

    if companies_failed:
        color = 0xED4245  # red
        status = f"⚠️ {companies_failed} company scraper(s) failed"
    else:
        color = 0x5865F2  # blurple
        status = f"✅ All {companies_ok} companies scraped successfully"

    payload = {
        "embeds": [{
            "title": "Scrape Run Complete",
            "color": color,
            "fields": [
                {"name": "New jobs found", "value": str(total_new),        "inline": True},
                {"name": "Status",         "value": status,                "inline": False},
            ],
            "footer": {"text": "Career Portal Monitor"},
        }]
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(DISCORD_WEBHOOK_URL, json=payload)
            resp.raise_for_status()
        except Exception as e:
            print(f"[notifier] Discord summary failed: {e}")
