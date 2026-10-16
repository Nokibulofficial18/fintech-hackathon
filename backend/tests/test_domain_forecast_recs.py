from datetime import date
from decimal import Decimal
import pytest
from app.schemas.profile import FullStudentScenario, StudentProfileData, AccountBalance, TuitionObligation
from app.schemas.common import SupportedCurrency
from app.services.demo_scenario_service import get_seeded_demo_scenario
from app.services.forecast_service import generate_cash_flow_forecast
from app.services.recommendation_service import generate_recommendations
from app.schemas.recommendations import RecommendationPriority, RecommendationUrgency


def test_forecast_distinguishes_actual_from_projected():
    """Verify that starting balances are actual verified values and timeline events are projected."""
    scenario = get_seeded_demo_scenario("us")
    res = generate_cash_flow_forecast(scenario, start_date=date(2026, 10, 15), horizon_days=90)

    # Initial actual balances matches verified scenario inputs
    assert res.initial_actual_balances["USD"] == Decimal("4200.00")
    assert res.initial_actual_balances["INR"] == Decimal("650000.00")

    # Timeline events must be marked as projected
    assert len(res.timeline_events) > 0
    for evt in res.timeline_events:
        assert evt.is_projected is True

    # Horizon is 90 days
    assert (res.forecast_end_date - res.forecast_start_date).days == 90


def test_forecast_detects_shortfall_event():
    """Verify that when tuition hits without enough USD, a discrete shortfall event is registered."""
    scenario = get_seeded_demo_scenario("us")
    # In Aarav's scenario, without remittance clearance, tuition on Nov 15 exceeds USD balance.
    res = generate_cash_flow_forecast(scenario, start_date=date(2026, 10, 15), horizon_days=90)

    # Notice: planned remittance of 500,000 INR arrives Oct 27 (~$5,950).
    # Checking: 4,200 + 1,200 (TA Oct) - 1,400 (Rent Nov) + 3,000 (Scholarship Nov 1) + 5,950 (Remittance) = ~12,950 USD.
    # Tuition is $14,500 due Nov 15. $12,950 - $14,500 = -$1,550 shortfall!
    assert len(res.shortfalls) > 0
    first_shortfall = res.shortfalls[0]
    assert first_shortfall.currency == SupportedCurrency.USD
    assert first_shortfall.shortfall_amount > Decimal("0.00")
    assert first_shortfall.shortfall_date >= date(2026, 10, 15)
    assert first_shortfall.urgency in ("CRITICAL", "HIGH", "MEDIUM")


def test_recommendation_engine_outputs_prioritized_items():
    """Verify deterministic recommendations contain quantitative evidence and no investment advice."""
    scenario = get_seeded_demo_scenario("us")
    recs_resp = generate_recommendations(scenario, reference_date=date(2026, 10, 15))

    assert recs_resp.total_recommendations >= 3
    assert recs_resp.critical_count >= 1

    # First item must be CRITICAL
    top_rec = recs_resp.recommendations[0]
    assert top_rec.priority == RecommendationPriority.CRITICAL
    assert len(top_rec.supporting_numbers) > 0
    assert len(top_rec.assumptions) > 0
    assert top_rec.uncertainty != ""
    assert top_rec.suggested_action != ""

    # Must contain compliance disclaimer
    assert "not provide investment advice" in recs_resp.compliance_disclaimer.lower()


def test_china_bd_recommendations_and_compliance():
    """Verify that China-Bangladesh scenario recommendations cite Bangladesh Bank Student File regulations."""
    scenario = get_seeded_demo_scenario("china")
    recs_resp = generate_recommendations(scenario, reference_date=date(2026, 10, 15))

    rec_texts = " ".join([r.title + " " + r.reason + " " + r.uncertainty + " " + r.suggested_action for r in recs_resp.recommendations])
    # Must cite Bangladesh Bank Student File / Form TM and China SAFE inward regulations
    assert "Bangladesh Bank" in rec_texts
    assert "Student File" in rec_texts
    assert "SAFE" in rec_texts or "State Administration of Foreign Exchange" in rec_texts
    assert "BDT" in rec_texts
    assert "CNY" in rec_texts


def test_deterministic_mock_copilot_china_bd():
    """Verify mock copilot adapter generates valid China-Bangladesh guidance with zero API keys."""
    from app.ai.mock_copilot import DeterministicMockCopilot
    copilot = DeterministicMockCopilot()
    resp = copilot.generate_financial_advice({
        "home_currency": "BDT",
        "destination_currency": "CNY",
        "university_name": "Tsinghua University",
        "runway_months": 2.6,
    })
    assert resp["engine"] == "Deterministic Heuristic Copilot (Offline Safe)"
    assert resp["recommendations_count"] >= 2
    summaries = " ".join([i["summary"] for i in resp["insights"]])
    assert "CNY" in summaries
    assert "BDT" in summaries
    assert "1,800 BDT" in summaries or "wire" in summaries.lower()


