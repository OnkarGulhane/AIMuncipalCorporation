import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.case import CaseStatus, CasePriority, CaseSeverity
from app.schemas.user import UserResponse
from app.schemas.organization import DepartmentResponse, CategoryResponse, TeamResponse


class CaseTimelineResponse(BaseModel):
    id: int
    case_id: int
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    notes: Optional[str] = None
    is_internal: bool = False
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CaseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5)
    category_id: Optional[int] = None
    department_id: Optional[int] = None
    ward: Optional[str] = Field(None, max_length=100)
    landmark: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CaseCreate(CaseBase):
    priority: Optional[CasePriority] = CasePriority.MEDIUM
    severity: Optional[CaseSeverity] = CaseSeverity.MODERATE


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=5)
    category_id: Optional[int] = None
    department_id: Optional[int] = None
    ward: Optional[str] = None
    landmark: Optional[str] = None
    priority: Optional[CasePriority] = None
    severity: Optional[CaseSeverity] = None


class CaseStatusUpdate(BaseModel):
    new_status: CaseStatus
    reason: Optional[str] = None
    resolution_notes: Optional[str] = None


class CaseAssignmentUpdate(BaseModel):
    assigned_to_id: Optional[int] = None
    team_id: Optional[int] = None
    department_id: Optional[int] = None
    reason: Optional[str] = None


class ResolutionConfirmRequest(BaseModel):
    notes: Optional[str] = None


class ResolutionRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=5, description="Citizen feedback on why the problem is not fixed.")


class CaseResponse(CaseBase):
    id: int
    case_number: str
    status: str
    priority: str
    severity: str
    citizen_id: int
    team_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    resolution_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    closed_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    # Hydrated nested relations
    citizen: Optional[UserResponse] = None
    assigned_to: Optional[UserResponse] = None
    department: Optional[DepartmentResponse] = None
    category: Optional[CategoryResponse] = None
    team: Optional[TeamResponse] = None
    timeline: Optional[List[CaseTimelineResponse]] = None

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    items: List[CaseResponse]
    total: int
    page: int
    size: int
