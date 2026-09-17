import enum
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class EscalationTrigger(str, enum.Enum):
    SLA_BREACH = "sla_breach"
    APPROACHING_DEADLINE = "approaching_deadline"
    RISK_THRESHOLD = "risk_threshold"
    OPERATOR_REQUEST = "operator_request"
    REOPENED_CASE = "reopened_case"
    SAFETY_CRITICAL = "safety_critical"
    MANUAL = "manual"


class EscalationStatus(str, enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class CaseEscalation(BaseModel):
    __tablename__ = "case_escalations"

    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False)
    escalated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null if system-triggered
    escalated_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Team Lead or Manager

    trigger_type = Column(String(50), default=EscalationTrigger.MANUAL.value, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default=EscalationStatus.ACTIVE.value, index=True, nullable=False)

    resolution_notes = Column(Text, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    case_rel = relationship("Case", back_populates="escalations")
    escalated_by = relationship("User", foreign_keys=[escalated_by_id])
    escalated_to = relationship("User", foreign_keys=[escalated_to_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])

    def __repr__(self) -> str:
        return f"<CaseEscalation case_id={self.case_id} trigger={self.trigger_type} status={self.status}>"
