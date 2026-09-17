from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.services.activity_service import activity_service
from app.schemas.activity import (
    CaseMessageCreate,
    CaseMessageResponse,
    InternalNoteCreate,
    InternalNoteResponse,
    CaseTaskCreate,
    CaseTaskUpdate,
    CaseTaskResponse,
    CaseInvestigationCreate,
    CaseInvestigationResponse,
)

router = APIRouter()

STAFF_ROLES = [
    UserRole.OPERATOR,
    UserRole.TEAM_LEAD,
    UserRole.MANAGER,
    UserRole.ADMINISTRATOR,
]


# ---------------------------------------------------------------------------
# Citizen <-> Staff Messages
# ---------------------------------------------------------------------------

@router.get(
    "/{case_id}/messages",
    response_model=List[CaseMessageResponse],
    summary="List all citizen-visible messages for a case",
)
def list_case_messages(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve all communication messages between citizen and municipal staff for a case."""
    return activity_service.list_messages(db, case_id=case_id, user=current_user)


@router.post(
    "/{case_id}/messages",
    response_model=CaseMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a communication message on a case",
)
def create_case_message(
    case_id: int,
    data: CaseMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Citizen or staff posting a case communication message."""
    return activity_service.create_message(
        db, case_id=case_id, data=data, user=current_user
    )


# ---------------------------------------------------------------------------
# Internal Notes (Strictly Staff-Only)
# ---------------------------------------------------------------------------

@router.get(
    "/{case_id}/internal-notes",
    response_model=List[InternalNoteResponse],
    summary="List private staff-only internal notes for a case",
)
def list_internal_notes(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """Retrieve private internal notes. Requesters are blocked with 403 Forbidden."""
    return activity_service.list_internal_notes(
        db, case_id=case_id, user=current_user
    )


@router.post(
    "/{case_id}/internal-notes",
    response_model=InternalNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a private staff internal note to a case",
)
def create_internal_note(
    case_id: int,
    data: InternalNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """Create a private internal note. Never exposed to requesters."""
    return activity_service.create_internal_note(
        db, case_id=case_id, data=data, user=current_user
    )


# ---------------------------------------------------------------------------
# Case Tasks
# ---------------------------------------------------------------------------

@router.get(
    "/{case_id}/tasks",
    response_model=List[CaseTaskResponse],
    summary="List all subtasks for a case",
)
def list_case_tasks(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List actionable subtasks for a case."""
    return activity_service.list_tasks(db, case_id=case_id, user=current_user)


@router.post(
    "/{case_id}/tasks",
    response_model=CaseTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task for a case (Staff only)",
)
def create_case_task(
    case_id: int,
    data: CaseTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """Staff creating an actionable task on a case."""
    return activity_service.create_task(
        db, case_id=case_id, data=data, user=current_user
    )


@router.patch(
    "/{case_id}/tasks/{task_id}",
    response_model=CaseTaskResponse,
    summary="Update a task's status, assignee, or details (Staff only)",
)
def update_case_task(
    case_id: int,
    task_id: int,
    data: CaseTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """Staff updating task progress, completing task, or reassigning."""
    return activity_service.update_task(
        db, case_id=case_id, task_id=task_id, data=data, user=current_user
    )


# ---------------------------------------------------------------------------
# Case Investigations
# ---------------------------------------------------------------------------

@router.get(
    "/{case_id}/investigations",
    response_model=List[CaseInvestigationResponse],
    summary="List investigation logs for a case (Staff only)",
)
def list_case_investigations(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """Staff viewing observations, findings, and evidence references."""
    return activity_service.list_investigations(
        db, case_id=case_id, user=current_user
    )


@router.post(
    "/{case_id}/investigations",
    response_model=CaseInvestigationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an investigation observation, findings, and actions taken (Staff only)",
)
def create_case_investigation(
    case_id: int,
    data: CaseInvestigationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(STAFF_ROLES)),
):
    """Staff logging structured field observations, actions taken, and follow-ups."""
    return activity_service.create_investigation(
        db, case_id=case_id, data=data, user=current_user
    )
