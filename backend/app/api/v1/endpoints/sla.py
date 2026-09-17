from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.models.case import Case
from app.schemas.sla import CaseSLAResponse, RiskAnalysisResponse
from app.services.sla_service import initialize_or_update_case_sla, build_case_sla_response
from app.services.risk_service import evaluate_case_risk

router = APIRouter()

STAFF_ROLES = [
    UserRole.OPERATOR,
    UserRole.TEAM_LEAD,
    UserRole.MANAGER,
    UserRole.ADMINISTRATOR,
]


@router.get("/cases/{case_id}/sla", response_model=CaseSLAResponse)
def get_case_sla(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get SLA status, deadlines, and plain-language remaining time for a case.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    # Authorization: citizen can only view their own case SLA; staff can view all
    if current_user.role == UserRole.REQUESTER.value and case.citizen_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view SLA details for this case",
        )

    sla = initialize_or_update_case_sla(db, case)
    return build_case_sla_response(sla)


@router.post("/cases/{case_id}/sla/recalculate", response_model=CaseSLAResponse)
def recalculate_case_sla(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """
    Force recalculate SLA targets (e.g. after priority or category changes).
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    sla = initialize_or_update_case_sla(db, case, force_recalc=True)
    return build_case_sla_response(sla)


@router.get("/cases/{case_id}/risk", response_model=RiskAnalysisResponse)
def get_case_risk(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """
    Get multi-factor operational and deadline risk analysis for staff/leads/managers.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    return evaluate_case_risk(db, case)
