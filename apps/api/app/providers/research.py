"""Research provider interface.

Abstraction over site fetching and SEO/performance/enrichment analysis.
Current builtin adapter reproduces `research.py` (PageSpeed + regex SEO).

SSRF contract: every adapter MUST validate the target URL before fetching —
reject non-http(s) schemes and any host resolving to private/link-local/
metadata ranges. Enforcement lives in `security/ssrf.py`; adapters call it.
"""

from typing import Protocol, runtime_checkable

from .common import Capability


@runtime_checkable
class ResearchProvider(Capability, Protocol):
    def fetch_site(self, url: str) -> str:
        """Return the site HTML for the validated URL. Raises on unreachable."""
        ...

    def analyze_seo(self, html: str, url: str) -> dict:
        """Return {'score': int, 'checks': [{'pass': bool, 'label': str}]}."""
        ...

    def analyze_performance(self, url: str) -> dict:
        """Return {'score': int | None, 'error': str | None}."""
        ...

    def enrich(self, report: dict) -> dict:
        """Augment a report with competitors/firmographics/news. Optional — may no-op."""
        ...
