from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_active_user, require_roles
from app.core.security import get_password_hash, verify_password, create_access_token
from app.main import app
from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.services.user_service import user_service

# Create dummy protected test routes to verify RBAC dependencies
rbac_test_router = APIRouter(prefix="/test-rbac", tags=["Test RBAC"])


@rbac_test_router.get("/operator-only")
def operator_only_endpoint(
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.TEAM_LEAD])),
):
    return {"message": f"Welcome operator {current_user.full_name}"}


@rbac_test_router.get("/admin-only")
def admin_only_endpoint(
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR])),
):
    return {"message": f"Welcome admin {current_user.full_name}"}


app.include_router(rbac_test_router)


def test_password_hashing():
    """Verify password hashing and verification logic."""
    raw = "SecureP@ss123"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_register_citizen_success(client: TestClient):
    """Verify citizen registration endpoint."""
    payload = {
        "email": "newcitizen@test.com",
        "password": "Password123",
        "full_name": "Test Citizen",
        "phone_number": "+91 9123456780",
        "ward": "Ward 5",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newcitizen@test.com"
    assert data["user"]["full_name"] == "Test Citizen"
    assert data["user"]["role"] == "requester"  # Must default to requester


def test_register_duplicate_email(client: TestClient, db_session: Session):
    """Verify duplicate email registration is rejected."""
    # Pre-create a user
    user_in = UserCreate(
        email="existing@test.com",
        password="Password123",
        full_name="Existing User",
    )
    user_service.create_user(db_session, user_in=user_in)

    payload = {
        "email": "existing@test.com",
        "password": "Password123",
        "full_name": "Another User",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client: TestClient, db_session: Session):
    """Verify login with valid credentials returns JWT token."""
    user_in = UserCreate(
        email="loginuser@test.com",
        password="MySecretPassword123",
        full_name="Login User",
    )
    user_service.create_user(db_session, user_in=user_in)

    login_payload = {
        "email": "loginuser@test.com",
        "password": "MySecretPassword123",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "loginuser@test.com"


def test_login_wrong_password(client: TestClient, db_session: Session):
    """Verify login with invalid password returns 401."""
    user_in = UserCreate(
        email="wrongpass@test.com",
        password="CorrectPassword123",
        full_name="Test User",
    )
    user_service.create_user(db_session, user_in=user_in)

    login_payload = {
        "email": "wrongpass@test.com",
        "password": "IncorrectPassword",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    """Verify login with non-existent user returns 401."""
    login_payload = {
        "email": "nobody@test.com",
        "password": "AnyPassword",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401


def test_get_current_user_profile(client: TestClient, db_session: Session):
    """Verify /api/v1/auth/me returns current user profile."""
    user_in = UserCreate(
        email="profile@test.com",
        password="Password123",
        full_name="Profile User",
        phone_number="+91 9999999999",
        ward="Ward 1",
    )
    user = user_service.create_user(db_session, user_in=user_in)
    token = create_access_token(subject=user.id, role=user.role)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile@test.com"
    assert data["full_name"] == "Profile User"
    assert data["phone_number"] == "+91 9999999999"


def test_get_me_unauthorized(client: TestClient):
    """Verify /api/v1/auth/me without token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_token_refresh(client: TestClient, db_session: Session):
    """Verify /api/v1/auth/refresh returns a fresh valid token."""
    user_in = UserCreate(
        email="refresh@test.com",
        password="Password123",
        full_name="Refresh User",
    )
    user = user_service.create_user(db_session, user_in=user_in)
    token = create_access_token(subject=user.id, role=user.role)

    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "refresh@test.com"


def test_rbac_authorization_success_and_forbidden(client: TestClient, db_session: Session):
    """Verify server-side RBAC dependencies allow permitted roles and reject forbidden roles."""
    # Create requester
    req_in = UserCreate(
        email="citizen_rbac@test.com",
        password="Password123",
        full_name="Citizen RBAC",
    )
    requester = user_service.create_user(db_session, user_in=req_in, forced_role=UserRole.REQUESTER)
    req_token = create_access_token(subject=requester.id, role=requester.role)

    # Create operator
    op_in = UserCreate(
        email="operator_rbac@test.com",
        password="Password123",
        full_name="Operator RBAC",
    )
    operator = user_service.create_user(db_session, user_in=op_in, forced_role=UserRole.OPERATOR)
    op_token = create_access_token(subject=operator.id, role=operator.role)

    # 1. Requester attempting to access operator route should be 403 Forbidden
    res1 = client.get(
        "/test-rbac/operator-only",
        headers={"Authorization": f"Bearer {req_token}"},
    )
    assert res1.status_code == 403
    assert "Insufficient permissions" in res1.json()["detail"]

    # 2. Operator accessing operator route should be 200 OK
    res2 = client.get(
        "/test-rbac/operator-only",
        headers={"Authorization": f"Bearer {op_token}"},
    )
    assert res2.status_code == 200
    assert "Welcome operator" in res2.json()["message"]

    # 3. Operator attempting to access admin-only route should be 403 Forbidden
    res3 = client.get(
        "/test-rbac/admin-only",
        headers={"Authorization": f"Bearer {op_token}"},
    )
    assert res3.status_code == 403
