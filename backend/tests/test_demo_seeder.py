import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.case import Case
from app.models.organization import Department, Category, Team
from scripts.seed_demo_data import seed_demo_database


def test_demo_seeder_execution_and_idempotency(db_session: Session):
    """Verify that the demo seeder runs successfully and idempotently."""
    # First execution
    seed_demo_database(db=db_session)

    # Verify counts in database
    dept_count = db_session.query(Department).count()
    cat_count = db_session.query(Category).count()
    team_count = db_session.query(Team).count()
    user_count = db_session.query(User).filter(User.email.like("%@demo.city.gov")).count()
    case_count = db_session.query(Case).filter(Case.case_number.like("MC-2026-100%")).count()

    assert dept_count >= 5
    assert cat_count >= 10
    assert team_count >= 3
    assert user_count == 5
    assert case_count == 5

    # Second execution to verify idempotency
    seed_demo_database(db=db_session)
    assert db_session.query(User).filter(User.email.like("%@demo.city.gov")).count() == 5
    assert db_session.query(Case).filter(Case.case_number.like("MC-2026-100%")).count() == 5


def test_all_5_demo_users_authentication(client: TestClient, db_session: Session):
    """Verify that all 5 seeded demo roles can authenticate via standard login API."""
    seed_demo_database(db=db_session)

    demo_emails = [
        ("citizen@demo.city.gov", UserRole.REQUESTER.value),
        ("operator@demo.city.gov", UserRole.OPERATOR.value),
        ("teamlead@demo.city.gov", UserRole.TEAM_LEAD.value),
        ("manager@demo.city.gov", UserRole.MANAGER.value),
        ("admin@demo.city.gov", UserRole.ADMINISTRATOR.value),
    ]

    for email, expected_role in demo_emails:
        res = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123"},
        )
        assert res.status_code == 200, f"Failed to login demo user: {email}"
        token_data = res.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert token_data["user"]["role"] == expected_role


def test_demo_cases_and_manager_analytics(client: TestClient, db_session: Session):
    """Verify that manager dashboard receives populated metrics from seeded cases."""
    seed_demo_database(db=db_session)

    # Login as manager
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "manager@demo.city.gov", "password": "Password123"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Retrieve manager dashboard analytics
    analytics_res = client.get(
        "/api/v1/analytics/manager",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert analytics_res.status_code == 200
    data = analytics_res.json()
    assert data["total_cases"] >= 5
    assert "department_metrics" in data
    assert "ward_metrics" in data
    assert "ai_operational_insights" in data
