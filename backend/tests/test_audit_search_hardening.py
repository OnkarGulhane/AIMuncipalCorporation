import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.case import Case, CaseStatus, CasePriority, CaseSeverity
from app.models.activity import CaseMessage, InternalNote, CaseTask, CaseInvestigation
from app.models.escalation import CaseEscalation, EscalationTrigger, EscalationStatus
from app.models.attachment import CaseAttachment
from app.schemas.user import UserCreate
from app.services.user_service import user_service
from app.services.audit_service import audit_service


@pytest.fixture
def test_users(db_session: Session):
    citizen = user_service.create_user(
        db_session,
        user_in=UserCreate(email="citizen_audit@test.com", password="Password123", full_name="Aarav Citizen", ward="Ward 12 - North"),
        forced_role=UserRole.REQUESTER,
    )
    operator = user_service.create_user(
        db_session,
        user_in=UserCreate(email="operator_audit@test.com", password="Password123", full_name="Kiran Operator", ward="Ward 12 - North"),
        forced_role=UserRole.OPERATOR,
    )
    admin = user_service.create_user(
        db_session,
        user_in=UserCreate(email="admin_audit@test.com", password="Password123", full_name="Chief Admin", ward="Ward 1"),
        forced_role=UserRole.ADMINISTRATOR,
    )

    return {
        "citizen": citizen,
        "operator": operator,
        "admin": admin,
        "token_citizen": create_access_token(subject=citizen.id, role=citizen.role),
        "token_operator": create_access_token(subject=operator.id, role=operator.role),
        "token_admin": create_access_token(subject=admin.id, role=admin.role),
    }


