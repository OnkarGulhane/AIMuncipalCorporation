from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import user_service

router = APIRouter()

# Enforce Administrator-only access for all routes in this router
AdminRequired = Depends(require_roles([UserRole.ADMINISTRATOR]))


class RoleUpdateRequest(BaseModel):
    role: UserRole


class StatusUpdateRequest(BaseModel):
    is_active: bool


@router.get("/users", response_model=List[UserResponse], summary="List All Users (Admin Only)")
def list_users(
    role: Optional[str] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin: User = AdminRequired,
) -> List[UserResponse]:
    """List system users with optional role filtering."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if department_id is not None:
        query = query.filter(User.department_id == department_id)

    users = query.order_by(User.id.asc()).all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create Staff User (Admin Only)")
def create_staff_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    admin: User = AdminRequired,
) -> UserResponse:
    """Create a staff user account with specific role assignment."""
    existing = user_service.get_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    new_user = user_service.create_user(db, user_in=user_in, forced_role=user_in.role)
    return UserResponse.model_validate(new_user)


@router.put("/users/{user_id}/role", response_model=UserResponse, summary="Change User Role (Admin Only)")
def update_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = AdminRequired,
) -> UserResponse:
    """Modify a user's role."""
    target_user = user_service.get_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    old_role = target_user.role
    target_user.role = payload.role.value
    db.add(target_user)
    db.commit()
    db.refresh(target_user)

    from app.services.audit_service import audit_service
    audit_service.log_event(
        db=db,
        action="USER_ROLE_CHANGED",
        resource_type="user",
        resource_id=str(target_user.id),
        actor_id=admin.id,
        details=f"Admin {admin.full_name} changed role of user {target_user.email} from {old_role} to {target_user.role}",
        old_values={"role": old_role},
        new_values={"role": target_user.role},
        is_ai_action=False,
    )

    return UserResponse.model_validate(target_user)


@router.put("/users/{user_id}/status", response_model=UserResponse, summary="Change User Active Status (Admin Only)")
def update_user_status(
    user_id: int,
    payload: StatusUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = AdminRequired,
):
    """Activate or deactivate a user account."""
    target_user = user_service.get_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    old_status = target_user.is_active
    target_user.is_active = payload.is_active
    db.add(target_user)
    db.commit()
    db.refresh(target_user)

    from app.services.audit_service import audit_service
    audit_service.log_event(
        db=db,
        action="USER_STATUS_CHANGED",
        resource_type="user",
        resource_id=str(target_user.id),
        actor_id=admin.id,
        details=f"Admin {admin.full_name} updated active status of user {target_user.email} from {old_status} to {target_user.is_active}",
        old_values={"is_active": old_status},
        new_values={"is_active": target_user.is_active},
        is_ai_action=False,
    )

    return UserResponse.model_validate(target_user)



@router.get("/system-stats", summary="Get System-Wide Statistics (Admin Only)")
def get_system_stats(
    db: Session = Depends(get_db),
    admin: User = AdminRequired,
):
    """Aggregates high-level system metrics and entity counts."""
    from app.models.case import Case
    from app.models.organization import Department, Team, Category
    from app.models.escalation import CaseEscalation
    from app.models.notification import Notification

    total_users = db.query(User).count()
    users_by_role = {}
    for r, count in db.query(User.role, func.count(User.id)).group_by(User.role).all():
        users_by_role[r] = count

    return {
        "total_users": total_users,
        "users_by_role": users_by_role,
        "total_departments": db.query(Department).count(),
        "total_teams": db.query(Team).count(),
        "total_categories": db.query(Category).count(),
        "total_cases": db.query(Case).count(),
        "total_escalations": db.query(CaseEscalation).count(),
        "total_notifications_sent": db.query(Notification).count(),
        "database_status": "healthy",
    }


@router.get("/audit-logs", summary="Explore System Audit Trail (Admin & Manager)")
def get_audit_logs(
    case_id: Optional[int] = None,
    action: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = AdminRequired,
):
    """Query comprehensive timeline history across all municipal cases."""
    from app.models.case import CaseTimeline, Case

    query = db.query(CaseTimeline)
    if case_id is not None:
        query = query.filter(CaseTimeline.case_id == case_id)
    if action is not None:
        query = query.filter(CaseTimeline.action == action)

    logs = query.order_by(CaseTimeline.created_at.desc()).offset(offset).limit(limit).all()

    results = []
    for l in logs:
        results.append({
            "id": l.id,
            "case_id": l.case_id,
            "case_number": l.case_rel.case_number if l.case_rel else None,
            "actor_id": l.actor_id,
            "actor_name": l.actor.full_name if l.actor else "System",
            "actor_role": l.actor.role if l.actor else "system",
            "action": l.action,
            "old_value": l.old_value,
            "new_value": l.new_value,
            "notes": l.notes,
            "created_at": l.created_at,
        })
    return results

