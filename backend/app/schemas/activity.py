from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.activity import CaseMessageType, InternalNoteType, TaskStatus


# ---------------------------------------------------------------------------
# Case Messages (Citizen <-> Staff Communication)
# ---------------------------------------------------------------------------

class CaseMessageCreate(BaseModel):
    message: str
    message_type: Optional[CaseMessageType] = CaseMessageType.GENERAL


class CaseMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    sender_id: int
    sender_name: Optional[str] = None
    sender_role: Optional[str] = None
    message: str
    message_type: str
    is_from_citizen: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Internal Notes (Staff-only private notes)
# ---------------------------------------------------------------------------

class InternalNoteCreate(BaseModel):
    note: str
    note_type: Optional[InternalNoteType] = InternalNoteType.GENERAL


class InternalNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    author_id: int
    author_name: Optional[str] = None
    author_role: Optional[str] = None
    note: str
    note_type: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Case Tasks
# ---------------------------------------------------------------------------

class CaseTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to_id: Optional[int] = None
    due_date: Optional[datetime] = None
    order: Optional[int] = 0


class CaseTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    assigned_to_id: Optional[int] = None
    due_date: Optional[datetime] = None
    order: Optional[int] = None


class CaseTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    title: str
    description: Optional[str] = None
    status: str
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    created_by_id: int
    created_by_name: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    order: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Case Investigations
# ---------------------------------------------------------------------------

class CaseInvestigationCreate(BaseModel):
    observations: Optional[str] = None
    actions_taken: Optional[str] = None
    findings: Optional[str] = None
    evidence_notes: Optional[str] = None
    follow_up_requirements: Optional[str] = None


class CaseInvestigationUpdate(BaseModel):
    observations: Optional[str] = None
    actions_taken: Optional[str] = None
    findings: Optional[str] = None
    evidence_notes: Optional[str] = None
    follow_up_requirements: Optional[str] = None


class CaseInvestigationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    investigator_id: int
    investigator_name: Optional[str] = None
    observations: Optional[str] = None
    actions_taken: Optional[str] = None
    findings: Optional[str] = None
    evidence_notes: Optional[str] = None
    follow_up_requirements: Optional[str] = None
    created_at: datetime
    updated_at: datetime
