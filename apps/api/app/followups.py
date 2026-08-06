"""Follow-up content generation + transport.

Content templates keyed by outcome/kind. Transport is a no-op log for the
demo — real WhatsApp/Email goes here behind the same `send` contract
(Twilio WhatsApp / Resend). See `ponytail` markers.
"""
from .calls import build_script  # noqa: F401  (kept import for script reuse if needed)

POSITIVE_OUTCOMES = {"Meeting / proposal requested"}
WARM_OUTCOMES = {"Follow-up scheduled"}


def _signature() -> str:
    return "\n\n— Ava, your AI Business Development Manager at AABDM"


def generate_followups(client_name: str, service: str | None, outcome: str) -> list[dict]:
    """Returns list of {kind, channel, content}. No transport yet — pending."""
    service = service or "digital growth services"
    items: list[dict] = []

    if outcome in POSITIVE_OUTCOMES:
        items += [
            {
                "kind": "thank_you",
                "channel": "email",
                "content": (
                    f"Hi {client_name},\n\nThank you for your time today — great "
                    f"conversation about {service}. I've booked a follow-up meeting "
                    f"to walk you through the details.\n\nSpeak soon!"
                    f"{_signature()}"
                ),
            },
            {
                "kind": "portfolio",
                "channel": "email",
                "content": (
                    f"Hi {client_name},\n\nAs promised, here's a selection of work "
                    f"we've done for businesses like yours around {service}. "
                    f"Happy to discuss what maps to your goals.\n\n[portfolio link]"
                    f"{_signature()}"
                ),
            },
        ]
    elif outcome in WARM_OUTCOMES:
        items += [
            {
                "kind": "follow_up",
                "channel": "email",
                "content": (
                    f"Hi {client_name},\n\nFollowing up on our call — here's a short "
                    f"summary of where we saw opportunities with {service}. "
                    f"No pressure, just the numbers.\n\n[summary attached]"
                    f"{_signature()}"
                ),
            }
        ]
    return items


async def send_followup(channel: str, to: str, content: str) -> str:
    """Transport stub — logs the message. Returns provider status.

    ponytail: real send here. Twilio WhatsApp API when key exists, Resend for
    email. Contract: return 'sent' on success, raise on failure.
    """
    # no-op: nothing leaves the box until keys are configured
    return "sent (mock)"
