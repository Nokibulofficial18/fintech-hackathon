from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError

from app.schemas.common import SupportedCurrency
from app.schemas.transfers import TransferCompareRequest
from app.schemas.assistant import ToolExecutionResult
from app.services.demo_scenario_service import get_seeded_demo_scenario
from app.services.forecast_service import generate_cash_flow_forecast
from app.services.funding_gap_service import analyze_funding_gap
from app.services.transfer_service import get_transfer_provider_quotes
from app.services.recommendation_service import generate_recommendations


# ==========================================
# Pydantic Tool Argument Schemas
# ==========================================

class EmptyToolArgs(BaseModel):
    """Empty argument model for parameterless tools."""
    pass


class ForecastToolArgs(BaseModel):
    """Validated arguments for the cash-flow forecast tool."""
    horizon_days: int = Field(default=90, ge=1, le=365, description="Forecast horizon in days (1-365)")
    as_of_date: Optional[date] = Field(default=None, description="Optional baseline start date")


class FundingGapToolArgs(BaseModel):
    """Validated arguments for funding-gap analysis tool."""
    horizon_days: int = Field(default=90, ge=1, le=365, description="Evaluation horizon in days (1-365)")
    as_of_date: Optional[date] = Field(default=None, description="Optional baseline start date")


class CompareTransfersToolArgs(BaseModel):
    """Validated arguments for cross-border transfer comparison tool."""
    send_amount: Decimal = Field(..., gt=0, description="Amount to send in home currency (must be positive)")
    send_currency: SupportedCurrency = Field(default=SupportedCurrency.CNY, description="Origin currency")
    receive_currency: SupportedCurrency = Field(default=SupportedCurrency.BDT, description="Target currency")


class SimulateDelayedIncomeToolArgs(BaseModel):
    """Validated arguments for delayed income simulation."""
    delay_days: int = Field(default=14, ge=1, le=120, description="Number of days the income disbursement is delayed")
    income_source_keyword: str = Field(default="Scholarship", description="Keyword matching the income source to delay")


# ==========================================
# Tool Execution Registry
# ==========================================

APPROVED_TOOLS: Dict[str, Dict[str, Any]] = {}


def register_tool(name: str, description: str, args_schema: type[BaseModel]):
    """Decorator registering an approved deterministic financial tool."""
    def decorator(fn: Callable[..., Dict[str, Any]]):
        APPROVED_TOOLS[name] = {
            "name": name,
            "description": description,
            "args_schema": args_schema,
            "fn": fn,
        }
        return fn
    return decorator


@register_tool(
    name="get_student_overview",
    description="Retrieve verified liquid balances by currency, tuition amount & deadline, monthly living burn, and local runway.",
    args_schema=EmptyToolArgs,
)
def execute_get_student_overview(args: EmptyToolArgs) -> Dict[str, Any]:
    scenario = get_seeded_demo_scenario()
    ref_date = date(2026, 10, 15)

    balances = {b.currency.value: float(b.actual_balance) for b in scenario.available_balances}
    tuit = scenario.tuition_obligations[0] if scenario.tuition_obligations else None
    tuit_amt = float(tuit.amount_due) if tuit else 0.0
    tuit_date = tuit.due_date.isoformat() if tuit else ref_date.isoformat()
    days_to_tuit = (tuit.due_date - ref_date).days if tuit else 0

    monthly_burn = float(sum(e.monthly_amount for e in scenario.monthly_living_expenses))
    study_bal = balances.get(scenario.profile.study_currency.value, 0.0)
    runway = round(study_bal / monthly_burn, 1) if monthly_burn > 0 else 0.0

    return {
        "student_name": scenario.profile.full_name,
        "home_country": scenario.profile.home_country,
        "study_country": scenario.profile.study_country,
        "home_currency": scenario.profile.home_currency.value,
        "study_currency": scenario.profile.study_currency.value,
        "verified_balances": balances,
        "tuition_amount_due": tuit_amt,
        "tuition_due_date": tuit_date,
        "days_until_tuition_due": days_to_tuit,
        "monthly_living_burn": monthly_burn,
        "study_currency_runway_months": runway,
    }


