import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.case import Case, CaseStatus, CasePriority
from app.models.organization import Department, Category
from app.models.user import User, UserRole
from app.schemas.organization import DepartmentCreate, CategoryCreate
from app.schemas.user import UserCreate
from app.services.organization_service import organization_service
from app.services.user_service import user_service


@pytest.fixture
def activity_test_env(db_session: Session):
    """Set up test users, department, and category for activity tests."""
    c1 = user_service.create_user(
        db_session,
        user_in=UserCreate(email="citizen_act@test.com", password="Password123", full_name="Aarav Citizen"),
        forced_role=UserRole.REQUESTER,
    )
    t1 = create_access_token(subject=c1.id, role=c1.role)

    c2 = user_service.create_user(
        db_session,
        user_in=UserCreate(email="other_citizen@test.com", password="Password123", full_name="Other Citizen"),
        forced_role=UserRole.REQUESTER,
    )
    t2 = create_access_token(subject=c2.id, role=c2.role)

    op = user_service.create_user(
        db_session,
        user_in=UserCreate(email="operator_act@test.com", password="Password123", full_name="Rohan Operator"),
        forced_role=UserRole.OPERATOR,
    )
    top = create_access_token(subject=op.id, role=op.role)

    dept = organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(name="Water Works Dept", code="WATER_ACT", description="Water test"),
    )
    cat = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(
            name="Leakage Repair",
            code="LEAK_ACT",
            department_id=dept.id,
            default_priority="high",
            sla_hours=24,
        ),
    )

    return {
        "citizen1": c1,
        "token1": t1,
        "citizen2": c2,
        "token2": t2,
        "operator": op,
        "token_op": top,
        "department": dept,
        "category": cat,
    }


