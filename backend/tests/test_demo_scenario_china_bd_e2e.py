from decimal import Decimal
from fastapi.testclient import TestClient


def test_signature_china_bd_demo_full_workflow_e2e(client: TestClient):
    """
    End-to-end test of the complete signature BorderWise AI competition demo journey.
    Scenario: Tanvir Hasan (Tsinghua University, Beijing, China) - Tuition/Living in CNY, Family in BDT.
    Absence of GBP and INR in the active demo workflow.
    Primary transfer direction: CNY -> BDT (1,000 CNY).
    """
    # 0. Clean reset to ensure pristine synthetic baseline
    reset_resp = client.post("/api/v1/demo/reset", json={"scenario": "china"})
    assert reset_resp.status_code == 200
    scenario_data = reset_resp.json()["scenario"]
    assert scenario_data["profile"]["full_name"] == "Tanvir Hasan"
    assert scenario_data["profile"]["study_currency"] == "CNY"
    assert scenario_data["profile"]["home_currency"] == "BDT"
    assert scenario_data["profile"]["study_country"] == "China"
    assert scenario_data["profile"]["home_country"] == "Bangladesh"

    # Step 1 & 2: Student opens dashboard; upcoming obligations and balances shown in CNY & BDT
    overview_resp = client.get("/api/v1/finance/overview")
    assert overview_resp.status_code == 200
    ov = overview_resp.json()
    assert ov["student_name"] == "Tanvir Hasan"
    assert ov["study_currency"] == "CNY"
    assert ov["home_currency"] == "BDT"
    assert float(ov["balances_by_currency"]["CNY"]) == 8500.0
    assert float(ov["balances_by_currency"]["BDT"]) == 350000.0
    assert float(ov["tuition_amount_due"]) == 24000.0
    assert ov["has_funding_gap"] is True
    assert "CNY" in ov["summary_alert"] or "shortfall" in ov["summary_alert"].lower()

    # Verify absence of GBP and INR in active balances
    assert "GBP" not in ov["balances_by_currency"]
    assert "INR" not in ov["balances_by_currency"]

    # Forecast shows timeline events and detects shortfalls mathematically
    forecast_resp = client.post("/api/v1/finance/forecast", json={"forecast_days": 90})
    assert forecast_resp.status_code == 200
    fc = forecast_resp.json()
    assert float(fc["initial_actual_balances"]["CNY"]) == 8500.0
    assert float(fc["initial_actual_balances"]["BDT"]) == 350000.0
    assert len(fc["timeline_events"]) > 0
    assert len(fc["shortfalls"]) > 0

    # Step 3, 4, 5: Student asks whether tuition is affordable; tools invoked; exact math explained
    chat_tuition = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Can I afford my tuition payment next month?"},
    )
    assert chat_tuition.status_code == 200
    t_res = chat_tuition.json()
    tool_names = [tr["tool_name"] for tr in t_res["tool_results"]]
    assert "get_student_overview" in tool_names
    assert "calculate_funding_gap" in tool_names

    # Check that calculation is explained and currency codes are explicit
    msg_t = t_res["message"]
    assert "24,000" in msg_t
    assert "CNY" in msg_t
    assert "BDT" in msg_t
    assert "shortfall" in msg_t.lower() or "gap" in msg_t.lower()
    assert t_res["is_demo_mode"] is True

    # Step 6 & 7: Student asks about sending money across borders; primary transfer CNY -> BDT
    compare_resp = client.post(
        "/api/v1/transfers/compare",
        json={"send_amount": 1000.0, "send_currency": "CNY", "receive_currency": "BDT"},
    )
    assert compare_resp.status_code == 200
    tr_data = compare_resp.json()
    assert len(tr_data["quotes"]) >= 2
    assert tr_data["send_currency"] == "CNY"
    assert tr_data["receive_currency"] == "BDT"

    # Verify provider decomposition: digital specialist delivers more BDT than traditional wire bank
    digital = next(q for q in tr_data["quotes"] if q["provider_type"] == "DIGITAL_SPECIALIST")
    bank = next(q for q in tr_data["quotes"] if q["provider_type"] == "TRADITIONAL_BANK")
    assert float(digital["recipient_amount_receive_currency"]) > float(bank["recipient_amount_receive_currency"])
    assert float(digital["total_fee_cost"]) < float(bank["total_fee_cost"])

    # Explicit quote labels and timestamps
    for quote in tr_data["quotes"]:
        assert quote["quote_provenance"] in ("PROVIDER_PUBLISHED", "SIMULATED")
        assert "T" in quote["quote_timestamp_utc"]

    # Step 8: Assistant answers specific CNY -> BDT question using backend calculations
    chat_transfer = client.post(
        "/api/v1/assistant/chat",
        json={"message": "If I send 1,000 CNY to Bangladesh, how much BDT might the recipient receive after fees?"},
    )
    assert chat_transfer.status_code == 200
    transfer_res = chat_transfer.json()
    msg_trans = transfer_res["message"]
    assert "1,000" in msg_trans
    assert "CNY" in msg_trans
    assert "BDT" in msg_trans
    assert "16," in msg_trans  # ~16,463 BDT recipient proceeds
    assert "DEMO DATA" in msg_trans or "simulated" in msg_trans.lower()

    # Step 9 & 10: Simulated action preview displayed; explicit notice that no money was moved
    assert transfer_res["requires_confirmation"] is True
    assert transfer_res["confirmation_preview"] is not None
    assert "money_movement" in transfer_res["confirmation_preview"]
    assert "No money was moved" in transfer_res["confirmation_preview"]["money_movement"]

    # Advisory notice in warnings
    assert any("no money was moved" in w.lower() for w in transfer_res["warnings"]) or "no money was moved" in msg_trans.lower()


