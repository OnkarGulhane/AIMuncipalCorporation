import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# --- Department Schemas ---
class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


# --- Team Schemas ---
class TeamBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    department_id: int
    leader_id: Optional[int] = None
    is_active: bool = True


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    department_id: Optional[int] = None
    leader_id: Optional[int] = None
    is_active: Optional[bool] = None


class TeamResponse(TeamBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)
    department_id: int
    default_priority: str = Field("medium", pattern="^(low|medium|high|critical)$")
    sla_hours: int = Field(48, ge=1, le=720)
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    department_id: Optional[int] = None
    default_priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    sla_hours: Optional[int] = Field(None, ge=1, le=720)
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


# --- Permissions Schema ---
class PermissionDescriptor(BaseModel):
    role: str
    can_create_case: bool
    can_view_all_cases: bool
    can_assign_cases: bool
    can_add_internal_notes: bool
    can_submit_resolution: bool
    can_confirm_resolution: bool
    can_escalate_case: bool
    can_manage_users: bool
    can_manage_departments: bool
    can_view_manager_analytics: bool
