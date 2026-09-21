import io
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.organization import Department, Category
from app.models.user import UserRole
from app.schemas.organization import DepartmentCreate, CategoryCreate
from app.schemas.user import UserCreate
from app.services.organization_service import organization_service
from app.services.user_service import user_service


@pytest.fixture
def vision_test_env(db_session: Session):
    citizen = user_service.create_user(
        db_session,
        user_in=UserCreate(
            email="vision_citizen@test.com",
            password="Password123",
            full_name="Pooja Sharma",
            ward="Ward 12",
        ),
        forced_role=UserRole.REQUESTER,
    )
    token_citizen = create_access_token(subject=citizen.id, role=citizen.role)

    dept_roads = organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(name="Roads & Infrastructure", code="ROADS_VIS", description="Roads dept"),
    )
    cat_potholes = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(
            name="Potholes & Road Damage",
            code="POTHOLES",
            department_id=dept_roads.id,
            default_priority="high",
            sla_hours=24,
        ),
    )

    dept_waste = organization_service.create_department(
        db_session,
        dept_in=DepartmentCreate(name="Solid Waste Management", code="WASTE_VIS", description="Waste dept"),
    )
    cat_waste = organization_service.create_category(
        db_session,
        cat_in=CategoryCreate(
            name="Garbage Dump & Waste Overflow",
            code="GARBAGE_OVERFLOW",
            department_id=dept_waste.id,
            default_priority="high",
            sla_hours=12,
        ),
    )

    return {
        "citizen": citizen,
        "token_citizen": token_citizen,
        "cat_potholes": cat_potholes,
        "cat_waste": cat_waste,
    }


def test_vision_triage_json_pothole(
    client: TestClient,
    vision_test_env: dict,
):
    """Test AI Vision triage with JSON payload detecting pothole road damage."""
    token = vision_test_env["token_citizen"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "filename": "pothole_on_main_crossroad.jpg",
        "landmark_hint": "Opposite City Bank ATM, MG Road",
        "voice_note": "huge crater on the road causing traffic jams",
    }

    resp = client.post("/api/v1/cases/ai/vision-triage", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["detected_issue"] == "POTHOLES"
    assert data["category_code"] == "POTHOLES"
    assert data["suggested_priority"] in ["high", "critical"]
    assert "pothole" in data["suggested_title"].lower() or "crater" in data["suggested_title"].lower()
    assert len(data["suggested_description"]) > 40
    assert data["confidence_score"] >= 0.90
    assert "pothole" in data["visual_tags"]
    assert data["landmark_inferred"] == "Opposite City Bank ATM, MG Road"


def test_vision_triage_json_garbage(
    client: TestClient,
    vision_test_env: dict,
):
    """Test AI Vision triage detecting garbage overflow."""
    token = vision_test_env["token_citizen"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "filename": "overflowing_garbage_bin_near_park.png",
        "landmark_hint": "Near Shivaji Park Gate 2",
    }

    resp = client.post("/api/v1/cases/ai/vision-triage", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["detected_issue"] == "GARBAGE_OVERFLOW"
    assert data["category_code"] == "GARBAGE_OVERFLOW"
    assert "garbage" in data["suggested_title"].lower() or "waste" in data["suggested_title"].lower()
    assert "sanitation" in data["recommended_action"].lower() or "compactor" in data["recommended_action"].lower()


def test_vision_triage_upload_multipart(
    client: TestClient,
    vision_test_env: dict,
):
    """Test AI Vision triage with direct file upload via multipart/form-data."""
    token = vision_test_env["token_citizen"]
    headers = {"Authorization": f"Bearer {token}"}

    # Simulate camera image byte content
    fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb" * 50
    files = {
        "file": ("camera_snap_water_pipe_leak.jpg", io.BytesIO(fake_image_bytes), "image/jpeg"),
    }
    data = {
        "landmark_hint": "Near Water Tank Road",
        "gps_latitude": "18.5204",
        "gps_longitude": "73.8567",
    }

    resp = client.post(
        "/api/v1/cases/ai/vision-triage-upload",
        files=files,
        data=data,
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    result = resp.json()

    assert result["detected_issue"] == "WATER_LEAK"
    assert "water" in result["suggested_title"].lower() or "leak" in result["suggested_title"].lower()
    assert result["confidence_score"] >= 0.90
    assert result["landmark_inferred"] == "Near Water Tank Road"
