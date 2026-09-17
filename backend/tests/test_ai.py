import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.case import Case, CaseStatus, CasePriority, CaseSeverity
from app.models.organization import Department, Category, Team
from app.models.user import UserRole
from app.schemas.organization import DepartmentCreate, CategoryCreate, TeamCreate
from app.schemas.user import UserCreate
from app.services.organization_service import organization_service
from app.services.user_service import user_service


@pytest.fixture
def ai_test_env(db_session: Session):
    """Set up test users, department, and category for AI integration tests."""
    c1 = user_service.create_user(
        db_session,
        user_in=UserCreate(email="citizen_ai@test.com", password="Password123", full_name="Aarav Citizen", ward="Ward 12"),
        forced_role=UserRole.REQUESTER,
    )
    t1 = create_access_token(subject=c1.id, role=c1.role)

    op = user_service.create_user(
        db_session,
        user_in=UserCreate(email="operator_ai@test.com", password="Password123", full_name="Rohan Operator", ward="Ward 12"),
        forced_role=UserRole.OPERATOR,
    )
    top = create_access_token(subject=op.id, role=op.role)

    dept = organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(name="Roads & Highways", code="ROADS_AI", description="Roads dept"),
    )
    cat = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(
            name="Pothole Repair",
            code="POTHOLES",
            department_id=dept.id,
            default_priority="high",
            sla_hours=24,
        ),
    )
    team = organization_service.create_team(
        db_session,
        team_in=TeamCreate(name="Roads Rapid Squad", department_id=dept.id),
    )

    return {
        "citizen": c1,
        "token_citizen": t1,
        "operator": op,
        "token_op": top,
        "department": dept,
        "category": cat,
        "team": team,
    }


