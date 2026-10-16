from decimal import Decimal
from fastapi.testclient import TestClient
from app.services.financial_calc import (
    compare_transfer_providers,
    calculate_runway_months,
    round_money,
    get_mid_market_rate,
)
from app.schemas.common import SupportedCurrency


def test_decimal_rounding_precision():
    """Verify monetary rounding conforms to half-up standards."""
    assert round_money(Decimal("100.004")) == Decimal("100.00")
    assert round_money(Decimal("100.005")) == Decimal("100.01")
    assert round_money(Decimal("100.006")) == Decimal("100.01")


def test_mid_market_rates():
    """Verify synthetic rates are positive and consistent."""
    rate = get_mid_market_rate("INR", "USD")
    assert rate == Decimal("0.0120")
    same_rate = get_mid_market_rate("USD", "USD")
    assert same_rate == Decimal("1.0000")


def test_transfer_comparison_calculation():
    """Verify transfer comparison returns structured quotes and positive savings."""
    send_amount = Decimal("100000.00")  # 100,000 INR
    result = compare_transfer_providers(
        send_amount=send_amount,
        send_currency=SupportedCurrency.INR,
        receive_currency=SupportedCurrency.USD,
    )
    assert result.send_amount == send_amount
    assert len(result.quotes) >= 3
    # Check that Digital FX delivers more USD than traditional bank due to lower fees and markup
    quotes_by_name = {q.provider_name: q for q in result.quotes}
    traditional = quotes_by_name["Global Wire Bank (Traditional)"]
    alipay = quotes_by_name["Alipay / Digital FX Specialist"]

    assert alipay.amount_received > traditional.amount_received
    assert alipay.total_cost < traditional.total_cost
    assert result.potential_savings > Decimal("0.00")


def test_transfer_comparison_cny_bdt_corridor():
    """Verify primary demo corridor CNY -> BDT and BDT -> CNY comparisons."""
    # 1. 1,000 CNY -> BDT
    res_cny = compare_transfer_providers(
        send_amount=Decimal("1000.00"),
        send_currency=SupportedCurrency.CNY,
        receive_currency=SupportedCurrency.BDT,
    )
    assert res_cny.send_amount == Decimal("1000.00")
    assert res_cny.potential_savings > Decimal("0.00")
    q_by_name = {q.provider_name: q for q in res_cny.quotes}
    assert q_by_name["Alipay / Digital FX Specialist"].amount_received > q_by_name["Global Wire Bank (Traditional)"].amount_received

    # 2. 250,000 BDT -> CNY
    res_bdt = compare_transfer_providers(
        send_amount=Decimal("250000.00"),
        send_currency=SupportedCurrency.BDT,
        receive_currency=SupportedCurrency.CNY,
    )
    assert res_bdt.send_amount == Decimal("250000.00")
    assert res_bdt.potential_savings > Decimal("0.00")



def test_runway_calculation():
    """Verify runway calculation logic."""
    # Available: $15,000, Tuition: $5,000, Monthly Burn: $2,000 => (15,000 - 5,000) / 2,000 = 5.0 months
    runway = calculate_runway_months(
        available_destination_funds=Decimal("15000.00"),
        remaining_tuition_due=Decimal("5000.00"),
        monthly_living_burn=Decimal("2000.00"),
    )
    assert runway == Decimal("5.0")

    # If burn is 0 or negative funds
    runway_zero = calculate_runway_months(
        available_destination_funds=Decimal("3000.00"),
        remaining_tuition_due=Decimal("5000.00"),
        monthly_living_burn=Decimal("1000.00"),
    )
    assert runway_zero == Decimal("0.0")


def test_api_compare_transfers_endpoint(client: TestClient):
    """Verify POST /api/v1/calculator/compare-transfers returns 200 OK and valid schema."""
    payload = {
        "send_amount": 50000.0,
        "send_currency": "INR",
        "receive_currency": "USD",
    }
    response = client.post("/api/v1/calculator/compare-transfers", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["send_currency"] == "INR"
    assert data["receive_currency"] == "USD"
    assert len(data["quotes"]) >= 3
    assert "recommended_provider" in data
    assert "potential_savings" in data
