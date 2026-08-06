"""Org-scoped repository layer.

Every query filters by organization_id and every insert stamps it — tenant
filtering cannot be forgotten. Routers never touch Session/Model directly.
"""

from .calls import CallRepository
from .clients import ClientRepository, EmailRepository, TimelineRepository
from .followups import FollowUpRepository
from .learning import LearningEntryRepository
from .meetings import MeetingRepository
from .memory import MemoryRepository
from .negotiation import NegotiationConfigRepository
from .research import ResearchReportRepository

__all__ = [
    "CallRepository",
    "ClientRepository",
    "EmailRepository",
    "TimelineRepository",
    "FollowUpRepository",
    "LearningEntryRepository",
    "MeetingRepository",
    "MemoryRepository",
    "NegotiationConfigRepository",
    "ResearchReportRepository",
]
