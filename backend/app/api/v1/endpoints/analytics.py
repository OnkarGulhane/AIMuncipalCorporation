from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.schemas.analytics import (
    ManagerAnalyticsResponse,
    TeamLeadAnalyticsResponse,
    OperatorAnalyticsResponse,
    CitizenAnalyticsResponse,
    WardIntelligenceResponse,
)
from app.services.analytics_service import analytics_service

router = APIRouter()

STAFF_ROLES = [
    UserRole.OPERATOR,
    UserRole.TEAM_LEAD,
    UserRole.MANAGER,
    UserRole.ADMINISTRATOR,
]

LEAD_AND_ABOVE = [
    UserRole.TEAM_LEAD,
    UserRole.MANAGER,
    UserRole.ADMINISTRATOR,
]

MANAGER_AND_ADMIN = [
    UserRole.MANAGER,
    UserRole.ADMINISTRATOR,
]


@router.get("/manager", response_model=ManagerAnalyticsResponse, summary="Executive Corporation Analytics (Manager & Admin)")
def get_manager_dashboard(
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    days: int = Query(30, ge=1, le=365, description="Time window in days"),
    current_user: User = Depends(require_roles(MANAGER_AND_ADMIN)),
    db: Session = Depends(get_db),
) -> ManagerAnalyticsResponse:
    """
    Returns executive metrics, resolution rate, SLA compliance %,
    ward breakdown, time-series trends, and AI operational insights.
    """
    return analytics_service.get_manager_analytics(db=db, department_id=department_id, days=days)


@router.get("/team-lead", response_model=TeamLeadAnalyticsResponse, summary="Team Workload & Operator Roster (Team Lead & Above)")
def get_team_lead_dashboard(
    current_user: User = Depends(require_roles(LEAD_AND_ABOVE)),
    db: Session = Depends(get_db),
) -> TeamLeadAnalyticsResponse:
    """
    Returns team-level workload, operator active/completed distribution,
    at-risk cases count, and unassigned queue items.
    """
    return analytics_service.get_team_lead_analytics(db=db, user=current_user)


@router.get("/operator", response_model=OperatorAnalyticsResponse, summary="Operator Workload & Queue (Operator & Above)")
def get_operator_dashboard(
    current_user: User = Depends(require_roles(STAFF_ROLES)),
    db: Session = Depends(get_db),
) -> OperatorAnalyticsResponse:
    """
    Returns personal workload metrics, high-priority ticket count,
    waiting-for-info count, pending tasks, and active escalations.
    """
    return analytics_service.get_operator_analytics(db=db, user=current_user)


@router.get("/citizen", response_model=CitizenAnalyticsResponse, summary="Citizen Personal Complaint Dashboard")
def get_citizen_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CitizenAnalyticsResponse:
    """
    Returns citizen's personal complaint breakdown, pending verification count,
    waiting for information count, and recent activity timeline.
    """
    return analytics_service.get_citizen_analytics(db=db, user=current_user)


@router.get("/wards", response_model=WardIntelligenceResponse, summary="Ward Intelligence & Geospatial Hotspots (Staff Only)")
def get_ward_intelligence(
    current_user: User = Depends(require_roles(STAFF_ROLES)),
    db: Session = Depends(get_db),
) -> WardIntelligenceResponse:
    """
    Returns ward-level grievance clustering, resolution efficiency,
    and top active hotspots across municipal sectors.
    """
    return analytics_service.get_ward_intelligence(db=db)
