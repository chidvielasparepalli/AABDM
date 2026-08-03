"""Business intelligence — rule-based synthesis of a research report.

Derives SWOT, client profile, opportunity score, budget estimate, recommended
service, and winning strategy. Pure functions: testable, no I/O. The `ponytail`
path to upgrade is an LLM pass over the same inputs once an API key exists.
"""
from dataclasses import dataclass


@dataclass
class Research:
    seo_score: int | None
    performance_score: int | None
    tech_stack: list[str]
    missing_features: list[str]
    opportunities: list[str]
    competitors: list[str]


@dataclass
class ClientInfo:
    name: str
    industry: str | None
    budget: float | None


# service name -> conditions
SERVICE_MATCHES: list[tuple[str, list[str]]] = [
    ("Website redesign", ["Modernize the website platform"]),
    ("SEO & Content Marketing", ["Fix on-page SEO", "Add blog / content"]),
    ("Lead Generation System", ["Add online booking", "Add whatsapp contact", "Add live chat widget"]),
    ("Conversion Optimization", ["Add newsletter", "Set up conversion tracking"]),
    ("Speed Optimization", ["Improve site speed"]),
]

# industry -> typical budget band (USD/mo)
INDUSTRY_BUDGETS: dict[str, tuple[int, int]] = {
    "real estate": (1500, 4000),
    "healthcare": (2000, 6000),
    "legal": (1500, 5000),
    "ecommerce": (1000, 5000),
    "restaurant": (800, 3000),
    "manufacturing": (1500, 4500),
    "technology": (2500, 8000),
    "finance": (2000, 6000),
}


def service_for(opportunities: list[str]) -> str | None:
    if not opportunities:
        return None
    # most conditions matched wins; list order breaks ties
    best = max(
        SERVICE_MATCHES,
        key=lambda item: sum(1 for c in item[1] if c in opportunities),
    )
    if any(c in opportunities for c in best[1]):
        return best[0]
    return "Full-funnel marketing"


def budget_estimate(industry: str | None, opportunity_count: int) -> tuple[int, int]:
    if industry:
        low, high = INDUSTRY_BUDGETS.get(industry.lower(), (1000, 4000))
    else:
        low, high = 1000, 4000
    # more gaps to fix -> higher estimate
    multiplier = 1 + min(opportunity_count, 6) * 0.1
    return round(low * multiplier), round(high * multiplier)


def opportunity_score(research: Research) -> int:
    score = 50
    if research.seo_score is not None and research.seo_score < 60:
        score += 15  # easy wins available
    if research.performance_score is not None and research.performance_score < 50:
        score += 10
    score += min(len(research.missing_features), 4) * 5
    score += min(len(research.opportunities), 4) * 5
    return min(score, 98)  # never 100 — always "room to grow"


def swot(research: Research, client_name: str) -> dict[str, list[str]]:
    s: list[str] = []
    w: list[str] = []
    o: list[str] = []
    t: list[str] = []

    if research.tech_stack:
        s.append(f"Uses {', '.join(research.tech_stack[:3])}")
    else:
        w.append("Undetectable / minimal web stack")

    if research.seo_score is not None and research.seo_score >= 60:
        s.append("Decent on-page SEO")
    else:
        w.append("Weak on-page SEO fundamentals")

    if research.performance_score is not None and research.performance_score >= 70:
        s.append("Fast site")
    else:
        w.append("Site speed needs work")

    for feat in research.missing_features[:3]:
        o.append(f"Missing: {feat.lower()} — quick win")

    if research.opportunities:
        o.append(research.opportunities[0])

    if not research.competitors:
        t.append("Unknown competitive landscape")
    else:
        t.append(f"Competing with {', '.join(research.competitors[:2])}")

    # pad to non-empty lists
    if not s:
        s.append("Active business in market")
    if not w:
        w.append("Unidentified weakness — needs deeper audit")
    if not o:
        o.append("Grow via outbound lead generation")
    if not t:
        t.append("Market fragmentation risk")

    return {"strengths": s, "weaknesses": w, "opportunities": o, "threats": t}


def client_profile(research: Research, client: ClientInfo) -> dict:
    profile: dict[str, str] = {}
    if client.industry:
        profile["Industry"] = client.industry
    if research.tech_stack:
        profile["Platform"] = ", ".join(research.tech_stack[:3])
    if research.seo_score is not None:
        profile["Digital maturity"] = (
            "Strong" if research.seo_score >= 70 else "Growing" if research.seo_score >= 40 else "Early"
        )
    if client.budget:
        profile["Budget signal"] = f"${client.budget:,.0f}"
    return profile


def winning_strategy(service: str | None, score: int) -> str:
    base = (
        f"Lead with '{service}'"
        if service
        else "Lead with a full digital-growth assessment"
    )
    if score >= 70:
        return base + " — high readiness, move fast, propose within a week."
    if score >= 45:
        return base + " — build trust with a mini-audit, then pitch."
    return base + " — start with education and small first engagement."


def build_bi(client: ClientInfo, research: Research) -> dict:
    service = service_for(research.opportunities)
    low, high = budget_estimate(client.industry, len(research.opportunities))
    score = opportunity_score(research)
    return {
        "opportunity_score": score,
        "swot": swot(research, client.name),
        "profile": client_profile(research, client),
        "budget_estimate": {"min": low, "max": high},
        "recommended_service": service,
        "winning_strategy": winning_strategy(service, score),
    }
