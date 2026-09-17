from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_active_user, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.organization import (
    DepartmentCreate,
    DepartmentResponse,
    TeamCreate,
    TeamResponse,
    CategoryCreate,
    CategoryResponse,
)
from app.services.organization_service import organization_service

router = APIRouter()


# --- Department Endpoints ---
@router.get("/departments", response_model=List[DepartmentResponse], summary="List Departments")
def list_departments(
    active_only: bool = True,
    db: Session = Depends(get_db),
) -> List[DepartmentResponse]:
    """Retrieve all municipal departments."""
    departments = organization_service.list_departments(db, active_only=active_only)
    return [DepartmentResponse.model_validate(d) for d in departments]


@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Department (Admin Only)",
)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles([UserRole.ADMINISTRATOR])),
) -> DepartmentResponse:
    """Create a new municipal department (Admin only)."""
    existing = organization_service.get_department_by_code(db, code=dept_in.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with code '{dept_in.code}' already exists.",
        )
    department = organization_service.create_department(db, dept_in=dept_in)
    return DepartmentResponse.model_validate(department)


# --- Team Endpoints ---
@router.get("/teams", response_model=List[TeamResponse], summary="List Teams")
def list_teams(
    department_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[TeamResponse]:
    """Retrieve operational teams (Authenticated users)."""
    teams = organization_service.list_teams(db, department_id=department_id, active_only=active_only)
    return [TeamResponse.model_validate(t) for t in teams]


@router.post(
    "/teams",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Team (Admin / TeamLead Only)",
)
def create_team(
    team_in: TeamCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.TEAM_LEAD])),
) -> TeamResponse:
    """Create a new operational team."""
    department = organization_service.get_department_by_id(db, department_id=team_in.department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")

    team = organization_service.create_team(db, team_in=team_in)
    return TeamResponse.model_validate(team)


# --- Category Endpoints ---
@router.get("/categories", response_model=List[CategoryResponse], summary="List Complaint Categories")
def list_categories(
    department_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
) -> List[CategoryResponse]:
    """Retrieve complaint categories and their SLA targets."""
    categories = organization_service.list_categories(db, department_id=department_id, active_only=active_only)
    return [CategoryResponse.model_validate(c) for c in categories]


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Complaint Category (Admin Only)",
)
def create_category(
    cat_in: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles([UserRole.ADMINISTRATOR])),
) -> CategoryResponse:
    """Create a new category and configure its SLA target (Admin only)."""
    existing = organization_service.get_category_by_code(db, code=cat_in.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with code '{cat_in.code}' already exists.",
        )
    department = organization_service.get_department_by_id(db, department_id=cat_in.department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")

    category = organization_service.create_category(db, cat_in=cat_in)
    return CategoryResponse.model_validate(category)
