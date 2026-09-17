import pytest
from unittest.mock import patch
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.case import Case, CasePriority, CaseStatus, CaseSeverity
from app.models.organization import Department, Category
from app.models.user import UserRole
from app.models.notification import Notification, NotificationPreference, NotificationEventType, NotificationChannel
from app.schemas.user import UserCreate
from app.schemas.organization import DepartmentCreate, CategoryCreate
from app.schemas.case import CaseCreate, CaseStatusUpdate, CaseAssignmentUpdate
from app.schemas.activity import CaseMessageCreate, CaseTaskCreate
from app.schemas.escalation import EscalationCreate
from app.schemas.notification import NotificationPreferenceUpdate
from app.services.user_service import user_service
from app.services.organization_service import organization_service
from app.services.case_service import case_service
from app.services.activity_service import activity_service
from app.services.escalation_service import create_case_escalation
from app.services.notification_service import notification_service
from app.services.email_service import email_service


@pytest.fixture
def notif_test_env(db_session: Session):
    citizen = user_service.create_user(
        db_session,
        user_in=UserCreate(email="citizen_notif@test.com", password="Password123", full_name="Aarav Citizen", ward="Ward 7"),
        forced_role=UserRole.REQUESTER,
    )
    token_citizen = create_access_token(subject=citizen.id, role=citizen.role)

    operator = user_service.create_user(
        db_session,
        user_in=UserCreate(email="operator_notif@test.com", password="Password123", full_name="Rohan Operator", ward="Ward 7"),
        forced_role=UserRole.OPERATOR,
    )
    token_op = create_access_token(subject=operator.id, role=operator.role)

    teamlead = user_service.create_user(
        db_session,
        user_in=UserCreate(email="teamlead_notif@test.com", password="Password123", full_name="Priya Lead", ward="Ward 7"),
        forced_role=UserRole.TEAM_LEAD,
    )
    token_lead = create_access_token(subject=teamlead.id, role=teamlead.role)

    dept = organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(name="Sanitation Dept", code="SAN_NOTIF", description="Sanitation dept"),
    )
    teamlead.department_id = dept.id
    operator.department_id = dept.id
    db_session.commit()

    cat = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(
            name="Garbage Overflow",
            code="GARB_NOTIF",
            department_id=dept.id,
            default_priority="medium",
            sla_hours=24,
        ),
    )

    case = case_service.create_case(
        db_session,
        case_in=CaseCreate(
            title="Garbage bin overflowing near market",
            description="Large pile of trash accumulating for 3 days near vegetable market",
            category_id=cat.id,
            ward="Ward 7",
            landmark="Central Vegetable Market",
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
        "dept": dept,
        "cat": cat,
        "case": case,
    }


def test_notification_creation_and_list(client: TestClient, notif_test_env, db_session: Session):
    citizen = notif_test_env["citizen"]
    token = notif_test_env["token_citizen"]

    # When case was created in fixture, a notification for citizen was dispatched
    response = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    assert data["unread_count"] >= 1
    assert len(data["items"]) >= 1
    assert "Complaint Registered" in data["items"][0]["title"]


def test_unread_count_endpoint(client: TestClient, notif_test_env, db_session: Session):
    citizen = notif_test_env["citizen"]
    token = notif_test_env["token_citizen"]

    response = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "unread_count" in data
    assert data["unread_count"] >= 1


def test_mark_single_notification_read(client: TestClient, notif_test_env, db_session: Session):
    citizen = notif_test_env["citizen"]
    token = notif_test_env["token_citizen"]

    # Fetch notification
    list_res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token}"})
    notif_id = list_res.json()["items"][0]["id"]

    # Mark as read
    patch_res = client.patch(f"/api/v1/notifications/{notif_id}/read", headers={"Authorization": f"Bearer {token}"})
    assert patch_res.status_code == status.HTTP_200_OK
    updated = patch_res.json()
    assert updated["is_read"] is True
    assert updated["read_at"] is not None

    # Check unread count decreased
    count_res = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {token}"})
    assert count_res.json()["unread_count"] == 0


def test_mark_all_notifications_read(client: TestClient, notif_test_env, db_session: Session):
    citizen = notif_test_env["citizen"]
    token = notif_test_env["token_citizen"]

    # Add a second notification
    notification_service.create_notification(
        db_session,
        user_id=citizen.id,
        title="Second Notification",
        message="Test message 2",
        event_type=NotificationEventType.STAFF_UPDATE.value,
    )

    # Verify multiple unread
    count_res = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {token}"})
    assert count_res.json()["unread_count"] >= 2

    # Mark all read
    mark_all_res = client.post("/api/v1/notifications/mark-all-read", headers={"Authorization": f"Bearer {token}"})
    assert mark_all_res.status_code == status.HTTP_200_OK
    assert mark_all_res.json()["status"] == "success"
    assert mark_all_res.json()["marked_read_count"] >= 2

    # Verify unread is now 0
    count_res2 = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {token}"})
    assert count_res2.json()["unread_count"] == 0


