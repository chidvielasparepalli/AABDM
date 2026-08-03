"""Rule-based website research.

Zero-key build: fetch the site's HTML + Google PageSpeed free API. Real
scraping/CSS-visible checks need Firecrawl/Tavily keys — see `ponytail`
markers. Heuristics are deliberately simple; AI summarization (Module 5)
replaces them once keys exist.
"""
import asyncio
import re

import httpx

UA = {
    "User-Agent": "Mozilla/5.0 (compatible; AABDM-research/0.1; +http://aabdm.ai)"
}

# (tech_name, list of html regexes)
TECH_STACK = [
    ("WordPress", [r"wp-content", r"wp-includes", r'generator[^>]+WordPress']),
    ("Shopify", [r"cdn\.shopify\.com", r"myshopify"]),
    ("Squarespace", [r"squarespace"]),
    ("Wix", [r"wix\.com", r"wixstatic"]),
    ("React", [r"__NEXT_DATA__", r"_next/", r"data-reactroot", r"react(\.min)?\.js"]),
    ("Vue", [r"__VUE__", r"vue(\.min)?\.js"]),
    ("Angular", [r"ng-app", r"angular(\.min)?\.js"]),
    ("Svelte", [r"svelte"]),
    ("Tailwind", [r"tailwindcss", r"tailwind"]),
    ("Bootstrap", [r"bootstrap(\.min)?\.(css|js)"]),
    ("jQuery", [r"jquery(\.min)?\.js"]),
    ("Cloudflare", [r"cloudflare"]),
    ("Google Analytics", [r"google-analytics", r"gtag\(|googletagmanager"]),
    ("HubSpot", [r"hubspot"]),
    ("Stripe", [r"js\.stripe\.com"]),
]

# (feature_name, html regex) — presence kills the "missing" flag
PRESENT = [
    ("Live chat widget", [r"intercom", r"crisp", r"tawk", r"drift", r"livechat"]),
    ("Online booking", [r"calendly", r"acuity", r"booking\.", r"book-online"]),
    ("Newsletter", [r"mailchimp", r"convertkit", r"subscribe", r"newsletter"]),
    ("WhatsApp contact", [r"wa\.me", r"whatsapp"]),
    ("Blog / content", [r"blog", r"insights", r"articles", r"resources"]),
]

# Common tech keys that imply "sophisticated" — missing these = opportunity
SOPHISTICATION_MARKERS = ["React", "Vue", "Angular", "Shopify", "Stripe", "WordPress"]


def _has(html: str, patterns: list[str]) -> bool:
    return any(re.search(p, html, re.IGNORECASE) for p in patterns)


async def fetch_site(url: str) -> str:
    target = url if url.startswith("http") else f"https://{url}"
    async with httpx.AsyncClient(headers=UA, follow_redirects=True, timeout=15) as c:
        r = await c.get(target)
        r.raise_for_status()
        return r.text


async def page_speed(url: str) -> dict:
    target = url if url.startswith("http") else f"https://{url}"
    api = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {"url": target, "category": "performance"}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(api, params=params)
        if r.status_code != 200:
            return {"score": None, "error": f"PageSpeed HTTP {r.status_code}"}
        data = r.json()
        score = data.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score")
        return {"score": round(score * 100) if score is not None else None}


def analyze_seo(html: str, url: str) -> tuple[int, list[dict]]:
    checks: list[dict] = []
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html, re.IGNORECASE)
    viewport = '<meta name="viewport"' in html.lower()
    h1s = len(re.findall(r"<h1[\s>]", html, re.IGNORECASE))
    og_title = '<meta property="og:title"' in html.lower()
    canonical = '<link rel="canonical"' in html.lower()
    imgs = len(re.findall(r"<img[\s>]", html, re.IGNORECASE))
    alt_imgs = len(re.findall(r'<img[^>]+alt=["\'][^"\'\\s]', html, re.IGNORECASE))

    def add(pass_: bool, label: str) -> None:
        checks.append({"pass": bool(pass_), "label": label})

    add(title is not None and 10 <= len(title.group(1)) <= 70, "Descriptive <title> tag")
    add(desc is not None and len(desc.group(1)) >= 50, "Meta description present")
    add(viewport, "Mobile viewport configured")
    add(h1s == 1, "Single H1 heading")
    add(og_title, "Open Graph meta tags")
    add(canonical, "Canonical URL")
    add(imgs == 0 or alt_imgs / max(imgs, 1) >= 0.8, "Image alt text coverage")

    score = round(sum(c["pass"] for c in checks) / len(checks) * 100)
    return score, checks


def detect_tech(html: str) -> list[str]:
    return [name for name, pats in TECH_STACK if _has(html, pats)]


def missing_features(html: str) -> list[str]:
    present = {name for name, pats in PRESENT if _has(html, pats)}
    return [name for name, _ in PRESENT if name not in present]


def opportunities(tech: list[str], missing: list[str], seo_score: int, perf_score: int | None) -> list[str]:
    opts: list[str] = []
    if not any(t in SOPHISTICATION_MARKERS for t in tech):
        opts.append("Modernize the website platform (static/legacy stack detected)")
    for m in missing:
        opts.append(f"Add {m.lower()}")
    if seo_score < 60:
        opts.append("Fix on-page SEO (title, meta, alt text, structure)")
    if perf_score is not None and perf_score < 60:
        opts.append("Improve site speed (Lighthouse under 60)")
    if "Google Analytics" not in tech:
        opts.append("Set up conversion tracking / analytics")
    return opts


def build_report(url: str, html: str, perf: dict) -> dict:
    seo_score, seo_checks = analyze_seo(html, url)
    tech = detect_tech(html)
    missing = missing_features(html)
    return {
        "url": url,
        "status": "done",
        "seo_score": seo_score,
        "performance_score": perf.get("score"),
        "tech_stack": tech,
        "seo_checks": seo_checks,
        "missing_features": missing,
        "opportunities": opportunities(tech, missing, seo_score, perf.get("score")),
        # ponytail: no competitors — needs Tavily/SerpAPI key. Add when key exists.
        "competitors": [],
        "error": None,
    }


async def run_research(url: str) -> dict:
    """Full research pipeline. Raises on hard failure (unreachable site)."""
    html = await fetch_site(url)
    perf = await page_speed(url)
    return build_report(url, html, perf)
