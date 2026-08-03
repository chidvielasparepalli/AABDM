"""AI call engine.

Deterministic conversation script derived from the BI report — the "digital
employee" brain for the demo/sim transport. Each line carries the emotion the
AI detected (client) and the AI's confidence (ai). Real speech transport
(Twilio/Vapi + Whisper/STT + ElevenLabs/TTS) replaces the sleep-replay in
`replay_call` behind the same ScriptLine contract.
"""
import asyncio
from dataclasses import dataclass

PACE_S = 1.4  # simulated seconds between lines


@dataclass
class ScriptLine:
    role: str  # ai | client
    text: str
    stage: str
    emotion: str | None = None  # for client lines
    confidence: float | None = None  # for ai lines


STAGES = ["Greeting", "Pitch", "Objection", "Resolution", "Close"]


def _ai(text: str, stage: str, conf: float) -> ScriptLine:
    return ScriptLine("ai", text, stage, confidence=round(conf, 2))


def _client(text: str, stage: str, emotion: str) -> ScriptLine:
    return ScriptLine("client", text, stage, emotion=emotion)


def build_script(client_name: str, bi: dict, negotiation: dict | None = None) -> list[ScriptLine]:
    service = bi.get("recommended_service") or "digital growth services"
    score = bi.get("opportunity_score", 50)
    lo, hi = bi["budget_estimate"]["min"], bi["budget_estimate"]["max"]

    # negotiation config overrides generic budget line when present
    neg = negotiation or {}
    pricing = neg.get("pricing") or []
    pricing_str = ""
    if pricing:
        try:
            pricing_str = "Our pricing starts at " + ", ".join(
                f"{p['label']} (${p['amount']:,})" for p in pricing[:2]
            )
        except (KeyError, TypeError):
            pricing_str = ""
    discount_str = ""
    if neg.get("discounts"):
        try:
            discount_str = ", and we can offer " + " or ".join(
                f"{d['percent']}% off {d['label']}" for d in neg["discounts"][:2]
            )
        except (KeyError, TypeError):
            discount_str = ""
        else:
            discount_str += "."
    freebie_str = ""
    if neg.get("freebies"):
        try:
            freebie_str = " plus " + " and ".join(f"{f}" for f in neg["freebies"][:2])
        except TypeError:
            freebie_str = ""

    s = []

    s.append(_ai(f"Hi {client_name}, this is Ava from AABDM — your AI business "
                 f"development manager. Thanks for taking my call.", "Greeting", 0.92))
    s.append(_client("Uh, hi. How did you get my number?", "Greeting", "neutral"))

    s.append(_ai(f"We've been analyzing {client_name}'s online presence. I believe "
                 f"a {service} program could be a strong fit for you.", "Pitch", 0.88))
    s.append(_client("We get calls like this all the time. What makes you different?",
                     "Pitch", "skeptical"))

    price_line = pricing_str or f"A typical engagement runs ${lo:,}-${hi:,} per month."
    price_line += f" Our first campaign usually pays for itself{discount_str or '.'}"
    if freebie_str:
        price_line += f" {freebie_str} included."

    if score >= 70:
        s += [
            _ai(f"Fair question. We don't just pitch — we did a full audit. Your site is "
                f"leaving real revenue on the table, and the fix is straightforward.",
                "Pitch", 0.90),
            _client("That sounds interesting, honestly. What would it cost?",
                    "Objection", "interested"),
            _ai(price_line, "Objection", 0.85),
            _client("That's more than I budgeted for. Can we start smaller?",
                    "Objection", "hesitant"),
            _ai(f"Absolutely. We can begin with a focused pilot at a lower scope, and "
                f"scale once you see results. Let me get you a tailored proposal.",
                "Resolution", 0.93),
            _client("Okay, a proposal sounds good. Email it to me this week.",
                    "Resolution", "positive"),
            _ai(f"Perfect — I'll have it to you within 48 hours. Great talking with you, "
                f"{client_name}.", "Close", 0.95),
            _client("Thanks, talk soon.", "Close", "positive"),
        ]
    else:
        s += [
            _ai(f"We saw some quick wins available on your site — low-hanging fruit "
                f"that's easy to capture.", "Pitch", 0.78),
            _client("We're actually pretty busy right now with other priorities.",
                    "Objection", "dismissive"),
            _ai(f"I understand — timing matters. I'll send over a short summary and "
                f"the numbers, no obligation. If it makes sense, we talk later.",
                "Resolution", 0.82),
            _client("Alright, you can send it. No promises though.", "Resolution", "neutral"),
            _ai(f"That's all I ask. I'll follow up with a quick email. Have a great "
                f"day, {client_name}.", "Close", 0.85),
            _client("You too.", "Close", "neutral"),
        ]
    return s


def outcome_for(score: int, lines: list[ScriptLine]) -> str:
    last_client = next(l for l in reversed(lines) if l.role == "client")
    if score >= 70 and last_client.emotion in ("positive",):
        return "Meeting / proposal requested"
    return "Follow-up scheduled"


async def replay_call(client_name: str, bi: dict, write, negotiation: dict | None = None) -> tuple[str, int, str]:
    """Replay the script line-by-line, calling `write(line)` for each.

    `write` is provided by the caller and persists the line. Returns
    (outcome, duration_s, sentiment).
    """
    lines = build_script(client_name, bi, negotiation)
    start = asyncio.get_event_loop().time()
    for line in lines:
        await asyncio.sleep(PACE_S)
        await write(line)
    elapsed = int(asyncio.get_event_loop().time() - start)
    # last client emotion = overall sentiment
    last_client = next(l for l in reversed(lines) if l.role == "client")
    return outcome_for(bi.get("opportunity_score", 50), lines), elapsed, last_client.emotion
