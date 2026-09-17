import io
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.case import Case, CaseStatus, CasePriority, CaseSeverity
from app.models.organization import Department, Category, Team
from app.schemas.user import UserCreate
from app.schemas.organization import DepartmentCreate, CategoryCreate, TeamCreate
from app.schemas.case import CaseCreate
from app.services.user_service import user_service
from app.services.organization_service import organization_service
from app.services.case_service import case_service


@pytest.fixture
def e2e_environment(db_session: Session):
    # 1. Setup Department, Category, and Team
    dept = organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(name="Public Works & Roads", code="ROADS_E2E", description="Road and bridge repairs"),
    )
    cat = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(name="Pothole Repair", code="POTHOLES", department_id=dept.id, default_sla_hours=24),
    )
    team = organization_service.create_team(
        db_session,
        team_in=TeamCreate(name="Road Squad Alpha", code="SQUAD_A", department_id=dept.id),
    )

    # 2. Setup 5 distinct role users
    citizen = user_service.create_user(
        db_session,
        user_in=UserCreate(email="citizen_e2e@city.gov", password="Password123", full_name="Rahul Deshmukh", ward="Ward 12 - North"),
        forced_role=UserRole.REQUESTER,
    )
    operator = user_service.create_user(
        db_session,
        user_in=UserCreate(email="operator_e2e@city.gov", password="Password123", full_name="Sanjay Field Operator", ward="Ward 12 - North"),
        forced_role=UserRole.OPERATOR,
    )
    operator.department_id = dept.id
    operator.team_id = team.id

    team_lead = user_service.create_user(
        db_session,
        user_in=UserCreate(email="teamlead_e2e@city.gov", password="Password123", full_name="Anjali Team Lead", ward="Ward 12 - North"),
        forced_role=UserRole.TEAM_LEAD,
    )
    team_lead.department_id = dept.id
    team_lead.team_id = team.id

    manager = user_service.create_user(
        db_session,
        user_in=UserCreate(email="manager_e2e@city.gov", password="Password123", full_name="Vikas Ward Manager", ward="Ward 12 - North"),
        forced_role=UserRole.MANAGER,
    )
    manager.department_id = dept.id

    admin = user_service.create_user(
        db_session,
        user_in=UserCreate(email="admin_e2e@city.gov", password="Password123", full_name="Chief Administrator", ward="Ward 01"),
        forced_role=UserRole.ADMINISTRATOR,
    )

    db_session.commit()

    return {
        "dept": dept,
        "cat": cat,
        "team": team,
        "citizen": citizen,
        "operator": operator,
        "team_lead": team_lead,
        "manager": manager,
        "admin": admin,
        "token_citizen": create_access_token(subject=citizen.id, role=citizen.role),
        "token_operator": create_access_token(subject=operator.id, role=operator.role),
        "token_team_lead": create_access_token(subject=team_lead.id, role=team_lead.role),
        "token_manager": create_access_token(subject=manager.id, role=manager.role),
        "token_admin": create_access_token(subject=admin.id, role=admin.role),
    }


