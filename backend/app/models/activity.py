import enum
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class CaseMessageType(str, enum.Enum):
    GENERAL = "general"
    QUERY = "query"
    STAFF_UPDATE = "staff_update"
    EVIDENCE_REQUEST = "evidence_request"
    RESOLUTION_UPDATE = "resolution_update"


class InternalNoteType(str, enum.Enum):
    GENERAL = "general"
    INVESTIGATION_DISCUSSION = "investigation_discussion"
    MANAGEMENT_NOTE = "management_note"
    HANDOVER = "handover"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CaseMessage(BaseModel):
    __tablename__ = "case_messages"

    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(50), default=CaseMessageType.GENERAL.value, nullable=False)
    is_from_citizen = Column(Boolean, default=False, nullable=False)

    case_rel = relationship("Case", foreign_keys=[case_id], back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

    def __repr__(self) -> str:
        return f"<CaseMessage {self.id} on Case {self.case_id} by User {self.sender_id}>"


class InternalNote(BaseModel):
    __tablename__ = "internal_notes"

    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=False)
    note_type = Column(String(50), default=InternalNoteType.GENERAL.value, nullable=False)

    case_rel = relationship("Case", foreign_keys=[case_id], back_populates="internal_notes")
    author = relationship("User", foreign_keys=[author_id])

    def __repr__(self) -> str:
        return f"<InternalNote {self.id} on Case {self.case_id} by User {self.author_id}>"


class CaseTask(BaseModel):
    __tablename__ = "case_tasks"

    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=TaskStatus.PENDING.value, index=True, nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    order = Column(Integer, default=0, nullable=False)

    case_rel = relationship("Case", foreign_keys=[case_id], back_populates="tasks")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self) -> str:
        return f"<CaseTask {self.title} ({self.status})>"


class CaseInvestigation(BaseModel):
    __tablename__ = "case_investigations"

    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    investigator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    observations = Column(Text, nullable=True)
    actions_taken = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    evidence_notes = Column(Text, nullable=True)
    follow_up_requirements = Column(Text, nullable=True)

    case_rel = relationship("Case", foreign_keys=[case_id], back_populates="investigations")
    investigator = relationship("User", foreign_keys=[investigator_id])

    def __repr__(self) -> str:
        return f"<CaseInvestigation on Case {self.case_id} by User {self.investigator_id}>"
