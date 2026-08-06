"""Domain vocabulary enums.

Single source of truth for every status/outcome string in the system.
Values are the exact strings persisted in the DB — changing a value here is
a data migration, not an edit.

StrEnum chosen so members compare equal to their raw string value: the read
path (ORM columns return plain strings) compares cleanly with `== member`.
Write `.value` explicitly at persistence boundaries where clarity matters;
ORM binding also handles members directly (they are str subclasses).
"""

from enum import StrEnum


class ClientStatus(StrEnum):
    LEAD = "Lead"
    PROPOSAL = "Proposal"
    CLOSED = "Closed"


class CallStatus(StrEnum):
    RUNNING = "running"
    DONE = "done"


class CallOutcome(StrEnum):
    MEETING_REQUESTED = "Meeting / proposal requested"
    FOLLOW_UP_SCHEDULED = "Follow-up scheduled"


class TranscriptRole(StrEnum):
    AI = "ai"
    CLIENT = "client"


class MeetingStatus(StrEnum):
    BOOKED = "booked"
    CONFIRMED = "confirmed"
    DONE = "done"
    CANCELLED = "cancelled"


class FollowUpKind(StrEnum):
    THANK_YOU = "thank_you"
    PORTFOLIO = "portfolio"
    FOLLOW_UP = "follow_up"


class FollowUpChannel(StrEnum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"


class FollowUpStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class MemoryKey(StrEnum):
    INTEREST = "interest"
    OBJECTION = "objection"
    BUDGET = "budget"
    LANGUAGE = "language"
    PREFERENCE = "preference"


class MemorySource(StrEnum):
    CALL = "call"
    MANUAL = "manual"


class ResearchStatus(StrEnum):
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
