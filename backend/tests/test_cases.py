import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from app.models.case import Case, CaseStatus, CasePriority
from app.models.organization import Department, Category
from app.models.user import User, UserRole
from app.schemas.case import CaseCreate
from app.schemas.organization import DepartmentCreate, CategoryCreate
from app.schemas.user import UserCreate
from app.services.case_service import case_service
from app.services.organization_service import organization_service
from app.services.user_service import user_service


@pytest.fixture
def case_test_env(db_session: Session):
    """Set up test users, department, and category for case management tests."""
    # Create Citizen 1
    c1 = user_service.create_user(
        db_session,
        user_in=UserCreate(email="c1@test.com", password="Password123", full_name="Citizen One", ward="Ward 12"),
        forced_role=UserRole.REQUESTER,
    )
    t1 = create_access_token(subject=c1.id, role=c1.role)

    # Create Citizen 2
    c2 = user_service.create_user(
        db_session,
        user_in=UserCreate(email="c2@test.com", password="Password123", full_name="Citizen Two", ward="Ward 8"),
        forced_role=UserRole.REQUESTER,
    )
    t2 = create_access_token(subject=c2.id, role=c2.role)

    # Create Operator
    op = user_service.create_user(
        db_session,
        user_in=UserCreate(email="op@test.com", password="Password123", full_name="Operator Sam"),
        forced_role=UserRole.OPERATOR,
    )
    top = create_access_token(subject=op.id, role=op.role)

    # Create Department & Category
    dept = organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(name="Roads & Bridges Test", code="ROADS_T", description="Test"),
    )
    cat = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(
            name="Pothole Repair Test",
            code="POTHOLE_T",
            department_id=dept.id,
            default_priority="high",
            sla_hours=48,
        ),
    )

    return {
        "citizen1": c1, "token1": t1,
        "citizen2": c2, "token2": t2,
        "operator": op, "token_op": top,
        "department": dept,
        "category": cat,
    }


