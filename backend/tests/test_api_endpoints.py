from fastapi.testclient import TestClient


def test_api_health_endpoint(client: TestClient):
    """Verify GET /api/health returns 200 OK and diagnostic metadata."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "BorderWise AI"
    assert data["database"] == "connected"


def test_demo_scenario_endpoint(client: TestClient):
    """Verify GET /api/v1/demo/scenario returns signature China student profile Tanvir Hasan."""
    # Ensure active scenario is reset to China
    reset_resp = client.post("/api/v1/demo/reset", json={"scenario": "china"})
    assert reset_resp.status_code == 200

    response = client.get("/api/v1/demo/scenario")
    assert response.status_code == 200
    data = response.json()
    assert data["is_synthetic_demo"] is True
    assert data["profile"]["full_name"] == "Tanvir Hasan"
    assert data["profile"]["home_currency"] == "BDT"
    assert data["profile"]["study_currency"] == "CNY"
    assert len(data["available_balances"]) >= 2
    assert len(data["tuition_obligations"]) >= 1


def test_demo_reset_and_selection_endpoint(client: TestClient):
    """Verify POST /api/v1/demo/reset reliably switches and reproduces scenarios."""
    # Switch to US student
    resp_us = client.post("/api/v1/demo/reset", json={"scenario": "us"})
    assert resp_us.status_code == 200
    us_data = resp_us.json()["scenario"]
    assert us_data["profile"]["full_name"] == "Aarav Sharma"
    assert us_data["profile"]["study_currency"] == "USD"

    # Reset back to China student
    resp_china = client.post("/api/v1/demo/reset", json={"scenario": "china"})
    assert resp_china.status_code == 200
    china_data = resp_china.json()["scenario"]
    assert china_data["profile"]["full_name"] == "Tanvir Hasan"
    assert china_data["profile"]["study_currency"] == "CNY"


def test_finance_overview_endpoint(client: TestClient):
    """Verify GET /api/v1/finance/overview returns summary statistics and separated balances."""
    client.post("/api/v1/demo/reset", json={"scenario": "china"})
    response = client.get("/api/v1/finance/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["student_name"] == "Tanvir Hasan"
    assert "CNY" in data["balances_by_currency"]
    assert "BDT" in data["balances_by_currency"]
    assert float(data["tuition_amount_due"]) == 24000.0
    assert "summary_alert" in data


def test_finance_forecast_endpoint(client: TestClient):
    """Verify POST /api/v1/finance/forecast returns 90-day multi-currency projection."""
    client.post("/api/v1/demo/reset", json={"scenario": "china"})
    response = client.post("/api/v1/finance/forecast", json={"forecast_days": 90})
    assert response.status_code == 200
    data = response.json()
    assert data["horizon_days"] == 90
    assert len(data["timeline_events"]) > 0
    assert "CNY" in data["initial_actual_balances"]
    assert "assumptions" in data
    assert data["data_completeness"]["completeness_score"] == 1.0


def test_finance_funding_gap_endpoint(client: TestClient):
    """Verify POST /api/v1/finance/funding-gap returns separated currencies and gap analysis."""
    client.post("/api/v1/demo/reset", json={"scenario": "china"})
    response = client.post("/api/v1/finance/funding-gap", json={"horizon_days": 90})
    assert response.status_code == 200
    data = response.json()
    assert data["horizon_days"] == 90
    assert data["study_currency"] == "CNY"
    assert data["home_currency"] == "BDT"
    assert "CNY" in data["currency_positions"]
    assert "BDT" in data["currency_positions"]
    assert data["target_currency_has_shortfall"] is True
    assert data["summary_status"] in ("COVERABLE_VIA_TRANSFER", "CRITICAL_DEFICIT", "FULLY_FUNDED")


def test_transfers_compare_endpoint(client: TestClient):
    """Verify POST /api/v1/transfers/compare returns decomposed provider quotes for CNY -> BDT."""
    response = client.post(
        "/api/v1/transfers/compare",
        json={
            "send_amount": 1000.0,
            "send_currency": "CNY",
            "receive_currency": "BDT",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert float(data["send_amount"]) == 1000.0
    assert data["send_currency"] == "CNY"
    assert data["receive_currency"] == "BDT"
    assert len(data["quotes"]) >= 2
    assert "recommended_cheapest" in data
    assert "quotes_timestamp_utc" in data
    for quote in data["quotes"]:
        assert "quote_provenance" in quote
        assert "offered_exchange_rate" in quote
        assert float(quote["total_fee_cost"]) >= 0


def test_recommendations_endpoint(client: TestClient):
    """Verify GET /api/v1/recommendations returns prioritized actions with uncertainty and assumptions."""
    client.post("/api/v1/demo/reset", json={"scenario": "china"})
    response = client.get("/api/v1/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert data["total_recommendations"] > 0
    assert len(data["recommendations"]) > 0
    for rec in data["recommendations"]:
        assert "priority" in rec
        assert "title" in rec
        assert "reason" in rec
        assert "assumptions" in rec
        assert "uncertainty" in rec
