from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verify that root endpoint responds with service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "BorderWise AI"
    assert data["status"] == "online"
    assert "health_check" in data


def test_top_level_health_endpoint(client: TestClient):
    """Verify the /health probe returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["app_name"] == "BorderWise AI"
    assert "timestamp_utc" in data


def test_api_v1_health_endpoint(client: TestClient):
    """Verify the versioned /api/v1/health endpoint returns 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["environment"] == "development"
