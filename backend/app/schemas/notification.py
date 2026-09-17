from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    case_id: Optional[int] = None
    case_number: Optional[str] = None
    case_title: Optional[str] = None
    title: str
    message: str
    event_type: str
    channel: str
    is_read: bool
    read_at: Optional[datetime] = None
    delivery_status: str
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    size: int


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email_enabled: bool
    in_app_enabled: bool
    notify_on_assignment: bool
    notify_on_status_change: bool
    notify_on_sla_warning: bool
    notify_on_escalation: bool
    notify_on_messages: bool


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    notify_on_assignment: Optional[bool] = None
    notify_on_status_change: Optional[bool] = None
    notify_on_sla_warning: Optional[bool] = None
    notify_on_escalation: Optional[bool] = None
    notify_on_messages: Optional[bool] = None


class UnreadCountResponse(BaseModel):
    unread_count: int
