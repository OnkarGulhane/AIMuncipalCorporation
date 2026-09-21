from typing import List, Optional
import base64
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, Body
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
    AIVisionAnalyzeRequest,
    AIVisionAnalyzeResponse,
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


@router.post(
    "/vision-triage",
    response_model=AIVisionAnalyzeResponse,
    summary="AI Camera / Photo Vision Triage (JSON Body)",
)
@router.post(
    "/ai/vision-triage",
    response_model=AIVisionAnalyzeResponse,
    summary="AI Camera / Photo Vision Triage alias (JSON Body)",
)
def vision_triage_json(
    request: AIVisionAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyzes visual evidence (base64 photo, filename hints, or GPS coords) to auto-detect
    the civic issue category, severity, priority, title, and technical description with 0 typing required.
    """
    image_bytes = None
    if request.image_base64:
        try:
            # Handle data URL prefix if present
            raw_base64 = request.image_base64
            if "," in raw_base64:
                raw_base64 = raw_base64.split(",", 1)[1]
            image_bytes = base64.b64decode(raw_base64)
        except Exception:
            image_bytes = None

    return ai_service.analyze_visual_evidence(
        db=db,
        image_bytes=image_bytes,
        filename=request.filename,
        image_base64=request.image_base64,
        gps_latitude=request.gps_latitude,
        gps_longitude=request.gps_longitude,
        landmark_hint=request.landmark_hint,
        voice_note=request.voice_note,
    )


@router.post(
    "/vision-triage-upload",
    response_model=AIVisionAnalyzeResponse,
    summary="AI Camera / Photo Vision Triage (Multipart File Upload)",
)
@router.post(
    "/ai/vision-triage-upload",
    response_model=AIVisionAnalyzeResponse,
    summary="AI Camera / Photo Vision Triage alias (Multipart File Upload)",
)
async def vision_triage_upload(
    file: UploadFile = File(...),
    landmark_hint: Optional[str] = Form(None),
    voice_note: Optional[str] = Form(None),
    gps_latitude: Optional[float] = Form(None),
    gps_longitude: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Accepts direct image uploads from mobile camera or web file picker and runs neural vision analysis.
    """
    content = await file.read()
    return ai_service.analyze_visual_evidence(
        db=db,
        image_bytes=content,
        filename=file.filename,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
        landmark_hint=landmark_hint,
        voice_note=voice_note,
    )

