import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.case import Case, CasePriority, CaseStatus, CaseSeverity, CaseTimeline
from app.models.organization import Department, Category, Team
from app.models.user import UserRole
from app.models.sla import CaseSLA, SLAStatus
from app.models.escalation import CaseEscalation, EscalationStatus, EscalationTrigger
from app.schemas.organization import DepartmentCreate, CategoryCreate, TeamCreate
from app.schemas.user import UserCreate
from app.schemas.case import CaseCreate
from app.services.organization_service import organization_service
from app.services.user_service import user_service
from app.services.case_service import case_service
from app.services.sla_service import (
    calculate_sla_targets,
    format_time_remaining,
    initialize_or_update_case_sla,
    evaluate_single_case_sla,
)
from app.services.risk_service import evaluate_case_risk
from app.services.escalation_service import create_case_escalation, update_case_escalation


@pytest.fixture
def sla_test_env(db_session: Session):
    """Set up test users, department, category, and case for SLA/Escalation tests."""
    citizen = user_service.create_user(
        db_session,
        user_in=UserCreate(email="citizen_sla@test.com", password="Password123", full_name="Aarav Citizen", ward="Ward 12"),
        forced_role=UserRole.REQUESTER,
    )
    token_citizen = create_access_token(subject=citizen.id, role=citizen.role)

    operator = user_service.create_user(
        db_session,
        user_in=UserCreate(email="operator_sla@test.com", password="Password123", full_name="Rohan Operator", ward="Ward 12"),
        forced_role=UserRole.OPERATOR,
    )
    token_op = create_access_token(subject=operator.id, role=operator.role)

    teamlead = user_service.create_user(
        db_session,
        user_in=UserCreate(email="teamlead_sla@test.com", password="Password123", full_name="Priya Lead", ward="Ward 12"),
        forced_role=UserRole.TEAM_LEAD,
    )
    token_lead = create_access_token(subject=teamlead.id, role=teamlead.role)

    dept = organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(name="Roads & Highways", code="ROADS_SLA", description="Roads dept"),
    )
    cat = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(
            name="Pothole Repair",
            code="POTHOLES_SLA",
            department_id=dept.id,
            default_priority="high",
            sla_hours=48,
        ),
    )
    team = organization_service.create_team(
        db_session,
        team_in=TeamCreate(name="Roads Rapid Squad", department_id=dept.id, leader_id=teamlead.id),
    )

    case = case_service.create_case(
        db_session,
        case_in=CaseCreate(
            title="Dangerous Pothole near Bus Stop",
            description="Large pothole in road causing traffic hazards.",
            category_id=cat.id,
            department_id=dept.id,
            ward="Ward 12",
            priority=CasePriority.HIGH,
        ),
        citizen_id=citizen.id,
    )

    return {
        "citizen": citizen,
        "token_citizen": token_citizen,
        "operator": operator,
        "token_op": token_op,
        "teamlead": teamlead,
        "token_lead": token_lead,
        "department": dept,
        "category": cat,
        "team": team,
        "case": case,
    }


def test_calculate_sla_targets_scaling():
    # Category with 48h baseline SLA
    resp_crit, res_crit = calculate_sla_targets(48, "critical")
    assert resp_crit == 4
    assert res_crit == 12

    resp_high, res_high = calculate_sla_targets(48, "high")
    assert resp_high == 8
    assert res_high == 24

    resp_med, res_med = calculate_sla_targets(48, "medium")
    assert resp_med == 12
    assert res_med == 48

    resp_low, res_low = calculate_sla_targets(48, "low")
    assert resp_low == 24
    assert res_low == 72


def test_format_time_remaining_plain_text():
    now = datetime.now(timezone.utc)
    created = now - timedelta(hours=2)

    # Future deadline
    due_future = now + timedelta(days=1, hours=2)
    text, prog = format_time_remaining(created, due_future)
    assert "remaining" in text
    assert prog > 0

    # Past deadline (Breached)
    due_past = now - timedelta(hours=3, minutes=10)
    text_breached, prog_breached = format_time_remaining(created, due_past)
    assert "Breached" in text_breached
    assert prog_breached == 100.0

    # Completed on time
    text_met, _ = format_time_remaining(created, due_future, completed_at=now)
    assert text_met == "Met on time"


def test_get_case_sla_endpoint(client: TestClient, sla_test_env: dict):
    env = sla_test_env
    case_id = env["case"].id
    headers = {"Authorization": f"Bearer {env['token_op']}"}

    resp = client.get(f"/api/v1/cases/{case_id}/sla", headers=headers)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    data = resp.json()

    assert data["case_id"] == case_id
    assert "response_remaining_text" in data
    assert "resolution_remaining_text" in data
    assert data["response_target_hours"] == 8  # High priority on 48h category
    assert data["resolution_target_hours"] == 24
    assert data["response_progress_percentage"] >= 0.0


