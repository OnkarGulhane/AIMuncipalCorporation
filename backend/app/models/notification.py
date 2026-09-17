import enum
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class NotificationEventType(str, enum.Enum):
    CASE_CREATED = "case_created"
    ASSIGNMENT = "assignment"
    STATUS_CHANGED = "status_changed"
    CITIZEN_RESPONSE = "citizen_response"
    STAFF_UPDATE = "staff_update"
    INFORMATION_REQUESTED = "information_requested"
    TASK_ASSIGNED = "task_assigned"
    SLA_WARNING = "sla_warning"
    ESCALATION = "escalation"
    ESCALATION_RESOLVED = "escalation_resolved"
    RESOLUTION_PROPOSED = "resolution_proposed"
    REOPENED = "reopened"
    CONFIRMED = "confirmed"
    CLOSED = "closed"


class NotificationChannel(str, enum.Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    MULTI = "multi"


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="SET NULL"), index=True, nullable=True)

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    event_type = Column(String(50), default=NotificationEventType.STATUS_CHANGED.value, index=True, nullable=False)
    channel = Column(String(20), default=NotificationChannel.IN_APP.value, nullable=False)

    is_read = Column(Boolean, default=False, index=True, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    delivery_status = Column(String(20), default="delivered", nullable=False)
    email_sent = Column(Boolean, default=False, nullable=False)
    email_to = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    case_rel = relationship("Case", foreign_keys=[case_id])

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} event={self.event_type} read={self.is_read}>"


class NotificationPreference(BaseModel):
    __tablename__ = "notification_preferences"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    email_enabled = Column(Boolean, default=True, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)

    notify_on_assignment = Column(Boolean, default=True, nullable=False)
    notify_on_status_change = Column(Boolean, default=True, nullable=False)
    notify_on_sla_warning = Column(Boolean, default=True, nullable=False)
    notify_on_escalation = Column(Boolean, default=True, nullable=False)
    notify_on_messages = Column(Boolean, default=True, nullable=False)

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<NotificationPreference user_id={self.user_id} email={self.email_enabled}>"
