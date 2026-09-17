from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EscalationCreate(BaseModel):
    reason: str = Field(..., min_length=3, description="Reason for escalation")
    trigger_type: str = Field(
        default="manual",
        description="Trigger: sla_breach, approaching_deadline, risk_threshold, operator_request, reopened_case, safety_critical, manual",
    )
    escalated_to_id: Optional[int] = None


class EscalationUpdate(BaseModel):
    status: str = Field(..., description="Status: acknowledged, resolved, dismissed")
    resolution_notes: Optional[str] = Field(None, description="Notes on how the escalation was addressed")


class EscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    case_number: Optional[str] = None
    case_title: Optional[str] = None
    escalated_by_id: Optional[int] = None
    escalated_by_name: Optional[str] = None
    escalated_to_id: Optional[int] = None
    escalated_to_name: Optional[str] = None
    trigger_type: str
    reason: str
    status: str
    resolution_notes: Optional[str] = None
    resolved_by_id: Optional[int] = None
    resolved_by_name: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