@register_tool(
    name="calculate_forecast",
    description="Calculate 90-day daily cash-flow trajectory, total inflows/outflows, and detect projected deficit shortfalls.",
    args_schema=ForecastToolArgs,
)
def execute_calculate_forecast(args: ForecastToolArgs) -> Dict[str, Any]:
    scenario = get_seeded_demo_scenario()
    res = generate_cash_flow_forecast(
        scenario=scenario,
        start_date=args.as_of_date or date(2026, 10, 15),
        horizon_days=args.horizon_days,
    )

    shortfalls_summary = [
        {
            "shortfall_date": s.shortfall_date.isoformat(),
            "currency": s.currency.value,
            "shortfall_amount": float(s.shortfall_amount),
            "trigger_event": s.trigger_event,
            "urgency": s.urgency,
        }
        for s in res.shortfalls
    ]

    return {
        "horizon_days": res.horizon_days,
        "forecast_start_date": res.forecast_start_date.isoformat(),
        "forecast_end_date": res.forecast_end_date.isoformat(),
        "initial_actual_balances": {k: float(v) for k, v in res.initial_actual_balances.items()},
        "projected_end_balances": {k: float(v) for k, v in res.projected_end_balances.items()},
        "total_inflows": {k: float(v) for k, v in res.total_inflows_by_currency.items()},
        "total_outflows": {k: float(v) for k, v in res.total_outflows_by_currency.items()},
        "shortfalls_count": len(res.shortfalls),
        "shortfalls": shortfalls_summary,
        "completeness_score": res.data_completeness.completeness_score,
    }


@register_tool(
    name="calculate_funding_gap",
    description="Audit multi-currency obligations against available resources. Evaluates cross-currency conversion feasibility without silently merging currencies.",
    args_schema=FundingGapToolArgs,
)
def execute_calculate_funding_gap(args: FundingGapToolArgs) -> Dict[str, Any]:
    scenario = get_seeded_demo_scenario()
    gap_res = analyze_funding_gap(
        scenario=scenario,
        horizon_days=args.horizon_days,
        as_of_date=args.as_of_date or date(2026, 10, 15),
    )

    positions_summary = {}
    for c_code, pos in gap_res.currency_positions.items():
        positions_summary[c_code] = {
            "actual_liquid_balance": float(pos.actual_liquid_balance),
            "expected_inflows": float(pos.expected_inflows),
            "total_obligations": float(pos.total_obligations),
            "net_position": float(pos.net_position),
            "has_direct_gap": pos.has_direct_gap,
            "direct_gap_amount": float(pos.direct_gap_amount),
        }

    remedy_summary = None
    if gap_res.cross_currency_remedy:
        r = gap_res.cross_currency_remedy
        remedy_summary = {
            "source_currency": r.source_currency.value,
            "target_currency": r.target_currency.value,
            "available_surplus": float(r.available_surplus_in_source),
            "benchmark_rate": float(r.dated_fx_quote.rate),
            "quote_timestamp": r.dated_fx_quote.timestamp_utc.isoformat(),
            "is_quote_stale": r.dated_fx_quote.is_stale,
            "estimated_fee": float(r.estimated_provider_fee),
            "net_convertible_study": float(r.net_convertible_in_target),
            "can_cover_full_gap": r.can_cover_full_gap,
            "remaining_gap": float(r.remaining_gap_after_conversion),
        }

    return {
        "analysis_date": gap_res.analysis_date.isoformat(),
        "horizon_days": gap_res.horizon_days,
        "study_currency": gap_res.study_currency.value,
        "home_currency": gap_res.home_currency.value,
        "target_currency_has_shortfall": gap_res.target_currency_has_shortfall,
        "target_currency_shortfall_amount": float(gap_res.target_currency_shortfall_amount),
        "currency_positions": positions_summary,
        "cross_currency_remedy": remedy_summary,
        "summary_status": gap_res.summary_status,
        "has_stale_rate_warning": gap_res.has_stale_rate_warning,
    }


