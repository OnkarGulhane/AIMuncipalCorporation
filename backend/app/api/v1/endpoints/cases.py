from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_active_user, require_roles
from app.core.database import get_db
from app.models.case import Case, CaseStatus
from app.models.user import User, UserRole
from datetime import datetime
from app.schemas.case import (
    CaseCreate,
    CaseResponse,
    CaseListResponse,
    CaseStatusUpdate,
    CaseAssignmentUpdate,
    CaseTimelineResponse,
    UnifiedTimelineItem,
    UnifiedTimelineResponse,
    ResolutionConfirmRequest,
    ResolutionRejectRequest,
)
from app.services.case_service import case_service

router = APIRouter()


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED, summary="Create Case / Report Complaint")
def create_case(
    case_in: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CaseResponse:
    """
    Report a new civic complaint.
    Generates a unique case number and initializes lifecycle in 'reported' status.
    """
    created_case = case_service.create_case(
        db,
        case_in=case_in,
        citizen_id=current_user.id,
    )
    return CaseResponse.model_validate(created_case)


@router.get("", response_model=CaseListResponse, summary="List & Search Cases")
def list_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    department_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    team_id: Optional[int] = Query(None),
    ward: Optional[str] = Query(None),
    assigned_to_id: Optional[int] = Query(None),
    citizen_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    created_from: Optional[datetime] = Query(None),
    created_to: Optional[datetime] = Query(None),
    is_overdue: Optional[bool] = Query(None),
    is_at_risk: Optional[bool] = Query(None),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|priority|status|case_number)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),

    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CaseListResponse:
    """
    List, filter, and multi-criteria search cases.
    Requesters only see their own reported cases; Staff see authorized cases.
    """
    items, total = case_service.list_cases(
        db,
        user=current_user,
        status=status_filter,
        priority=priority,
        severity=severity,
        department_id=department_id,
        category_id=category_id,
        team_id=team_id,
        ward=ward,
        assigned_to_id=assigned_to_id,
        citizen_id=citizen_id,
        search=search,
        created_from=created_from,
        created_to=created_to,
        is_overdue=is_overdue,
        is_at_risk=is_at_risk,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )
    return CaseListResponse(
        items=[CaseResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{case_id}", response_model=CaseResponse, summary="Get Case Details with Timeline")
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CaseResponse:
    """
    Retrieve full case details, history timeline, and current status.
    """
    case_obj = case_service.get_by_id(db, case_id=case_id)
    if not case_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    # Requester authorization guard: cannot view another citizen's case
    if current_user.role == UserRole.REQUESTER.value and case_obj.citizen_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this case.",
        )

    return CaseResponse.model_validate(case_obj)


@router.get("/{case_id}/timeline", response_model=UnifiedTimelineResponse, summary="Get Unified Case Timeline")
def get_case_timeline(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UnifiedTimelineResponse:
    """
    Retrieve unified chronological timeline consolidating lifecycle events,
    messages, tasks, investigations, and escalations.
    Maintains strict Requester privacy isolation.
    """
    try:
        return case_service.get_unified_case_timeline(db, case_id=case_id, user=current_user)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))



@router.put("/{case_id}/status", response_model=CaseResponse, summary="Update Case Lifecycle Status")
def update_case_status(
    case_id: int,
    status_in: CaseStatusUpdate,
    db: Session = Depends(get_db),
    staff_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.TEAM_LEAD, UserRole.MANAGER, UserRole.ADMINISTRATOR])),
) -> CaseResponse:
    """
    Advance or transition case lifecycle state.
    Strictly validates allowed state machine transitions.
    """
    case_obj = case_service.get_by_id(db, case_id=case_id)
    if not case_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    try:
        updated_case = case_service.update_case_status(
            db,
            case_obj=case_obj,
            new_status=status_in.new_status,
            actor=staff_user,
            reason=status_in.reason,
            resolution_notes=status_in.resolution_notes,
        )
        return CaseResponse.model_validate(updated_case)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.put("/{case_id}/assignment", response_model=CaseResponse, summary="Assign Case to Operator / Team")
def update_case_assignment(
    case_id: int,
    assign_in: CaseAssignmentUpdate,
    db: Session = Depends(get_db),
    staff_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.TEAM_LEAD, UserRole.MANAGER, UserRole.ADMINISTRATOR])),
) -> CaseResponse:
    """
    Assign or reassign case ownership.
    """
    case_obj = case_service.get_by_id(db, case_id=case_id)
    if not case_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    updated_case = case_service.update_assignment(
        db,
        case_obj=case_obj,
        actor=staff_user,
        assigned_to_id=assign_in.assigned_to_id,
        team_id=assign_in.team_id,
        department_id=assign_in.department_id,
        reason=assign_in.reason,
    )
    return CaseResponse.model_validate(updated_case)


@router.post("/{case_id}/confirm-resolution", response_model=CaseResponse, summary="Citizen Confirm Resolution")
def confirm_resolution(
    case_id: int,
    confirm_in: ResolutionConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CaseResponse:
    """
    Citizen confirms that proposed resolution is satisfactory, closing the case.
    """
    case_obj = case_service.get_by_id(db, case_id=case_id)
    if not case_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    try:
        updated_case = case_service.confirm_resolution(
            db,
            case_obj=case_obj,
            citizen=current_user,
            notes=confirm_in.notes,
        )
        return CaseResponse.model_validate(updated_case)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.post("/{case_id}/reject-resolution", response_model=CaseResponse, summary="Citizen Reject Resolution (Reopen Case)")
def reject_resolution(
    case_id: int,
    reject_in: ResolutionRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CaseResponse:
    """
    Citizen rejects proposed resolution, reopening the case while preserving full history.
    """
    case_obj = case_service.get_by_id(db, case_id=case_id)
    if not case_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    try:
        updated_case = case_service.reject_resolution(
            db,
            case_obj=case_obj,
            citizen=current_user,
            rejection_reason=reject_in.rejection_reason,
        )
        return CaseResponse.model_validate(updated_case)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