def test_citizen_and_staff_case_messages(
    client: TestClient,
    db_session: Session,
    activity_test_env: dict,
):
    """Verify citizen can post message to their case and operator can reply."""
    citizen = activity_test_env["citizen1"]
    token_citizen = activity_test_env["token1"]
    token_op = activity_test_env["token_op"]
    token_c2 = activity_test_env["token2"]

    # 1. Create a test case owned by citizen
    case = Case(
        case_number="MC-2026-MSG1",
        title="Water pipeline leak",
        description="Pipeline leaking on 2nd cross street.",
        citizen_id=citizen.id,
        status=CaseStatus.REPORTED.value,
        priority=CasePriority.HIGH.value,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # 2. Citizen posts a message
    msg_payload = {
        "message": "Water pressure has completely dropped in our lane.",
        "message_type": "query",
    }
    resp = client.post(
        f"/api/v1/cases/{case.id}/messages",
        headers={"Authorization": f"Bearer {token_citizen}"},
        json=msg_payload,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["message"] == msg_payload["message"]
    assert data["is_from_citizen"] is True
    assert data["sender_id"] == citizen.id

    # 3. Another citizen attempts to post message to this case -> 403
    resp_unauth = client.post(
        f"/api/v1/cases/{case.id}/messages",
        headers={"Authorization": f"Bearer {token_c2}"},
        json={"message": "I am not the owner"},
    )
    assert resp_unauth.status_code == status.HTTP_403_FORBIDDEN

    # 4. Operator posts a response
    staff_reply = {
        "message": "Plumbing crew is en route to repair valve.",
        "message_type": "staff_update",
    }
    resp_staff = client.post(
        f"/api/v1/cases/{case.id}/messages",
        headers={"Authorization": f"Bearer {token_op}"},
        json=staff_reply,
    )
    assert resp_staff.status_code == status.HTTP_201_CREATED
    staff_data = resp_staff.json()
    assert staff_data["is_from_citizen"] is False

    # 5. List messages
    list_resp = client.get(
        f"/api/v1/cases/{case.id}/messages",
        headers={"Authorization": f"Bearer {token_citizen}"},
    )
    assert list_resp.status_code == status.HTTP_200_OK
    messages = list_resp.json()
    assert len(messages) == 2
    assert messages[0]["message"] == msg_payload["message"]
    assert messages[1]["message"] == staff_reply["message"]


def test_internal_notes_strict_isolation(
    client: TestClient,
    db_session: Session,
    activity_test_env: dict,
):
    """Verify internal notes are strictly accessible to staff and 403 Forbidden for requesters."""
    citizen = activity_test_env["citizen1"]
    token_citizen = activity_test_env["token1"]
    token_op = activity_test_env["token_op"]

    case = Case(
        case_number="MC-2026-NOTE1",
        title="Illegal dumping investigation",
        description="Construction debris dumped on sidewalk.",
        citizen_id=citizen.id,
        status=CaseStatus.REPORTED.value,
        priority=CasePriority.MEDIUM.value,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # 1. Citizen attempts to create internal note -> 403 Forbidden
    resp_blocked_post = client.post(
        f"/api/v1/cases/{case.id}/internal-notes",
        headers={"Authorization": f"Bearer {token_citizen}"},
        json={"note": "Citizen trying to add note", "note_type": "general"},
    )
    assert resp_blocked_post.status_code == status.HTTP_403_FORBIDDEN

    # 2. Citizen attempts to view internal notes -> 403 Forbidden
    resp_blocked_get = client.get(
        f"/api/v1/cases/{case.id}/internal-notes",
        headers={"Authorization": f"Bearer {token_citizen}"},
    )
    assert resp_blocked_get.status_code == status.HTTP_403_FORBIDDEN

    # 3. Operator creates internal note -> 201 Created
    resp_ok_post = client.post(
        f"/api/v1/cases/{case.id}/internal-notes",
        headers={"Authorization": f"Bearer {token_op}"},
        json={
            "note": "Suspect vehicle license plate tracked to nearby contractor.",
            "note_type": "investigation_discussion",
        },
    )
    assert resp_ok_post.status_code == status.HTTP_201_CREATED
    note_data = resp_ok_post.json()
    assert note_data["note"] == "Suspect vehicle license plate tracked to nearby contractor."

    # 4. Operator reads internal notes -> 200 OK
    resp_ok_get = client.get(
        f"/api/v1/cases/{case.id}/internal-notes",
        headers={"Authorization": f"Bearer {token_op}"},
    )
    assert resp_ok_get.status_code == status.HTTP_200_OK
    assert len(resp_ok_get.json()) == 1


def test_case_tasks_crud_and_completion(
    client: TestClient,
    db_session: Session,
    activity_test_env: dict,
):
    """Verify staff can create, update, and complete tasks with completion timestamp."""
    citizen = activity_test_env["citizen1"]
    token_op = activity_test_env["token_op"]
    operator = activity_test_env["operator"]

    case = Case(
        case_number="MC-2026-TASK1",
        title="Fallen tree branch",
        description="Large tree branch blocking lane.",
        citizen_id=citizen.id,
        status=CaseStatus.ASSIGNED.value,
        priority=CasePriority.HIGH.value,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # 1. Operator creates task
    task_payload = {
        "title": "Dispatch tree cutter team with chainsaw",
        "description": "Clear primary roadway for emergency vehicle access.",
        "assigned_to_id": operator.id,
        "order": 1,
    }
    resp = client.post(
        f"/api/v1/cases/{case.id}/tasks",
        headers={"Authorization": f"Bearer {token_op}"},
        json=task_payload,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    task = resp.json()
    assert task["status"] == "pending"
    assert task["title"] == task_payload["title"]
    assert task["completed_at"] is None

    # 2. Update task status to completed
    task_id = task["id"]
    update_resp = client.patch(
        f"/api/v1/cases/{case.id}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token_op}"},
        json={"status": "completed"},
    )
    assert update_resp.status_code == status.HTTP_200_OK
    updated_task = update_resp.json()
    assert updated_task["status"] == "completed"
    assert updated_task["completed_at"] is not None


def test_case_investigation_recording(
    client: TestClient,
    db_session: Session,
    activity_test_env: dict,
):
    """Verify staff can record structured investigation findings and verify status transition."""
    citizen = activity_test_env["citizen1"]
    token_op = activity_test_env["token_op"]

    case = Case(
        case_number="MC-2026-INV1",
        title="Open manhole cover risk",
        description="Manhole cover missing on pavement.",
        citizen_id=citizen.id,
        status=CaseStatus.ASSIGNED.value,
        priority=CasePriority.CRITICAL.value,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Operator logs investigation findings
    inv_payload = {
        "observations": "Cast iron cover cracked due to heavy commercial truck loading.",
        "actions_taken": "Installed heavy-duty reinforced fiber concrete replacement cover.",
        "findings": "Vehicle weight limit signs were missing on alley entrance.",
        "evidence_notes": "Photos of installed replacement cover attached.",
        "follow_up_requirements": "Install 5-ton maximum weight restriction sign.",
    }
    resp = client.post(
        f"/api/v1/cases/{case.id}/investigations",
        headers={"Authorization": f"Bearer {token_op}"},
        json=inv_payload,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    inv_data = resp.json()
    assert inv_data["findings"] == inv_payload["findings"]

    # Verify case status progressed to action_taken (since actions_taken was provided)
    db_session.refresh(case)
    assert case.status == CaseStatus.ACTION_TAKEN.value