def test_delete_notification(client: TestClient, notif_test_env, db_session: Session):
    citizen = notif_test_env["citizen"]
    token = notif_test_env["token_citizen"]

    list_res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token}"})
    notif_id = list_res.json()["items"][0]["id"]

    del_res = client.delete(f"/api/v1/notifications/{notif_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Fetching or deleting again returns 404
    del_res2 = client.delete(f"/api/v1/notifications/{notif_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res2.status_code == status.HTTP_404_NOT_FOUND


def test_notification_preferences_get_and_update(client: TestClient, notif_test_env, db_session: Session):
    token = notif_test_env["token_citizen"]

    # Get initial defaults
    pref_res = client.get("/api/v1/notifications/preferences", headers={"Authorization": f"Bearer {token}"})
    assert pref_res.status_code == status.HTTP_200_OK
    prefs = pref_res.json()
    assert prefs["email_enabled"] is True
    assert prefs["in_app_enabled"] is True

    # Update preferences to disable emails and status changes
    update_res = client.put(
        "/api/v1/notifications/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email_enabled": False,
            "notify_on_status_change": False,
        },
    )
    assert update_res.status_code == status.HTTP_200_OK
    updated_prefs = update_res.json()
    assert updated_prefs["email_enabled"] is False
    assert updated_prefs["notify_on_status_change"] is False
    assert updated_prefs["in_app_enabled"] is True


def test_dispatch_matrix_events(client: TestClient, notif_test_env, db_session: Session):
    citizen = notif_test_env["citizen"]
    operator = notif_test_env["operator"]
    teamlead = notif_test_env["teamlead"]
    case = notif_test_env["case"]

    # 1. Assignment dispatch
    case_service.update_assignment(
        db_session,
        case_obj=case,
        actor=teamlead,
        assigned_to_id=operator.id,
    )

    op_unread = notification_service.get_unread_count(db_session, operator.id)
    assert op_unread >= 1

    # 2. Citizen message dispatch to assigned operator
    activity_service.create_message(
        db_session,
        case_id=case.id,
        data=CaseMessageCreate(message="I have added photos of the overflowing garbage"),
        user=citizen,
    )
    op_unread_after_msg = notification_service.get_unread_count(db_session, operator.id)
    assert op_unread_after_msg > op_unread

    # 3. Staff message dispatch to citizen
    cit_unread_before = notification_service.get_unread_count(db_session, citizen.id)
    activity_service.create_message(
        db_session,
        case_id=case.id,
        data=CaseMessageCreate(message="Our sanitation truck is scheduled to clear this today at 4 PM"),
        user=operator,
    )
    cit_unread_after = notification_service.get_unread_count(db_session, citizen.id)
    assert cit_unread_after > cit_unread_before

    # 4. Task assignment dispatch to operator
    activity_service.create_task(
        db_session,
        case_id=case.id,
        data=CaseTaskCreate(title="Dispatch Waste Compactor Truck", assigned_to_id=operator.id),
        user=teamlead,
    )
    op_unread_after_task = notification_service.get_unread_count(db_session, operator.id)
    assert op_unread_after_task > op_unread_after_msg

    # 5. Escalation dispatch to teamlead
    lead_unread_before = notification_service.get_unread_count(db_session, teamlead.id)
    create_case_escalation(
        db_session,
        case=case,
        escalation_data=EscalationCreate(
            reason="High sanitation risk near food market",
            trigger_type="manual",
        ),
        current_user=operator,
    )
    lead_unread_after = notification_service.get_unread_count(db_session, teamlead.id)
    assert lead_unread_after > lead_unread_before


def test_email_template_rendering_and_send(db_session: Session):
    # Test branded email formatting
    subj, text_b, html_b = email_service.format_case_email(
        case_number="MC-2026-0001",
        case_title="Streetlight Failure",
        event_title="Case Assigned to Field Tech",
        event_message="Your case has been assigned to the electrical department.",
        recipient_name="John Citizen",
    )
    assert "MC-2026-0001" in subj
    assert "Streetlight Failure" in text_b
    assert "John Citizen" in text_b
    assert "MC-2026-0001" in html_b
    assert "#0284c7" in html_b  # Brand sky blue color
    assert "AI Municipal Grievance Redressal" in html_b

    # Test send method in test environment (mock / fallback)
    with patch("smtplib.SMTP") as mock_smtp:
        sent = email_service.send_transactional_email(
            to_email="citizen@example.com",
            subject=subj,
            text_body=text_b,
            html_body=html_b,
        )
        assert sent is True
