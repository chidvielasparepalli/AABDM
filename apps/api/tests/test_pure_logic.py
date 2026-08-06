"""Unit tests for pure service modules — no DB, no network."""
from app.analytics import build_analytics
from app.bi import ClientInfo, Research, build_bi, opportunity_score
from app.calls import ScriptLine, build_script, outcome_for
from app.learning import review_call
from app.memory import extract_memories
from app.research import analyze_seo, detect_tech, missing_features, opportunities


class FakeCreated:
    """Stand-in for ORM rows used by build_analytics."""

    def __init__(self, status, outcome, created_at, budget=0):
        from datetime import datetime, timezone

        self.status = status
        self.outcome = outcome
        self.created_at = created_at or datetime.now(timezone.utc)
        self.budget = budget


# ---- bi ----

def test_opportunity_score_caps_at_98():
    r = Research(10, 10, [], ["x"] * 10, ["y"] * 10, [])
    assert opportunity_score(r) <= 98


def test_build_bi_shape():
    r = Research(80, 90, ["React"], [], [], [])
    c = ClientInfo("Acme", "technology", 5000)
    bi = build_bi(c, r)
    assert bi["opportunity_score"] == 50  # healthy site, no gaps
    assert bi["budget_estimate"]["min"] >= 1500
    assert bi["recommended_service"] is None  # no opportunities detected
    expected = {"opportunity_score", "swot", "profile", "budget_estimate", "recommended_service", "winning_strategy"}
    assert set(bi.keys()) == expected


# ---- analytics ----

def test_build_analytics_empty():
    out = build_analytics([], [], [])
    assert out["kpis"]["total_calls"] == 0
    assert len(out["calls_series"]) == 14
    assert len(out["revenue_series"]) == 14


def test_build_analytics_conversion():
    calls = [FakeCreated("done", "Meeting / proposal requested", None)]
    out = build_analytics([], calls, [])
    assert out["kpis"]["conversion_rate"] == 100


# ---- research ----

SAMPLE_HTML = """<html><head><title>Acme Corp</title>
<meta name="description" content="A reasonably long meta description for the page, longer than fifty chars ok">
<meta name="viewport" content="width=device-width">
<link rel="canonical" href="https://acme.com">
<meta property="og:title" content="Acme">
</head><body><h1>Welcome</h1><img src="a.jpg" alt="hero"><img src="b.jpg" alt="two">
<script src="wp-content/x.js"></script></body></html>"""


def test_analyze_seo_scores_well():
    score, checks = analyze_seo(SAMPLE_HTML, "https://acme.com")
    assert score >= 70
    assert any(c["label"] == "Mobile viewport configured" for c in checks)


def test_detect_tech_wordpress():
    assert "WordPress" in detect_tech(SAMPLE_HTML)


def test_missing_features():
    missing = missing_features("<html><body>no widgets here</body></html>")
    assert "Live chat widget" in missing


def test_opportunities_modernize():
    opts = opportunities([], [], 30, 30)
    assert any("Modernize" in o for o in opts)


# ---- calls ----

def test_build_script_stages():
    bi = {"recommended_service": "SEO", "opportunity_score": 80, "budget_estimate": {"min": 1000, "max": 4000}}
    lines = build_script("Acme", bi)
    assert lines[0].role == "ai"
    assert any(line.stage == "Close" for line in lines)
    assert all(isinstance(line, ScriptLine) for line in lines)


def test_outcome_for_positive():
    lines = [ScriptLine("client", "ok", "Close", emotion="positive")]
    assert outcome_for(80, lines) == "Meeting / proposal requested"


def test_outcome_for_warm():
    lines = [ScriptLine("client", "ok", "Close", emotion="neutral")]
    assert outcome_for(50, lines) == "Follow-up scheduled"


# ---- learning ----

def test_review_call_positive():
    review = review_call(["That sounds interesting"], "Meeting / proposal requested", "positive")
    assert review["success_score"] >= 80
    assert "High-signal close" in review["lesson"]


def test_review_call_objection():
    review = review_call(["That's more than we budgeted"], "Follow-up scheduled", "hesitant")
    assert review["objection"]
    assert review["success_score"] < 80


# ---- memory ----

def test_extract_budget():
    facts = extract_memories(set(), ["We have about $5000 to spend"], [])
    assert any(k == "budget" and "5,000" in v for k, v in facts)


def test_extract_dedupe():
    first = extract_memories(set(), ["budget is $2000"], [])
    second = extract_memories({v.lower() for _, v in first}, ["budget is $2000"], [])
    assert second == []


def test_extract_interest():
    facts = extract_memories(set(), ["we're looking for SEO help"], [])
    assert any(k == "interest" for k, v in facts)
