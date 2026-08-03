from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    company: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(300))
    industry: Mapped[str | None] = mapped_column(String(100))
    budget: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="Lead")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    calls = relationship("Call", back_populates="client", cascade="all, delete-orphan")
    timeline = relationship("TimelineEvent", back_populates="client", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="client", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="client", cascade="all, delete-orphan")
    research = relationship("ResearchReport", back_populates="client", cascade="all, delete-orphan")
    negotiation = relationship("NegotiationConfig", back_populates="client", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="client", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="client", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="client", cascade="all, delete-orphan")


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    summary: Mapped[str | None] = mapped_column(Text)
    outcome: Mapped[str | None] = mapped_column(String(100))
    sentiment: Mapped[str | None] = mapped_column(String(50))
    duration_s: Mapped[int | None]
    status: Mapped[str] = mapped_column(String(20), default="running")  # running | done
    stage: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    client = relationship("Client", back_populates="calls")
    transcript = relationship("TranscriptLine", back_populates="call", cascade="all, delete-orphan")


class TranscriptLine(Base):
    __tablename__ = "transcript_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[int] = mapped_column(ForeignKey("calls.id"))
    role: Mapped[str] = mapped_column(String(10))  # ai | client
    text: Mapped[str] = mapped_column(Text)
    emotion: Mapped[str | None] = mapped_column(String(50))
    confidence: Mapped[float | None]
    stage: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    call = relationship("Call", back_populates="transcript")


class TimelineEvent(Base):
    __tablename__ = "timeline"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    event: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    client = relationship("Client", back_populates="timeline")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str | None] = mapped_column(String(50))  # proposal | contract | portfolio
    url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    client = relationship("Client", back_populates="documents")


class LearningEntry(Base):
    __tablename__ = "learning_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[int] = mapped_column(ForeignKey("calls.id"), unique=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    outcome: Mapped[str | None] = mapped_column(String(100))
    success_score: Mapped[int | None]  # 0-100
    objection: Mapped[str | None] = mapped_column(Text)
    strategy_used: Mapped[str | None] = mapped_column(Text)
    lesson: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    key: Mapped[str] = mapped_column(String(50))  # interest | objection | budget | language | preference
    value: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(50))  # call | manual
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    client = relationship("Client", back_populates="memories")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    call_id: Mapped[int | None] = mapped_column(ForeignKey("calls.id"))
    kind: Mapped[str] = mapped_column(String(50))  # thank_you | portfolio | proposal | follow_up
    channel: Mapped[str] = mapped_column(String(20), default="email")  # email | whatsapp | sms
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | sent | failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    client = relationship("Client", back_populates="follow_ups")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    call_id: Mapped[int | None] = mapped_column(ForeignKey("calls.id"))
    title: Mapped[str] = mapped_column(String(200))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="booked")  # booked | confirmed | done | cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    client = relationship("Client", back_populates="meetings")


class NegotiationConfig(Base):
    __tablename__ = "negotiation_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), unique=True)
    pricing: Mapped[list | None] = mapped_column(JSON)  # [{label, amount}]
    discounts: Mapped[list | None] = mapped_column(JSON)  # [{label, percent}]
    freebies: Mapped[list | None] = mapped_column(JSON)  # [str]
    payment_terms: Mapped[list | None] = mapped_column(JSON)  # [str]
    escalation_rules: Mapped[list | None] = mapped_column(JSON)  # [str]
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    client = relationship("Client", back_populates="negotiation")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    url: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(30), default="running")  # running | done | error
    error: Mapped[str | None] = mapped_column(Text)
    seo_score: Mapped[int | None]
    performance_score: Mapped[int | None]
    tech_stack: Mapped[list | None] = mapped_column(JSON)
    seo_checks: Mapped[list | None] = mapped_column(JSON)
    missing_features: Mapped[list | None] = mapped_column(JSON)
    opportunities: Mapped[list | None] = mapped_column(JSON)
    competitors: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    client = relationship("Client", back_populates="research")


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str | None] = mapped_column(Text)
    direction: Mapped[str] = mapped_column(String(20), default="out")  # in | out
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    client = relationship("Client", back_populates="emails")
