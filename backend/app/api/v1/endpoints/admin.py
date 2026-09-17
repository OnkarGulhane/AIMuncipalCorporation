from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
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

    target_user.role = payload.role.value
    db.add(target_user)
    db.commit()
    db.refresh(target_user)
    return UserResponse.model_validate(target_user)


@router.put("/users/{user_id}/status", response_model=UserResponse, summary="Change User Active Status (Admin Only)")
def update_user_status(
    user_id: int,
    payload: StatusUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = AdminRequired,
) -> UserResponse:
    """Activate or deactivate a user account."""
    target_user = user_service.get_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    target_user.is_active = payload.is_active
    db.add(target_user)
    db.commit()
    db.refresh(target_user)
    return UserResponse.model_validate(target_user)
