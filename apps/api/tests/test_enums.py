"""Unit tests for the domain vocabulary enums.

Guards the contract that enum values are exactly the strings persisted in
the DB and consumed across the app — changing a value is a data migration.
"""

from app.domain.enums import (
    CallOutcome,
    CallStatus,
    ClientStatus,
    FollowUpChannel,
    FollowUpKind,
    FollowUpStatus,
    MeetingStatus,
    MemoryKey,
    MemorySource,
    ResearchStatus,
    TranscriptRole,
)


def test_call_outcome_values():
    assert CallOutcome.MEETING_REQUESTED == "Meeting / proposal requested"
    assert CallOutcome.FOLLOW_UP_SCHEDULED == "Follow-up scheduled"


def test_status_values():
    assert CallStatus.RUNNING == "running"
    assert CallStatus.DONE == "done"
    assert ClientStatus.LEAD == "Lead"
    assert ClientStatus.PROPOSAL == "Proposal"
    assert ClientStatus.CLOSED == "Closed"


def test_meeting_status_values():
    assert MeetingStatus.BOOKED == "booked"
    assert MeetingStatus.CONFIRMED == "confirmed"
    assert MeetingStatus.DONE == "done"
    assert MeetingStatus.CANCELLED == "cancelled"


def test_followup_values():
    assert FollowUpKind.THANK_YOU == "thank_you"
    assert FollowUpKind.PORTFOLIO == "portfolio"
    assert FollowUpKind.FOLLOW_UP == "follow_up"
    assert FollowUpChannel.EMAIL == "email"
    assert FollowUpStatus.PENDING == "pending"
    assert FollowUpStatus.SENT == "sent"
    assert FollowUpStatus.FAILED == "failed"


def test_memory_values():
    assert MemoryKey.INTEREST == "interest"
    assert MemoryKey.OBJECTION == "objection"
    assert MemoryKey.BUDGET == "budget"
    assert MemoryKey.LANGUAGE == "language"
    assert MemoryKey.PREFERENCE == "preference"
    assert MemorySource.CALL == "call"
    assert MemorySource.MANUAL == "manual"


def test_research_and_transcript_values():
    assert ResearchStatus.RUNNING == "running"
    assert ResearchStatus.DONE == "done"
    assert ResearchStatus.ERROR == "error"
    assert TranscriptRole.AI == "ai"
    assert TranscriptRole.CLIENT == "client"


def test_members_are_str_instances():
    """StrEnum members must equal their raw string — read path relies on it."""
    assert isinstance(CallOutcome.MEETING_REQUESTED, str)
    assert CallOutcome.MEETING_REQUESTED == "Meeting / proposal requested"