@register_tool(
    name="compare_transfers",
    description="Compare real wire bank benchmarks vs. digital FX specialists on sending amount and currency pair. Shows fee breakdown, net recipient proceeds, and delivery times.",
    args_schema=CompareTransfersToolArgs,
)
def execute_compare_transfers(args: CompareTransfersToolArgs) -> Dict[str, Any]:
    req = TransferCompareRequest(
        send_amount=args.send_amount,
        send_currency=args.send_currency,
        receive_currency=args.receive_currency,
    )
    quotes_res = get_transfer_provider_quotes(req)

    quotes_list = [
        {
            "provider_name": q.provider_name,
            "provider_type": q.provider_type,
            "provenance": q.quote_provenance.value,
            "offered_rate": float(q.offered_exchange_rate),
            "upfront_fee": float(q.upfront_transfer_fee),
            "fx_markup_pct": float(q.fx_markup_percentage),
            "fx_markup_amount": float(q.fx_markup_amount),
            "total_fee_cost": float(q.total_fee_cost),
            "recipient_amount": float(q.recipient_amount_receive_currency),
            "delivery_time": q.estimated_delivery_time,
        }
        for q in quotes_res.quotes
    ]

    return {
        "send_amount": float(quotes_res.send_amount),
        "send_currency": quotes_res.send_currency.value,
        "receive_currency": quotes_res.receive_currency.value,
        "mid_market_rate": float(quotes_res.mid_market_rate),
        "recommended_cheapest": quotes_res.recommended_cheapest,
        "recommended_fastest": quotes_res.recommended_fastest,
        "potential_savings_vs_bank": float(quotes_res.potential_savings_vs_bank),
        "quotes": quotes_list,
    }


@register_tool(
    name="simulate_delayed_income",
    description="Simulate the cash-flow impact if expected income (e.g. scholarship or stipend) arrives late by N days.",
    args_schema=SimulateDelayedIncomeToolArgs,
)
def execute_simulate_delayed_income(args: SimulateDelayedIncomeToolArgs) -> Dict[str, Any]:
    scenario = get_seeded_demo_scenario()
    base_date = date(2026, 10, 15)

    # Delay the targeted income event
    modified_income = []
    delayed_item_name = ""
    original_date = ""
    new_date = ""
    delayed_amount = 0.0

    for inc in scenario.expected_income:
        if args.income_source_keyword.lower() in inc.source_name.lower() and not delayed_item_name:
            delayed_item_name = inc.source_name
            original_date = inc.expected_date.isoformat()
            delayed_dt = inc.expected_date + timedelta(days=args.delay_days)
            new_date = delayed_dt.isoformat()
            delayed_amount = float(inc.amount)
            # Create delayed copy
            mod_inc = inc.model_copy(update={"expected_date": delayed_dt})
            modified_income.append(mod_inc)
        else:
            modified_income.append(inc)

    modified_scenario = scenario.model_copy(update={"expected_income": modified_income})

    # Run forecast with delayed income
    delayed_forecast = generate_cash_flow_forecast(
        scenario=modified_scenario,
        start_date=base_date,
        horizon_days=90,
    )

    baseline_forecast = generate_cash_flow_forecast(
        scenario=scenario,
        start_date=base_date,
        horizon_days=90,
    )

    return {
        "simulation": f"Income delay of {args.delay_days} days for {delayed_item_name or 'Income'}",
        "delayed_income_source": delayed_item_name or "Not Found",
        "delayed_amount": delayed_amount,
        "original_date": original_date,
        "new_disbursement_date": new_date,
        "baseline_shortfalls_count": len(baseline_forecast.shortfalls),
        "delayed_scenario_shortfalls_count": len(delayed_forecast.shortfalls),
        "new_shortfalls": [
            {
                "date": s.shortfall_date.isoformat(),
                "currency": s.currency.value,
                "shortfall_amount": float(s.shortfall_amount),
                "trigger_event": s.trigger_event,
            }
            for s in delayed_forecast.shortfalls
        ],
        "impact_summary": (
            f"Delaying {delayed_item_name} by {args.delay_days} days moves funds past the Nov 15 tuition deadline, "
            f"increasing liquidity pressure before cross-border remittances arrive."
            if new_date > "2026-11-15"
            else f"Funds still arrive before the Nov 15 deadline on {new_date}."
        ),
    }


