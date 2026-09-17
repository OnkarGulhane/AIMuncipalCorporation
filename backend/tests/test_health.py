from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test that root endpoint returns service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AI Case Manager"
    assert data["version"] == "1.0.0"
    assert "environment" in data
    assert "health" in data
    assert "ready" in data


def test_health_liveness_endpoint(client: TestClient):
    """Test /health liveness probe."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "AI Case Manager"
    assert "timestamp" in data


def test_ready_readiness_endpoint(client: TestClient):
    """Test /ready readiness probe with database verification."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_api_v1_health_endpoint(client: TestClient):
    """Test /api/v1/health endpoint routing."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_api_v1_ready_endpoint(client: TestClient):
    """Test /api/v1/ready endpoint routing."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
