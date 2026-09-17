import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.case import Case, CaseStatus, CasePriority, CaseSeverity
from app.models.organization import Department, Category, Team
from app.schemas.user import UserCreate
from app.schemas.organization import DepartmentCreate, CategoryCreate
from app.schemas.ai import AIApplySuggestionsRequest
from app.services.user_service import user_service
from app.services.organization_service import organization_service
from app.services.ai_service import ai_service


@pytest.fixture
def ai_edge_env(db_session: Session):
    dept = organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(name="General Sanitation", code="SANITATION_AI", description="Waste management"),
    )
    cat_garbage = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(name="Garbage Overflow", code="GARBAGE_OVERFLOW", department_id=dept.id, default_sla_hours=12),
    )
    cat_road = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(name="Pothole Repair", code="POTHOLES", department_id=dept.id, default_sla_hours=48),
    )

    citizen = user_service.create_user(
        db_session,
        user_in=UserCreate(email="citizen_ai_edge@test.com", password="Password123", full_name="Tanvi Rao", ward="Ward 05"),
        forced_role=UserRole.REQUESTER,
    )
    operator = user_service.create_user(
        db_session,
        user_in=UserCreate(email="operator_ai_edge@test.com", password="Password123", full_name="Manish Operator", ward="Ward 05"),
        forced_role=UserRole.OPERATOR,
    )

    db_session.commit()

    return {
        "dept": dept,
        "cat_garbage": cat_garbage,
        "cat_road": cat_road,
        "citizen": citizen,
        "operator": operator,
        "token_citizen": create_access_token(subject=citizen.id, role=citizen.role),
        "token_operator": create_access_token(subject=operator.id, role=operator.role),
    }


def test_ai_triage_minimal_and_ambiguous_text(client: TestClient, db_session: Session, ai_edge_env: dict):
    citizen = ai_edge_env["citizen"]
    t_op = ai_edge_env["token_operator"]

    # Case with minimal text
    case = Case(
        case_number="MC-2026-8801",
        title="Fix this",
        description="Problem here please fix soon.",
        citizen_id=citizen.id,
        ward="Ward 05",
    )
    db_session.add(case)
    db_session.commit()

    res = client.post(
        f"/api/v1/cases/{case.id}/ai-analysis",
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["confidence_score"] > 0
    # Must flag missing information due to short length
    assert len(data["missing_information"]) >= 1
    assert any("short" in m.lower() or "landmark" in m.lower() for m in data["missing_information"])


def test_ai_triage_unrecognized_civic_category(client: TestClient, db_session: Session, ai_edge_env: dict):
    citizen = ai_edge_env["citizen"]
    t_op = ai_edge_env["token_operator"]

    # Case with completely unusual or vague description
    case = Case(
        case_number="MC-2026-8802",
        title="Unusual sound from park",
        description="Heard high frequency whistling noise from park trees at 2 AM.",
        citizen_id=citizen.id,
        ward="Ward 05",
    )
    db_session.add(case)
    db_session.commit()

    res = client.post(
        f"/api/v1/cases/{case.id}/ai-analysis",
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert res.status_code == 200
    data = res.json()
    # Falls back gracefully without 500 error
    assert data["suggested_priority"] in ["low", "medium", "high", "critical"]
    assert data["recommended_action"] is not None


def test_duplicate_detection_disjoint_and_matching(client: TestClient, db_session: Session, ai_edge_env: dict):
    citizen = ai_edge_env["citizen"]
    t_op = ai_edge_env["token_operator"]

    # Existing case
    c1 = Case(
        case_number="MC-2026-8803",
        title="Overflowing trash bin near market",
        description="Foul smell and uncollected rotting garbage bags near market gate.",
        citizen_id=citizen.id,
        ward="Ward 05",
    )
    # Disjoint case
    c2 = Case(
        case_number="MC-2026-8804",
        title="Broken playground swing",
        description="Children swing chain snapped in public garden.",
        citizen_id=citizen.id,
        ward="Ward 12",
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    # Target case matching c1
    c3 = Case(
        case_number="MC-2026-8805",
        title="Severe garbage dump spill",
        description="Uncollected garbage and stinking trash bags near market gate.",
        citizen_id=citizen.id,
        ward="Ward 05",
    )
    db_session.add(c3)
    db_session.commit()

    res = client.post(
        f"/api/v1/cases/{c3.id}/ai-analysis",
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert res.status_code == 200
    data = res.json()
    duplicate_ids = [d["case_id"] for d in data["duplicate_cases"]]
    assert c1.id in duplicate_ids
    assert c2.id not in duplicate_ids


def test_human_override_of_ai_recommendations(client: TestClient, db_session: Session, ai_edge_env: dict):
    citizen = ai_edge_env["citizen"]
    t_op = ai_edge_env["token_operator"]

    case = Case(
        case_number="MC-2026-8806",
        title="Trash piled up near hospital",
        description="Garbage dump overflowing outside emergency ward.",
        citizen_id=citizen.id,
        ward="Ward 05",
    )
    db_session.add(case)
    db_session.commit()

    # Run AI analysis (AI suggests GARBAGE)
    client.post(
        f"/api/v1/cases/{case.id}/ai-analysis",
        headers={"Authorization": f"Bearer {t_op}"},
    )

    # Human operator deliberately chooses NOT to apply AI category, but sets Road Repair manually
    override_res = client.put(
        f"/api/v1/cases/{case.id}/assignment",
        json={"assigned_to_id": ai_edge_env["operator"].id, "reason": "Manually assigned to road squad instead"},
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert override_res.status_code == 200

    # Verify case was not overwritten by AI silently
    get_case_res = client.get(
        f"/api/v1/cases/{case.id}",
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert get_case_res.status_code == 200
    assert get_case_res.json()["assigned_to_id"] == ai_edge_env["operator"].id
