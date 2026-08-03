"""Memory extraction from call transcripts.

Rule-based fact extraction. Each fact deduped against what's already stored
for the client. Upgrade path: LLM keyphrase extraction over the same
transcript when an API key exists (`ponytail`).
"""
import re

BUDGET_RE = re.compile(r"\$([\d,]+)")

# (fact_key, trigger words) — AI lines we parse for facts
INTEREST_TRIGGERS = ["interested in", "wants", "looking for", "needs help with", "focused on"]
OBJECTION_TRIGGERS = ["budget", "too expensive", "not now", "other priorities", "no budget", "busy"]
LANGUAGE_TRIGGERS = []  # inferred from transcript text below
PREFERENCE_TRIGGERS = ["prefer", "prefers", "start smaller", "email it", "call me"]


def _dedupe(existing: set, new: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Only facts not already stored."""
    seen = existing.copy()
    out: list[tuple[str, str]] = []
    for key, value in new:
        norm = value.lower()
        if norm not in seen:
            seen.add(norm)
            out.append((key, value))
    return out


def extract_memories(existing: set, client_lines: list[str], ai_lines: list[str]) -> list[tuple[str, str]]:
    """Returns [(key, value)] of new facts from a transcript."""
    new: list[tuple[str, str]] = []

    all_lines = " ".join(client_lines + ai_lines).lower()

    # budget: any $ figure mentioned
    for m in BUDGET_RE.finditer(all_lines):
        new.append(("budget", f"mentioned ${int(m.group(1).replace(',', '')):,}"))

    # interests: client says what they want
    for line in client_lines:
        low = line.lower()
        for trig in INTEREST_TRIGGERS:
            if trig in low:
                after = low.split(trig, 1)[1].strip(" .,!?")
                if after and len(after) < 80:
                    new.append(("interest", f"wants {after}"))

    # objections: client pushes back
    for line in client_lines:
        low = line.lower()
        if any(t in low for t in OBJECTION_TRIGGERS):
            new.append(("objection", low[:100]))

    # preferences
    for line in client_lines:
        low = line.lower()
        for trig in PREFERENCE_TRIGGERS:
            if trig in low:
                new.append(("preference", f"{trig} mentioned"))

    # language: ASCII/non-ASCII heuristic (demo: english vs not)
    non_ascii = sum(1 for ch in all_lines if ord(ch) > 127)
    if non_ascii / max(len(all_lines), 1) > 0.05:
        new.append(("language", "non-english detected"))

    return _dedupe(existing, new)
