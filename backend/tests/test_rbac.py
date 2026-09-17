import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from app.models.organization import Department
from app.models.user import User, UserRole
from app.schemas.organization import DepartmentCreate
from app.schemas.user import UserCreate
from app.services.organization_service import organization_service
from app.services.user_service import user_service


@pytest.fixture
def test_roles(db_session: Session):
    """Create test users for all 5 system roles."""
    roles_map = {}
    for role in [
        UserRole.REQUESTER,
        UserRole.OPERATOR,
        UserRole.TEAM_LEAD,
        UserRole.MANAGER,
        UserRole.ADMINISTRATOR,
    ]:
        user_in = UserCreate(
            email=f"{role.value}_test@muni.gov",
            password="Password123!",
            full_name=f"{role.value.capitalize()} Test User",
            role=role,
        )
        user = user_service.create_user(db_session, user_in=user_in, forced_role=role)
        token = create_access_token(subject=user.id, role=user.role)
        roles_map[role.value] = {"user": user, "token": token}
    return roles_map


@pytest.fixture
def sample_department(db_session: Session):
    """Create a sample department for testing."""
    return organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(
            name="Roads & Public Works Test",
            code="ROADS_TEST",
            description="Testing department",
        ),
    )


def test_permissions_endpoint_for_all_roles(client: TestClient, test_roles: dict):
    """Verify that /api/v1/auth/permissions returns accurate matrix for every role."""
    for role_name, data in test_roles.items():
        token = data["token"]
        response = client.get(
            "/api/v1/auth/permissions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        perms = response.json()
        assert perms["role"] == role_name

        if role_name == UserRole.REQUESTER.value:
            assert perms["can_create_case"] is True
            assert perms["can_confirm_resolution"] is True
            assert perms["can_view_all_cases"] is False
            assert perms["can_add_internal_notes"] is False
            assert perms["can_manage_users"] is False

        elif role_name == UserRole.OPERATOR.value:
            assert perms["can_view_all_cases"] is True
            assert perms["can_add_internal_notes"] is True
            assert perms["can_submit_resolution"] is True
            assert perms["can_manage_users"] is False

        elif role_name == UserRole.ADMINISTRATOR.value:
            assert perms["can_manage_users"] is True
            assert perms["can_manage_departments"] is True
            assert perms["can_view_all_cases"] is True


def test_admin_list_users_rbac(client: TestClient, test_roles: dict):
    """Verify that only Administrators can list all users."""
    admin_token = test_roles[UserRole.ADMINISTRATOR.value]["token"]
    citizen_token = test_roles[UserRole.REQUESTER.value]["token"]
    operator_token = test_roles[UserRole.OPERATOR.value]["token"]
    manager_token = test_roles[UserRole.MANAGER.value]["token"]

    # Admin gets 200 OK
    res_admin = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert len(res_admin.json()) >= 5

    # Citizen, Operator, Manager get 403 Forbidden
    for token in [citizen_token, operator_token, manager_token]:
        res = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403


def test_admin_create_staff_user(client: TestClient, test_roles: dict):
    """Verify that only Admin can create staff accounts."""
    admin_token = test_roles[UserRole.ADMINISTRATOR.value]["token"]
    citizen_token = test_roles[UserRole.REQUESTER.value]["token"]

    payload = {
        "email": "newoperator@muni.gov",
        "password": "Password123!",
        "full_name": "New Staff Member",
        "role": "operator",
        "department": "ROADS",
    }

    # Citizen gets 403 Forbidden
    res_citizen = client.post(
        "/api/v1/admin/users",
        json=payload,
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert res_citizen.status_code == 403

    # Admin gets 201 Created
    res_admin = client.post(
        "/api/v1/admin/users",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 201
    assert res_admin.json()["role"] == "operator"


def test_admin_update_user_role_and_status(client: TestClient, test_roles: dict):
    """Verify that only Admin can modify user roles and active status."""
    admin_token = test_roles[UserRole.ADMINISTRATOR.value]["token"]
    citizen_user = test_roles[UserRole.REQUESTER.value]["user"]
    citizen_token = test_roles[UserRole.REQUESTER.value]["token"]

    # 1. Citizen cannot change roles (403)
    res_unauth = client.put(
        f"/api/v1/admin/users/{citizen_user.id}/role",
        json={"role": "operator"},
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert res_unauth.status_code == 403

    # 2. Admin can promote Citizen to Operator (200)
    res_auth = client.put(
        f"/api/v1/admin/users/{citizen_user.id}/role",
        json={"role": "operator"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_auth.status_code == 200
    assert res_auth.json()["role"] == "operator"

    # 3. Admin can deactivate account (200)
    res_status = client.put(
        f"/api/v1/admin/users/{citizen_user.id}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_status.status_code == 200
    assert res_status.json()["is_active"] is False


def test_department_and_category_rbac(client: TestClient, test_roles: dict, sample_department: Department):
    """Verify department and category permissions."""
    admin_token = test_roles[UserRole.ADMINISTRATOR.value]["token"]
    operator_token = test_roles[UserRole.OPERATOR.value]["token"]
    citizen_token = test_roles[UserRole.REQUESTER.value]["token"]

    # 1. Listing departments is public/accessible by all
    res_list = client.get("/api/v1/organization/departments")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 2. Creating department is Admin-only
    dept_payload = {
        "name": "Public Health & Sanitation",
        "code": "HEALTH",
        "description": "City health and clinics",
    }
    # Operator fails (403)
    assert client.post(
        "/api/v1/organization/departments",
        json=dept_payload,
        headers={"Authorization": f"Bearer {operator_token}"},
    ).status_code == 403

    # Admin succeeds (201)
    res_dept = client.post(
        "/api/v1/organization/departments",
        json=dept_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_dept.status_code == 201
    assert res_dept.json()["code"] == "HEALTH"

    # 3. Creating Category is Admin-only
    cat_payload = {
        "name": "Pothole Emergency Repair",
        "code": "POTHOLE_EMERGENCY",
        "department_id": sample_department.id,
        "default_priority": "high",
        "sla_hours": 24,
    }
    assert client.post(
        "/api/v1/organization/categories",
        json=cat_payload,
        headers={"Authorization": f"Bearer {citizen_token}"},
    ).status_code == 403

    res_cat = client.post(
        "/api/v1/organization/categories",
        json=cat_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_cat.status_code == 201
    assert res_cat.json()["sla_hours"] == 24


def test_team_creation_rbac(client: TestClient, test_roles: dict, sample_department: Department):
    """Verify TeamLead and Admin can create operational teams."""
    admin_token = test_roles[UserRole.ADMINISTRATOR.value]["token"]
    team_lead_token = test_roles[UserRole.TEAM_LEAD.value]["token"]
    operator_token = test_roles[UserRole.OPERATOR.value]["token"]

    team_payload = {
        "name": "Pothole Patching Alpha Unit",
        "department_id": sample_department.id,
    }

    # Operator fails (403)
    assert client.post(
        "/api/v1/organization/teams",
        json=team_payload,
        headers={"Authorization": f"Bearer {operator_token}"},
    ).status_code == 403

    # Team Lead succeeds (201)
    res_lead = client.post(
        "/api/v1/organization/teams",
        json=team_payload,
        headers={"Authorization": f"Bearer {team_lead_token}"},
    )
    assert res_lead.status_code == 201
    assert res_lead.json()["name"] == "Pothole Patching Alpha Unit"
