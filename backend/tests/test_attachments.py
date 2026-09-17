import io
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.case import Case, CaseStatus, CasePriority
from app.models.user import UserRole
from app.schemas.organization import DepartmentCreate, CategoryCreate
from app.schemas.user import UserCreate
from app.services.organization_service import organization_service
from app.services.user_service import user_service


@pytest.fixture
def attachment_test_env(db_session: Session):
    """Set up test users, department, and category for attachment tests."""
    c1 = user_service.create_user(
        db_session,
        user_in=UserCreate(email="citizen_att@test.com", password="Password123", full_name="Aarav Citizen"),
        forced_role=UserRole.REQUESTER,
    )
    t1 = create_access_token(subject=c1.id, role=c1.role)

    c2 = user_service.create_user(
        db_session,
        user_in=UserCreate(email="other_citizen_att@test.com", password="Password123", full_name="Other Citizen"),
        forced_role=UserRole.REQUESTER,
    )
    t2 = create_access_token(subject=c2.id, role=c2.role)

    op = user_service.create_user(
        db_session,
        user_in=UserCreate(email="operator_att@test.com", password="Password123", full_name="Rohan Operator"),
        forced_role=UserRole.OPERATOR,
    )
    top = create_access_token(subject=op.id, role=op.role)

    dept = organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(name="Sanitation Dept", code="SANITATION_ATT", description="Sanitation test"),
    )
    cat = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(
            name="Garbage Overflow",
            code="GARBAGE_ATT",
            department_id=dept.id,
            default_priority="medium",
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


def test_attachment_upload_and_download(
    client: TestClient,
    db_session: Session,
    attachment_test_env: dict,
):
    """Test citizen uploading photo evidence and downloading it."""
    citizen = attachment_test_env["citizen1"]
    token_citizen = attachment_test_env["token1"]
    token_c2 = attachment_test_env["token2"]

    # 1. Create a case
    case = Case(
        case_number="MC-2026-ATT01",
        title="Overflowing Dumpster on Park Road",
        description="Waste bin is completely full.",
        citizen_id=citizen.id,
        status=CaseStatus.REPORTED.value,
        priority=CasePriority.MEDIUM.value,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # 2. Upload a test image file
    fake_image_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtest_image_data_bytes_12345"
    files = {
        "file": ("dumpster_photo.png", io.BytesIO(fake_image_content), "image/png"),
    }
    data = {
        "description": "Photo of overflowing dumpster taken at 9 AM.",
        "is_public_to_citizen": "true",
    }

    resp = client.post(
        f"/api/v1/cases/{case.id}/attachments",
        headers={"Authorization": f"Bearer {token_citizen}"},
        files=files,
        data=data,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    att_data = resp.json()
    assert att_data["original_filename"] == "dumpster_photo.png"
    assert att_data["file_size"] == len(fake_image_content)
    assert att_data["content_type"] == "image/png"
    assert att_data["description"] == data["description"]
    attachment_id = att_data["id"]

    # 3. List attachments
    list_resp = client.get(
        f"/api/v1/cases/{case.id}/attachments",
        headers={"Authorization": f"Bearer {token_citizen}"},
    )
    assert list_resp.status_code == status.HTTP_200_OK
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["id"] == attachment_id

    # 4. Download file
    dl_resp = client.get(
        f"/api/v1/cases/{case.id}/attachments/{attachment_id}/download",
        headers={"Authorization": f"Bearer {token_citizen}"},
    )
    assert dl_resp.status_code == status.HTTP_200_OK
    assert dl_resp.content == fake_image_content

    # 5. Another citizen attempts to download file -> 403 Forbidden
    dl_unauth = client.get(
        f"/api/v1/cases/{case.id}/attachments/{attachment_id}/download",
        headers={"Authorization": f"Bearer {token_c2}"},
    )
    assert dl_unauth.status_code == status.HTTP_403_FORBIDDEN


def test_disallowed_file_extension(
    client: TestClient,
    db_session: Session,
    attachment_test_env: dict,
):
    """Test uploading an executable or unsupported file extension is rejected."""
    citizen = attachment_test_env["citizen1"]
    token_citizen = attachment_test_env["token1"]

    case = Case(
        case_number="MC-2026-ATT02",
        title="Pothole complaint",
        description="Road surface broken.",
        citizen_id=citizen.id,
        status=CaseStatus.REPORTED.value,
        priority=CasePriority.LOW.value,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Disallowed .exe file
    bad_files = {
        "file": ("malicious_payload.exe", io.BytesIO(b"MZ\x90\x00executable"), "application/octet-stream"),
    }
    resp = client.post(
        f"/api/v1/cases/{case.id}/attachments",
        headers={"Authorization": f"Bearer {token_citizen}"},
        files=bad_files,
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "not supported" in resp.json()["detail"].lower()


def test_attachment_delete(
    client: TestClient,
    db_session: Session,
    attachment_test_env: dict,
):
    """Test deleting an uploaded attachment."""
    citizen = attachment_test_env["citizen1"]
    token_citizen = attachment_test_env["token1"]

    case = Case(
        case_number="MC-2026-ATT03",
        title="Broken bench in public garden",
        description="Bench damaged.",
        citizen_id=citizen.id,
        status=CaseStatus.REPORTED.value,
        priority=CasePriority.LOW.value,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Upload file
    files = {
        "file": ("bench.jpg", io.BytesIO(b"\xff\xd8\xff\xe0test_jpg_data"), "image/jpeg"),
    }
    resp = client.post(
        f"/api/v1/cases/{case.id}/attachments",
        headers={"Authorization": f"Bearer {token_citizen}"},
        files=files,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    attachment_id = resp.json()["id"]

    # Delete file
    del_resp = client.delete(
        f"/api/v1/cases/{case.id}/attachments/{attachment_id}",
        headers={"Authorization": f"Bearer {token_citizen}"},
    )
    assert del_resp.status_code == status.HTTP_200_OK

    # Verify listing is now empty
    list_resp = client.get(
        f"/api/v1/cases/{case.id}/attachments",
        headers={"Authorization": f"Bearer {token_citizen}"},
    )
    assert list_resp.status_code == status.HTTP_200_OK
    assert len(list_resp.json()) == 0