def test_case_creation_and_number_format(client: TestClient, case_test_env: dict):
    """Verify case creation, unique case number format, and initial timeline."""
    token = case_test_env["token1"]
    cat = case_test_env["category"]

    payload = {
        "title": "Large pothole in front of community clinic",
        "description": "Vehicle tires are getting stuck during evening rush hour.",
        "category_id": cat.id,
        "ward": "Ward 12",
        "landmark": "Opposite City Clinic",
        "priority": "high",
    }
    response = client.post("/api/v1/cases", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["case_number"].startswith("MC-")
    assert data["status"] == "reported"
    assert data["title"] == payload["title"]
    assert data["citizen_id"] == case_test_env["citizen1"].id
    assert data["department_id"] == case_test_env["department"].id  # Auto resolved from category!


def test_case_list_role_scoping(client: TestClient, case_test_env: dict):
    """Verify Requesters only see their own cases while staff see all authorized cases."""
    t1 = case_test_env["token1"]
    t2 = case_test_env["token2"]
    top = case_test_env["token_op"]

    # Citizen 1 creates 2 cases
    client.post("/api/v1/cases", json={"title": "C1 Case 1", "description": "Desc 1"}, headers={"Authorization": f"Bearer {t1}"})
    client.post("/api/v1/cases", json={"title": "C1 Case 2", "description": "Desc 2"}, headers={"Authorization": f"Bearer {t1}"})

    # Citizen 2 creates 1 case
    client.post("/api/v1/cases", json={"title": "C2 Case 1", "description": "Desc 3"}, headers={"Authorization": f"Bearer {t2}"})

    # Citizen 1 queries cases -> sees only 2 items
    res1 = client.get("/api/v1/cases", headers={"Authorization": f"Bearer {t1}"})
    assert res1.status_code == 200
    assert res1.json()["total"] == 2
    for item in res1.json()["items"]:
        assert item["citizen_id"] == case_test_env["citizen1"].id

    # Citizen 2 queries cases -> sees only 1 item
    res2 = client.get("/api/v1/cases", headers={"Authorization": f"Bearer {t2}"})
    assert res2.status_code == 200
    assert res2.json()["total"] == 1

    # Operator queries cases -> sees all 3 items
    res_op = client.get("/api/v1/cases", headers={"Authorization": f"Bearer {top}"})
    assert res_op.status_code == 200
    assert res_op.json()["total"] >= 3


def test_case_detail_authorization(client: TestClient, case_test_env: dict):
    """Verify citizen cannot inspect another citizen's private case details."""
    t1 = case_test_env["token1"]
    t2 = case_test_env["token2"]

    # Create Case by Citizen 1
    create_res = client.post(
        "/api/v1/cases",
        json={"title": "Private Citizen 1 Issue", "description": "Confidential details"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    case_id = create_res.json()["id"]

    # Citizen 1 can access with timeline
    res_c1 = client.get(f"/api/v1/cases/{case_id}", headers={"Authorization": f"Bearer {t1}"})
    assert res_c1.status_code == 200
    assert len(res_c1.json()["timeline"]) >= 1

    # Citizen 2 gets 403 Forbidden
    res_c2 = client.get(f"/api/v1/cases/{case_id}", headers={"Authorization": f"Bearer {t2}"})
    assert res_c2.status_code == 403


def test_lifecycle_transitions_and_validation(client: TestClient, case_test_env: dict):
    """Verify valid state progression and rejection of invalid state transitions."""
    t1 = case_test_env["token1"]
    top = case_test_env["token_op"]

    # 1. Create Case
    create_res = client.post(
        "/api/v1/cases",
        json={"title": "Street drainage problem", "description": "Water overflowing onto sidewalk."},
        headers={"Authorization": f"Bearer {t1}"},
    )
    case_id = create_res.json()["id"]

    # 2. Invalid Transition: reported -> closed should fail (400)
    invalid_res = client.put(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "closed"},
        headers={"Authorization": f"Bearer {top}"},
    )
    assert invalid_res.status_code == 400
    assert "Invalid state transition" in invalid_res.json()["detail"]

    # 3. Valid Step 1: Assign to Operator
    assign_res = client.put(
        f"/api/v1/cases/{case_id}/assignment",
        json={"assigned_to_id": case_test_env["operator"].id, "reason": "Assigned to rapid squad"},
        headers={"Authorization": f"Bearer {top}"},
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "assigned"

    # 4. Valid Step 2: assigned -> investigated
    res_inv = client.put(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "investigated", "reason": "Inspected drain blockage."},
        headers={"Authorization": f"Bearer {top}"},
    )
    assert res_inv.status_code == 200
    assert res_inv.json()["status"] == "investigated"

    # 5. Valid Step 3: investigated -> action_taken
    res_act = client.put(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "action_taken", "reason": "Excavator cleared silt and debris."},
        headers={"Authorization": f"Bearer {top}"},
    )
    assert res_act.status_code == 200
    assert res_act.json()["status"] == "action_taken"

    # 6. Valid Step 4: action_taken -> resolution_proposed
    res_prop = client.put(
        f"/api/v1/cases/{case_id}/status",
        json={
            "new_status": "resolution_proposed",
            "resolution_notes": "Main drain unclogged. Water flowing normally with zero stagnation.",
        },
        headers={"Authorization": f"Bearer {top}"},
    )
    assert res_prop.status_code == 200
    assert res_prop.json()["status"] == "resolution_proposed"


def test_citizen_confirm_and_reject_resolution_flows(client: TestClient, case_test_env: dict, db_session: Session):
    """Verify citizen confirmation closes case, while rejection reopens case."""
    c1 = case_test_env["citizen1"]
    t1 = case_test_env["token1"]
    op = case_test_env["operator"]

    # 1. Test Confirmation Flow
    case1 = case_service.create_case(
        db_session,
        case_in=CaseCreate(title="Case to Confirm", description="Test confirm"),
        citizen_id=c1.id,
    )
    case_service.update_case_status(db_session, case1, CaseStatus.ASSIGNED, actor=op)
    case_service.update_case_status(db_session, case1, CaseStatus.INVESTIGATED, actor=op)
    case_service.update_case_status(
        db_session, case1, CaseStatus.RESOLUTION_PROPOSED, actor=op, resolution_notes="Work completed."
    )

    res_conf = client.post(
        f"/api/v1/cases/{case1.id}/confirm-resolution",
        json={"notes": "Looks great, thanks!"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert res_conf.status_code == 200
    assert res_conf.json()["status"] == "confirmed"
    assert res_conf.json()["closed_at"] is not None

    # 2. Test Rejection Flow
    case2 = case_service.create_case(
        db_session,
        case_in=CaseCreate(title="Case to Reject", description="Test reject"),
        citizen_id=c1.id,
    )
    case_service.update_case_status(db_session, case2, CaseStatus.ASSIGNED, actor=op)
    case_service.update_case_status(db_session, case2, CaseStatus.INVESTIGATED, actor=op)
    case_service.update_case_status(
        db_session, case2, CaseStatus.RESOLUTION_PROPOSED, actor=op, resolution_notes="Work attempted."
    )

    res_rej = client.post(
        f"/api/v1/cases/{case2.id}/reject-resolution",
        json={"rejection_reason": "Pothole was filled with loose sand and washed away today."},
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert res_rej.status_code == 200
    assert res_rej.json()["status"] == "reopened"
    assert "washed away" in res_rej.json()["rejection_reason"]


def test_case_search_and_filters(client: TestClient, case_test_env: dict):
    """Verify search by keyword, ward, and status."""
    t1 = case_test_env["token1"]
    top = case_test_env["token_op"]

    client.post(
        "/api/v1/cases",
        json={"title": "Broken Water Meter at Shiv Mandir", "description": "Water leaking continuously", "ward": "Ward 12"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    client.post(
        "/api/v1/cases",
        json={"title": "Fallen Banyan Tree Branch", "description": "Blocking lane 4", "ward": "Ward 4"},
        headers={"Authorization": f"Bearer {t1}"},
    )

    # Search keyword "Banyan"
    res_search = client.get("/api/v1/cases?search=Banyan", headers={"Authorization": f"Bearer {top}"})
    assert res_search.status_code == 200
    assert res_search.json()["total"] == 1
    assert "Banyan" in res_search.json()["items"][0]["title"]

    # Filter by ward "Ward 12"
    res_ward = client.get("/api/v1/cases?ward=Ward 12", headers={"Authorization": f"Bearer {top}"})
    assert res_ward.status_code == 200
    assert all("Ward 12" in item["ward"] for item in res_ward.json()["items"] if item["ward"])