def test_recalculate_sla_endpoint(client: TestClient, sla_test_env: dict):
    env = sla_test_env
    case = env["case"]
    headers = {"Authorization": f"Bearer {env['token_op']}"}

    # Change case priority to CRITICAL
    case.priority = CasePriority.CRITICAL.value

    resp = client.post(f"/api/v1/cases/{case.id}/sla/recalculate", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["case_id"] == case.id
    assert data["response_target_hours"] == 4
    assert data["resolution_target_hours"] == 12


def test_get_case_risk_endpoint(client: TestClient, sla_test_env: dict):
    env = sla_test_env
    case_id = env["case"].id
    headers = {"Authorization": f"Bearer {env['token_op']}"}

    resp = client.get(f"/api/v1/cases/{case_id}/risk", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert "risk_score" in data
    assert "risk_tier" in data
    assert isinstance(data["risk_factors"], list)
    assert isinstance(data["signals"], list)
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_tier"] in ["low", "medium", "high", "critical"]


def test_citizen_sla_authorization(client: TestClient, sla_test_env: dict, db_session: Session):
    env = sla_test_env
    case = env["case"]

    # Citizen accessing their own case
    citizen_headers = {"Authorization": f"Bearer {env['token_citizen']}"}
    resp = client.get(f"/api/v1/cases/{case.id}/sla", headers=citizen_headers)
    assert resp.status_code == status.HTTP_200_OK

    # Another citizen accessing this case
    other_citizen = user_service.create_user(
        db_session,
        user_in=UserCreate(email="other_cit@test.com", password="Password123", full_name="Other Cit"),
        forced_role=UserRole.REQUESTER,
    )
    other_token = create_access_token(subject=other_citizen.id, role=other_citizen.role)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    resp_forbidden = client.get(f"/api/v1/cases/{case.id}/sla", headers=other_headers)
    assert resp_forbidden.status_code == status.HTTP_403_FORBIDDEN


def test_manual_escalation_lifecycle(client: TestClient, sla_test_env: dict, db_session: Session):
    env = sla_test_env
    case = env["case"]
    op_headers = {"Authorization": f"Bearer {env['token_op']}"}
    lead_headers = {"Authorization": f"Bearer {env['token_lead']}"}

    # 1. Create manual escalation as operator
    payload = {
        "reason": "Road collapse hazard near underground water main.",
        "trigger_type": "safety_critical",
    }
    resp = client.post(f"/api/v1/cases/{case.id}/escalations", json=payload, headers=op_headers)
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    esc_data = resp.json()
    assert esc_data["case_id"] == case.id
    assert esc_data["trigger_type"] == "safety_critical"
    assert esc_data["status"] == "active"
    esc_id = esc_data["id"]

    # Verify case is now marked as escalated
    db_session.refresh(case)
    assert case.is_escalated is True

    # 2. List case escalations
    resp_list = client.get(f"/api/v1/cases/{case.id}/escalations", headers=op_headers)
    assert resp_list.status_code == status.HTTP_200_OK
    escalations = resp_list.json()
    assert len(escalations) >= 1
    assert any(e["id"] == esc_id for e in escalations)

    # 3. Team Lead resolves escalation
    resolve_payload = {
        "status": "resolved",
        "resolution_notes": "Emergency shoring installed by civil engineering team. Site stabilized.",
    }
    resp_resolve = client.patch(
        f"/api/v1/cases/{case.id}/escalations/{esc_id}",
        json=resolve_payload,
        headers=lead_headers,
    )
    assert resp_resolve.status_code == status.HTTP_200_OK
    res_data = resp_resolve.json()
    assert res_data["status"] == "resolved"
    assert "Emergency shoring" in res_data["resolution_notes"]

    # Verify case is un-escalated
    db_session.refresh(case)
    assert case.is_escalated is False


def test_list_all_escalations_global(client: TestClient, sla_test_env: dict):
    env = sla_test_env
    lead_headers = {"Authorization": f"Bearer {env['token_lead']}"}

    resp = client.get("/api/v1/escalations", headers=lead_headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert isinstance(data, list)


def test_automation_sweep_endpoint(client: TestClient, sla_test_env: dict):
    env = sla_test_env
    op_headers = {"Authorization": f"Bearer {env['token_op']}"}

    resp = client.post("/api/v1/automation/sweep-slas-and-risks", headers=op_headers)
    assert resp.status_code == status.HTTP_200_OK
    assert "completed successfully" in resp.json()["message"]
