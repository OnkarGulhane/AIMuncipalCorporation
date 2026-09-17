from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.user_service import user_service

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Citizen Registration")
def register_citizen(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Public self-registration for Citizens / Requesters.
    Role is strictly defaulted to 'requester' for security.
    """
    existing_user = user_service.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Force role to requester on public registration
    created_user = user_service.create_user(
        db,
        user_in=user_in,
        forced_role=UserRole.REQUESTER,
    )

    access_token = create_access_token(
        subject=created_user.id,
        role=created_user.role,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(created_user),
    )


@router.post("/login", response_model=TokenResponse, summary="User Authentication & Token Issuance")
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email and password to receive a signed JWT access token.
    """
    user = user_service.authenticate(
        db,
        email=login_data.email,
        password=login_data.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user account has been deactivated.",
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse, summary="Current User Profile")
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    Retrieve authenticated user profile.
    """
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh Access Token")
def refresh_token(
    current_user: User = Depends(get_current_active_user),
) -> TokenResponse:
    """
    Issue a renewed JWT access token for the authenticated user.
    """
    new_token = create_access_token(
        subject=current_user.id,
        role=current_user.role,
    )
    return TokenResponse(
        access_token=new_token,
        token_type="bearer",
        user=UserResponse.model_validate(current_user),
    )
