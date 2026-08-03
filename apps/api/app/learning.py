"""AI self-learning: post-call review.

Rule-based review of a completed call — scores success, tags the objection,
records the strategy used, and derives a lesson. Each review is stored as a
LearningEntry; aggregated stats feed Module 10's AI learning charts.
Upgrade path: LLM-based review/summary of the same transcript (`ponytail`).
"""

# objection -> counter-strategy playbook (ordered best-fit)
PLAYBOOK = [
    ("budget", "frame ROI / offer phased pilot or smaller scope"),
    ("too expensive", "anchor against cost of inaction, offer discount or freebie"),
    ("other priorities", "keep in warm list, send case-study follow-up, re-approach later"),
    ("not now", "schedule a future check-in, keep sending value"),
    ("no budget", "offer free audit / trial to build value first"),
]

OBJECTION_KEYWORDS = {
    "budget": ["budget", "too expensive", "can't afford", "cost"],
    "priorities": ["other priorities", "busy", "no time", "not now"],
    "no budget": ["no budget", "don't have", "not in the budget"],
    "not interested": ["not interested", "no thanks", "happy with current"],
}


def _success_score(outcome: str | None, sentiment: str | None) -> int:
    score = 50
    if outcome == "Meeting / proposal requested":
        score += 30
    if sentiment == "positive":
        score += 10
    elif sentiment in ("hesitant", "skeptical", "dismissive"):
        score -= 10
    return max(5, min(score, 95))


def _detect_objection(client_lines: list[str]) -> str | None:
    for line in client_lines:
        low = line.lower()
        for label, keywords in OBJECTION_KEYWORDS.items():
            if any(k in low for k in keywords):
                return label
    return None


def _strategy_for(objection: str | None) -> str:
    if not objection:
        return "value pitch"
    for keyword, tactic in PLAYBOOK:
        if keyword in objection:
            return tactic
    return "acknowledge + pivot to benefit"


def _lesson(objection: str | None, score: int, outcome: str | None) -> str:
    if outcome == "Meeting / proposal requested":
        return f"High-signal close. Repeat the {_strategy_for(objection)} approach."
    if objection:
        return f"Objection '{objection}' recurred; counter with {_strategy_for(objection)} next call."
    return "No objection raised — call lost on timing or fit, not pushback."


def review_call(client_lines: list[str], outcome: str | None, sentiment: str | None) -> dict:
    objection = _detect_objection(client_lines)
    score = _success_score(outcome, sentiment)
    return {
        "success_score": score,
        "objection": objection,
        "strategy_used": _strategy_for(objection),
        "lesson": _lesson(objection, score, outcome),
    }
