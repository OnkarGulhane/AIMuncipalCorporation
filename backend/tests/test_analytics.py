import pytest
from datetime import datetime, timezone
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.case import Case, CasePriority, CaseStatus, CaseSeverity
from app.models.organization import Department, Category, Team
from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.schemas.organization import DepartmentCreate, CategoryCreate, TeamCreate
from app.schemas.case import CaseCreate, CaseStatusUpdate
from app.schemas.activity import CaseTaskCreate
from app.services.user_service import user_service
from app.services.organization_service import organization_service
from app.services.case_service import case_service
from app.services.activity_service import activity_service
from app.services.sla_service import initialize_or_update_case_sla
from app.services.escalation_service import create_case_escalation
from app.schemas.escalation import EscalationCreate


@pytest.fixture
def analytics_test_env(db_session: Session):
    citizen1 = user_service.create_user(
        db_session,
        user_in=UserCreate(email="citizen1_analytics@test.com", password="Password123", full_name="Aarav Sharma", ward="Ward 4"),
        forced_role=UserRole.REQUESTER,
    )
    token_citizen1 = create_access_token(subject=citizen1.id, role=citizen1.role)

    citizen2 = user_service.create_user(
        db_session,
        user_in=UserCreate(email="citizen2_analytics@test.com", password="Password123", full_name="Meera Joshi", ward="Ward 9"),
        forced_role=UserRole.REQUESTER,
    )
    token_citizen2 = create_access_token(subject=citizen2.id, role=citizen2.role)

    manager = user_service.create_user(
        db_session,
        user_in=UserCreate(email="manager_analytics@test.com", password="Password123", full_name="Sunil Patil", ward="Ward 1"),
        forced_role=UserRole.MANAGER,
    )
    token_manager = create_access_token(subject=manager.id, role=manager.role)

    admin = user_service.create_user(
        db_session,
        user_in=UserCreate(email="admin_analytics@test.com", password="Password123", full_name="Chief Admin", ward="Ward 1"),
        forced_role=UserRole.ADMINISTRATOR,
    )
    token_admin = create_access_token(subject=admin.id, role=admin.role)

    teamlead = user_service.create_user(
        db_session,
        user_in=UserCreate(email="lead_analytics@test.com", password="Password123", full_name="Ramesh Lead", ward="Ward 4"),
        forced_role=UserRole.TEAM_LEAD,
    )
    token_lead = create_access_token(subject=teamlead.id, role=teamlead.role)

    operator1 = user_service.create_user(
        db_session,
        user_in=UserCreate(email="op1_analytics@test.com", password="Password123", full_name="Vikram Op", ward="Ward 4"),
        forced_role=UserRole.OPERATOR,
    )
    token_op1 = create_access_token(subject=operator1.id, role=operator1.role)

    operator2 = user_service.create_user(
        db_session,
        user_in=UserCreate(email="op2_analytics@test.com", password="Password123", full_name="Ananya Op", ward="Ward 9"),
        forced_role=UserRole.OPERATOR,
    )
    token_op2 = create_access_token(subject=operator2.id, role=operator2.role)

    dept = organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(name="Water Works & Sanitation", code="WTR_ANALYTICS", description="Water department"),
    )
    team = organization_service.create_team(
        db_session,
        team_in=TeamCreate(name="Pipeline Squad", department_id=dept.id, leader_id=teamlead.id),
    )
    teamlead.department_id = dept.id
    teamlead.team_id = team.id
    operator1.department_id = dept.id
    operator1.team_id = team.id
    operator2.department_id = dept.id
    operator2.team_id = team.id
    db_session.commit()

    cat1 = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(
            name="Water Pipe Leakage",
            code="LEAK_ANALYTICS",
            department_id=dept.id,
            default_priority="high",
            sla_hours=24,
        ),
    )
    cat2 = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(
            name="Contaminated Water",
            code="CONTAM_ANALYTICS",
            department_id=dept.id,
            default_priority="critical",
            sla_hours=12,
        ),
    )

    # Create Case 1 (Ward 4, Assigned to Op1, High Priority)
    case1 = case_service.create_case(
        db_session,
        case_in=CaseCreate(
            title="Burst water main in market square",
            description="Massive water leaking from underground pipeline flooding the market",
            priority=CasePriority.HIGH,
            category_id=cat1.id,
            ward="Ward 4",
            landmark="Market Square",
        ),
        citizen_id=citizen1.id,
    )
    case_service.update_assignment(db_session, case_obj=case1, actor=teamlead, assigned_to_id=operator1.id, team_id=team.id, department_id=dept.id)
    initialize_or_update_case_sla(db_session, case1)

    # Create Case 2 (Ward 4, Assigned to Op1, Critical Priority, Escalated)
    case2 = case_service.create_case(
        db_session,
        case_in=CaseCreate(
            title="Sewage contamination in drinking water line",
            description="Black water coming out of taps in residential society",
            priority=CasePriority.CRITICAL,
            category_id=cat2.id,
            ward="Ward 4",
            landmark="Gokul Society",
        ),
        citizen_id=citizen1.id,
    )
    case_service.update_assignment(db_session, case_obj=case2, actor=teamlead, assigned_to_id=operator1.id, team_id=team.id, department_id=dept.id)
    initialize_or_update_case_sla(db_session, case2)
    create_case_escalation(
        db_session,
        case=case2,
        escalation_data=EscalationCreate(reason="Health safety emergency", trigger_type="safety_critical"),
        current_user=operator1,
    )

    # Create Case 3 (Ward 9, Assigned to Op2, Closed/Resolved)
    case3 = case_service.create_case(
        db_session,
        case_in=CaseCreate(
            title="Low water pressure on 3rd floor",
            description="Pressure dropped significantly over the past two days",
            category_id=cat1.id,
            ward="Ward 9",
            landmark="Tower 5",
        ),
        citizen_id=citizen2.id,
    )
    case_service.update_assignment(db_session, case_obj=case3, actor=teamlead, assigned_to_id=operator2.id, team_id=team.id, department_id=dept.id)
    initialize_or_update_case_sla(db_session, case3)
    # Transition to Resolution Proposed -> Confirmed
    case_service.update_case_status(db_session, case_obj=case3, new_status=CaseStatus.INVESTIGATED, actor=operator2)
    case_service.update_case_status(db_session, case_obj=case3, new_status=CaseStatus.RESOLUTION_PROPOSED, actor=operator2, resolution_notes="Valve replaced")
    case_service.confirm_resolution(db_session, case_obj=case3, citizen=citizen2, notes="Fixed, thank you!")

    # Add a pending task for Operator 1 on Case 1
    activity_service.create_task(
        db_session,
        case_id=case1.id,
        data=CaseTaskCreate(title="Excavate main road pipeline", assigned_to_id=operator1.id),
        user=teamlead,
    )

    return {
        "citizen1": citizen1,
        "token_citizen1": token_citizen1,
        "citizen2": citizen2,
        "token_citizen2": token_citizen2,
        "manager": manager,
        "token_manager": token_manager,
        "admin": admin,
        "token_admin": token_admin,
        "teamlead": teamlead,
        "token_lead": token_lead,
        "operator1": operator1,
        "token_op1": token_op1,
        "operator2": operator2,
        "token_op2": token_op2,
        "dept": dept,
        "team": team,
        "cat1": cat1,
        "cat2": cat2,
        "case1": case1,
        "case2": case2,
        "case3": case3,
    }