def test_reverse_transfer_bdt_to_cny(client: TestClient):
    """
    Verify reverse transfer direction: BDT -> CNY (e.g. family funding tuition).
    """
    compare_resp = client.post(
        "/api/v1/transfers/compare",
        json={"send_amount": 250000.0, "send_currency": "BDT", "receive_currency": "CNY"},
    )
    assert compare_resp.status_code == 200
    tr_data = compare_resp.json()
    assert tr_data["send_currency"] == "BDT"
    assert tr_data["receive_currency"] == "CNY"
    assert len(tr_data["quotes"]) >= 2

    # Check recipient amount is in CNY
    top_q = tr_data["quotes"][0]
    assert float(top_q["recipient_amount_receive_currency"]) > 10000.0  # ~14,640+ CNY


def test_mathematical_consistency_china_bd_dataset(client: TestClient):
    """
    Verify complete numerical and mathematical consistency across all models in China-BD dataset:
    Liquid CNY: 8,500 + Stipend 3,500 = 12,000 CNY resources.
    Tuition: 24,000 CNY. Living: 3,300 CNY/mo.
    Direct gap: obligations exceed local resources.
    Home BDT DBBL savings: 350,000 BDT + 150,000 BDT = 500,000 BDT.
    """
    client.post("/api/v1/demo/reset", json={"scenario": "china"})
    gap_resp = client.post("/api/v1/finance/funding-gap", json={"horizon_days": 90})
    assert gap_resp.status_code == 200
    gap = gap_resp.json()

    cny_pos = gap["currency_positions"]["CNY"]
    assert float(cny_pos["actual_liquid_balance"]) == 8500.0
    assert float(cny_pos["expected_inflows"]) == 3500.0
    assert float(cny_pos["total_available_resources"]) == 12000.0

    bdt_pos = gap["currency_positions"]["BDT"]
    assert float(bdt_pos["actual_liquid_balance"]) == 350000.0
    assert float(bdt_pos["expected_inflows"]) == 150000.0


def test_default_currencies_and_absence_of_gbp_inr(client: TestClient):
    """
    Verify default transfer and scenario endpoints default to CNY and BDT,
    and active scenario does not present GBP or INR.
    """
    client.post("/api/v1/demo/reset", json={"scenario": "china"})
    overview = client.get("/api/v1/finance/overview").json()
    assert overview["study_currency"] == "CNY"
    assert overview["home_currency"] == "BDT"
    assert "GBP" not in overview["balances_by_currency"]
    assert "INR" not in overview["balances_by_currency"]
