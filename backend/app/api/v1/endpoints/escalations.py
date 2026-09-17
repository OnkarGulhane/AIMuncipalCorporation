from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.models.case import Case
from app.models.escalation import CaseEscalation, EscalationStatus
from app.schemas.escalation import EscalationCreate, EscalationUpdate, EscalationResponse
from app.services.escalation_service import (
    create_case_escalation,
    update_case_escalation,
    build_escalation_response,
)
from app.core.scheduler import sweep_slas_and_risks_sync

router = APIRouter()

STAFF_ROLES = [
    UserRole.OPERATOR,
    UserRole.TEAM_LEAD,
    UserRole.MANAGER,
    UserRole.ADMINISTRATOR,
]

LEAD_ROLES = [
    UserRole.TEAM_LEAD,
    UserRole.MANAGER,
    UserRole.ADMINISTRATOR,
]


@router.get("/cases/{case_id}/escalations", response_model=List[EscalationResponse])
def list_case_escalations(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """
    List all escalations logged for a specific case (Staff only).
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    escalations = (
        db.query(CaseEscalation)
        .filter(CaseEscalation.case_id == case_id)
        .order_by(CaseEscalation.created_at.desc())
        .all()
    )
    return [build_escalation_response(e) for e in escalations]


@router.post("/cases/{case_id}/escalations", response_model=EscalationResponse, status_code=status.HTTP_201_CREATED)
def create_escalation(
    case_id: int,
    payload: EscalationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """
    Trigger manual escalation for a case (Operator, Team Lead, Manager, Administrator).
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    escalation = create_case_escalation(
        db=db,
        case=case,
        escalation_data=payload,
        current_user=current_user,
    )
    return build_escalation_response(escalation)


@router.patch("/cases/{case_id}/escalations/{escalation_id}", response_model=EscalationResponse)
def update_escalation(
    case_id: int,
    escalation_id: int,
    payload: EscalationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(LEAD_ROLES)),
):
    """
    Acknowledge, resolve, or dismiss an escalation (Team Lead, Manager, Administrator).
    """
    escalation = (
        db.query(CaseEscalation)
        .filter(
            CaseEscalation.id == escalation_id,
            CaseEscalation.case_id == case_id,
        )
        .first()
    )
    if not escalation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation record not found")

    updated = update_case_escalation(
        db=db,
        escalation=escalation,
        update_data=payload,
        current_user=current_user,
    )
    return build_escalation_response(updated)


@router.get("/escalations", response_model=List[EscalationResponse])
def list_all_escalations(
    status_filter: Optional[str] = Query(None, alias="status"),
    trigger_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(LEAD_ROLES)),
):
    """
    Global list of escalations for Team Leads, Managers, and Admins.
    """
    query = db.query(CaseEscalation).order_by(CaseEscalation.created_at.desc())

    if status_filter:
        query = query.filter(CaseEscalation.status == status_filter)
    if trigger_type:
        query = query.filter(CaseEscalation.trigger_type == trigger_type)

    escalations = query.offset(offset).limit(limit).all()
    return [build_escalation_response(e) for e in escalations]


@router.post("/automation/sweep-slas-and-risks")
def trigger_manual_sla_risk_sweep(
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """
    Manually trigger an immediate SLA and Risk sweep across all active cases.
    """
    sweep_slas_and_risks_sync()
    return {"message": "SLA and Risk sweep completed successfully."}
