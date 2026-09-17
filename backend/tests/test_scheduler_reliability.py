import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.case import Case, CaseStatus, CasePriority, CaseSeverity
from app.models.sla import CaseSLA, SLAStatus
from app.models.escalation import CaseEscalation
from app.schemas.user import UserCreate
from app.services.user_service import user_service
from app.services.sla_service import evaluate_single_case_sla, initialize_or_update_case_sla
from app.core.scheduler import sweep_slas_and_risks_sync


@pytest.fixture
def scheduler_test_env(db_session: Session):
    citizen = user_service.create_user(
        db_session,
        user_in=UserCreate(email="citizen_sched@test.com", password="Password123", full_name="Omkar Citizen", ward="Ward 02"),
        forced_role=UserRole.REQUESTER,
    )
    admin = user_service.create_user(
        db_session,
        user_in=UserCreate(email="admin_sched@test.com", password="Password123", full_name="Admin Sched", ward="Ward 02"),
        forced_role=UserRole.ADMINISTRATOR,
    )
    operator = user_service.create_user(
        db_session,
        user_in=UserCreate(email="operator_sched@test.com", password="Password123", full_name="Operator Sched", ward="Ward 02"),
        forced_role=UserRole.OPERATOR,
    )
    db_session.commit()

    return {
        "citizen": citizen,
        "admin": admin,
        "operator": operator,
        "token_admin": create_access_token(subject=admin.id, role=admin.role),
        "token_operator": create_access_token(subject=operator.id, role=operator.role),
    }


def test_batch_sla_and_risk_evaluation_logic(db_session: Session, scheduler_test_env: dict):
    citizen = scheduler_test_env["citizen"]
    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. Compliant Case
    case_ok = Case(
        case_number="MC-2026-7001",
        title="Normal street cleaning",
        description="Daily sweeping request",
        citizen_id=citizen.id,
        status=CaseStatus.ASSIGNED.value,
        priority=CasePriority.LOW.value,
        severity=CaseSeverity.MINOR.value,
    )
    db_session.add(case_ok)
    db_session.commit()
    sla_ok = CaseSLA(
        case_id=case_ok.id,
        response_target_hours=8,
        resolution_target_hours=48,
        response_due_at=now + datetime.timedelta(hours=6),
        resolution_due_at=now + datetime.timedelta(hours=40),
        response_status=SLAStatus.WITHIN_TARGET.value,
        resolution_status=SLAStatus.WITHIN_TARGET.value,
    )
    db_session.add(sla_ok)

    # 2. At-Risk Case (Resolution deadline in 1 hour)
    case_risk = Case(
        case_number="MC-2026-7002",
        title="Water contamination complaint",
        description="Brown water coming from residential line",
        citizen_id=citizen.id,
        status=CaseStatus.ASSIGNED.value,
        priority=CasePriority.HIGH.value,
        severity=CaseSeverity.MAJOR.value,
    )
    db_session.add(case_risk)
    db_session.commit()
    sla_risk = CaseSLA(
        case_id=case_risk.id,
        response_target_hours=2,
        resolution_target_hours=12,
        response_due_at=now - datetime.timedelta(hours=1),
        resolution_due_at=now + datetime.timedelta(minutes=30),
        response_status=SLAStatus.WITHIN_TARGET.value,
        resolution_status=SLAStatus.WITHIN_TARGET.value,
    )
    db_session.add(sla_risk)

    # 3. Breached Case (Resolution deadline expired 5 hours ago)
    case_breached = Case(
        case_number="MC-2026-7003",
        title="Unattended open trench",
        description="Dangerous unbarricaded excavation",
        citizen_id=citizen.id,
        status=CaseStatus.ASSIGNED.value,
        priority=CasePriority.CRITICAL.value,
        severity=CaseSeverity.CRITICAL.value,
    )
    db_session.add(case_breached)
    db_session.commit()
    sla_breached = CaseSLA(
        case_id=case_breached.id,
        response_target_hours=1,
        resolution_target_hours=6,
        response_due_at=now - datetime.timedelta(hours=10),
        resolution_due_at=now - datetime.timedelta(hours=5),
        response_status=SLAStatus.WITHIN_TARGET.value,
        resolution_status=SLAStatus.WITHIN_TARGET.value,
    )
    db_session.add(sla_breached)
    db_session.commit()

    # Evaluate each case individually
    eval_ok = evaluate_single_case_sla(db_session, case_ok, sla_ok)
    eval_risk = evaluate_single_case_sla(db_session, case_risk, sla_risk)
    eval_breached = evaluate_single_case_sla(db_session, case_breached, sla_breached)

    assert eval_ok.resolution_status == SLAStatus.WITHIN_TARGET.value
    assert eval_risk.resolution_status in [SLAStatus.APPROACHING_BREACH.value, SLAStatus.BREACHED.value]
    assert eval_breached.resolution_status == SLAStatus.BREACHED.value
    assert eval_breached.is_breached is True


def test_scheduler_sweep_endpoint_execution(client: TestClient, scheduler_test_env: dict):
    t_adm = scheduler_test_env["token_admin"]

    res = client.post(
        "/api/v1/automation/sweep-slas-and-risks",
        headers={"Authorization": f"Bearer {t_adm}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "completed" in data["message"].lower()