def test_manager_analytics_dashboard(client: TestClient, analytics_test_env):
    token = analytics_test_env["token_manager"]

    response = client.get("/api/v1/analytics/manager", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["total_cases"] >= 3
    assert data["active_cases"] >= 2
    assert data["resolved_cases"] >= 1
    assert data["escalated_cases"] >= 1
    assert data["resolution_rate_percent"] > 0
    assert data["sla_compliance_percent"] > 0
    assert "cases_by_status" in data
    assert "ward_metrics" in data
    assert len(data["ward_metrics"]) >= 2
    assert "department_metrics" in data
    assert "time_series_trends" in data
    assert len(data["time_series_trends"]) == 7
    assert "ai_operational_insights" in data
    assert len(data["ai_operational_insights"]) >= 1


def test_team_lead_analytics_dashboard(client: TestClient, analytics_test_env):
    token = analytics_test_env["token_lead"]

    response = client.get("/api/v1/analytics/team-lead", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["team_name"] == "Pipeline Squad"
    assert data["department_name"] == "Water Works & Sanitation"
    assert data["total_cases"] >= 3
    assert data["active_cases"] >= 2
    assert data["active_escalations"] >= 1
    assert "operator_workloads" in data
    assert len(data["operator_workloads"]) >= 2

    # Operator 1 has 2 active cases
    op1_load = next((op for op in data["operator_workloads"] if op["operator_name"] == "Vikram Op"), None)
    assert op1_load is not None
    assert op1_load["active_cases"] >= 2


def test_operator_analytics_dashboard(client: TestClient, analytics_test_env):
    token = analytics_test_env["token_op1"]

    response = client.get("/api/v1/analytics/operator", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["operator_name"] == "Vikram Op"
    assert data["assigned_active_count"] >= 2
    assert data["high_priority_count"] >= 1
    assert data["active_escalations_count"] >= 1
    assert data["pending_tasks_count"] >= 1


def test_citizen_analytics_dashboard(client: TestClient, analytics_test_env):
    token1 = analytics_test_env["token_citizen1"]
    token2 = analytics_test_env["token_citizen2"]

    # Citizen 1 has 2 active cases
    res1 = client.get("/api/v1/analytics/citizen", headers={"Authorization": f"Bearer {token1}"})
    assert res1.status_code == status.HTTP_200_OK
    data1 = res1.json()
    assert data1["total_reported"] == 2
    assert data1["active_count"] == 2
    assert data1["resolved_count"] == 0
    assert len(data1["recent_activity"]) >= 1

    # Citizen 2 has 1 resolved case
    res2 = client.get("/api/v1/analytics/citizen", headers={"Authorization": f"Bearer {token2}"})
    assert res2.status_code == status.HTTP_200_OK
    data2 = res2.json()
    assert data2["total_reported"] == 1
    assert data2["active_count"] == 0
    assert data2["resolved_count"] == 1


def test_ward_intelligence_endpoint(client: TestClient, analytics_test_env):
    token = analytics_test_env["token_op1"]

    response = client.get("/api/v1/analytics/wards", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["total_wards_tracked"] >= 2
    assert len(data["ward_summaries"]) >= 2
    assert len(data["top_hotspots"]) >= 1

    # Ward 4 has 2 cases with 1 escalation
    ward4 = next((w for w in data["ward_summaries"] if w["ward"] == "Ward 4"), None)
    assert ward4 is not None
    assert ward4["total_cases"] == 2
    assert ward4["high_risk_cases"] >= 1


def test_admin_system_stats_and_audit_logs(client: TestClient, analytics_test_env):
    token_admin = analytics_test_env["token_admin"]

    # System stats
    stats_res = client.get("/api/v1/admin/system-stats", headers={"Authorization": f"Bearer {token_admin}"})
    assert stats_res.status_code == status.HTTP_200_OK
    stats = stats_res.json()
    assert stats["total_users"] >= 6
    assert stats["total_departments"] >= 1
    assert stats["total_cases"] >= 3
    assert stats["total_escalations"] >= 1
    assert stats["database_status"] == "healthy"

    # Audit logs
    audit_res = client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {token_admin}"})
    assert audit_res.status_code == status.HTTP_200_OK
    logs = audit_res.json()
    assert len(logs) >= 3
    assert "action" in logs[0]
    assert "created_at" in logs[0]


def test_analytics_rbac_barriers(client: TestClient, analytics_test_env):
    token_citizen = analytics_test_env["token_citizen1"]
    token_op = analytics_test_env["token_op1"]

    # Citizen cannot access manager or team lead analytics
    res_cit_mgr = client.get("/api/v1/analytics/manager", headers={"Authorization": f"Bearer {token_citizen}"})
    assert res_cit_mgr.status_code == status.HTTP_403_FORBIDDEN

    res_cit_lead = client.get("/api/v1/analytics/team-lead", headers={"Authorization": f"Bearer {token_citizen}"})
    assert res_cit_lead.status_code == status.HTTP_403_FORBIDDEN

    res_cit_ward = client.get("/api/v1/analytics/wards", headers={"Authorization": f"Bearer {token_citizen}"})
    assert res_cit_ward.status_code == status.HTTP_403_FORBIDDEN

    # Operator cannot access manager analytics
    res_op_mgr = client.get("/api/v1/analytics/manager", headers={"Authorization": f"Bearer {token_op}"})
    assert res_op_mgr.status_code == status.HTTP_403_FORBIDDEN
