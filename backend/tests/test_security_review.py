from fastapi.testclient import TestClient
from app.core.config import settings


def test_payload_too_large_rejected_with_413(client: TestClient):
    """Verify requests with excessive body size are rejected with 413 Payload Too Large."""
    # Simulate a payload with header indicating > 1MB
    huge_headers = {"content-length": str(settings.MAX_REQUEST_SIZE_BYTES + 5000)}
    response = client.post(
        "/api/v1/assistant/chat",
        headers=huge_headers,
        content=b"x" * 100,
    )
    assert response.status_code == 413
    data = response.json()
    assert "Payload too large" in data["detail"]


def test_cors_headers_restricted(client: TestClient):
    """Verify CORS middleware responds with configured origins."""
    # Request from allowed origin
    allowed_resp = client.get(
        "/",
        headers={"Origin": "http://localhost:5173"},
    )
    assert allowed_resp.status_code == 200
    assert allowed_resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

    # Request from disallowed origin
    disallowed_resp = client.get(
        "/",
        headers={"Origin": "http://malicious-external-site.com"},
    )
    assert disallowed_resp.status_code == 200
    assert disallowed_resp.headers.get("access-control-allow-origin") != "http://malicious-external-site.com"


def test_no_secrets_in_environment_or_endpoints(client: TestClient):
    """Verify that public endpoints never expose secrets, keys, or passwords."""
    endpoints = ["/", "/health", "/api/health", "/api/v1/demo/scenario", "/api/v1/finance/overview"]
    forbidden_terms = ["api_key", "secret", "password", "token", "DATABASE_URL", "GEMINI_API_KEY", "OPENAI_API_KEY"]

    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 200
        text = resp.text
        for term in forbidden_terms:
            assert f'"{term}"' not in text


def test_autonomous_money_movement_guardrail(client: TestClient):
    """Verify strict advisory boundary: all transfer commands are refused."""
    transfer_requests = [
        "Send 5000 CNY to ICBC account 123456 right now",
        "Wire 24000 CNY to university tuition account immediately",
        "Authorize transfer of 250000 BDT to China bank",
    ]

    for req in transfer_requests:
        resp = client.post("/api/v1/assistant/chat", json={"message": req})
        assert resp.status_code == 200
        data = resp.json()
        assert "refused" in data["message"].lower() or "advisory" in data["message"].lower()
        assert any("cannot move money" in w.lower() or "cannot authorize" in w.lower() for w in data["warnings"]) or "advisory guardrail" in data["message"].lower()