@register_tool(
    name="get_action_recommendations",
    description="Retrieve deterministic prioritized action items derived from current tuition obligations, gap analysis, and burn runway.",
    args_schema=EmptyToolArgs,
)
def execute_get_action_recommendations(args: EmptyToolArgs) -> Dict[str, Any]:
    scenario = get_seeded_demo_scenario()
    recs_res = generate_recommendations(scenario, reference_date=date(2026, 10, 15))

    return {
        "total_recommendations": recs_res.total_recommendations,
        "critical_count": recs_res.critical_count,
        "high_count": recs_res.high_count,
        "recommendations": [
            {
                "id": r.id,
                "priority": r.priority.value,
                "urgency": r.urgency.value,
                "category": r.category.value,
                "title": r.title,
                "reason": r.reason,
                "supporting_numbers": r.supporting_numbers,
                "assumptions": r.assumptions,
                "uncertainty": r.uncertainty,
                "suggested_action": r.suggested_action,
            }
            for r in recs_res.recommendations
        ],
        "disclaimer": recs_res.compliance_disclaimer,
    }


# ==========================================
# Dispatcher with Pydantic Validation
# ==========================================

def dispatch_tool(tool_name: str, raw_arguments: Dict[str, Any]) -> ToolExecutionResult:
    """
    Safely validate and execute an approved deterministic financial tool.
    Strictly prevents unauthorized commands, SQL injection, or unvalidated parameters.
    """
    now_utc = datetime.now(timezone.utc)

    if tool_name not in APPROVED_TOOLS:
        return ToolExecutionResult(
            tool_name=tool_name,
            arguments=raw_arguments,
            output={"error": f"Tool '{tool_name}' is not in the approved financial tool catalog."},
            timestamp_utc=now_utc,
            execution_status="FAILED_VALIDATION",
        )

    tool_def = APPROVED_TOOLS[tool_name]
    args_schema = tool_def["args_schema"]
    fn = tool_def["fn"]

    try:
        validated_args = args_schema(**raw_arguments)
    except ValidationError as val_err:
        return ToolExecutionResult(
            tool_name=tool_name,
            arguments=raw_arguments,
            output={"validation_error": str(val_err)},
            timestamp_utc=now_utc,
            execution_status="FAILED_VALIDATION",
        )
    except Exception as exc:
        return ToolExecutionResult(
            tool_name=tool_name,
            arguments=raw_arguments,
            output={"argument_error": str(exc)},
            timestamp_utc=now_utc,
            execution_status="FAILED_VALIDATION",
        )

    try:
        output_data = fn(validated_args)
        return ToolExecutionResult(
            tool_name=tool_name,
            arguments=raw_arguments,
            output=output_data,
            timestamp_utc=now_utc,
            execution_status="SUCCESS",
        )
    except Exception as exec_err:
        return ToolExecutionResult(
            tool_name=tool_name,
            arguments=raw_arguments,
            output={"execution_error": str(exec_err)},
            timestamp_utc=now_utc,
            execution_status="FAILED_VALIDATION",
        )