def test_ai_triage_and_case_understanding(
    client: TestClient,
    db_session: Session,
    ai_test_env: dict,
):
    """Test AI triage correctly classifies category, priority, and extracts key details."""
    citizen = ai_test_env["citizen"]
    token_op = ai_test_env["token_op"]
    cat = ai_test_env["category"]

    case = Case(
        case_number="MC-2026-AI01",
        title="Deep dangerous pothole near vegetable market",
        description="Huge 2-foot deep pothole causing severe traffic congestion and school bus slowdown.",
        citizen_id=citizen.id,
        ward="Ward 12",
        status=CaseStatus.REPORTED.value,
        priority=CasePriority.MEDIUM.value,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # 1. Trigger AI Analysis
    resp = client.post(
        f"/api/v1/cases/{case.id}/ai-analysis",
        headers={"Authorization": f"Bearer {token_op}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["suggested_category_id"] == cat.id
    assert data["suggested_priority"] in ["high", "critical"]
    assert data["confidence_score"] >= 0.80
    assert "asphalt" in data["recommended_action"].lower() or "road" in data["recommended_action"].lower()
    assert len(data["key_details"]) >= 1


def test_ai_duplicate_detection(
    client: TestClient,
    db_session: Session,
    ai_test_env: dict,
):
    """Test AI similarity matcher flags similar reports in the same ward."""
    citizen = ai_test_env["citizen"]
    token_op = ai_test_env["token_op"]
    cat = ai_test_env["category"]

    # Case 1 (Existing)
    case1 = Case(
        case_number="MC-2026-AI02A",
        title="Road broken with deep pothole near market",
        description="Pothole near vegetable market slowing traffic in Ward 12.",
        citizen_id=citizen.id,
        category_id=cat.id,
        ward="Ward 12",
        status=CaseStatus.REPORTED.value,
        priority=CasePriority.HIGH.value,
    )
    db_session.add(case1)
    db_session.commit()

    # Case 2 (New similar report)
    case2 = Case(
        case_number="MC-2026-AI02B",
        title="Pothole on main market road",
        description="Severe road pothole near vegetable market in Ward 12.",
        citizen_id=citizen.id,
        category_id=cat.id,
        ward="Ward 12",
        status=CaseStatus.REPORTED.value,
        priority=CasePriority.HIGH.value,
    )
    db_session.add(case2)
    db_session.commit()
    db_session.refresh(case2)

    # Run AI Analysis on Case 2
    resp = client.post(
        f"/api/v1/cases/{case2.id}/ai-analysis",
        headers={"Authorization": f"Bearer {token_op}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    # Verify duplicate cases list
    duplicates = data.get("duplicate_cases", [])
    assert len(duplicates) >= 1
    matched_numbers = [d["case_number"] for d in duplicates]
    assert case1.case_number in matched_numbers


def test_ai_communication_drafting(
    client: TestClient,
    db_session: Session,
    ai_test_env: dict,
):
    """Test AI Communication Copilot draft generation."""
    citizen = ai_test_env["citizen"]
    token_op = ai_test_env["token_op"]

    case = Case(
        case_number="MC-2026-AI03",
        title="Dark street corner",
        description="Streetlight fixture not turning on at night.",
        citizen_id=citizen.id,
        ward="Ward 12",
        status=CaseStatus.ASSIGNED.value,
        priority=CasePriority.MEDIUM.value,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # 1. Draft Information Request
    resp = client.post(
        f"/api/v1/cases/{case.id}/ai/draft-communication",
        headers={"Authorization": f"Bearer {token_op}"},
        json={
            "draft_type": "information_request",
            "context_notes": "Please specify pole number written on yellow stencil.",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "pole number" in data["body_text"].lower()
    assert "Clarification" in data["subject"]

    # 2. Draft Resolution Message
    resp_res = client.post(
        f"/api/v1/cases/{case.id}/ai/draft-communication",
        headers={"Authorization": f"Bearer {token_op}"},
        json={
            "draft_type": "resolution_message",
            "context_notes": "Replaced faulty photocell sensor and LED driver.",
        },
    )
    assert resp_res.status_code == status.HTTP_200_OK
    assert "photocell sensor" in resp_res.json()["body_text"].lower()


def test_apply_ai_suggestions(
    client: TestClient,
    db_session: Session,
    ai_test_env: dict,
):
    """Test staff accepting AI recommendations and updating the live case."""
    citizen = ai_test_env["citizen"]
    token_op = ai_test_env["token_op"]
    token_citizen = ai_test_env["token_citizen"]
    cat = ai_test_env["category"]

    case = Case(
        case_number="MC-2026-AI04",
        title="Road surface crater near bus stand",
        description="Hazardous crater in asphalt road.",
        citizen_id=citizen.id,
        ward="Ward 12",
        status=CaseStatus.REPORTED.value,
        priority=CasePriority.LOW.value,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # 1. Run AI analysis first
    client.post(
        f"/api/v1/cases/{case.id}/ai-analysis",
        headers={"Authorization": f"Bearer {token_op}"},
    )

    # 2. Citizen tries to apply suggestions -> 403 Forbidden
    resp_unauth = client.post(
        f"/api/v1/cases/{case.id}/ai/apply-suggestions",
        headers={"Authorization": f"Bearer {token_citizen}"},
        json={"apply_category": True, "apply_priority": True, "apply_team": True},
    )
    assert resp_unauth.status_code == status.HTTP_403_FORBIDDEN

    # 3. Operator applies suggestions -> 200 OK
    resp_staff = client.post(
        f"/api/v1/cases/{case.id}/ai/apply-suggestions",
        headers={"Authorization": f"Bearer {token_op}"},
        json={"apply_category": True, "apply_priority": True, "apply_team": True},
    )
    assert resp_staff.status_code == status.HTTP_200_OK
    updated_case = resp_staff.json()

    assert updated_case["category_id"] == cat.id
    assert updated_case["priority"] in ["high", "critical"]


def test_ai_case_summary(
    client: TestClient,
    db_session: Session,
    ai_test_env: dict,
):
    """Test AI case journey summary retrieval."""
    citizen = ai_test_env["citizen"]
    token_op = ai_test_env["token_op"]

    case = Case(
        case_number="MC-2026-AI05",
        title="Garbage bin overflowing",
        description="Waste overflowing for 3 days.",
        citizen_id=citizen.id,
        ward="Ward 12",
        status=CaseStatus.REPORTED.value,
        priority=CasePriority.MEDIUM.value,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    resp = client.get(
        f"/api/v1/cases/{case.id}/summary",
        headers={"Authorization": f"Bearer {token_op}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["case_number"] == case.case_number
    assert "reported" in data["summary"].lower()