def test_multi_criteria_search_and_filters(client: TestClient, db_session: Session, test_users: dict):
    citizen = test_users["citizen"]
    operator = test_users["operator"]
    admin_token = test_users["token_admin"]

    # Create 3 distinct cases
    case1 = Case(
        case_number="MC-2026-9001",
        title="Severe Water Pipeline Burst",
        description="Main municipal pipeline burst causing flooding near Gandhi Market",
        status=CaseStatus.ASSIGNED.value,
        priority=CasePriority.CRITICAL.value,
        severity=CaseSeverity.CRITICAL.value,
        citizen_id=citizen.id,
        ward="Ward 12 - North",
        landmark="Near Gandhi Market",
        assigned_to_id=operator.id,
    )
    case2 = Case(
        case_number="MC-2026-9002",
        title="Streetlight Malfunction on 5th Cross",
        description="Dark street after 7 PM causing night safety concerns",
        status=CaseStatus.REPORTED.value,
        priority=CasePriority.LOW.value,
        severity=CaseSeverity.MINOR.value,
        citizen_id=citizen.id,
        ward="Ward 04 - East",
        landmark="Opposite SBI Bank",
    )
    case3 = Case(
        case_number="MC-2026-9003",
        title="Garbage Dump Overflow",
        description="Uncollected municipal trash heap spilling onto road",
        status=CaseStatus.CLOSED.value,
        priority=CasePriority.HIGH.value,
        severity=CaseSeverity.MAJOR.value,
        citizen_id=citizen.id,
        ward="Ward 12 - North",
        landmark="Behind Bus Stop",
    )
    db_session.add_all([case1, case2, case3])
    db_session.commit()

    # 1. Search by keyword "Pipeline"
    res_search = client.get(
        "/api/v1/cases?search=Pipeline",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert data_search["total"] >= 1
    assert any(c["case_number"] == "MC-2026-9001" for c in data_search["items"])

    # 2. Filter by Ward "Ward 12"
    res_ward = client.get(
        "/api/v1/cases?ward=Ward 12",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_ward.status_code == 200
    data_ward = res_ward.json()
    assert all("Ward 12" in (c["ward"] or "") for c in data_ward["items"])

    # 3. Filter by Priority "critical"
    res_prio = client.get(
        "/api/v1/cases?priority=critical",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_prio.status_code == 200
    data_prio = res_prio.json()
    assert all(c["priority"] == "critical" for c in data_prio["items"])

    # 4. Filter by Status "assigned"
    res_status = client.get(
        "/api/v1/cases?status=assigned",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert all(c["status"] == "assigned" for c in data_status["items"])


def test_unified_case_timeline_and_privacy_isolation(client: TestClient, db_session: Session, test_users: dict):
    citizen = test_users["citizen"]
    admin = test_users["admin"]
    citizen_token = test_users["token_citizen"]
    admin_token = test_users["token_admin"]

    # Create Case
    case = Case(
        case_number="MC-2026-9100",
        title="Open Storm Drain Manhole",
        description="Hazardous open manhole during monsoon",
        status=CaseStatus.INVESTIGATED.value,
        priority=CasePriority.CRITICAL.value,
        severity=CaseSeverity.CRITICAL.value,
        citizen_id=citizen.id,
        ward="Ward 08",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Add Citizen Message
    msg = CaseMessage(
        case_id=case.id,
        sender_id=citizen.id,
        message_type="query",
        is_from_citizen=True,
        message="Water is filling up quickly, please hurry!",
    )
    # Add Internal Staff Note (CONFIDENTIAL)
    internal_note = InternalNote(
        case_id=case.id,
        author_id=admin.id,
        note_type="technical",
        note="CONFIDENTIAL: Replacement casting is on backorder until Friday.",
    )

    # Add Task
    task = CaseTask(
        case_id=case.id,
        case_rel=case,
        title="Place safety barricades and warning tape",
        status="completed",
        assigned_to_id=admin.id,
        created_by_id=admin.id,
        order=1,
    )
    # Add Investigation
    inv = CaseInvestigation(
        case_id=case.id,
        investigator_id=admin.id,
        observations="Manhole lid missing, 2m depth.",
        findings="Immediate safety risk verified.",
        follow_up_requirements="Immediate lid installation needed",
    )

    db_session.add_all([msg, internal_note, task, inv])
    db_session.commit()

    # Test 1: Citizen requests unified timeline -> Internal Note & Investigation MUST be absent
    citizen_timeline_res = client.get(
        f"/api/v1/cases/{case.id}/timeline",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert citizen_timeline_res.status_code == 200
    cit_data = citizen_timeline_res.json()
    assert cit_data["case_id"] == case.id
    assert cit_data["total_events"] >= 2

    descriptions = [e["description"] for e in cit_data["timeline"]]
    # Strictly assert CONFIDENTIAL internal note is NOT leaked to requester
    assert not any("CONFIDENTIAL: Replacement casting" in (d or "") for d in descriptions)
    assert not any(e["is_internal"] is True for e in cit_data["timeline"])

    # Test 2: Admin/Staff requests unified timeline -> Sees EVERYTHING including internal note
    admin_timeline_res = client.get(
        f"/api/v1/cases/{case.id}/timeline",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_timeline_res.status_code == 200
    adm_data = admin_timeline_res.json()
    adm_descriptions = [e["description"] for e in adm_data["timeline"]]
    assert any("CONFIDENTIAL: Replacement casting" in (d or "") for d in adm_descriptions)


def test_audit_service_and_logging(db_session: Session, client: TestClient, test_users: dict):
    admin = test_users["admin"]
    admin_token = test_users["token_admin"]

    # Log event manually via service
    entry = audit_service.log_event(
        db=db_session,
        action="SYSTEM_CONFIG_UPDATED",
        resource_type="system",
        resource_id="general_config",
        actor_id=admin.id,
        details="SLA response thresholds reconfigured for monsoon season",
        is_ai_action=False,
    )
    assert entry.id is not None
    assert entry.action == "SYSTEM_CONFIG_UPDATED"

    # Query audit logs via API
    res = client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_standardized_error_handling(client: TestClient, test_users: dict):
    admin_token = test_users["token_admin"]

    # 1. 404 Not Found error formatting
    res_404 = client.get(
        "/api/v1/cases/999999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_404.status_code == 404
    body_404 = res_404.json()
    assert "error" in body_404
    assert body_404["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "action_hint" in body_404["error"]

    # 2. 422 Validation Error formatting
    res_422 = client.post(
        "/api/v1/cases",
        json={"title": "A"},  # Invalid short title (< 3 chars)
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_422.status_code == 422
    body_422 = res_422.json()
    assert "error" in body_422
    assert body_422["error"]["code"] == "VALIDATION_FAILED"
    assert "details" in body_422["error"]
