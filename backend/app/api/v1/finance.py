from datetime import date
from decimal import Decimal
from fastapi import APIRouter
from app.schemas.overview import FinanceOverviewResponse
from app.schemas.forecast import ForecastRequest, CashFlowForecastResponse
from app.schemas.funding_gap import FundingGapRequest, FundingGapResponse
from app.services.demo_scenario_service import get_seeded_demo_scenario
from app.services.forecast_service import generate_cash_flow_forecast
from app.services.funding_gap_service import analyze_funding_gap

router = APIRouter(prefix="/finance", tags=["Finance & Planning"])


@router.get("/overview", response_model=FinanceOverviewResponse)
def get_finance_overview() -> FinanceOverviewResponse:
    """
    Retrieve executive financial overview for the student.
    Reports separated currency balances, tuition deadlines, upcoming obligations, and runway.
    """
    scenario = get_seeded_demo_scenario()
    ref_date = date(2026, 10, 15)

    balances_by_curr: dict[str, Decimal] = {}
    for bal in scenario.available_balances:
        c = bal.currency.value
        balances_by_curr[c] = balances_by_curr.get(c, Decimal("0.00")) + bal.actual_balance

    tuit = scenario.tuition_obligations[0] if scenario.tuition_obligations else None
    tuit_amt = tuit.amount_due if tuit else Decimal("0.00")
    tuit_date = tuit.due_date if tuit else ref_date
    days_to_tuit = (tuit_date - ref_date).days if tuit else 0

    monthly_burn = sum(e.monthly_amount for e in scenario.monthly_living_expenses)
    study_balance = balances_by_curr.get(scenario.profile.study_currency.value, Decimal("0.00"))

    # Standalone study runway (months of living expense covered by local liquid funds)
    runway = (
        round(study_balance / monthly_burn, 1)
        if monthly_burn > Decimal("0.00")
        else Decimal("0.0")
    )

    # 30-day and 90-day obligations in study currency
    tuit_in_30 = tuit_amt if days_to_tuit <= 30 else Decimal("0.00")
    tuit_in_90 = tuit_amt if days_to_tuit <= 90 else Decimal("0.00")
    ob_30 = tuit_in_30 + monthly_burn
    ob_90 = tuit_in_90 + (monthly_burn * Decimal("3.0"))

    gap_res = analyze_funding_gap(scenario, horizon_days=90, as_of_date=ref_date)
    has_gap = gap_res.target_currency_has_shortfall

    summary_alert = (
        f"Tuition of {tuit_amt} {scenario.profile.study_currency.value} is due in {days_to_tuit} days. "
        + ("Action needed: Study account requires replenishment via remittance." if has_gap else "Funds currently adequate.")
    )

    return FinanceOverviewResponse(
        student_id=scenario.profile.student_id,
        student_name=scenario.profile.full_name,
        home_currency=scenario.profile.home_currency,
        study_currency=scenario.profile.study_currency,
        as_of_date=ref_date,
        balances_by_currency=balances_by_curr,
        tuition_amount_due=tuit_amt,
        tuition_due_date=tuit_date,
        days_until_tuition_due=days_to_tuit,
        obligations_next_30_days_study_currency=ob_30,
        obligations_next_90_days_study_currency=ob_90,
        monthly_living_burn_study_currency=monthly_burn,
        study_currency_standalone_runway_months=Decimal(str(runway)),
        has_imminent_shortfall=days_to_tuit <= 35 and has_gap,
        has_funding_gap=has_gap,
        summary_alert=summary_alert,
    )


@router.post("/forecast", response_model=CashFlowForecastResponse)
def get_cash_flow_forecast(request: ForecastRequest | None = None) -> CashFlowForecastResponse:
    """
    Forecast 90-day multi-currency cash flow timeline.
    Tracks income and expenses by calendar date and currency, distinguishes actual verified balances
    from projected balances, detects deficit shortfalls, and audits data completeness.
    """
    if request is None:
        request = ForecastRequest()

    scenario = request.scenario or get_seeded_demo_scenario()
    return generate_cash_flow_forecast(
        scenario=scenario,
        start_date=request.start_date,
        horizon_days=request.forecast_days,
        safety_reserve_by_currency=request.safety_reserve_by_currency,
    )


@router.post("/funding-gap", response_model=FundingGapResponse)
def get_funding_gap_analysis(request: FundingGapRequest | None = None) -> FundingGapResponse:
    """
    Audit funding gaps across upcoming obligations.
    Preserves multi-currency separation (NEVER silently merges currencies).
    Evaluates cross-currency coverage using dated FX quotes with source provenance and staleness checks.
    """
    if request is None:
        request = FundingGapRequest()

    scenario = request.scenario or get_seeded_demo_scenario()
    return analyze_funding_gap(
        scenario=scenario,
        horizon_days=request.horizon_days,
        stale_quote_threshold_hours=request.stale_quote_threshold_hours,
        custom_fx_quote=request.custom_fx_quote,
    )
