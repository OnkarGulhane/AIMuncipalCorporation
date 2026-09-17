import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings


def test_security_headers_present_on_all_responses(client: TestClient):
    """Verify production security headers are attached to responses."""
    res = client.get("/health")
    assert res.status_code == 200
    headers = res.headers

    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_health_and_readiness_probes(client: TestClient):
    """Verify container orchestrator health and readiness endpoints."""
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    ready_res = client.get("/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["status"] in ["ready", "ok"]
    assert ready_res.json()["database"] in ["connected", "ok"]


def test_root_endpoint_metadata(client: TestClient):
    """Verify root API metadata and documentation toggle."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] is not None
    assert data["version"] is not None
    assert "health" in data
    assert "ready" in data


def test_cors_origin_resolution():
    """Verify CORS origin parsing from strings and JSON lists."""
    s1 = Settings(CORS_ORIGINS="https://city.gov, https://admin.city.gov")
    assert "https://city.gov" in s1.CORS_ORIGINS
    assert "https://admin.city.gov" in s1.CORS_ORIGINS

    s2 = Settings(CORS_ORIGINS=["https://grievance.city.gov"])
    assert s2.CORS_ORIGINS == ["https://grievance.city.gov"]


def test_production_jwt_secret_guard():
    """Verify that production mode rejects default development secrets."""
    # Development mode accepts default
    dev_settings = Settings(ENVIRONMENT="development", JWT_SECRET_KEY="development_jwt_secret_key_minimum_32_characters_long_12345")
    assert dev_settings.is_production is False

    # Production mode rejects default secret
    with pytest.raises(ValueError, match="Production requires a strong, randomly generated JWT_SECRET_KEY"):
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY="development_jwt_secret_key_minimum_32_characters_long_12345")

    # Production mode rejects short secrets
    with pytest.raises(ValueError, match="Production JWT_SECRET_KEY must be at least 32 characters long"):
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY="short_prod_secret")

    # Production mode accepts strong 32+ character secrets
    prod_valid = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a_very_strong_secure_production_secret_key_64_bytes_entropy_token",
    )
    assert prod_valid.is_production is True
