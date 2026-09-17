import enum
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SLAStatus(str, enum.Enum):
    WITHIN_TARGET = "within_target"
    APPROACHING_BREACH = "approaching_breach"
    BREACHED = "breached"
    MET = "met"


class CaseSLA(BaseModel):
    __tablename__ = "case_slas"

    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    # Target configurations (in hours)
    response_target_hours = Column(Integer, default=8, nullable=False)
    resolution_target_hours = Column(Integer, default=48, nullable=False)

    # Target deadlines
    response_due_at = Column(DateTime(timezone=True), nullable=False)
    resolution_due_at = Column(DateTime(timezone=True), nullable=False)

    # Actual completion timestamps
    first_responded_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Status tracking
    response_status = Column(String(50), default=SLAStatus.WITHIN_TARGET.value, nullable=False)
    resolution_status = Column(String(50), default=SLAStatus.WITHIN_TARGET.value, nullable=False)

    # Breach & Warning indicators
    is_breached = Column(Boolean, default=False, index=True, nullable=False)
    breached_at = Column(DateTime(timezone=True), nullable=True)
    warning_issued_at = Column(DateTime(timezone=True), nullable=True)

    case_rel = relationship("Case", back_populates="sla")

    def __repr__(self) -> str:
        return f"<CaseSLA case_id={self.case_id} res_status={self.resolution_status} breached={self.is_breached}>"
