from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
import pytest
from app.schemas.common import SupportedCurrency, DatedFXQuote, QuoteProvenance
from app.schemas.profile import (
    FullStudentScenario,
    StudentProfileData,
    AccountBalance,
    ExpectedIncome,
    LivingExpenseItem,
    TuitionObligation,
    PlannedRemittance,
)
from app.services.demo_scenario_service import get_seeded_demo_scenario
from app.services.funding_gap_service import analyze_funding_gap
from app.services.forecast_service import evaluate_data_completeness


def test_currencies_are_never_silently_combined():
    """Verify that funds in BDT and CNY are kept completely distinct in single currency positions."""
    scenario = get_seeded_demo_scenario("china")
    result = analyze_funding_gap(scenario, horizon_days=90, as_of_date=date(2026, 10, 15))

    # Positions dictionary must separate BDT from CNY
    assert "BDT" in result.currency_positions
    assert "CNY" in result.currency_positions

    bdt_pos = result.currency_positions["BDT"]
    cny_pos = result.currency_positions["CNY"]

    assert bdt_pos.currency == SupportedCurrency.BDT
    assert cny_pos.currency == SupportedCurrency.CNY

    # Balances must not be summed together into a single number
    assert bdt_pos.actual_liquid_balance == Decimal("350000.00")
    assert cny_pos.actual_liquid_balance == Decimal("8500.00")


def test_funding_gap_detected_with_tuition():
    """Verify that a tuition obligation in CNY exceeding liquid study funds triggers a direct target shortfall."""
    scenario = get_seeded_demo_scenario("china")
    result = analyze_funding_gap(scenario, horizon_days=90, as_of_date=date(2026, 10, 15))

    # In our demo, tuition is ¥24,000 + living expenses = direct CNY shortfall exists
    assert result.target_currency_has_shortfall is True
    assert result.target_currency_shortfall_amount > Decimal("0.00")

    # Home currency BDT has 350,000 balance + 150,000 deposit = 500,000 BDT surplus
    # Cross currency remedy must evaluate whether this surplus can cover the CNY gap
    assert result.cross_currency_remedy is not None
    assert result.cross_currency_remedy.source_currency == SupportedCurrency.BDT
    assert result.cross_currency_remedy.target_currency == SupportedCurrency.CNY
    assert result.cross_currency_remedy.dated_fx_quote.rate == Decimal("0.059347")


def test_zero_balances_edge_case():
    """Verify system handles a student starting with 0 liquid balances without crashing."""
    scenario = FullStudentScenario(
        profile=StudentProfileData(study_currency=SupportedCurrency.USD),
        available_balances=[
            AccountBalance(
                account_name="Empty Checking",
                currency=SupportedCurrency.USD,
                actual_balance=Decimal("0.00"),
                as_of_date=date(2026, 10, 15),
            ),
            AccountBalance(
                account_name="Empty Home Account",
                currency=SupportedCurrency.INR,
                actual_balance=Decimal("0.00"),
                as_of_date=date(2026, 10, 15),
            ),
        ],
        expected_income=[],
        monthly_living_expenses=[
            LivingExpenseItem(
                category="Rent",
                monthly_amount=Decimal("1000.00"),
                currency=SupportedCurrency.USD,
            )
        ],
        tuition_obligations=[
            TuitionObligation(
                term="Fall 2026",
                amount_due=Decimal("5000.00"),
                currency=SupportedCurrency.USD,
                due_date=date(2026, 11, 1),
            )
        ],
        planned_remittances=[],
    )

    result = analyze_funding_gap(scenario, horizon_days=60, as_of_date=date(2026, 10, 15))
    assert result.target_currency_has_shortfall is True
    # Total deficit should be tuition (5000) + 2 months rent (~2000) = ~7000
    assert result.target_currency_shortfall_amount >= Decimal("5000.00")
    # Home currency has 0 surplus, so cannot cover
    assert result.cross_currency_remedy is None
    assert result.summary_status == "CRITICAL_DEFICIT"


def test_tuition_deadline_timing():
    """Verify that tuition due outside the horizon window is not counted in obligations."""
    scenario = FullStudentScenario(
        profile=StudentProfileData(study_currency=SupportedCurrency.USD),
        available_balances=[
            AccountBalance(
                account_name="Checking",
                currency=SupportedCurrency.USD,
                actual_balance=Decimal("2000.00"),
                as_of_date=date(2026, 10, 15),
            )
        ],
        expected_income=[],
        monthly_living_expenses=[],
        tuition_obligations=[
            TuitionObligation(
                term="Spring 2027",
                amount_due=Decimal("15000.00"),
                currency=SupportedCurrency.USD,
                due_date=date(2027, 2, 1),  # ~108 days away
            )
        ],
        planned_remittances=[],
    )

    # 30-day horizon: Spring tuition should NOT be included
    res_30 = analyze_funding_gap(scenario, horizon_days=30, as_of_date=date(2026, 10, 15))
    assert len(res_30.obligations) == 0
    assert res_30.target_currency_has_shortfall is False

    # 120-day horizon: Spring tuition MUST be included
    res_120 = analyze_funding_gap(scenario, horizon_days=120, as_of_date=date(2026, 10, 15))
    assert len(res_120.obligations) == 1
    assert res_120.target_currency_has_shortfall is True


def test_missing_data_completeness_scoring():
    """Verify that missing critical data elements lowers completeness score."""
    empty_scenario = FullStudentScenario(
        profile=StudentProfileData(),
        available_balances=[],
        expected_income=[],
        monthly_living_expenses=[],
        tuition_obligations=[],
        planned_remittances=[],
    )

    report = evaluate_data_completeness(empty_scenario)
    assert report.completeness_score == 0.0
    assert len(report.missing_elements) == 4
    assert report.has_verified_actual_balances is False
    assert report.has_tuition_deadline is False

    full_scenario = get_seeded_demo_scenario()
    full_report = evaluate_data_completeness(full_scenario)
    assert full_report.completeness_score == 1.0
    assert len(full_report.missing_elements) == 0


def test_stale_quote_flagging_in_funding_gap():
    """Verify that when a custom stale quote is provided, the analysis reports has_stale_rate_warning=True."""
    scenario = get_seeded_demo_scenario()
    stale_quote = DatedFXQuote(
        base_currency=SupportedCurrency.INR,
        quote_currency=SupportedCurrency.USD,
        rate=Decimal("0.012000"),
        timestamp_utc=datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc),
        source="Ancient Feed",
        provenance=QuoteProvenance.SIMULATED,
        is_stale=True,
        staleness_warning="Quote is 12 days old. Do not settle against this rate.",
    )

    result = analyze_funding_gap(
        scenario,
        horizon_days=90,
        custom_fx_quote=stale_quote,
        as_of_date=date(2026, 10, 15),
    )
    assert result.has_stale_rate_warning is True
    assert len(result.rate_warnings) > 0
    assert "STALE QUOTE" in result.rate_warnings[0]
