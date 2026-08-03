"""Analytics aggregates computed from live data.

Pure functions over ORM rows — no external store. Returns everything the
frontend charts need in one response.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone


def _fmt_d(iso: datetime) -> str:
    return iso.strftime("%m-%d")


def build_analytics(clients: list, calls: list, meetings: list) -> dict:
    now = datetime.now(timezone.utc)

    # ---- KPIs ----
    total_calls = len(calls)
    done_calls = [c for c in calls if c.status == "done"]
    positive = [c for c in done_calls if c.outcome == "Meeting / proposal requested"]
    conversion = round(len(positive) / len(done_calls) * 100) if done_calls else 0

    # revenue estimate: closed deals (none yet) + budget of research-ready clients
    revenue = sum(c.budget or 0 for c in clients if c.status in ("Proposal", "Closed"))
    avg_budget = (
        round(sum(c.budget or 0 for c in clients if c.budget) / len([c for c in clients if c.budget]))
        if any(c.budget for c in clients)
        else 0
    )

    # lead quality: client status distribution
    statuses = Counter(c.status or "Lead" for c in clients)
    lead_quality = [{"status": s, "count": n} for s, n in statuses.most_common()]

    # ---- time series: last 14 days ----
    days = [now - timedelta(days=d) for d in range(13, -1, -1)]
    calls_by_day: dict[str, int] = {_fmt_d(d): 0 for d in days}
    positive_by_day: dict[str, int] = {_fmt_d(d): 0 for d in days}
    for c in calls:
        created = c.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if created >= days[0] - timedelta(days=1):
            key = _fmt_d(created)
            calls_by_day[key] = calls_by_day.get(key, 0) + 1
            if c.outcome == "Meeting / proposal requested":
                positive_by_day[key] = positive_by_day.get(key, 0) + 1

    calls_series = [
        {"date": d, "calls": calls_by_day[d], "positive": positive_by_day[d]} for d in calls_by_day
    ]

    # meeting funnel
    booked = len(meetings)
    confirmed = len([m for m in meetings if m.status == "confirmed"])

    return {
        "kpis": {
            "total_calls": total_calls,
            "conversion_rate": conversion,
            "meetings_booked": booked,
            "meetings_confirmed": confirmed,
            "avg_budget": avg_budget,
            "revenue": revenue,
        },
        "calls_series": calls_series,
        "lead_quality": lead_quality,
        # ponytail: revenue trend + AI learning progress need closed-deal & memory
        # data — both appear once Module 11/12 land. Until then: zeros.
        "revenue_series": [
            {"date": _fmt_d(d), "revenue": 0} for d in days
        ],
        "ai_learning": [
            {"label": "Strategies updated", "value": 0},
            {"label": "Objections learned", "value": 0},
        ],
    }
