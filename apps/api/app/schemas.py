from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    summary: str | None
    outcome: str | None
    sentiment: str | None
    duration_s: int | None
    status: str
    stage: str | None
    created_at: datetime


class TranscriptLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    text: str
    emotion: str | None
    confidence: float | None
    stage: str | None
    created_at: datetime


class CallDetail(CallOut):
    transcript: list[TranscriptLineOut] = []


class TimelineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event: str
    created_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: str | None
    url: str | None
    created_at: datetime


class EmailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str
    body: str | None
    direction: str
    created_at: datetime


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str | None
    email: str | None
    phone: str | None
    website: str | None
    industry: str | None
    budget: float | None
    notes: str | None
    status: str
    created_at: datetime


class ClientDetail(ClientOut):
    calls: list[CallOut] = []
    timeline: list[TimelineOut] = []
    documents: list[DocumentOut] = []
    emails: list[EmailOut] = []


class ClientCreate(BaseModel):
    name: str
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    industry: str | None = None
    budget: float | None = None
    notes: str | None = None
    status: str = "Lead"


class ClientUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    industry: str | None = None
    budget: float | None = None
    notes: str | None = None
    status: str | None = None


class LearningEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    call_id: int
    client_id: int
    outcome: str | None
    success_score: int | None
    objection: str | None
    strategy_used: str | None
    lesson: str | None
    created_at: datetime


class LearningStats(BaseModel):
    total_reviews: int
    avg_score: int
    top_objections: list[dict]  # [{objection, count}]
    strategies: list[dict]  # [{strategy, count}]


class MemoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    key: str
    value: str
    source: str | None
    created_at: datetime


class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    call_id: int | None
    kind: str
    channel: str
    content: str
    status: str
    created_at: datetime


class MeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    call_id: int | None
    title: str
    scheduled_at: datetime
    status: str
    created_at: datetime


class MeetingCreate(BaseModel):
    client_id: int
    title: str
    scheduled_at: datetime


class NegotiationConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    pricing: list | None
    discounts: list | None
    freebies: list | None
    payment_terms: list | None
    escalation_rules: list | None
    updated_at: datetime


class NegotiationConfigUpdate(BaseModel):
    pricing: list | None = None
    discounts: list | None = None
    freebies: list | None = None
    payment_terms: list | None = None
    escalation_rules: list | None = None


class ResearchReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    url: str
    status: str
    error: str | None
    seo_score: int | None
    performance_score: int | None
    tech_stack: list | None
    seo_checks: list | None
    missing_features: list | None
    opportunities: list | None
    competitors: list | None
    created_at: datetime


class TimelineCreate(BaseModel):
    event: str


class EmailCreate(BaseModel):
    subject: str
    body: str | None = None
    direction: str = "out"
