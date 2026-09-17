from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.services.ai_service import ai_service
from app.schemas.ai import (
    AIAnalysisResponse,
    AIDraftRequest,
    AIDraftResponse,
    AIApplySuggestionsRequest,
    AICaseSummaryResponse,
    DuplicateCaseMatch,
)
from app.schemas.case import CaseResponse

router = APIRouter()

STAFF_ROLES = [
    UserRole.OPERATOR,
    UserRole.TEAM_LEAD,
    UserRole.MANAGER,
    UserRole.ADMINISTRATOR,
]


@router.post(
    "/{case_id}/ai-analysis",
    response_model=AIAnalysisResponse,
    summary="Trigger or re-run AI triage and case understanding",
)
def run_ai_analysis(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Run automated AI classification, priority suggestion, missing-information detection,
    and duplicate matching for the specified case.
    """
    return ai_service.run_case_analysis(db, case_id=case_id, user=current_user)


@router.get(
    "/{case_id}/ai-analysis",
    response_model=AIAnalysisResponse,
    summary="Get the latest AI analysis for a case",
)
def get_ai_analysis(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve saved AI insights and recommendations for the case."""
    return ai_service.get_latest_analysis(db, case_id=case_id, user=current_user)


@router.post(
    "/{case_id}/ai/apply-suggestions",
    response_model=CaseResponse,
    summary="Staff accepts and applies AI recommendations (Staff only)",
)
def apply_ai_suggestions(
    case_id: int,
    data: AIApplySuggestionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """
    Human-in-the-loop: Operator explicitly accepts recommended category,
    priority, or team assignment and updates the live case.
    """
    updated_case = ai_service.apply_suggestions(
        db, case_id=case_id, data=data, user=current_user
    )
    return CaseResponse.model_validate(updated_case)


@router.post(
    "/{case_id}/ai/draft-communication",
    response_model=AIDraftResponse,
    summary="Generate AI-crafted communication draft for citizen or team",
)
def draft_communication(
    case_id: int,
    request: AIDraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    AI Communication Copilot: Generates contextual drafts for information requests,
    progress updates, resolution messages, or internal escalation memos.
    """
    return ai_service.generate_communication_draft(
        db, case_id=case_id, request=request, user=current_user
    )


@router.get(
    "/{case_id}/summary",
    response_model=AICaseSummaryResponse,
    summary="Get AI-generated comprehensive case journey summary",
)
def get_case_summary(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate or retrieve a concise explanation of case history and unresolved items."""
    return ai_service.get_case_summary(db, case_id=case_id, user=current_user)


@router.get(
    "/{case_id}/duplicates",
    response_model=List[DuplicateCaseMatch],
    summary="Get potential duplicate or related case matches",
)
def get_duplicate_cases(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Check for related civic complaints reported in the same vicinity."""
    analysis = ai_service.get_latest_analysis(db, case_id=case_id, user=current_user)
    return analysis.duplicate_cases or []
