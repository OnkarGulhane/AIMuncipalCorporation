import enum
from sqlalchemy import Column, String, Boolean, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class CaseStatus(str, enum.Enum):
    REPORTED = "reported"
    UNDERSTOOD = "understood"
    ASSIGNED = "assigned"
    INVESTIGATED = "investigated"
    ACTION_TAKEN = "action_taken"
    RESOLUTION_PROPOSED = "resolution_proposed"
    CONFIRMED = "confirmed"
    CLOSED = "closed"
    WAITING_INFO = "waiting_info"
    ESCALATED = "escalated"
    DUPLICATE = "duplicate"
    REOPENED = "reopened"
    CANCELLED = "cancelled"


class CasePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseSeverity(str, enum.Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class Case(BaseModel):
    __tablename__ = "cases"

    case_number = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default=CaseStatus.REPORTED.value, index=True, nullable=False)
    priority = Column(String(20), default=CasePriority.MEDIUM.value, index=True, nullable=False)
    severity = Column(String(20), default=CaseSeverity.MODERATE.value, nullable=False)

    # Ownership & Organizational Links
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Location & Context
    ward = Column(String(100), nullable=True)
    landmark = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Resolution & Confirmation Details
    resolution_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    is_escalated = Column(Boolean, default=False, index=True, nullable=False)

    # Relationships
    citizen = relationship("User", foreign_keys=[citizen_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    department = relationship("Department", foreign_keys=[department_id])
    category = relationship("Category", foreign_keys=[category_id])
    team = relationship("Team", foreign_keys=[team_id])
    timeline = relationship(
        "CaseTimeline",
        back_populates="case_rel",
        cascade="all, delete-orphan",
        order_by="CaseTimeline.created_at.desc()",
    )
    messages = relationship(
        "CaseMessage",
        back_populates="case_rel",
        cascade="all, delete-orphan",
        order_by="CaseMessage.created_at.asc()",
    )
    internal_notes = relationship(
        "InternalNote",
        back_populates="case_rel",
        cascade="all, delete-orphan",
        order_by="InternalNote.created_at.desc()",
    )
    tasks = relationship(
        "CaseTask",
        back_populates="case_rel",
        cascade="all, delete-orphan",
        order_by="CaseTask.order.asc(), CaseTask.created_at.asc()",
    )
    investigations = relationship(
        "CaseInvestigation",
        back_populates="case_rel",
        cascade="all, delete-orphan",
        order_by="CaseInvestigation.created_at.desc()",
    )
    attachments = relationship(
        "CaseAttachment",
        back_populates="case_rel",
        cascade="all, delete-orphan",
        order_by="CaseAttachment.created_at.desc()",
    )
    ai_analyses = relationship(
        "AIAnalysis",
        back_populates="case_rel",
        cascade="all, delete-orphan",
        order_by="AIAnalysis.created_at.desc()",
    )
    sla = relationship(
        "CaseSLA",
        back_populates="case_rel",
        uselist=False,
        cascade="all, delete-orphan",
    )
    escalations = relationship(
        "CaseEscalation",
        back_populates="case_rel",
        cascade="all, delete-orphan",
        order_by="CaseEscalation.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<Case {self.case_number}: {self.title} ({self.status})>"


class CaseTimeline(BaseModel):
    __tablename__ = "case_timeline"

    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_internal = Column(Boolean, default=False, nullable=False)

    case_rel = relationship("Case", back_populates="timeline")
    actor = relationship("User", foreign_keys=[actor_id])

    def __repr__(self) -> str:
        return f"<CaseTimeline {self.case_id} - {self.action}>"