def test_complete_connected_e2e_lifecycle(client: TestClient, e2e_environment: dict):
    """
    Complete PRD Section 51 connected lifecycle scenario:
    1. Citizen reports complaint
    2. Evidence uploaded
    3. AI triage analysis generated
    4. Operator takes ownership & accepts AI triage
    5. Clarification requested (WAITING_INFO) & answered
    6. Investigation & tasks delegated
    7. Team Lead escalation intervention
    8. Operator proposes resolution
    9. Citizen confirms resolution
    10. Manager reviews analytics & insights
    11. Admin audits complete immutable history
    """
    env = e2e_environment
    t_cit = env["token_citizen"]
    t_op = env["token_operator"]
    t_lead = env["token_team_lead"]
    t_mgr = env["token_manager"]
    t_adm = env["token_admin"]

    # -------------------------------------------------------------------------
    # Step 1: Citizen creates complaint
    # -------------------------------------------------------------------------
    create_res = client.post(
        "/api/v1/cases",
        json={
            "title": "Severe dangerous pothole on MG Road near Central School",
            "description": "Large 1-meter deep pothole causing severe traffic congestion and near-accidents for school buses.",
            "ward": "Ward 12 - North",
            "landmark": "Near Central School Main Gate",
            "address": "MG Road, Sector 4",
            "priority": "high",
            "severity": "major",
        },
        headers={"Authorization": f"Bearer {t_cit}"},
    )
    assert create_res.status_code == 201
    case_data = create_res.json()
    case_id = case_data["id"]
    case_number = case_data["case_number"]
    assert case_number.startswith("MC-")
    assert case_data["status"] == "reported"

    # -------------------------------------------------------------------------
    # Step 2: Citizen uploads photo evidence
    # -------------------------------------------------------------------------
    dummy_image = io.BytesIO(b"fake-image-bytes-pothole-photo")
    upload_res = client.post(
        f"/api/v1/cases/{case_id}/attachments",
        files={"file": ("pothole_evidence.jpg", dummy_image, "image/jpeg")},
        headers={"Authorization": f"Bearer {t_cit}"},
    )
    assert upload_res.status_code == 201
    assert upload_res.json()["original_filename"] == "pothole_evidence.jpg"

    # -------------------------------------------------------------------------
    # Step 3: AI Copilot runs triage analysis
    # -------------------------------------------------------------------------
    ai_res = client.post(
        f"/api/v1/cases/{case_id}/ai-analysis",
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert ai_data["confidence_score"] > 0.5
    assert len(ai_data["key_details"]) > 0
    assert ai_data["recommended_action"] is not None

    # -------------------------------------------------------------------------
    # Step 4: Operator takes ownership & accepts AI triage recommendations
    # -------------------------------------------------------------------------
    apply_res = client.post(
        f"/api/v1/cases/{case_id}/ai/apply-suggestions",
        json={"apply_category": True, "apply_priority": True, "apply_team": True},
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert apply_res.status_code == 200

    assign_res = client.put(
        f"/api/v1/cases/{case_id}/assignment",
        json={"assigned_to_id": env["operator"].id, "reason": "Claimed by field squad alpha"},
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "assigned"

    # -------------------------------------------------------------------------
    # Step 5: Operator requests clarification (Sets WAITING_INFO) & Citizen responds
    # -------------------------------------------------------------------------
    status_wait_res = client.put(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "waiting_info", "reason": "Need exact electric pole reference number"},
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert status_wait_res.status_code == 200
    assert status_wait_res.json()["status"] == "waiting_info"

    op_msg_res = client.post(
        f"/api/v1/cases/{case_id}/messages",
        json={"message": "Could you please confirm if the crater is near electric pole #44?", "message_type": "query"},
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert op_msg_res.status_code == 201

    cit_msg_res = client.post(
        f"/api/v1/cases/{case_id}/messages",
        json={"message": "Yes, exactly opposite pole #44 next to the school boundary wall.", "message_type": "query"},
        headers={"Authorization": f"Bearer {t_cit}"},
    )
    assert cit_msg_res.status_code == 201

    # Status advances back to assigned
    status_back_res = client.put(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "assigned", "reason": "Citizen clarification received"},
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert status_back_res.status_code == 200

    # -------------------------------------------------------------------------
    # Step 6: Operator conducts field investigation and delegates sub-tasks
    # -------------------------------------------------------------------------
    inv_res = client.post(
        f"/api/v1/cases/{case_id}/investigations",
        json={
            "observations": "Crater is 1.2m wide, depth 15cm on asphalt surface.",
            "actions_taken": "Placed 3 safety warning cones around pothole perimeter.",
            "findings": "Sub-base eroded due to heavy monsoon runoff.",
            "follow_up_requirements": "Requires 2 metric tons hot-mix asphalt and roller.",
        },
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert inv_res.status_code == 201

    task_res = client.post(
        f"/api/v1/cases/{case_id}/tasks",
        json={"title": "Deliver 2 tons hot asphalt and roller machine", "assigned_to_id": env["operator"].id, "order": 1},
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # Status moves to investigated
    client.put(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "investigated", "reason": "Site measurement completed"},
        headers={"Authorization": f"Bearer {t_op}"},
    )

    # -------------------------------------------------------------------------
    # Step 7: Team Lead escalation intervention
    # -------------------------------------------------------------------------
    esc_res = client.post(
        f"/api/v1/cases/{case_id}/escalations",
        json={"reason": "Asphalt delivery delayed by central supplier", "trigger_type": "operator_request"},
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert esc_res.status_code == 201
    esc_id = esc_res.json()["id"]

    # Team Lead approves emergency supplier allocation and resolves escalation
    esc_resolve_res = client.patch(
        f"/api/v1/cases/{case_id}/escalations/{esc_id}",
        json={"status": "resolved", "resolution_notes": "Authorized emergency depot dispatch."},
        headers={"Authorization": f"Bearer {t_lead}"},
    )
    assert esc_resolve_res.status_code == 200

    # -------------------------------------------------------------------------
    # Step 8: Field repair execution & Resolution proposed
    # -------------------------------------------------------------------------
    # Complete task
    client.patch(
        f"/api/v1/cases/{case_id}/tasks/{task_id}",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {t_op}"},
    )

    # Action taken
    client.put(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "action_taken", "reason": "Asphalt laid and compacted"},
        headers={"Authorization": f"Bearer {t_op}"},
    )

    # Propose resolution
    prop_res = client.put(
        f"/api/v1/cases/{case_id}/status",
        json={
            "new_status": "resolution_proposed",
            "resolution_notes": "Pothole completely filled with hot asphalt mix, compacted level with road surface, and inspected.",
        },
        headers={"Authorization": f"Bearer {t_op}"},
    )
    assert prop_res.status_code == 200
    assert prop_res.json()["status"] == "resolution_proposed"

    # -------------------------------------------------------------------------
    # Step 9: Citizen confirms resolution
    # -------------------------------------------------------------------------
    confirm_res = client.post(
        f"/api/v1/cases/{case_id}/confirm-resolution",
        json={"notes": "Inspected on the way to school; road is smooth and safe now. Thank you!"},
        headers={"Authorization": f"Bearer {t_cit}"},
    )
    assert confirm_res.status_code == 200
    final_case = confirm_res.json()
    assert final_case["status"] == "confirmed"
    assert final_case["closed_at"] is not None

    # -------------------------------------------------------------------------
    # Step 10: Manager checks dashboard analytics & SLA compliance
    # -------------------------------------------------------------------------
    mgr_analytics_res = client.get(
        "/api/v1/analytics/manager",
        headers={"Authorization": f"Bearer {t_mgr}"},
    )
    assert mgr_analytics_res.status_code == 200
    mgr_data = mgr_analytics_res.json()
    assert mgr_data["resolved_cases"] >= 1
    assert "ai_operational_insights" in mgr_data

    # -------------------------------------------------------------------------
    # Step 11: Administrator reviews system statistics and audit trail
    # -------------------------------------------------------------------------
    stats_res = client.get(
        "/api/v1/admin/system-stats",
        headers={"Authorization": f"Bearer {t_adm}"},
    )
    assert stats_res.status_code == 200
    assert stats_res.json()["total_cases"] >= 1

    audit_res = client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {t_adm}"},
    )
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 3


def test_citizen_rejection_and_reopen_lifecycle(client: TestClient, e2e_environment: dict):
    env = e2e_environment
    t_cit = env["token_citizen"]
    t_op = env["token_operator"]

    # 1. Create and progress case to resolution_proposed
    case_res = client.post(
        "/api/v1/cases",
        json={"title": "Broken street lamp post", "description": "Sparking wire on 3rd cross street.", "ward": "Ward 12 - North"},
        headers={"Authorization": f"Bearer {t_cit}"},
    )
    case_id = case_res.json()["id"]

    client.put(
        f"/api/v1/cases/{case_id}/assignment",
        json={"assigned_to_id": env["operator"].id},
        headers={"Authorization": f"Bearer {t_op}"},
    )
    client.put(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "investigated"},
        headers={"Authorization": f"Bearer {t_op}"},
    )
    client.put(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "action_taken"},
        headers={"Authorization": f"Bearer {t_op}"},
    )
    client.put(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "resolution_proposed", "resolution_notes": "Taped wires."},
        headers={"Authorization": f"Bearer {t_op}"},
    )

    # 2. Citizen rejects proposed resolution with feedback
    reject_res = client.post(
        f"/api/v1/cases/{case_id}/reject-resolution",
        json={"rejection_reason": "Wires are still dangling and sparking during rain. Needs permanent casing."},
        headers={"Authorization": f"Bearer {t_cit}"},
    )
    assert reject_res.status_code == 200
    rejected_case = reject_res.json()
    assert rejected_case["status"] == "reopened"
    assert rejected_case["rejection_reason"] is not None
    assert rejected_case["closed_at"] is None
